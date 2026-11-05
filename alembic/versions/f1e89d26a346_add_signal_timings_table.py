

"""add signal timings table

Revision ID: f1e89d26a346
Revises: a1b8aa04b7ac
"""

from alembic import op
import sqlalchemy as sa


revision = 'f1e89d26a346'
down_revision = 'a1b8aa04b7ac'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'signal_timings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'signal_id',
            sa.Integer(),
            sa.ForeignKey('signals.id'),
            nullable=False
        ),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('green_time', sa.Integer(), nullable=False),
        sa.Column('yellow_time', sa.Integer(), nullable=False),
        sa.Column('red_time', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False
        )
    )


def downgrade() -> None:
    op.drop_table('signal_timings')
