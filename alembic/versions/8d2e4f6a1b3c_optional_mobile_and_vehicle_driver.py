"""users.mobile optional, emergency_vehicles.driver_id

Email becomes the required contact (checked in the API), so mobile can be empty.
Emergency vehicles can be linked to the emergency driver who registered them.

Revision ID: 8d2e4f6a1b3c
Revises: 7c1d2e3f4a5b
"""
from alembic import op
import sqlalchemy as sa


revision = "8d2e4f6a1b3c"
down_revision = "7c1d2e3f4a5b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("users", "mobile", existing_type=sa.String(length=10), nullable=True)
    op.add_column("emergency_vehicles", sa.Column("driver_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "emergency_vehicles_driver_id_fkey", "emergency_vehicles", "users", ["driver_id"], ["id"]
    )


def downgrade() -> None:
    op.drop_constraint("emergency_vehicles_driver_id_fkey", "emergency_vehicles", type_="foreignkey")
    op.drop_column("emergency_vehicles", "driver_id")
    op.alter_column("users", "mobile", existing_type=sa.String(length=10), nullable=False)
