"""Pilot workload and authentication controls, independent of the CT6 math."""
import base64
import json
import time

import pytest
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives import hashes

from cat_treaty.pilot_auth import AccessVerifier, PilotUnauthorized
from cat_treaty.pilot_policy import PilotLimits, PilotLimitExceeded


def limits():
    return PilotLimits.from_json(json.dumps({
        "max_body_bytes": 16384, "max_trials": 1, "max_occurrences": 1,
        "max_layers": 1, "max_hours_components": 2,
        "max_requests_per_minute": 2, "allow_full_detail": True,
    }))


def test_pilot_requires_explicit_complete_limits_and_rejects_large_shapes():
    with pytest.raises(ValueError):
        PilotLimits.from_json("{}")
    with pytest.raises(ValueError):
        PilotLimits.from_json(json.dumps({**limits().__dict__, "max_body_bytes": True}))
    with pytest.raises(PilotLimitExceeded):
        limits().check("catalogue", {"input": {
            "program": {"layers": [{}]}, "simulation": {"trial_count": 2},
            "trials": [{"occurrences": [{}, {}]}]}})
    with pytest.raises(PilotLimitExceeded):
        limits().check("hours-clause", {"input": {
            "program": {"layers": [{}]}, "components": [{}, {}, {}]}})


def signed(verifier, key, claims):
    def enc(obj):
        return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=").decode()
    header = enc({"alg": "RS256", "kid": "review-key"})
    body = enc(claims)
    signature = key.sign(f"{header}.{body}".encode(), padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{body}.{base64.urlsafe_b64encode(signature).rstrip(b'=').decode()}"


def test_access_token_signature_audience_expiry_and_named_tester():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    verifier = AccessVerifier(team="review", audience="pilot-audience", allowed_emails=("person@example.org",))
    verifier._load_keys = lambda: {"review-key": key.public_key()}
    now = time.time()
    claims = {"iss": verifier.issuer, "aud": [verifier.audience], "exp": now + 120,
              "iat": now - 2, "email": "person@example.org"}
    token = signed(verifier, key, claims)
    assert verifier.verify(token, now=now) == "person@example.org"
    for changes in ({"aud": ["wrong"]}, {"exp": now - 1}, {"email": "outsider@example.org"}):
        with pytest.raises(PilotUnauthorized):
            verifier.verify(signed(verifier, key, {**claims, **changes}), now=now)
    with pytest.raises(PilotUnauthorized):
        verifier.verify(signed(verifier, rsa.generate_private_key(public_exponent=65537, key_size=2048), claims), now=now)
