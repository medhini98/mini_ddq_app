from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import csv
import io
import json

from mini_ddq_app.db import get_db
from mini_ddq_app.deps import get_current_user, require_role
from mini_ddq_app.models.questionnaire import Questionnaire
from mini_ddq_app.models.question import Question

router = APIRouter(prefix="/imports", tags=["imports"])

# --------- helpers ---------
def _str_to_bool(val: Optional[str]) -> Optional[bool]:
    if val is None:
        return None
    s = str(val).strip().lower()
    if s in {"1", "true", "yes", "y"}:
        return True
    if s in {"0", "false", "no", "n"}:
        return False
    return None

def _ensure_questionnaire_in_tenant(db: Session, questionnaire_id: str, tenant_id) -> bool:
    return db.query(Questionnaire).filter(
        Questionnaire.id == questionnaire_id,
        Questionnaire.tenant_id == tenant_id
    ).first() is not None

def _parse_csv(content: bytes) -> List[Dict[str, Any]]:
    text = content.decode("utf-8-sig")  # handle BOM if present
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        rows.append({
            "questionnaire_id": (row.get("questionnaire_id") or "").strip(),
            "text": (row.get("text") or "").strip(),
            "category": (row.get("category") or None),
            "is_required": _str_to_bool(row.get("is_required")),
            "display_order": int(row["display_order"]) if (row.get("display_order") or "").strip().isdigit() else None,
        })
    return rows

def _parse_json(content: bytes) -> List[Dict[str, Any]]:
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("JSON must be a list of objects")
    rows = []
    for row in data:
        rows.append({
            "questionnaire_id": str(row.get("questionnaire_id") or "").strip(),
            "text": str(row.get("text") or "").strip(),
            "category": row.get("category"),
            "is_required": _str_to_bool(row.get("is_required")),
            "display_order": int(row["display_order"]) if str(row.get("display_order") or "").isdigit() else None,
        })
    return rows

def _import_rows(db: Session, tenant_id, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Core importer: validate rows, enforce tenant, insert in small batches."""
    stats = {"rows_total": len(rows), "rows_ok": 0, "rows_failed": 0, "errors": []}
    BATCH = 100
    batch_count = 0

    for idx, r in enumerate(rows, start=1):
        qn_id = r.get("questionnaire_id")
        text = r.get("text")

        # basic validation
        if not qn_id or not text:
            stats["rows_failed"] += 1
            stats["errors"].append({"row": idx, "error": "Missing questionnaire_id or text"})
            continue

        # tenant check
        if not _ensure_questionnaire_in_tenant(db, qn_id, tenant_id):
            stats["rows_failed"] += 1
            stats["errors"].append({"row": idx, "error": "Questionnaire not found for this tenant"})
            continue

        # create question
        q = Question(
            tenant_id=tenant_id,
            questionnaire_id=qn_id,
            question_text=text,
            category=r.get("category"),
            is_required=(r.get("is_required") if r.get("is_required") is not None else False),
            display_order=r.get("display_order"),
        )
        db.add(q)
        stats["rows_ok"] += 1
        batch_count += 1

        if batch_count >= BATCH:
            db.commit()
            batch_count = 0

    if batch_count:
        db.commit()
    return stats

def _detect_format(filename: str, content_type: str) -> str:
    # simple heuristic by extension, fallback to content-type
    if filename.lower().endswith(".csv"):
        return "csv"
    if filename.lower().endswith(".json"):
        return "json"
    if "csv" in (content_type or "").lower():
        return "csv"
    if "json" in (content_type or "").lower():
        return "json"
    return "csv"  # default to CSV


# --------- background worker ---------
def _background_import(file_bytes: bytes, fmt: str, tenant_id, db_factory) -> None:
    db = db_factory()
    try:
        rows = _parse_csv(file_bytes) if fmt == "csv" else _parse_json(file_bytes)
        _import_rows(db, tenant_id, rows)
    except Exception:
        # best-effort background; log in real app
        pass
    finally:
        db.close()


# --------- routes ---------
@router.post(
    "/questions",
    dependencies=[Depends(require_role("admin", "analyst"))],
    summary="Bulk import questions (CSV or JSON). Use ?sync=true to wait for result."
)
async def import_questions(
    background: BackgroundTasks,
    file: UploadFile = File(..., description="CSV with headers: questionnaire_id,text,category,is_required,display_order OR JSON list of objects with same keys"),
    sync: bool = Query(False, description="Run synchronously and return summary"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    data = await file.read()
    fmt = _detect_format(file.filename or "", file.content_type or "")

    if sync:
        try:
            rows = _parse_csv(data) if fmt == "csv" else _parse_json(data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Parse error: {e}")

        stats = _import_rows(db, user.tenant_id, rows)
        # Trim error samples for brevity
        if len(stats["errors"]) > 10:
            stats["errors"] = stats["errors"][:10] + [{"row": "...", "error": "…truncated…"}]
        return {"mode": "sync", "format": fmt, **stats}

    # async path: fire-and-forget
    background.add_task(_background_import, data, fmt, user.tenant_id, type(db))
    # simple receipt (in a real app you'd persist a job record)
    return {"mode": "async", "status": "accepted", "format": fmt, "note": "Job running in background"}