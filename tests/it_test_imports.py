import io

def _authhed(client, token): return {"Authorization": f"Bearer {token}"}

def test_import_questions_sync_csv(client, alpha_fixture, alpha_token):
    qn_id = str(alpha_fixture["questionnaire"].id)
    csv_content = (
        "questionnaire_id,text,category,is_required,display_order\n"
        f"{qn_id},Do you have a DR plan?,governance,true,10\n"
        f"{qn_id},Do you have audit logs?,security,false,11\n"
    ).encode("utf-8")

    files = {"file": ("alpha_additions.csv", io.BytesIO(csv_content), "text/csv")}
    r = client.post("/imports/questions", params={"sync": "true"}, headers=_authhed(client, alpha_token), files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["rows_ok"] == 2
    assert body["rows_failed"] == 0