# mini_ddq_app/scripts/bench_imports.py
import time, io, csv
from typing import Optional
from starlette.testclient import TestClient
from mini_ddq_app.main import app

def make_csv(questionnaire_id: str, n: int = 1000) -> bytes:
    """
    Build a CSV that matches imports._parse_csv headers:
    questionnaire_id,text,category,is_required,display_order
    """
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["questionnaire_id", "text", "category", "is_required", "display_order"])
    for i in range(n):
        w.writerow([questionnaire_id, f"Bench Q {i}", "bench", "false", i])
    buf.seek(0)
    return buf.read().encode()

def discover_questionnaire_id(client: TestClient, token: str) -> Optional[str]:
    """
    Try to fetch one question and read its 'questionnaire_id'.
    If your /questions endpoint doesn't include it, return None.
    """
    r = client.get("/questions", headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        return None
    arr = r.json()
    if not arr:
        return None
    # Try common field names
    for key in ("questionnaire_id", "questionnaireId"):
        if key in arr[0]:
            return arr[0][key]
    return None

def _debug_list_routes():
    # Handy when you need to confirm routes
    from fastapi.routing import APIRoute
    print("== Registered routes ==")
    for rt in app.routes:
        if isinstance(rt, APIRoute):
            print(f"{','.join(sorted(rt.methods)):<12} {rt.path}")

if __name__ == "__main__":
    client = TestClient(app)

    # Optional: print routes if you ever see 404 again
    # _debug_list_routes()

    # Get a token (assumes alice@alpha.com from your seed)
    tok_resp = client.post("/auth/login", json={"email": "alice@alpha.com", "password": "alpha_admin"})
    tok_resp.raise_for_status()
    tok = tok_resp.json()["access_token"]

    # Try to discover a questionnaire_id automatically
    qn_id = discover_questionnaire_id(client, tok)
    if not qn_id:
        # If your /questions output doesn't include questionnaire_id,
        # paste one here (from psql: SELECT id FROM questionnaires WHERE tenant_id=... LIMIT 1)
        raise SystemExit(
            "Couldn't auto-discover questionnaire_id from /questions. "
            "Edit this script and set qn_id manually."
        )

    # Build payload
    payload = make_csv(qn_id, n=2000)

    t0 = time.perf_counter()
    r = client.post(
        "/imports/questions?sync=true",
        headers={"Authorization": f"Bearer {tok}"},
        files={"file": ("bench.csv", payload, "text/csv")},  # <-- multipart upload
    )
    dt_ms = int((time.perf_counter() - t0) * 1000)

    print("Status:", r.status_code, "Time(ms):", dt_ms)
    try:
        print("Result:", r.json())
    except Exception:
        print("Body:", r.text)