# mini_ddq_app/tests/test_auth_form.py
def test_oauth2_form_token(client, alpha_fixture):
    # OAuth2PasswordRequestForm expects form fields: username, password
    r = client.post(
        "/auth/token",
        data={"username": "alice@alpha.com", "password": "alpha_admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "access_token" in body and body["token_type"] == "bearer"