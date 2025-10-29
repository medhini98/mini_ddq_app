from starlette.testclient import TestClient
from mini_ddq_app.main import app

def test_login_json_success(client: TestClient, alpha_fixture):
    r = client.post("/auth/login", json={"email": "alice@alpha.com", "password": "alpha_admin"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"

def test_login_json_invalid_password(client: TestClient, alpha_fixture):
    r = client.post("/auth/login", json={"email": "alice@alpha.com", "password": "wrong"})
    assert r.status_code == 401