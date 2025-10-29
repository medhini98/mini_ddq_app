# mini_ddq_app/models/question.py
from sqlalchemy import Column, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Text, TIMESTAMP
from sqlalchemy import text as sa_text  # alias the function safely
from mini_ddq_app.db import Base

class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    questionnaire_id = Column(UUID(as_uuid=True), ForeignKey("questionnaires.id", ondelete="CASCADE"), nullable=False)
    question_text = Column("text", Text, nullable=False)
    category = Column(Text)
    display_order = Column(Integer)
    is_required = Column(Boolean, server_default=sa_text("false"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=sa_text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=sa_text("now()"))