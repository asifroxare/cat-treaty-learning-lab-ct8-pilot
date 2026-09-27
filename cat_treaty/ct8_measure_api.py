"""Owner-only, no-card CT8 capacity measurement; never mount full CT6 API."""
from __future__ import annotations

import asyncio
from collections import deque
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from cat_treaty.api import _normalize_json_value
from cat_treaty.ct6_models import CatalogueRunRequest, HoursRunRequest
from cat_treaty.ct6_responses import project_catalogue_success, project_hours_success
from cat_treaty.ct8_executor import run_isolated
from cat_treaty.pilot_observability import record


FIXTURES = Path(__file__).resolve().parents[1] / "deployment" / "fixtures" / "ct7"
BODY_LIMIT = 4096
CHALLENGE_SECONDS = 20
PATH = "/api/ct8-measure/v1"
HOST_RE = re.compile(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}")


def _error(status: int, category: str):
    record(mode="pilot", outcome=category, include_resource=False)
    return JSONResponse({"status": status, "code": category}, status_code=status,
                        headers={"Cache-Control": "no-store"})


def _fixture_digests(root: Path) -> dict[str, str]:
    manifest = json.loads((root / "baseline-candidates.json").read_text(encoding="utf-8"))
    if manifest.get("source_commit") != "2a45727b9621a860ee074d6b14172b65fd836ad3":
        raise ValueError("frozen CT7 fixture identity required")
    entries = manifest.get("fixtures")
    if not isinstance(entries, list) or len(entries) != 2 or {x.get("route") for x in entries} != {"catalogue", "hours-clause"}:
        raise ValueError("exact CT7 fixture pair required")
    result = {}
    for entry in entries:
        mode = entry["route"]
        if entry.get("request_file") != f"approved-{mode}.json":
            raise ValueError("unexpected fixture path")
        raw = (root / entry["request_file"]).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if len(raw) > BODY_LIMIT or digest != entry.get("request_sha256"):
            raise ValueError("frozen CT7 fixture digest mismatch")
        result[mode] = digest
    return result


def create_measure_app(*, config: dict[str, str] | None = None) -> FastAPI:
    env = os.environ if config is None else config
    if env.get("CT8_MEASURE_ENABLED") != "true" or env.get("CT8_PILOT_ENABLED") != "false":
        raise ValueError("CT8 measurement disabled or pilot enabled")
    host = env.get("CT8_MEASURE_HOST", "")
    secret = env.get("CT8_MEASURE_SECRET", "")
    if not HOST_RE.fullmatch(host) or not 43 <= len(secret) <= 256 or any(ord(c) < 33 or ord(c) > 126 for c in secret):
        raise ValueError("exact host and private high-entropy probe secret required")
    expected = _fixture_digests(FIXTURES)
    secret_bytes = secret.encode("ascii")
    app = FastAPI(title="CT8 owner capacity measurement", docs_url=None, redoc_url=None, openapi_url=None)
    active = threading.BoundedSemaphore(1)
    lock = threading.Lock()
    pending: dict[str, float] = {}
    challenges: deque[float] = deque()

    def same_host(request: Request) -> bool:
        return request.headers.get("host") == host

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request):
        return {"status": "ready", "mode": "owner-capacity-measurement"} if same_host(request) else _error(404, "CT8_PROBE_ROUTE")

    @app.get(PATH + "/challenge", include_in_schema=False)
    async def challenge(request: Request):
        if not same_host(request):
            return _error(404, "CT8_PROBE_ROUTE")
        now = time.monotonic()
        with lock:
            while challenges and now - challenges[0] >= 60:
                challenges.popleft()
            if len(challenges) >= 6:
                return _error(429, "CT8_PROBE_RATE")
            challenges.append(now)
            for nonce, expiry in list(pending.items()):
                if expiry <= now:
                    del pending[nonce]
            nonce = secrets.token_urlsafe(24)
            pending[nonce] = now + CHALLENGE_SECONDS
        return JSONResponse({"nonce": nonce, "expires_in_seconds": CHALLENGE_SECONDS},
                            headers={"Cache-Control": "no-store"})

    async def execute(mode: str, request: Request):
        started = time.monotonic()
        if not same_host(request):
            return _error(404, "CT8_PROBE_ROUTE")
        nonce = request.headers.get("X-CT8-Probe-Nonce", "")
        signature = request.headers.get("X-CT8-Probe-Signature", "")
        digest = request.headers.get("X-CT8-Probe-Body-SHA256", "")
        if (not re.fullmatch("[A-Za-z0-9_-]{32}", nonce) or
                not re.fullmatch("[0-9a-f]{64}", signature) or
                digest != expected[mode]):
            return _error(401, "CT8_PROBE_AUTH")
        message = f"{nonce}\n{mode}\n{digest}".encode("ascii")
        candidate = hmac.new(secret_bytes, message, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(candidate, signature):
            return _error(401, "CT8_PROBE_AUTH")
        with lock:
            expiry = pending.pop(nonce, None)  # consume once, before reading any body
        if expiry is None or expiry <= time.monotonic():
            return _error(401, "CT8_PROBE_AUTH")
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            return _error(400, "CT8_PROBE_INPUT")
        length = request.headers.get("content-length", "")
        if length and (not length.isdecimal() or int(length) > BODY_LIMIT):
            return _error(413, "CT8_PROBE_LIMIT")
        raw = bytearray()
        async for chunk in request.stream():
            if len(raw) + len(chunk) > BODY_LIMIT:
                return _error(413, "CT8_PROBE_LIMIT")
            raw.extend(chunk)
        if not hmac.compare_digest(hashlib.sha256(raw).hexdigest(), digest):
            return _error(422, "CT8_PROBE_FIXTURE")
        try:
            data = json.loads(raw)
            model = CatalogueRunRequest if mode == "catalogue" else HoursRunRequest
            body = model.model_validate(_normalize_json_value(model, data))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError, ValidationError, RecursionError):
            return _error(422, "CT8_PROBE_FIXTURE")
        if not active.acquire(blocking=False):
            return _error(503, "CT8_PROBE_BUSY")

        def compute():
            try:
                return run_isolated(mode, body, deadline_seconds=30)
            finally:
                active.release()
        try:
            task = asyncio.create_task(asyncio.to_thread(compute))
            try:
                result = await asyncio.shield(task)
            except asyncio.CancelledError:
                task.add_done_callback(lambda completed: completed.exception() if not completed.cancelled() else None)
                raise
            request_id = str(uuid4())
            projected = (project_catalogue_success(result, request_id=request_id)
                         if mode == "catalogue" else project_hours_success(result, request_id=request_id))
            response = JSONResponse(projected.model_dump(mode="json"), headers={"Cache-Control": "no-store"})
            record(mode=mode, outcome="complete", elapsed_ms=int((time.monotonic()-started)*1000),
                   request_bytes=len(raw), response_bytes=len(response.body))
            return response
        except Exception:
            record(mode=mode, outcome="probe_failure", elapsed_ms=int((time.monotonic()-started)*1000))
            return _error(500, "CT8_PROBE_FAILURE")

    @app.post(PATH + "/runs/catalogue", include_in_schema=False)
    async def catalogue(request: Request):
        return await execute("catalogue", request)

    @app.post(PATH + "/runs/hours-clause", include_in_schema=False)
    async def hours(request: Request):
        return await execute("hours-clause", request)

    return app
