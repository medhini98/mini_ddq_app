# mini_ddq_app/tests/it_test_questions_responses.py
from uuid import UUID, uuid4

def _authhed(client, token):
    return {"Authorization": f"Bearer {token}"}

def test_questions_scoped_to_tenant(client, alpha_fixture, beta_fixture, alpha_token, beta_token):
    r1 = client.get("/questions", headers=_authhed(client, alpha_token))
    r2 = client.get("/questions", headers=_authhed(client, beta_token))
    assert r1.status_code == 200 and r2.status_code == 200
    alpha_ids = {q["id"] for q in r1.json()}
    beta_ids = {q["id"] for q in r2.json()}
    assert alpha_ids.isdisjoint(beta_ids)

def test_response_upsert_and_get(client, alpha_fixture, alpha_token):
    q_id = str(alpha_fixture["questions"][0].id)

    # Upsert draft
    r = client.put(
        f"/responses/{q_id}",
        headers=_authhed(client, alpha_token),
        json={"answer": "Yes", "status": "draft"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["question_id"] == q_id
    assert body["answer"] == "Yes"

    # Get
    r2 = client.get(f"/responses/{q_id}", headers=_authhed(client, alpha_token))
    assert r2.status_code == 200
    assert r2.json()["answer"] == "Yes"

def test_cross_tenant_404_on_response(client, alpha_fixture, beta_fixture, beta_token):
    # Beta tries to fetch Alpha's response (should be 404)
    alpha_q_id = str(alpha_fixture["questions"][0].id)
    r = client.get(f"/responses/{alpha_q_id}", headers=_authhed(client, beta_token))
    assert r.status_code == 404

def test_response_upsert_404_if_question_not_in_tenant(client, beta_fixture, beta_token):
    # Covers 404 path when tenant tries to update a question not belonging to them
    alien_qid = str(uuid4())  # simulate a question that doesn't exist for this tenant
    r = client.put(
        f"/responses/{alien_qid}",
        json={"answer": "nope"},
        headers=_authhed(client, beta_token),
    )
    assert r.status_code == 404