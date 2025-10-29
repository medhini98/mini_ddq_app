from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, UUID4
from typing import Optional, List
from sqlalchemy.orm import Session

from mini_ddq_app.db import get_db
from mini_ddq_app.deps import get_current_user, require_role
from mini_ddq_app.models.response import Response as ResponseModel
from mini_ddq_app.models.question import Question as QuestionModel

router = APIRouter(prefix="/responses", tags=["responses"])


# ---------- Schemas ----------
class ResponseOut(BaseModel):
    id: UUID4
    question_id: UUID4
    tenant_id: UUID4
    answer: Optional[str] = None
    status: str

    class Config:
        from_attributes = True  # pydantic v2 (a.k.a. orm_mode=True in v1)


class ResponseUpsert(BaseModel):
    answer: Optional[str] = None
    status: Optional[str] = "draft"   # 'draft' | 'final' | 'rejected'


# ---------- Helpers ----------
def _ensure_same_tenant_or_404(db: Session, question_id: UUID4, tenant_id: str) -> QuestionModel:
    q = (
        db.query(QuestionModel)
        .filter(
            QuestionModel.id == str(question_id),  # stored as UUID in DB but comparing safely
            QuestionModel.tenant_id == tenant_id
        )
        .first()
    )
    if not q:
        # Either the question doesn't exist OR it's not in caller's tenant
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return q


# ---------- Routes ----------

@router.get("/", response_model=List[ResponseOut], summary="List responses for current tenant")
def list_responses(
    status_filter: Optional[str] = Query(default=None, description="Filter by status: draft/final/rejected"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    q = db.query(ResponseModel).filter(ResponseModel.tenant_id == user.tenant_id)
    if status_filter:
        q = q.filter(ResponseModel.status == status_filter)
    return q.all()


@router.get("/{question_id}", response_model=ResponseOut, summary="Get response for a question (tenant-scoped)")
def get_response_for_question(
    question_id: UUID4,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Validate question belongs to caller’s tenant
    _ensure_same_tenant_or_404(db, question_id, user.tenant_id)

    resp = (
        db.query(ResponseModel)
        .filter(
            ResponseModel.tenant_id == user.tenant_id,
            ResponseModel.question_id == str(question_id),
        )
        .first()
    )
    if not resp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found")
    return resp


@router.put("/{question_id}", response_model=ResponseOut,
            dependencies=[Depends(require_role("admin", "analyst"))],
            summary="Create/update the single response for a question (upsert)")
def upsert_response_for_question(
    question_id: UUID4,
    payload: ResponseUpsert,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Ensure the question is in the same tenant
    _ensure_same_tenant_or_404(db, question_id, user.tenant_id)

    # Try fetch existing single response (enforced by unique (tenant_id, question_id))
    resp = (
        db.query(ResponseModel)
        .filter(
            ResponseModel.tenant_id == user.tenant_id,
            ResponseModel.question_id == str(question_id),
        )
        .first()
    )

    if resp:
        # update
        resp.answer = payload.answer
        if payload.status:
            resp.status = payload.status
        resp.updated_by = user.id
        db.add(resp)
    else:
        # create
        resp = ResponseModel(
            tenant_id=user.tenant_id,
            question_id=str(question_id),
            answer=payload.answer,
            status=payload.status or "draft",
            updated_by=user.id,
        )
        db.add(resp)

    db.commit()
    db.refresh(resp)
    return resp