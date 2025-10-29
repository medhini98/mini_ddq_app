"""
- Confirms claims are present.
- Confirms expiration is enforced
"""

# mini_ddq_app/tests/test_jwt_utils.py
import pytest
from jose import jwt as jose_jwt, ExpiredSignatureError
from datetime import datetime, timedelta, timezone

from mini_ddq_app.auth.jwt import create_access_token, decode_token
from mini_ddq_app.config import settings

def test_create_and_decode_token_contains_claims():
    tok = create_access_token(
        sub="user-123",
        tenant_id="tenant-abc",
        role="admin",
        minutes=10,
    )
    payload = decode_token(tok)
    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-abc"
    assert payload["role"] == "admin"
    assert "exp" in payload

def test_expired_token_raises():
    # minutes=-1 => exp in the past
    tok = create_access_token(
        sub="u", tenant_id="t", role="viewer", minutes=-1
    )
    with pytest.raises(ExpiredSignatureError):
        decode_token(tok)

def test_jwt_alg_and_secret_match_config():
    tok = create_access_token(sub="u", tenant_id="t", role="analyst", minutes=1)
    # Ensure token can be decoded using the configured secret/alg
    jose_jwt.decode(tok, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])