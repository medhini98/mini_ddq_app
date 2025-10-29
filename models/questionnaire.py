from sqlalchemy import Column, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Text, Integer, TIMESTAMP
from mini_ddq_app.db import Base

class Questionnaire(Base):
    __tablename__ = "questionnaires"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default=text("'draft'"))
    version = Column(Integer, nullable=False, server_default=text("1"))
    created_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    __table_args__ = (UniqueConstraint("tenant_id", "name", "version", name="uq_questionnaires_name_version"),)