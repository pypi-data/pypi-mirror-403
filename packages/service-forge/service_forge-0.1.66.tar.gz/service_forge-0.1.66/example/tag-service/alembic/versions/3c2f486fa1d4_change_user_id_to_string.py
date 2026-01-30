"""change_user_id_to_string

Revision ID: 3c2f486fa1d4
Revises: 78e0ab93b1e5
Create Date: 2026-01-09 23:14:18.264394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c2f486fa1d4'
down_revision: Union[str, Sequence[str], None] = '78e0ab93b1e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Change column type from Integer to String
    # postgresql_using will automatically convert integer values to text
    op.alter_column('tag', 'user_id',
                    type_=sa.String(255),
                    existing_type=sa.Integer(),
                    existing_nullable=True,
                    postgresql_using='user_id::text')


def downgrade() -> None:
    """Downgrade schema."""
    # Change column type from String back to Integer
    # postgresql_using will automatically convert text values to integer
    # Note: This will fail if any user_id values are not valid integers
    op.alter_column('tag', 'user_id',
                    type_=sa.Integer(),
                    existing_type=sa.String(255),
                    existing_nullable=True,
                    postgresql_using='user_id::integer')
