"""Separate, disabled-by-default CT8 Worker-authenticated review candidate.

The Worker owns GitHub login. This process only trusts a bounded, signed,
one-use assertion, never a browser cookie or a forwarded identity header.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import hashlib
import hmac
import json
import os
import re
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from cat_treaty.api import _normalize_json_value
from cat_treaty.ct6_hours import CT6HoursContractBlockedError
from cat_treaty.ct6_models import CatalogueRunRequest, HoursRunRequest
from cat_treaty.ct6_responses import project_catalogue_success, project_hours_success
from cat_treaty.ct8_executor import CT8ExecutionFailure, CT8ExecutionTimeout, run_isolated
from cat_treaty.pilot_observability import record
from cat_treaty.pilot_policy import PilotLimits, PilotLimitExceeded
from cat_treaty.simulation import CT4PreflightError

PREFIX = "/api/pilot/v1"
EMPTY_DIGEST = hashlib.sha256(b"").hexdigest()
HOST = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")
HEX = re.compile(r"[0-9a-f]{64}")
NONCE = re.compile(r"[A-Za-z0-9_-]{32}")
ID = re.compile(r"[1-9][0-9]{0,19}")
MAX_ASSERTION_SKEW = 15
MAX_NONCES = 2048


def _problem(status: int, code: str, request_id: str) -> JSONResponse:
    record(mode="pilot", outcome=code, include_resource=False)
    return JSONResponse({"type": "about:blank", "title": "Pilot request unavailable",
        "status": status, "code": code, "detail": "Pilot request unavailable",
        "request_id": request_id, "instance": PREFIX + "/runs", "errors": []},
        status_code=status, headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})


def create_nocard_app(*, config: dict[str, str] | None = None) -> FastAPI:
    env = os.environ if config is None else config
    if (env.get("CT8_NOCARD_ENABLED") != "true" or env.get("CT8_PILOT_ENABLED") != "false"
            or env.get("CT8_MEASURE_ENABLED") != "false"):
        raise ValueError("no-card pilot disabled or another CT8 entrypoint enabled")
    host = env.get("CT8_NOCARD_API_HOST", "")
    public = env.get("CT8_NOCARD_PUBLIC_HOST", "")
    if not HOST.fullmatch(host) or not HOST.fullmatch(public) or host == public:
        raise ValueError("two exact pilot hostnames required")
    keys = {"current": env.get("CT8_NOCARD_ASSERTION_KEY", "")}
    previous = env.get("CT8_NOCARD_ASSERTION_PREVIOUS", "")
    if previous:
        keys["previous"] = previous
    if any(not 43 <= len(key) <= 256 or any(not 33 <= ord(c) <= 126 for c in key)
           for key in keys.values()):
        raise ValueError("high entropy assertion key required")
    allowed_raw = env.get("CT8_NOCARD_ID_ALLOWLIST", "")
    allowed = set(allowed_raw.split(","))
    if not allowed or any(not ID.fullmatch(uid) for uid in allowed) or len(allowed) > 25:
        raise ValueError("numeric tester allowlist required")
    limits = PilotLimits.from_json(env.get("CT8_NOCARD_LIMITS_JSON", ""))
    try:
        deadline = int(env["CT8_NOCARD_DEADLINE_SECONDS"])
        result_limit = int(env["CT8_NOCARD_RESULT_BYTES"])
    except (KeyError, ValueError) as error:
        raise ValueError("explicit deadline and pilot result budget required") from error
    if not 1 <= deadline <= 30 or not 1_000_000 <= result_limit <= 16 * 1024 * 1024:
        raise ValueError("invalid unmeasured pilot deadline/result ceiling")

    app = FastAPI(title="CT8 no-card private review candidate", docs_url=None,
                  redoc_url=None, openapi_url=None)
    active = threading.BoundedSemaphore(1)
    lock = threading.Lock()
    seen: dict[str, float] = {}
    activity: dict[str, deque[float]] = defaultdict(deque)

    def verified(request: Request, path: str, method: str, digest: str) -> str | None:
        if request.headers.get("host") != host:
            return None
        headers = request.headers
        kid = headers.get("X-CT8-Assertion-Key", "")
        uid = headers.get("X-CT8-Assertion-ID", "")
        nonce = headers.get("X-CT8-Assertion-Nonce", "")
        timestamp = headers.get("X-CT8-Assertion-Time", "")
        signature = headers.get("X-CT8-Assertion-Signature", "")
        claimed_digest = headers.get("X-CT8-Assertion-Digest", "")
        if (kid not in keys or uid not in allowed or not ID.fullmatch(uid) or
                not NONCE.fullmatch(nonce) or not HEX.fullmatch(signature) or
                not HEX.fullmatch(claimed_digest) or claimed_digest != digest or
                not re.fullmatch(r"[0-9]{10}", timestamp)):
            return None
        now = time.time()
        if abs(now - int(timestamp)) > MAX_ASSERTION_SKEW:
            return None
        message = "\n".join(("ct8.1", kid, method, path, host, public, uid,
                             claimed_digest, timestamp, nonce)).encode("ascii")
        expected = hmac.new(keys[kid].encode("ascii"), message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return None
        # One instance/worker only. This cache is deliberately bounded; a
        # restart may forget a nonce within the narrow assertion skew.
        with lock:
            for old, expiry in list(seen.items()):
                if expiry <= now:
                    del seen[old]
            if nonce in seen or len(seen) >= MAX_NONCES:
                return None
            seen[nonce] = now + 2 * MAX_ASSERTION_SKEW
        return uid

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request):
        if request.headers.get("host") != host:
            return _problem(404, "CT8_PRIVATE_ROUTE", str(uuid4()))
        return {"status": "ready", "mode": "private-review"}

    @app.get(PREFIX + "/capabilities", include_in_schema=False)
    async def capabilities(request: Request):
        if verified(request, PREFIX + "/capabilities", "GET", EMPTY_DIGEST) is None:
            return _problem(401, "CT8_PRIVATE_AUTH", str(uuid4()))
        return JSONResponse({"mode": "invited-test", "limits": {
            "max_body_bytes": limits.max_body_bytes, "max_trials": limits.max_trials,
            "max_occurrences": limits.max_occurrences, "max_layers": limits.max_layers,
            "max_hours_components": limits.max_hours_components,
            "allow_full_detail": limits.allow_full_detail}}, headers={"Cache-Control": "no-store"})

    async def execute(mode: str, request: Request):
        started = time.monotonic()
        request_id = str(uuid4())
        path = PREFIX + "/runs/" + mode
        claimed_digest = request.headers.get("X-CT8-Assertion-Digest", "")
        uid = verified(request, path, "POST", claimed_digest)
        if uid is None:
            return _problem(401, "CT8_PRIVATE_AUTH", request_id)
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return _problem(400, "CT8_PILOT_INPUT", request_id)
        length = request.headers.get("content-length", "")
        if length and (not length.isdecimal() or int(length) > limits.max_body_bytes):
            return _problem(413, "CT8_PILOT_LIMIT", request_id)
        with lock:
            now = time.monotonic()
            queue = activity[uid]
            while queue and now - queue[0] >= 60:
                queue.popleft()
            if len(queue) >= limits.max_requests_per_minute:
                return _problem(429, "CT8_PILOT_BUSY", request_id)
            queue.append(now)
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > limits.max_body_bytes:
                return _problem(413, "CT8_PILOT_LIMIT", request_id)
            raw.extend(chunk)
        if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), claimed_digest):
            return _problem(401, "CT8_PRIVATE_AUTH", request_id)
        try:
            data = json.loads(raw)
            limits.check(mode, data)
            model = CatalogueRunRequest if mode == "catalogue" else HoursRunRequest
            body = model.model_validate(_normalize_json_value(model, data))
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValidationError, TypeError, ValueError) as error:
            return _problem(413 if isinstance(error, PilotLimitExceeded) else 422,
                            "CT8_PILOT_LIMIT" if isinstance(error, PilotLimitExceeded) else "CT8_PILOT_INPUT", request_id)
        if not active.acquire(blocking=False):
            return _problem(503, "CT8_PILOT_BUSY", request_id)

        def isolated():
            try:
                return run_isolated(mode, body, deadline_seconds=deadline,
                                    max_result_bytes=result_limit)
            finally:
                active.release()

        try:
            task = asyncio.create_task(asyncio.to_thread(isolated))
            try:
                result = await asyncio.shield(task)
            except asyncio.CancelledError:
                task.add_done_callback(lambda finished: finished.exception() if not finished.cancelled() else None)
                raise
            projected = (project_catalogue_success(result, request_id=request_id)
                         if mode == "catalogue" else project_hours_success(result, request_id=request_id))
            response = JSONResponse(projected.model_dump(mode="json"),
                                    headers={"X-Request-ID": request_id, "Cache-Control": "no-store"})
            if len(response.body) > result_limit:
                return _problem(500, "CT8_PILOT_FAILURE", request_id)
            record(mode=mode, outcome="complete", elapsed_ms=int((time.monotonic()-started)*1000),
                   request_bytes=len(raw), response_bytes=len(response.body))
            return response
        except (CT4PreflightError, CT6HoursContractBlockedError):
            return _problem(422, "CT8_PILOT_CONTRACT", request_id)
        except CT8ExecutionTimeout:
            record(mode=mode, outcome="deadline", elapsed_ms=int((time.monotonic()-started)*1000))
            return _problem(500, "CT8_PILOT_FAILURE", request_id)
        except CT8ExecutionFailure:
            record(mode=mode, outcome="child_failure", elapsed_ms=int((time.monotonic()-started)*1000))
            return _problem(500, "CT8_PILOT_FAILURE", request_id)
        except Exception:
            record(mode=mode, outcome="internal_failure", elapsed_ms=int((time.monotonic()-started)*1000))
            return _problem(500, "CT8_PILOT_FAILURE", request_id)

    @app.post(PREFIX + "/runs/catalogue", include_in_schema=False)
    async def catalogue(request: Request):
        return await execute("catalogue", request)

    @app.post(PREFIX + "/runs/hours-clause", include_in_schema=False)
    async def hours(request: Request):
        return await execute("hours-clause", request)

    return app
