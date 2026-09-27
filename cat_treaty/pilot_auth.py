"""Independent Access JWT verification for the opt-in, separate CT8 pilot."""
from __future__ import annotations

import base64
import json
import re
import threading
import time
import urllib.request

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes


class PilotUnauthorized(ValueError):
    """Reject the caller before reading a pilot request body."""


def _decode(part: str) -> bytes:
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))


class AccessVerifier:
    def __init__(self, *, team: str, audience: str, allowed_emails: tuple[str, ...]):
        if not re.fullmatch(r"[a-z0-9-]{1,63}", team) or not audience.strip():
            raise ValueError("invalid pilot Access team or audience")
        self.issuer = f"https://{team}.cloudflareaccess.com"
        self.audience = audience
        self.allowed = frozenset(address.strip().lower() for address in allowed_emails)
        if not self.allowed or any(not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address) for address in self.allowed):
            raise ValueError("explicit individual pilot email allowlist required")
        self._keys: dict[str, rsa.RSAPublicKey] = {}
        self._refreshed = 0.0
        self._lock = threading.Lock()

    def _load_keys(self) -> dict[str, rsa.RSAPublicKey]:
        address = f"{self.issuer}/cdn-cgi/access/certs"
        with urllib.request.urlopen(address, timeout=3) as response:
            raw = response.read(65537)
        if len(raw) > 65536:
            raise PilotUnauthorized("Access key response too large")
        keys = {}
        for key in json.loads(raw).get("keys", ()):
            if key.get("kty") == "RSA" and key.get("alg", "RS256") == "RS256":
                kid = key.get("kid")
                if isinstance(kid, str) and kid:
                    keys[kid] = rsa.RSAPublicNumbers(
                        int.from_bytes(_decode(key["e"]), "big"),
                        int.from_bytes(_decode(key["n"]), "big"),
                    ).public_key()
        if not keys:
            raise PilotUnauthorized("Access signing keys unavailable")
        return keys

    def verify(self, token: str, *, now: float | None = None) -> str:
        try:
            if not isinstance(token, str) or len(token) > 8192:
                raise PilotUnauthorized("invalid Access token")
            header_part, claim_part, signature_part = token.split(".")
            header = json.loads(_decode(header_part))
            claims = json.loads(_decode(claim_part))
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str):
                raise PilotUnauthorized("unsupported Access signature")
            with self._lock:
                if time.monotonic() - self._refreshed > 300 or header["kid"] not in self._keys:
                    self._keys = self._load_keys()
                    self._refreshed = time.monotonic()
                key = self._keys.get(header["kid"])
            if key is None:
                raise PilotUnauthorized("unrecognized Access key")
            key.verify(_decode(signature_part), f"{header_part}.{claim_part}".encode(),
                       padding.PKCS1v15(), hashes.SHA256())
            current = time.time() if now is None else now
            audience = claims.get("aud")
            if not isinstance(audience, list) or self.audience not in audience:
                raise PilotUnauthorized("wrong Access audience")
            expiry, issued = claims.get("exp"), claims.get("iat")
            not_before = claims.get("nbf", issued)
            if (claims.get("iss") != self.issuer or not isinstance(expiry, (float, int))
                    or isinstance(expiry, bool) or expiry <= current
                    or not isinstance(issued, (float, int)) or isinstance(issued, bool)
                    or not isinstance(not_before, (float, int)) or isinstance(not_before, bool)
                    or not_before > current + 30 or issued > current + 30
                    or current - issued > 86400):
                raise PilotUnauthorized("expired or invalid Access claim")
            email = claims.get("email")
            if not isinstance(email, str) or email.lower() not in self.allowed:
                raise PilotUnauthorized("pilot tester not allowed")
            return email.lower()
        except (InvalidSignature, OSError, KeyError, TypeError, ValueError, OverflowError) as error:
            raise PilotUnauthorized("pilot authentication failed") from error
