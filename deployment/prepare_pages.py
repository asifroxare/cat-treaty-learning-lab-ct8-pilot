"""Prepare the built static assets for split-origin Cloudflare Pages staging."""
import argparse
from pathlib import Path
import re
import sys

ROUTES = ("/guided", "/explore", "/hours-clause", "/compare", "/audit")


def prepare(dist: Path, api_origin: str) -> None:
    origin = api_origin.rstrip("/")
    if not re.fullmatch(r"https://[A-Za-z0-9.-]+(?::\d+)?", origin) or "localhost" in origin:
        raise ValueError("a specific HTTPS API origin is required")
    if not (dist / "index.html").is_file():
        raise ValueError("build first: dist/index.html is missing")
    assets = list(dist.glob("assets/*.js"))
    if not assets or not any(origin.encode() in asset.read_bytes() for asset in assets):
        raise ValueError("built JS does not contain the approved API origin")
    if any(b"http://localhost:8000" in asset.read_bytes() for asset in assets):
        raise ValueError("development API origin found in built JS")
    # The reviewed CT7 React app uses geometry widths via inline style attributes.
    # Permit CSS inline styles only; no inline or eval JavaScript.
    csp = ("default-src 'none'; base-uri 'self'; object-src 'none'; "
           "frame-ancestors 'none'; form-action 'self'; script-src 'self'; "
           "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
           f"font-src 'self'; connect-src 'self' {origin}")
    headers = ("/*\n"
               "  X-Content-Type-Options: nosniff\n"
               "  X-Frame-Options: DENY\n"
               "  Referrer-Policy: strict-origin-when-cross-origin\n"
               "  Permissions-Policy: camera=(), microphone=(), geolocation=()\n"
               f"  Content-Security-Policy: {csp}\n"
               "/\n"
               "  Cache-Control: no-cache, max-age=0, must-revalidate\n"
               "/index.html\n"
               "  Cache-Control: no-cache, max-age=0, must-revalidate\n"
               "/assets/*\n"
               "  Cache-Control: public, max-age=31536000, immutable\n")
    redirects = "".join(f"{route} /index.html 200\n" for route in ROUTES)
    (dist / "_headers").write_text(headers, encoding="utf-8")
    (dist / "_redirects").write_text(redirects, encoding="utf-8")
    print("Cloudflare Pages staging asset policy: generated; edge behavior still requires staging verification")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", required=True, type=Path)
    parser.add_argument("--api-origin", required=True)
    args = parser.parse_args()
    try:
        prepare(args.dist, args.api_origin)
    except (OSError, ValueError) as error:
        print(f"Cloudflare Pages asset policy: FAIL ({error})", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
