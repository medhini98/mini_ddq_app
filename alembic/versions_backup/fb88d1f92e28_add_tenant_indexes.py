"""add tenant indexes

Revision ID: fb88d1f92e28
Revises: 
Create Date: 2025-10-28 18:08:50.998531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb88d1f92e28'
#down_revision: Union[str, Sequence[str], None] = None
down_revision = "<INIT_SCHEMA_REVISION_ID>"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index("users_tenant_idx", "users", ["tenant_id"])
    op.create_index("questions_tenant_idx", "questions", ["tenant_id"])

def downgrade():
    op.drop_index("questions_tenant_idx", table_name="questions")
    op.drop_index("users_tenant_idx", table_name="users")
