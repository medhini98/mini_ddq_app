from sqlalchemy import Column, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Text, TIMESTAMP
from mini_ddq_app.db import Base

class Response(Base):
    __tablename__ = "responses"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    answer = Column(Text)
    status = Column(Text, nullable=False, server_default=text("'draft'"))
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    __table_args__ = (UniqueConstraint("tenant_id", "question_id", name="uq_responses_one_per_question"),)