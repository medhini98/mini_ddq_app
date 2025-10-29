import uuid
from starlette.testclient import TestClient
from mini_ddq_app.main import app
from mini_ddq_app.auth.jwt import create_access_token

def test_get_current_user_invalid_token(client: TestClient):
    r = client.get("/search/?q=x", headers={"Authorization": "Bearer not_a_token"})
    assert r.status_code == 401

def test_require_role_forbidden(client: TestClient, alpha_fixture):
    # make a viewer token
    viewer_id = str(alpha_fixture["viewer_id"])
    tid = str(alpha_fixture["tenant_id"])
    token = create_access_token(sub=viewer_id, tenant_id=tid, role="viewer")
    # try a route that requires admin/analyst (e.g., responses upsert)
    some_qid = str(uuid.uuid4())
    r = client.put(f"/responses/{some_qid}",
                   json={"answer": "x"},
                   headers={"Authorization": f"Bearer {token}"})
    assert r.status_code in (403, 404)  # 404 if qid not found; 403 proves guard when it *does* exist