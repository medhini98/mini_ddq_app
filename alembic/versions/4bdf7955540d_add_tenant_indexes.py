"""add tenant indexes

Revision ID: 4bdf7955540d
Revises: bdebe07196c5
Create Date: 2025-10-28 18:49:35.640768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4bdf7955540d'
down_revision: Union[str, Sequence[str], None] = 'bdebe07196c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_index("users_tenant_idx", "users", ["tenant_id"])
    op.create_index("questions_tenant_idx", "questions", ["tenant_id"])

def downgrade():
    op.drop_index("questions_tenant_idx", table_name="questions")
    op.drop_index("users_tenant_idx", table_name="users")
