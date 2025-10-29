# mini_ddq_app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from mini_ddq_app.db import get_db
from mini_ddq_app.models.user import User
from mini_ddq_app.auth.hashing import verify_password
from mini_ddq_app.auth.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginJSON(BaseModel):
    email: EmailStr
    password: str

@router.post("/login", summary="JSON login for tests/clients")
def login_json(payload: LoginJSON, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active.is_(True)).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=str(user.id), tenant_id=str(user.tenant_id), role=user.role)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/token", summary="OAuth2 token endpoint (form: username, password)")
def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2PasswordRequestForm uses 'username' → treat it as email
    user = db.query(User).filter(User.email == form_data.username, User.is_active.is_(True)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(sub=str(user.id), tenant_id=str(user.tenant_id), role=user.role)
    return {"access_token": token, "token_type": "bearer"}