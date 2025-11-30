from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Column, Text, BigInteger, DateTime, Identity, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import VECTOR
from sqlmodel import SQLModel, Field


class DocumentType(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    CSV = "csv"
    XLSX = "xlsx"
    HTML = "html"
    JSON = "json"


class ChunkingStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"  # Fixed character count
    PARAGRAPH = "paragraph"  # Split by paragraphs
    SENTENCE = "sentence"  # Split by sentences
    SEMANTIC = "semantic"  # Semantic-based splitting
    RECURSIVE = "recursive"  # Recursive character text splitter


class IndexStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeBase(SQLModel, table=True):
    """Knowledge Base - container for documents"""
    __tablename__ = "knowledge_base"
    
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    name: str = Field(max_length=255)
    description: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    
    # Embedding configuration
    embedding_model: Optional[str] = Field(max_length=255, nullable=True)
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)
    chunking_strategy: str = Field(max_length=50, default="recursive")
    
    # Retrieval settings
    similarity_threshold: float = Field(sa_column=Column(Float, default=0.6))
    top_k: int = Field(default=5)
    
    # Association with datasources (optional)
    datasource_ids: Optional[list[int]] = Field(sa_column=Column(JSONB), default=[])
    
    # Statistics
    document_count: int = Field(default=0)
    chunk_count: int = Field(default=0)
    
    # Status
    enabled: Optional[bool] = Field(sa_column=Column(Boolean, default=True))
    
    # Timestamps
    create_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    update_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    
    # Creator
    created_by: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))


class Document(SQLModel, table=True):
    """Document in a knowledge base"""
    __tablename__ = "kb_document"
    
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    kb_id: int = Field(sa_column=Column(BigInteger, nullable=False))  # Knowledge base ID
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    
    # Document info
    name: str = Field(max_length=255)
    original_filename: str = Field(max_length=512)
    file_path: Optional[str] = Field(max_length=1024, nullable=True)
    file_size: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True))
    file_type: str = Field(max_length=50)  # markdown, pdf, txt, etc.
    mime_type: Optional[str] = Field(max_length=255, nullable=True)
    
    # Content hash for deduplication
    content_hash: Optional[str] = Field(max_length=64, nullable=True)
    
    # Processing status
    index_status: str = Field(max_length=50, default="pending")
    chunk_count: int = Field(default=0)
    error_message: Optional[str] = Field(sa_column=Column(Text, nullable=True))
    
    # Metadata
    metadata: Optional[dict] = Field(sa_column=Column(JSONB), default={})
    
    # Status
    enabled: Optional[bool] = Field(sa_column=Column(Boolean, default=True))
    
    # Timestamps
    create_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    update_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))
    processed_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))


class DocumentChunk(SQLModel, table=True):
    """Chunked content from documents with embeddings"""
    __tablename__ = "kb_document_chunk"
    
    id: Optional[int] = Field(sa_column=Column(BigInteger, Identity(always=True), primary_key=True))
    document_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    kb_id: int = Field(sa_column=Column(BigInteger, nullable=False))
    oid: Optional[int] = Field(sa_column=Column(BigInteger, nullable=True, default=1))
    
    # Chunk content
    content: str = Field(sa_column=Column(Text, nullable=False))
    chunk_index: int = Field(default=0)  # Position in document
    
    # Token/character counts
    char_count: int = Field(default=0)
    token_count: Optional[int] = Field(default=0)
    
    # Embedding vector
    embedding: Optional[List[float]] = Field(sa_column=Column(VECTOR(), nullable=True))
    
    # Source location in original document
    start_char: Optional[int] = Field(default=0)
    end_char: Optional[int] = Field(default=0)
    page_number: Optional[int] = Field(default=0)  # For PDF
    
    # Metadata
    metadata: Optional[dict] = Field(sa_column=Column(JSONB), default={})
    
    # Timestamps
    create_time: Optional[datetime] = Field(sa_column=Column(DateTime(timezone=False), nullable=True))


# Pydantic models for API

class KnowledgeBaseInfo(BaseModel):
    """Knowledge base info for API"""
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: int = 500
    chunk_overlap: int = 50
    chunking_strategy: str = "recursive"
    similarity_threshold: float = 0.6
    top_k: int = 5
    datasource_ids: Optional[List[int]] = []
    enabled: bool = True
    document_count: int = 0
    chunk_count: int = 0
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class DocumentInfo(BaseModel):
    """Document info for API"""
    id: Optional[int] = None
    kb_id: int
    name: str
    original_filename: str
    file_size: Optional[int] = None
    file_type: str
    mime_type: Optional[str] = None
    index_status: str = "pending"
    chunk_count: int = 0
    error_message: Optional[str] = None
    metadata: Optional[dict] = {}
    enabled: bool = True
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    processed_time: Optional[datetime] = None


class DocumentChunkInfo(BaseModel):
    """Document chunk info for API"""
    id: Optional[int] = None
    document_id: int
    kb_id: int
    content: str
    chunk_index: int = 0
    char_count: int = 0
    token_count: int = 0
    page_number: Optional[int] = None
    metadata: Optional[dict] = {}


class SearchResult(BaseModel):
    """Search result from knowledge base"""
    chunk_id: int
    document_id: int
    document_name: str
    kb_id: int
    kb_name: str
    content: str
    score: float
    page_number: Optional[int] = None
    metadata: Optional[dict] = {}
