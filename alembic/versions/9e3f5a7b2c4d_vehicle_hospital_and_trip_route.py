"""emergency_vehicles.hospital_id, emergency_trips.route

A vehicle can belong to a hospital (its trips always end at that hospital).
A trip remembers its route (road ids) so its green corridor can be switched off later.

Revision ID: 9e3f5a7b2c4d
Revises: 8d2e4f6a1b3c
"""
from alembic import op
import sqlalchemy as sa


revision = "9e3f5a7b2c4d"
down_revision = "8d2e4f6a1b3c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("emergency_vehicles", sa.Column("hospital_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "emergency_vehicles_hospital_id_fkey", "emergency_vehicles", "hospitals", ["hospital_id"], ["id"]
    )
    op.add_column("emergency_trips", sa.Column("route", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("emergency_trips", "route")
    op.drop_constraint("emergency_vehicles_hospital_id_fkey", "emergency_vehicles", type_="foreignkey")
    op.drop_column("emergency_vehicles", "hospital_id")
