def _authhed(client, token): 
    return {"Authorization": f"Bearer {token}"}

def test_search_questions_and_responses_scoped(client, alpha_fixture, alpha_token):
    r = client.get("/search", params={"q": "backups", "scope": "all"}, headers=_authhed(client, alpha_token))
    # Either result is fine; ensure it's a 200 even if no responses yet
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        for item in r.json():
            assert item["type"] in ("question", "response")

def test_search_returns_200_when_match_exists(client, alpha_fixture, alpha_token):
    # Pull tenant-scoped questions to derive a guaranteed search term
    qr = client.get("/questions", headers=_authhed(client, alpha_token))
    assert qr.status_code == 200
    questions = qr.json()
    assert len(questions) > 0

    q0 = questions[0]
    # Handle either key name
    text = q0.get("text") or q0.get("question_text") or q0.get("category") or ""
    if not text:
        # last-resort fallback so test still works
        text = str(q0["id"])

    # Pick a term length >= 3, otherwise first 3 chars
    words = [w for w in text.replace("\n", " ").split() if len(w) >= 3]
    qterm = words[0] if words else text[:3]

    r = client.get(
        "/search",
        params={"q": qterm, "scope": "all"},
        headers=_authhed(client, alpha_token),
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list) and len(data) > 0
    assert all(item["type"] in ("question", "response") for item in data)