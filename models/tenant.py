from sqlalchemy import Column, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Text, Date, TIMESTAMP
from mini_ddq_app.db import Base

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    org_name = Column(Text, nullable=False)
    contract_start = Column(Date, nullable=False)
    contract_end = Column(Date)
    status = Column(Text, nullable=False, server_default=text("'active'"))
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))