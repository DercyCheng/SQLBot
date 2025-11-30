import datetime
import hashlib
import logging
from typing import Optional, List, Tuple

from sqlalchemy import select, func, delete, update, and_, text
from sqlalchemy.orm import Session

from apps.knowledge_base.models.knowledge_model import (
    KnowledgeBase, Document, DocumentChunk,
    KnowledgeBaseInfo, DocumentInfo, SearchResult
)
from common.core.deps import SessionDep

logger = logging.getLogger(__name__)


# ==================== Knowledge Base CRUD ====================

def create_knowledge_base(
    session: SessionDep,
    info: KnowledgeBaseInfo,
    oid: int,
    user_id: int
) -> KnowledgeBase:
    """Create a new knowledge base"""
    now = datetime.datetime.now()
    
    kb = KnowledgeBase(
        oid=oid,
        name=info.name,
        description=info.description,
        embedding_model=info.embedding_model,
        chunk_size=info.chunk_size,
        chunk_overlap=info.chunk_overlap,
        chunking_strategy=info.chunking_strategy,
        similarity_threshold=info.similarity_threshold,
        top_k=info.top_k,
        datasource_ids=info.datasource_ids or [],
        enabled=info.enabled,
        document_count=0,
        chunk_count=0,
        create_time=now,
        update_time=now,
        created_by=user_id
    )
    
    session.add(kb)
    session.commit()
    session.refresh(kb)
    
    return kb


def update_knowledge_base(
    session: SessionDep,
    kb_id: int,
    info: KnowledgeBaseInfo,
    oid: int
) -> Optional[KnowledgeBase]:
    """Update an existing knowledge base"""
    kb = session.get(KnowledgeBase, kb_id)
    
    if not kb or kb.oid != oid:
        return None
    
    kb.name = info.name
    kb.description = info.description
    kb.embedding_model = info.embedding_model
    kb.chunk_size = info.chunk_size
    kb.chunk_overlap = info.chunk_overlap
    kb.chunking_strategy = info.chunking_strategy
    kb.similarity_threshold = info.similarity_threshold
    kb.top_k = info.top_k
    kb.datasource_ids = info.datasource_ids or []
    kb.enabled = info.enabled
    kb.update_time = datetime.datetime.now()
    
    session.commit()
    session.refresh(kb)
    
    return kb


def delete_knowledge_base(session: SessionDep, kb_ids: List[int], oid: int) -> int:
    """Delete knowledge bases and all associated documents and chunks"""
    # Delete chunks first
    stmt_chunks = delete(DocumentChunk).where(
        and_(
            DocumentChunk.kb_id.in_(kb_ids),
            DocumentChunk.oid == oid
        )
    )
    session.execute(stmt_chunks)
    
    # Delete documents
    stmt_docs = delete(Document).where(
        and_(
            Document.kb_id.in_(kb_ids),
            Document.oid == oid
        )
    )
    session.execute(stmt_docs)
    
    # Delete knowledge bases
    stmt_kb = delete(KnowledgeBase).where(
        and_(
            KnowledgeBase.id.in_(kb_ids),
            KnowledgeBase.oid == oid
        )
    )
    result = session.execute(stmt_kb)
    session.commit()
    
    return result.rowcount


def get_knowledge_base(session: SessionDep, kb_id: int, oid: int) -> Optional[KnowledgeBase]:
    """Get a knowledge base by ID"""
    stmt = select(KnowledgeBase).where(
        and_(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.oid == oid
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def page_knowledge_bases(
    session: SessionDep,
    current_page: int,
    page_size: int,
    oid: int,
    name: Optional[str] = None
) -> Tuple[int, int, int, int, List[KnowledgeBase]]:
    """Get paginated knowledge bases"""
    
    conditions = [KnowledgeBase.oid == oid]
    
    if name:
        conditions.append(KnowledgeBase.name.ilike(f"%{name}%"))
    
    # Count total
    count_stmt = select(func.count()).select_from(KnowledgeBase).where(and_(*conditions))
    total_count = session.execute(count_stmt).scalar() or 0
    
    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size
    offset = (current_page - 1) * page_size
    
    # Fetch data
    stmt = (
        select(KnowledgeBase)
        .where(and_(*conditions))
        .order_by(KnowledgeBase.create_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    kbs = session.execute(stmt).scalars().all()
    
    return current_page, page_size, total_count, total_pages, list(kbs)


def get_all_knowledge_bases(session: SessionDep, oid: int) -> List[KnowledgeBase]:
    """Get all enabled knowledge bases"""
    stmt = select(KnowledgeBase).where(
        and_(
            KnowledgeBase.oid == oid,
            KnowledgeBase.enabled == True
        )
    ).order_by(KnowledgeBase.create_time.desc())
    
    return list(session.execute(stmt).scalars().all())


# ==================== Document CRUD ====================

def create_document(
    session: SessionDep,
    kb_id: int,
    name: str,
    original_filename: str,
    file_path: str,
    file_size: int,
    file_type: str,
    mime_type: str,
    content_hash: str,
    oid: int,
    metadata: dict = None
) -> Document:
    """Create a new document"""
    now = datetime.datetime.now()
    
    doc = Document(
        kb_id=kb_id,
        oid=oid,
        name=name,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_type,
        mime_type=mime_type,
        content_hash=content_hash,
        index_status="pending",
        chunk_count=0,
        metadata=metadata or {},
        enabled=True,
        create_time=now,
        update_time=now
    )
    
    session.add(doc)
    session.commit()
    session.refresh(doc)
    
    # Update knowledge base document count
    update_kb_stats(session, kb_id)
    
    return doc


def update_document_status(
    session: SessionDep,
    doc_id: int,
    status: str,
    chunk_count: int = 0,
    error_message: str = None
):
    """Update document processing status"""
    now = datetime.datetime.now()
    values = {
        "index_status": status,
        "chunk_count": chunk_count,
        "update_time": now
    }
    
    if status == "completed":
        values["processed_time"] = now
    
    if error_message:
        values["error_message"] = error_message
    
    stmt = update(Document).where(Document.id == doc_id).values(**values)
    session.execute(stmt)
    session.commit()


def delete_documents(session: SessionDep, doc_ids: List[int], oid: int) -> int:
    """Delete documents and their chunks"""
    # Get kb_ids for updating stats
    stmt_kb = select(Document.kb_id).where(Document.id.in_(doc_ids))
    kb_ids = set(session.execute(stmt_kb).scalars().all())
    
    # Delete chunks
    stmt_chunks = delete(DocumentChunk).where(
        and_(
            DocumentChunk.document_id.in_(doc_ids),
            DocumentChunk.oid == oid
        )
    )
    session.execute(stmt_chunks)
    
    # Delete documents
    stmt_docs = delete(Document).where(
        and_(
            Document.id.in_(doc_ids),
            Document.oid == oid
        )
    )
    result = session.execute(stmt_docs)
    session.commit()
    
    # Update KB stats
    for kb_id in kb_ids:
        update_kb_stats(session, kb_id)
    
    return result.rowcount


def get_document(session: SessionDep, doc_id: int, oid: int) -> Optional[Document]:
    """Get a document by ID"""
    stmt = select(Document).where(
        and_(
            Document.id == doc_id,
            Document.oid == oid
        )
    )
    return session.execute(stmt).scalar_one_or_none()


def page_documents(
    session: SessionDep,
    current_page: int,
    page_size: int,
    kb_id: int,
    oid: int,
    name: Optional[str] = None,
    status: Optional[str] = None
) -> Tuple[int, int, int, int, List[Document]]:
    """Get paginated documents in a knowledge base"""
    
    conditions = [Document.kb_id == kb_id, Document.oid == oid]
    
    if name:
        conditions.append(Document.name.ilike(f"%{name}%"))
    if status:
        conditions.append(Document.index_status == status)
    
    # Count total
    count_stmt = select(func.count()).select_from(Document).where(and_(*conditions))
    total_count = session.execute(count_stmt).scalar() or 0
    
    # Calculate pagination
    total_pages = (total_count + page_size - 1) // page_size
    offset = (current_page - 1) * page_size
    
    # Fetch data
    stmt = (
        select(Document)
        .where(and_(*conditions))
        .order_by(Document.create_time.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    docs = session.execute(stmt).scalars().all()
    
    return current_page, page_size, total_count, total_pages, list(docs)


def get_pending_documents(session: SessionDep) -> List[Document]:
    """Get all pending documents for processing"""
    stmt = select(Document).where(Document.index_status == "pending")
    return list(session.execute(stmt).scalars().all())


# ==================== Document Chunk CRUD ====================

def create_chunks(
    session: SessionDep,
    document_id: int,
    kb_id: int,
    oid: int,
    chunks: List[dict]
) -> int:
    """Create document chunks in batch"""
    now = datetime.datetime.now()
    
    chunk_objects = []
    for i, chunk_data in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document_id,
            kb_id=kb_id,
            oid=oid,
            content=chunk_data["content"],
            chunk_index=i,
            char_count=len(chunk_data["content"]),
            token_count=chunk_data.get("token_count", 0),
            embedding=chunk_data.get("embedding"),
            start_char=chunk_data.get("start_char", 0),
            end_char=chunk_data.get("end_char", 0),
            page_number=chunk_data.get("page_number", 0),
            metadata=chunk_data.get("metadata", {}),
            create_time=now
        )
        chunk_objects.append(chunk)
    
    session.add_all(chunk_objects)
    session.commit()
    
    # Update document chunk count
    update_document_status(session, document_id, "completed", len(chunks))
    
    # Update KB stats
    update_kb_stats(session, kb_id)
    
    return len(chunks)


def delete_chunks_by_document(session: SessionDep, document_id: int):
    """Delete all chunks for a document"""
    stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    session.execute(stmt)
    session.commit()


def update_chunk_embedding(session: SessionDep, chunk_id: int, embedding: List[float]):
    """Update embedding for a chunk"""
    stmt = update(DocumentChunk).where(DocumentChunk.id == chunk_id).values(embedding=embedding)
    session.execute(stmt)
    session.commit()


# ==================== Search ====================

def search_knowledge_base(
    session: SessionDep,
    query_embedding: List[float],
    kb_ids: List[int],
    oid: int,
    top_k: int = 5,
    similarity_threshold: float = 0.6
) -> List[SearchResult]:
    """Search knowledge base using vector similarity"""
    
    # Use pgvector cosine distance
    # Note: pgvector uses <=> for cosine distance (1 - similarity)
    # Lower distance = higher similarity
    
    kb_ids_str = ",".join(str(id) for id in kb_ids)
    
    sql = text(f"""
        SELECT 
            c.id as chunk_id,
            c.document_id,
            d.name as document_name,
            c.kb_id,
            kb.name as kb_name,
            c.content,
            1 - (c.embedding <=> :embedding) as score,
            c.page_number,
            c.metadata
        FROM kb_document_chunk c
        JOIN kb_document d ON c.document_id = d.id
        JOIN knowledge_base kb ON c.kb_id = kb.id
        WHERE c.kb_id IN ({kb_ids_str})
            AND c.oid = :oid
            AND c.embedding IS NOT NULL
            AND 1 - (c.embedding <=> :embedding) >= :threshold
        ORDER BY c.embedding <=> :embedding
        LIMIT :top_k
    """)
    
    results = session.execute(sql, {
        "embedding": str(query_embedding),
        "oid": oid,
        "threshold": similarity_threshold,
        "top_k": top_k
    }).fetchall()
    
    return [
        SearchResult(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            document_name=row.document_name,
            kb_id=row.kb_id,
            kb_name=row.kb_name,
            content=row.content,
            score=float(row.score),
            page_number=row.page_number,
            metadata=row.metadata or {}
        )
        for row in results
    ]


# ==================== Utilities ====================

def update_kb_stats(session: SessionDep, kb_id: int):
    """Update knowledge base document and chunk counts"""
    # Count documents
    doc_count = session.execute(
        select(func.count()).select_from(Document).where(Document.kb_id == kb_id)
    ).scalar() or 0
    
    # Count chunks
    chunk_count = session.execute(
        select(func.count()).select_from(DocumentChunk).where(DocumentChunk.kb_id == kb_id)
    ).scalar() or 0
    
    # Update KB
    stmt = update(KnowledgeBase).where(KnowledgeBase.id == kb_id).values(
        document_count=doc_count,
        chunk_count=chunk_count,
        update_time=datetime.datetime.now()
    )
    session.execute(stmt)
    session.commit()


def compute_content_hash(content: bytes) -> str:
    """Compute SHA256 hash of content for deduplication"""
    return hashlib.sha256(content).hexdigest()


def check_duplicate_document(session: SessionDep, kb_id: int, content_hash: str) -> Optional[Document]:
    """Check if document with same hash already exists"""
    stmt = select(Document).where(
        and_(
            Document.kb_id == kb_id,
            Document.content_hash == content_hash
        )
    )
    return session.execute(stmt).scalar_one_or_none()
