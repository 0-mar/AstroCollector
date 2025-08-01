"""add task status

Revision ID: 80b7e16d0ace
Revises: 07ab9c27f0dc
Create Date: 2025-07-30 11:32:40.541161

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "80b7e16d0ace"
down_revision: Union[str, None] = "07ab9c27f0dc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    task_status_enum = sa.Enum("in_progress", "completed", "failed", name="taskstatus")
    task_status_enum.create(op.get_bind())
    op.add_column("ac_task", sa.Column("status", task_status_enum, nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("ac_task", "status")
    sa.Enum(name="taskstatus").drop(op.get_bind())

    # ### end Alembic commands ###
