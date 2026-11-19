"""restore signal_timings table

The create users migration (4985453c63a2) dropped signal_timings by mistake.
This puts it back. It does nothing if the table is already there.

Revision ID: 7c1d2e3f4a5b
Revises: fe8a4d5768b9
"""
from alembic import op
import sqlalchemy as sa


revision = "7c1d2e3f4a5b"
down_revision = "fe8a4d5768b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "signal_timings" in inspector.get_table_names():
        return
    op.create_table(
        "signal_timings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("signal_id", sa.Integer(), sa.ForeignKey("signals.id"), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("green_time", sa.Integer(), nullable=False),
        sa.Column("yellow_time", sa.Integer(), nullable=False),
        sa.Column("red_time", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    pass
