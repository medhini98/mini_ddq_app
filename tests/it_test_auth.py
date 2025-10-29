def test_login_success_and_failure(client, alpha_fixture):
    ok = client.post("/auth/login", json={"email": "alice@alpha.com", "password": "alpha_admin"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = client.post("/auth/login", json={"email": "alice@alpha.com", "password": "wrong"})
    assert bad.status_code in (400, 401)