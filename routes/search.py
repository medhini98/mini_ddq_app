# mini_ddq_app/routes/search.py
from typing import Literal
from sqlalchemy import func
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from mini_ddq_app.db import get_db
from mini_ddq_app.deps import get_current_user
from mini_ddq_app.models.question import Question
from mini_ddq_app.models.response import Response

router = APIRouter(prefix="/search", tags=["search"])

@router.get("/", summary="Search questions/responses within current tenant")
def search_items(
    q: str = Query(..., min_length=2, description="Search text"),
    scope: Literal["all", "questions", "responses"] = Query("all"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    results = []

    if scope in ("all", "questions"):
        questions = (
            db.query(Question)
            .filter(
                Question.tenant_id == user.tenant_id,
                Question.question_text.ilike(f"%{q}%"),
            )
            .limit(50)
            .all()
        )
        results += [
            {"type": "question", "id": str(x.id), "text": x.question_text, "category": x.category}
            for x in questions
        ]

    if scope in ("all", "responses"):
        responses = (
            db.query(Response)
            .filter(
                Response.tenant_id == user.tenant_id,
                Response.answer.isnot(None),
                Response.answer.ilike(f"%{q}%"),
            )
            .limit(50)
            .all()
        )
        results += [
            {
                "type": "response",
                "id": str(r.id),
                "question_id": str(r.question_id),
                "answer": r.answer,
                "status": r.status,
            }
            for r in responses
        ]

    if not results:
        raise HTTPException(status_code=404, detail="No matches found")

    return results[:50]