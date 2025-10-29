from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, UUID4, Field

from mini_ddq_app.db import get_db
from mini_ddq_app.deps import get_current_user, require_role
from mini_ddq_app.models.question import Question
from mini_ddq_app.models.questionnaire import Questionnaire

router = APIRouter(prefix="/questions", tags=["questions"])

# ----- Schemas -----
class QuestionCreate(BaseModel):
    questionnaire_id: UUID4 = Field(..., description="Questionnaire this question belongs to")
    text: str = Field(..., description="Question text")
    category: Optional[str] = None
    is_required: bool = False
    display_order: Optional[int] = None

class QuestionOut(BaseModel):
    id: UUID4
    tenant_id: UUID4
    questionnaire_id: UUID4
    question_text: str
    category: Optional[str] = None
    is_required: bool
    display_order: Optional[int] = None

    class Config:
        from_attributes = True  # Pydantic v2

# ----- Helpers -----
def _ensure_questionnaire_in_tenant(db: Session, questionnaire_id: UUID4, tenant_id: str) -> Questionnaire:
    qn = (
        db.query(Questionnaire)
        .filter(Questionnaire.id == str(questionnaire_id), Questionnaire.tenant_id == tenant_id)
        .first()
    )
    if not qn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questionnaire not found")
    return qn

# ----- Routes -----
@router.get(
    "/",
    response_model=List[QuestionOut],
    summary="List questions for current tenant (optionally filter by questionnaire)"
)
def list_questions(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    questionnaire_id: Optional[UUID4] = Query(default=None),
):
    q = db.query(Question).filter(Question.tenant_id == user.tenant_id)
    if questionnaire_id:
        q = q.filter(Question.questionnaire_id == str(questionnaire_id))
    return q.order_by(Question.display_order).all()

@router.post(
    "/",
    response_model=QuestionOut,
    dependencies=[Depends(require_role("admin", "analyst"))],
    summary="Create a question (admin/analyst)"
)
def create_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    # Ensure the questionnaire belongs to the caller's tenant
    _ensure_questionnaire_in_tenant(db, data.questionnaire_id, user.tenant_id)

    new_q = Question(
        tenant_id=user.tenant_id,
        questionnaire_id=str(data.questionnaire_id),
        question_text=data.text,                # maps to the "text" column
        category=data.category,
        is_required=data.is_required,
        display_order=data.display_order,
    )
    db.add(new_q)
    db.commit()
    db.refresh(new_q)
    return new_q

