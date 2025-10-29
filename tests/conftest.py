# mini_ddq_app/tests/conftest.py
import os
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# --- 1) Force TEST settings early (session, autouse) ---
TEST_DB_URL = "postgresql+psycopg2://ddq_user:ddq_pass@localhost:5432/mini_ddq_test"

@pytest.fixture(scope="session", autouse=True)
def test_settings_env():
    os.environ["DATABASE_URL"] = TEST_DB_URL
    os.environ["JWT_SECRET"] = "integration-secret"
    os.environ["JWT_ALG"] = "HS256"
    os.environ["ACCESS_TOKEN_EXPIRE_MIN"] = "30"
    yield

# --- 2) Alembic upgrade head against TEST DB (session, autouse) ---
@pytest.fixture(scope="session", autouse=True)
def _run_migrations(test_settings_env):
    from alembic.config import Config as AlembicConfig
    from alembic import command as alembic_cmd

    # repo_root = .../sandbox
    repo_root = Path(__file__).resolve().parents[2]
    alembic_ini = repo_root / "mini_ddq_app" / "alembic.ini"

    cfg = AlembicConfig(str(alembic_ini))
    # env.py reads settings.DATABASE_URL (already set to TEST_DB_URL)
    alembic_cmd.upgrade(cfg, "head")
    yield

# --- 3) DB session per-test (transaction/rollback) ---
@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    from mini_ddq_app.config import settings
    engine = create_engine(settings.DATABASE_URL, future=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()

# --- 4) FastAPI TestClient with get_db override ---
@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    from mini_ddq_app.main import app
    from mini_ddq_app.db import get_db

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- 5) Seed minimal data for IT tests ---
def _seed_minimal(db: Session):
    from mini_ddq_app.models.tenant import Tenant
    from mini_ddq_app.models.user import User
    from mini_ddq_app.models.questionnaire import Questionnaire
    from mini_ddq_app.models.question import Question
    from mini_ddq_app.auth.hashing import hash_password

    alpha = Tenant(org_name="Alpha Corp", contract_start="2025-01-01")
    beta = Tenant(org_name="Beta LLC", contract_start="2025-01-01")
    db.add_all([alpha, beta])
    db.flush()

    def mk_user(tenant, email, password, role):
        return User(
            tenant_id=tenant.id,
            email=email,
            first_name=email.split("@")[0],
            last_name="",
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

    # Alpha users – include the ones your test expects
    a_admin_test = mk_user(alpha, "alice@alpha.com", "alpha_admin", "admin")  # <— test uses these
    a_admin      = mk_user(alpha, "admin@alpha.com", "password123", "admin")
    a_analyst    = mk_user(alpha, "analyst@alpha.com", "password123", "analyst")
    a_viewer     = mk_user(alpha, "viewer@alpha.com", "password123", "viewer")

    # Beta users
    b_admin   = mk_user(beta, "admin@beta.com", "password123", "admin")
    b_analyst = mk_user(beta, "analyst@beta.com", "password123", "analyst")
    b_viewer  = mk_user(beta, "viewer@beta.com", "password123", "viewer")

    db.add_all([a_admin_test, a_admin, a_analyst, a_viewer, b_admin, b_analyst, b_viewer])
    db.flush()

    # One questionnaire + one question for alpha
    qnr = Questionnaire(tenant_id=alpha.id, name="DDQ v1", created_by=a_admin.id)
    db.add(qnr)
    db.flush()

    q1 = Question(
        tenant_id=alpha.id,
        questionnaire_id=qnr.id,
        question_text="Does your org have SOC2?",
        category="security",
        display_order=1,
        is_required=True,
    )
    db.add(q1)
    db.commit()

    # Return both IDs and objects so IT tests can use either style
    return {
        "alpha": {
            "tenant_id": alpha.id,
            "admin_id": a_admin.id,
            "analyst_id": a_analyst.id,
            "viewer_id": a_viewer.id,
            "questionnaire_id": qnr.id,
            "question_id": q1.id,
            "questionnaire": qnr,          # <— added
            "questions": [q1],             # <— added
        },
        "beta": {
            "tenant_id": beta.id,
            "admin_id": b_admin.id,
            "analyst_id": b_analyst.id,
            "viewer_id": b_viewer.id,
        },
    }

@pytest.fixture()
def alpha_fixture(db_session: Session):
    data = _seed_minimal(db_session)
    return data["alpha"]

@pytest.fixture()
def beta_fixture(db_session: Session):
    data = _seed_minimal(db_session)
    return data["beta"]

# --- 6) JWT helpers (tokens & auth headers) ---
@pytest.fixture()
def alpha_token(alpha_fixture):
    from mini_ddq_app.auth.jwt import create_access_token
    return create_access_token(
        sub=str(alpha_fixture["admin_id"]),
        tenant_id=str(alpha_fixture["tenant_id"]),
        role="admin",
        minutes=60,
    )

@pytest.fixture()
def beta_token(beta_fixture):
    from mini_ddq_app.auth.jwt import create_access_token
    return create_access_token(
        sub=str(beta_fixture["admin_id"]),
        tenant_id=str(beta_fixture["tenant_id"]),
        role="admin",
        minutes=60,
    )

@pytest.fixture()
def auth_header(alpha_token):
    return {"Authorization": f"Bearer {alpha_token}"}