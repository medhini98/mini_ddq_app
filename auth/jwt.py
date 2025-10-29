"""
Minimal JWT utilities (HS256) for issuing and verifying access tokens.

- create_access_token(): signs a payload with user id (sub), tenant_id, role, and expiry (exp).
- decode_token(): verifies signature + expiry and returns the payload.

Notes:
- payload = the JSON data inside a JWT (e.g., user id, role, tenant_id, expiry).
- Clients send tokens in the HTTP header: Authorization: Bearer <token>
- Keep JWTs small (IDs/roles only); never put sensitive data inside.
- Tokens are UTC time-bound via 'exp'.
- Uses HS256 with a shared secret (JWT_SECRET). Rotate the secret if it’s ever exposed.
"""

from jose import jwt
from datetime import datetime, timedelta
from mini_ddq_app.config import settings
from typing import Optional

def create_access_token(sub: str, tenant_id: str, role: str, minutes: Optional[int] = None):
    exp = datetime.utcnow() + timedelta(minutes=minutes or settings.ACCESS_TOKEN_EXPIRE_MIN)
    payload = {"sub": sub, "tenant_id": tenant_id, "role": role, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def decode_token(token:str):
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])