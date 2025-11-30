"""knowledge base tables

Revision ID: 054_knowledge_base_ddl
Revises: 053_scheduler_ddl
Create Date: 2024-11-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '054_knowledge_base_ddl'
down_revision: Union[str, None] = '053_scheduler_ddl'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create knowledge_base table
    op.create_table(
        'knowledge_base',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('oid', sa.BigInteger(), nullable=True, default=1),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('embedding_model', sa.String(255), nullable=True),
        sa.Column('chunk_size', sa.Integer(), nullable=False, default=500),
        sa.Column('chunk_overlap', sa.Integer(), nullable=False, default=50),
        sa.Column('chunking_strategy', sa.String(50), nullable=False, default='recursive'),
        sa.Column('similarity_threshold', sa.Float(), nullable=True, default=0.6),
        sa.Column('top_k', sa.Integer(), nullable=True, default=5),
        sa.Column('datasource_ids', postgresql.JSONB(), nullable=True, default=[]),
        sa.Column('document_count', sa.Integer(), nullable=True, default=0),
        sa.Column('chunk_count', sa.Integer(), nullable=True, default=0),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('create_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('update_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('created_by', sa.BigInteger(), nullable=True),
    )
    
    # Create kb_document table
    op.create_table(
        'kb_document',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('kb_id', sa.BigInteger(), nullable=False),
        sa.Column('oid', sa.BigInteger(), nullable=True, default=1),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(512), nullable=False),
        sa.Column('file_path', sa.String(1024), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=True),
        sa.Column('file_type', sa.String(50), nullable=False),
        sa.Column('mime_type', sa.String(255), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=True),
        sa.Column('index_status', sa.String(50), nullable=True, default='pending'),
        sa.Column('chunk_count', sa.Integer(), nullable=True, default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('create_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('update_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('processed_time', sa.DateTime(timezone=False), nullable=True),
    )
    
    # Create kb_document_chunk table
    op.create_table(
        'kb_document_chunk',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column('document_id', sa.BigInteger(), nullable=False),
        sa.Column('kb_id', sa.BigInteger(), nullable=False),
        sa.Column('oid', sa.BigInteger(), nullable=True, default=1),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=True, default=0),
        sa.Column('char_count', sa.Integer(), nullable=True, default=0),
        sa.Column('token_count', sa.Integer(), nullable=True, default=0),
        sa.Column('embedding', Vector(), nullable=True),
        sa.Column('start_char', sa.Integer(), nullable=True, default=0),
        sa.Column('end_char', sa.Integer(), nullable=True, default=0),
        sa.Column('page_number', sa.Integer(), nullable=True, default=0),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, default={}),
        sa.Column('create_time', sa.DateTime(timezone=False), nullable=True),
    )
    
    # Create indexes
    op.create_index('idx_knowledge_base_oid', 'knowledge_base', ['oid'])
    op.create_index('idx_knowledge_base_enabled', 'knowledge_base', ['enabled'])
    
    op.create_index('idx_kb_document_kb_id', 'kb_document', ['kb_id'])
    op.create_index('idx_kb_document_oid', 'kb_document', ['oid'])
    op.create_index('idx_kb_document_status', 'kb_document', ['index_status'])
    op.create_index('idx_kb_document_hash', 'kb_document', ['content_hash'])
    
    op.create_index('idx_kb_chunk_document_id', 'kb_document_chunk', ['document_id'])
    op.create_index('idx_kb_chunk_kb_id', 'kb_document_chunk', ['kb_id'])
    op.create_index('idx_kb_chunk_oid', 'kb_document_chunk', ['oid'])
    
    # Create vector index for similarity search
    op.execute("""
        CREATE INDEX idx_kb_chunk_embedding ON kb_document_chunk 
        USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
    """)


def downgrade() -> None:
    op.drop_index('idx_kb_chunk_embedding')
    op.drop_index('idx_kb_chunk_oid')
    op.drop_index('idx_kb_chunk_kb_id')
    op.drop_index('idx_kb_chunk_document_id')
    op.drop_index('idx_kb_document_hash')
    op.drop_index('idx_kb_document_status')
    op.drop_index('idx_kb_document_oid')
    op.drop_index('idx_kb_document_kb_id')
    op.drop_index('idx_knowledge_base_enabled')
    op.drop_index('idx_knowledge_base_oid')
    op.drop_table('kb_document_chunk')
    op.drop_table('kb_document')
    op.drop_table('knowledge_base')
