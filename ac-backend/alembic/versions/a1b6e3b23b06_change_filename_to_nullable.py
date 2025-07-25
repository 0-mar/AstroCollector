"""Change filename to nullable

Revision ID: a1b6e3b23b06
Revises: f079aeb009d1
Create Date: 2025-06-19 00:07:27.426914

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b6e3b23b06"
down_revision: Union[str, None] = "f079aeb009d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "ac_plugin", "file_name", existing_type=sa.VARCHAR(length=100), nullable=True
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "ac_plugin", "file_name", existing_type=sa.VARCHAR(length=100), nullable=False
    )
    # ### end Alembic commands ###
