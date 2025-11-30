"""scheduler tables

Revision ID: 053_scheduler_ddl
Revises: 052_add_recommended_problem
Create Date: 2024-11-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '053_scheduler_ddl'
down_revision: Union[str, None] = '052_add_recommended_problem'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create scheduled_task table
    op.create_table(
        'scheduled_task',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('oid', sa.BigInteger(), nullable=True, default=1),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False, default='cron'),
        sa.Column('cron_expression', sa.String(255), nullable=True),
        sa.Column('interval_seconds', sa.Integer(), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(timezone=False), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=False),
        sa.Column('action_config', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('status', sa.String(50), nullable=True, default='pending'),
        sa.Column('max_retries', sa.Integer(), nullable=True, default=3),
        sa.Column('retry_delay', sa.Integer(), nullable=True, default=60),
        sa.Column('create_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('update_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('last_run_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('next_run_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
    )
    
    # Create task_log table
    op.create_table(
        'task_log',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('oid', sa.BigInteger(), nullable=True, default=1),
        sa.Column('start_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('duration_ms', sa.BigInteger(), nullable=True),
        sa.Column('status', sa.String(50), nullable=True, default='running'),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True, default=0),
    )
    
    # Create indexes
    op.create_index('idx_scheduled_task_oid', 'scheduled_task', ['oid'])
    op.create_index('idx_scheduled_task_enabled', 'scheduled_task', ['enabled'])
    op.create_index('idx_task_log_task_id', 'task_log', ['task_id'])
    op.create_index('idx_task_log_oid', 'task_log', ['oid'])
    op.create_index('idx_task_log_start_time', 'task_log', ['start_time'])


def downgrade() -> None:
    op.drop_index('idx_task_log_start_time')
    op.drop_index('idx_task_log_oid')
    op.drop_index('idx_task_log_task_id')
    op.drop_index('idx_scheduled_task_enabled')
    op.drop_index('idx_scheduled_task_oid')
    op.drop_table('task_log')
    op.drop_table('scheduled_task')
