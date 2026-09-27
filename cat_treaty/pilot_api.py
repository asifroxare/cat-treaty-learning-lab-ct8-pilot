"""Separate opt-in, invited-test API. Never mount the unrestricted CT6 app."""
from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import hmac
import json
import os
import re
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from cat_treaty.api import _normalize_json_value
from cat_treaty.ct6_hours import CT6HoursContractBlockedError
from cat_treaty.ct6_models import CatalogueRunRequest, HoursRunRequest
from cat_treaty.ct6_responses import project_catalogue_success, project_hours_success
from cat_treaty.ct8_executor import CT8ExecutionFailure, CT8ExecutionTimeout, run_isolated
from cat_treaty.pilot_auth import AccessVerifier, PilotUnauthorized
from cat_treaty.pilot_policy import PilotLimits, PilotLimitExceeded
from cat_treaty.simulation import CT4PreflightError


def _response(status: int, code: str, request_id: str) -> JSONResponse:
    titles = {
        "CT8_PILOT_AUTH": "Pilot authentication required",
        "CT8_PILOT_INPUT": "Pilot input invalid",
        "CT8_PILOT_LIMIT": "Outside pilot test limits",
        "CT8_PILOT_BUSY": "Pilot currently busy",
        "CT8_PILOT_FAILURE": "Pilot request failed",
        "CT8_PILOT_CONTRACT": "Pilot contract blocked",
    }
    return JSONResponse({"type": "about:blank", "title": titles[code], "status": status,
        "code": code, "detail": titles[code], "request_id": request_id,
        "instance": "/api/pilot/v1/runs", "errors": []}, status_code=status,
        headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})


def create_pilot_app(*, config: dict[str, str] | None = None, verifier: AccessVerifier | None = None) -> FastAPI:
    """Refuse to start without explicit pilot-only deployment configuration."""
    env = os.environ if config is None else config
    if env.get("CT8_PILOT_ENABLED") != "true":
        raise ValueError("pilot entrypoint disabled")
    host = env.get("CT8_PILOT_API_HOST", "")
    origin = env.get("CT8_PILOT_UI_ORIGIN", "")
    domain = r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
    if not re.fullmatch(domain, host) or not re.fullmatch(rf"https://{domain}", origin):
        raise ValueError("exact HTTPS pilot host and UI origin required")
    limits = PilotLimits.from_json(env.get("CT8_PILOT_LIMITS_JSON", ""))
    try:
        deadline = int(env["CT8_PILOT_DEADLINE_SECONDS"])
    except (KeyError, ValueError) as error:
        raise ValueError("explicit pilot deadline required") from error
    if not 1 <= deadline <= 90:
        raise ValueError("invalid pilot deadline")
    origin_proof = env.get("CT8_PILOT_ORIGIN_SECRET", "")
    if len(origin_proof) < 32 or len(origin_proof) > 256 or any(ord(char) < 33 or ord(char) > 126 for char in origin_proof):
        raise ValueError("independent high-entropy origin proof required")
    auth = verifier or AccessVerifier(team=env.get("CT8_PILOT_ACCESS_TEAM", ""),
        audience=env.get("CT8_PILOT_ACCESS_AUDIENCE", ""),
        allowed_emails=tuple(env.get("CT8_PILOT_EMAIL_ALLOWLIST", "").split(",")))
    app = FastAPI(title="EdInsured CT8 invited test pilot", docs_url=None,
        redoc_url=None, openapi_url=None)
    app.add_middleware(CORSMiddleware, allow_origins=[origin], allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"], allow_credentials=True)
    active = threading.BoundedSemaphore(1)
    rate_lock = threading.Lock()
    activity: dict[str, deque[float]] = defaultdict(deque)

    def permitted(email: str) -> bool:
        with rate_lock:
            now = time.monotonic()
            queue = activity[email]
            while queue and now - queue[0] >= 60:
                queue.popleft()
            if len(queue) >= limits.max_requests_per_minute:
                return False
            queue.append(now)
            return True

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request):
        if request.headers.get("host") != host:
            return _response(404, "CT8_PILOT_INPUT", str(uuid4()))
        return {"status": "ready", "pilot": True}

    def has_origin_proof(request: Request) -> bool:
        supplied_proof = request.headers.get("X-CT8-Pilot-Origin", "")
        return len(supplied_proof) <= 256 and hmac.compare_digest(supplied_proof, origin_proof)

    async def authenticated(request: Request) -> str | None:
        if not has_origin_proof(request):
            return None
        try:
            # JWKS refresh and signature verification must not block health
            # or the single Uvicorn event loop on a cold Free instance.
            return await asyncio.to_thread(auth.verify, request.headers.get("Cf-Access-Jwt-Assertion", ""))
        except PilotUnauthorized:
            return None

    @app.get("/api/pilot/v1/capabilities", include_in_schema=False)
    async def capabilities(request: Request):
        request_id = str(uuid4())
        if request.headers.get("host") != host:
            return _response(404, "CT8_PILOT_INPUT", request_id)
        if await authenticated(request) is None:
            return _response(401, "CT8_PILOT_AUTH", request_id)
        return JSONResponse({"mode": "invited-test", "limits": {
            "max_body_bytes": limits.max_body_bytes, "max_trials": limits.max_trials,
            "max_occurrences": limits.max_occurrences, "max_layers": limits.max_layers,
            "max_hours_components": limits.max_hours_components,
            "allow_full_detail": limits.allow_full_detail,
        }}, headers={"Cache-Control": "no-store"})

    async def execute(mode: str, request: Request) -> JSONResponse:
        request_id = str(uuid4())
        if request.headers.get("host") != host:
            return _response(404, "CT8_PILOT_INPUT", request_id)
        # Cloudflare Access at the edge is insufficient: always verify at API.
        email = await authenticated(request)
        if email is None:
            return _response(401, "CT8_PILOT_AUTH", request_id)
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return _response(400, "CT8_PILOT_INPUT", request_id)
        length = request.headers.get("content-length", "")
        if length:
            if not length.isdecimal():
                return _response(400, "CT8_PILOT_INPUT", request_id)
            if int(length) > limits.max_body_bytes:
                return _response(413, "CT8_PILOT_LIMIT", request_id)
        if not permitted(email):
            return _response(429, "CT8_PILOT_BUSY", request_id)
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > limits.max_body_bytes:
                return _response(413, "CT8_PILOT_LIMIT", request_id)
            raw.extend(chunk)
        try:
            data = json.loads(raw.decode("utf-8"))
            limits.check(mode, data)
            model = CatalogueRunRequest if mode == "catalogue" else HoursRunRequest
            body = model.model_validate(_normalize_json_value(model, data))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValidationError, TypeError, ValueError) as error:
            return _response(413 if isinstance(error, PilotLimitExceeded) else 422,
                "CT8_PILOT_LIMIT" if isinstance(error, PilotLimitExceeded) else "CT8_PILOT_INPUT", request_id)

        # Acquire before creating a thread; hundreds of authenticated callers
        # cannot create hundreds of waiting thread-pool jobs on a Free host.
        if not active.acquire(blocking=False):
            return _response(503, "CT8_PILOT_BUSY", request_id)

        def isolated():
            try:
                return run_isolated(mode, body, deadline_seconds=deadline)
            finally:
                active.release()
        try:
            task = asyncio.create_task(asyncio.to_thread(isolated))
            try:
                result = await asyncio.shield(task)
            except asyncio.CancelledError:
                # Keep the slot occupied until the calculation is actually
                # stopped, even if a browser tab closes mid-request.
                task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)
                raise
            projected = (project_catalogue_success(result, request_id=request_id)
                         if mode == "catalogue" else project_hours_success(result, request_id=request_id))
            return JSONResponse(projected.model_dump(mode="json"),
                headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})
        except CT8ExecutionFailure:
            return _response(500, "CT8_PILOT_FAILURE", request_id)
        except (CT4PreflightError, CT6HoursContractBlockedError):
            return _response(422, "CT8_PILOT_CONTRACT", request_id)
        except Exception:
            return _response(500, "CT8_PILOT_FAILURE", request_id)

    @app.post("/api/pilot/v1/runs/catalogue", include_in_schema=False)
    async def catalogue(request: Request):
        return await execute("catalogue", request)

    @app.post("/api/pilot/v1/runs/hours-clause", include_in_schema=False)
    async def hours(request: Request):
        return await execute("hours-clause", request)

    return app


# Start with `uvicorn --factory cat_treaty.pilot_api:create_pilot_app` only;
# missing pilot configuration causes startup to fail, never a default app.
