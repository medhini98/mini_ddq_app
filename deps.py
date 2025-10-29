"""
FastAPI dependencies for auth + multi-tenant scoping.

- get_current_user(): parses/validates Bearer JWT, loads user from DB, ensures active.
- require_role(*roles): 
    - guard that enforces role-based access (e.g., admin/analyst/viewer).
    - Authorization: require_role("admin","analyst") guards endpoints; get_current_user (in deps.py)
      decodes JWT, loads user, and provides user.role + user.tenant_id to routes.
- Use these in routes to (a) authenticate, (b) authorize, and (c) scope to tenant_id.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from mini_ddq_app.db import get_db
from mini_ddq_app.auth.jwt import decode_token
from mini_ddq_app.models.user import User

# For Swagger / OAuth2 flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# For standard bearer-token validation
bearer = HTTPBearer(auto_error=True)

class CurrentUser:
    def __init__(self, id: str, tenant_id: str, role: str):
        self.id = id
        self.tenant_id = tenant_id
        self.role = role


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """
    Extracts/validates JWT, then loads the user and returns a minimal CurrentUser object.
    Raises 401 if token invalid/expired or user not found/inactive.
    """
    token = creds.credentials
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        tid = payload.get("tenant_id")
        role = payload.get("role")
        if not sub or not tid or not role:
            raise ValueError("missing claims")

        user = (
            db.query(User)
            .filter(User.id == sub, User.tenant_id == tid, User.is_active.is_(True))
            .first()
        )
        if not user:
            raise ValueError("user not found or inactive")

        return CurrentUser(id=str(user.id), tenant_id=str(user.tenant_id), role=user.role)

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def require_role(*roles: str):
    """
    Usage example:
        @router.get("/admin-only")
        def handler(user = Depends(require_role("admin"))):
            ...
    """
    def _guard(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return _guard