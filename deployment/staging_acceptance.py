"""Non-destructive HTTPS staging contract checks; no load or real user payloads."""
import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from probe import fixture_digest


def fetch(url, method="GET", body=None, headers=None):
    request = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as response:
        return response.code, response.headers, response.read()


def require(ok, message):
    if not ok:
        raise RuntimeError(message)
    print("PASS:", message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontend", required=True, help="Approved HTTPS staging frontend origin")
    parser.add_argument("--api", required=True, help="Approved HTTPS staging API origin")
    parser.add_argument("--manifest", required=True, type=Path, help="Reviewed fixture manifest")
    args = parser.parse_args()
    frontend, api = args.frontend.rstrip("/"), args.api.rstrip("/")
    for value in (frontend, api):
        parsed = urlparse(value)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
            parser.error("frontend and API must be HTTPS origins without paths")
    if frontend == api:
        parser.error("this check expects the approved split-origin topology")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("api_origin") != api or manifest.get("frontend_origin") != frontend:
        raise RuntimeError("manifest origins do not match arguments")
    status, headers, content = fetch(frontend + "/")
    require(status == 200 and b"<html" in content.lower(), "frontend HTML available")
    require(b"http://localhost:8000" not in content, "no localhost in entry HTML")
    cache = headers.get("Cache-Control", "").lower()
    require("no-cache" in cache or "no-store" in cache or "max-age=0" in cache, "HTML revalidates at edge")
    require(headers.get("X-Content-Type-Options", "").lower() == "nosniff", "HTML nosniff header")
    require(bool(headers.get("Content-Security-Policy")), "HTML CSP present")
    status, _, content = fetch(frontend + "/hours-clause")
    require(status == 200 and b"<html" in content.lower(), "SPA deep-link fallback")
    status, _, _ = fetch(frontend + "/assets/ct8-certainly-missing.js")
    require(status == 404, "missing asset stays 404")
    for path in ("/health/live", "/health/ready", "/api/v1/capabilities"):
        status, _, content = fetch(api + path)
        obj = json.loads(content)
        require(status == 200 and (path != "/health/ready" or obj.get("status") == "ready"), path)
    preflight = {"Origin": frontend, "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type,x-request-id"}
    status, headers, _ = fetch(api + "/api/v1/runs/catalogue", "OPTIONS", headers=preflight)
    require(status == 200 and headers.get("Access-Control-Allow-Origin") == frontend, "approved CORS preflight")
    denied = dict(preflight, Origin="https://unapproved.example.invalid")
    status, headers, _ = fetch(api + "/api/v1/runs/catalogue", "OPTIONS", headers=denied)
    require(headers.get("Access-Control-Allow-Origin") != denied["Origin"], "foreign origin not CORS-authorized")
    # Error responses below are small and non-sensitive; keep ingress and CT6
    # precedence evidence distinct when a future front proxy intercepts requests.
    cases = (
        (b'{"bad":', "application/json", 400, "CT6_MALFORMED_JSON"),
        (b'{}', "text/plain", 400, "CT6_MALFORMED_JSON"),
        (b'{"api_schema_version":"ct-invalid"}', "application/json", 409, "CT6_VERSION_CONFLICT"),
    )
    for raw, media, expected_status, expected_code in cases:
        status, headers, content = fetch(api + "/api/v1/runs/catalogue", "POST", raw,
            {"Content-Type": media, "Origin": frontend})
        body = json.loads(content)
        require(status == expected_status and body.get("code") == expected_code
                and body.get("request_id") == headers.get("X-Request-ID"),
                f"structured CT6 error {expected_code}")
    status, headers, content = fetch(api + "/api/v1/runs/catalogue", "POST", b'{}',
        {"Content-Type": "text/plain", "Origin": frontend})
    require(status == 400 and json.loads(content).get("code") == "CT6_MALFORMED_JSON",
            "media-type precedence remains frozen")
    for entry in manifest["fixtures"]:
        route = entry["route"]
        if route not in ("catalogue", "hours-clause"):
            raise RuntimeError("unsupported manifest route")
        request_path = args.manifest.parent / entry["request_file"]
        if request_path.resolve() != args.manifest.parent.resolve() and args.manifest.parent.resolve() not in request_path.resolve().parents:
            raise RuntimeError("fixture path escapes manifest folder")
        raw = request_path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == entry["request_sha256"], f"{route} approved input digest")
        status, headers, content = fetch(api + "/api/v1/runs/" + route, "POST", raw,
            {"Content-Type": "application/json", "Origin": frontend})
        require(status == 200 and bool(headers.get("X-Request-ID")), f"{route} complete HTTP response")
        obj = json.loads(content)
        require(obj.get("api", {}).get("completion_status") == "complete", f"{route} authoritative completion")
        digest = fixture_digest(obj, [("api", "request_id")])
        require(digest == entry["response_sha256"], f"{route} approved golden response digest")
    print("STAGING CONTRACT CHECKS: PASS; manual browser, resource, and rollback gates remain separate")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, RuntimeError, urllib.error.URLError, KeyError) as error:
        print(f"STAGING CONTRACT CHECKS: FAIL ({error})", file=sys.stderr)
        sys.exit(1)
