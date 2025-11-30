import logging
import os
import uuid
import asyncio
from typing import Optional, List

from fastapi import APIRouter, Query, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from apps.ai_model.embedding import EmbeddingModelCache
from apps.knowledge_base.crud.knowledge_crud import (
    create_knowledge_base, update_knowledge_base, delete_knowledge_base,
    get_knowledge_base, page_knowledge_bases, get_all_knowledge_bases,
    create_document, delete_documents, get_document, page_documents,
    search_knowledge_base, compute_content_hash, check_duplicate_document
)
from apps.knowledge_base.models.knowledge_model import (
    KnowledgeBaseInfo, DocumentInfo, SearchResult
)
from apps.knowledge_base.service.document_processor import (
    DocumentProcessor, process_document_async
)
from common.core.config import settings
from common.core.deps import SessionDep, CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(tags=["KnowledgeBase"], prefix="/system/knowledge-base")

# Upload directory
KNOWLEDGE_UPLOAD_DIR = getattr(settings, 'KNOWLEDGE_BASE_UPLOAD_DIR', '/opt/sqlbot/data/knowledge')
os.makedirs(KNOWLEDGE_UPLOAD_DIR, exist_ok=True)


# ==================== Knowledge Base Endpoints ====================

@router.get("/list")
async def list_all_knowledge_bases(
    session: SessionDep,
    current_user: CurrentUser
):
    """Get all enabled knowledge bases"""
    kbs = get_all_knowledge_bases(session, current_user.oid)
    return [
        {
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "document_count": kb.document_count,
            "chunk_count": kb.chunk_count
        }
        for kb in kbs
    ]


@router.get("/page/{current_page}/{page_size}")
async def get_knowledge_bases_page(
    session: SessionDep,
    current_user: CurrentUser,
    current_page: int,
    page_size: int,
    name: Optional[str] = Query(None, description="Filter by name")
):
    """Get paginated knowledge bases"""
    current_page, page_size, total_count, total_pages, kbs = page_knowledge_bases(
        session, current_page, page_size, current_user.oid, name
    )
    
    return {
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": [
            {
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "embedding_model": kb.embedding_model,
                "chunk_size": kb.chunk_size,
                "chunk_overlap": kb.chunk_overlap,
                "chunking_strategy": kb.chunking_strategy,
                "similarity_threshold": kb.similarity_threshold,
                "top_k": kb.top_k,
                "datasource_ids": kb.datasource_ids,
                "enabled": kb.enabled,
                "document_count": kb.document_count,
                "chunk_count": kb.chunk_count,
                "create_time": kb.create_time,
                "update_time": kb.update_time
            }
            for kb in kbs
        ]
    }


@router.get("/{kb_id}")
async def get_knowledge_base_detail(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int
):
    """Get knowledge base details"""
    kb = get_knowledge_base(session, kb_id, current_user.oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "embedding_model": kb.embedding_model,
        "chunk_size": kb.chunk_size,
        "chunk_overlap": kb.chunk_overlap,
        "chunking_strategy": kb.chunking_strategy,
        "similarity_threshold": kb.similarity_threshold,
        "top_k": kb.top_k,
        "datasource_ids": kb.datasource_ids,
        "enabled": kb.enabled,
        "document_count": kb.document_count,
        "chunk_count": kb.chunk_count,
        "create_time": kb.create_time,
        "update_time": kb.update_time
    }


@router.post("")
async def create_kb(
    session: SessionDep,
    current_user: CurrentUser,
    info: KnowledgeBaseInfo
):
    """Create a new knowledge base"""
    kb = create_knowledge_base(session, info, current_user.oid, current_user.id)
    return {"id": kb.id, "message": "Knowledge base created successfully"}


@router.put("/{kb_id}")
async def update_kb(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    info: KnowledgeBaseInfo
):
    """Update a knowledge base"""
    kb = update_knowledge_base(session, kb_id, info, current_user.oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    return {"id": kb.id, "message": "Knowledge base updated successfully"}


@router.delete("")
async def delete_kbs(
    session: SessionDep,
    current_user: CurrentUser,
    kb_ids: List[int]
):
    """Delete knowledge bases"""
    count = delete_knowledge_base(session, kb_ids, current_user.oid)
    return {"deleted": count, "message": f"Deleted {count} knowledge bases"}


# ==================== Document Endpoints ====================

@router.get("/{kb_id}/documents/page/{current_page}/{page_size}")
async def get_documents_page(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    current_page: int,
    page_size: int,
    name: Optional[str] = Query(None, description="Filter by name"),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """Get paginated documents in a knowledge base"""
    # Verify KB exists
    kb = get_knowledge_base(session, kb_id, current_user.oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    current_page, page_size, total_count, total_pages, docs = page_documents(
        session, current_page, page_size, kb_id, current_user.oid, name, status
    )
    
    return {
        "current_page": current_page,
        "page_size": page_size,
        "total_count": total_count,
        "total_pages": total_pages,
        "data": [
            {
                "id": doc.id,
                "name": doc.name,
                "original_filename": doc.original_filename,
                "file_size": doc.file_size,
                "file_type": doc.file_type,
                "index_status": doc.index_status,
                "chunk_count": doc.chunk_count,
                "error_message": doc.error_message,
                "enabled": doc.enabled,
                "create_time": doc.create_time,
                "processed_time": doc.processed_time
            }
            for doc in docs
        ]
    }


@router.post("/{kb_id}/documents/upload")
async def upload_document(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload a document to knowledge base"""
    # Verify KB exists
    kb = get_knowledge_base(session, kb_id, current_user.oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Validate file type
    file_type = DocumentProcessor.get_file_type(file.filename)
    if not file_type:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: {list(DocumentProcessor.SUPPORTED_TYPES.keys())}"
        )
    
    # Read file content
    content = await file.read()
    
    # Check for duplicates
    content_hash = compute_content_hash(content)
    existing = check_duplicate_document(session, kb_id, content_hash)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Document already exists: {existing.name}"
        )
    
    # Save file
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_name = f"{file_id}{file_ext}"
    file_path = os.path.join(KNOWLEDGE_UPLOAD_DIR, str(kb_id), file_name)
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Create document record
    mime_type = DocumentProcessor.get_mime_type(file.filename)
    doc = create_document(
        session=session,
        kb_id=kb_id,
        name=file.filename,
        original_filename=file.filename,
        file_path=file_path,
        file_size=len(content),
        file_type=file_type,
        mime_type=mime_type,
        content_hash=content_hash,
        oid=current_user.oid
    )
    
    # Process document in background
    background_tasks.add_task(
        process_document_async, doc.id, kb_id, current_user.oid
    )
    
    return {
        "id": doc.id,
        "name": doc.name,
        "status": "pending",
        "message": "Document uploaded successfully, processing started"
    }


@router.post("/{kb_id}/documents/batch-upload")
async def batch_upload_documents(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload multiple documents to knowledge base"""
    # Verify KB exists
    kb = get_knowledge_base(session, kb_id, current_user.oid)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    results = []
    
    for file in files:
        try:
            # Validate file type
            file_type = DocumentProcessor.get_file_type(file.filename)
            if not file_type:
                results.append({
                    "name": file.filename,
                    "status": "error",
                    "message": "Unsupported file type"
                })
                continue
            
            # Read file content
            content = await file.read()
            
            # Check for duplicates
            content_hash = compute_content_hash(content)
            existing = check_duplicate_document(session, kb_id, content_hash)
            if existing:
                results.append({
                    "name": file.filename,
                    "status": "skipped",
                    "message": f"Duplicate of {existing.name}"
                })
                continue
            
            # Save file
            file_id = str(uuid.uuid4())
            file_ext = os.path.splitext(file.filename)[1]
            file_name = f"{file_id}{file_ext}"
            file_path = os.path.join(KNOWLEDGE_UPLOAD_DIR, str(kb_id), file_name)
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Create document record
            mime_type = DocumentProcessor.get_mime_type(file.filename)
            doc = create_document(
                session=session,
                kb_id=kb_id,
                name=file.filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                file_type=file_type,
                mime_type=mime_type,
                content_hash=content_hash,
                oid=current_user.oid
            )
            
            # Process document in background
            background_tasks.add_task(
                process_document_async, doc.id, kb_id, current_user.oid
            )
            
            results.append({
                "id": doc.id,
                "name": doc.name,
                "status": "pending",
                "message": "Processing started"
            })
            
        except Exception as e:
            results.append({
                "name": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    return {
        "total": len(files),
        "results": results
    }


@router.delete("/{kb_id}/documents")
async def delete_docs(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    doc_ids: List[int]
):
    """Delete documents from knowledge base"""
    count = delete_documents(session, doc_ids, current_user.oid)
    return {"deleted": count, "message": f"Deleted {count} documents"}


@router.post("/{kb_id}/documents/{doc_id}/reprocess")
async def reprocess_document(
    session: SessionDep,
    current_user: CurrentUser,
    kb_id: int,
    doc_id: int,
    background_tasks: BackgroundTasks
):
    """Reprocess a document"""
    doc = get_document(session, doc_id, current_user.oid)
    if not doc or doc.kb_id != kb_id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Clear existing chunks and reprocess
    from apps.knowledge_base.crud.knowledge_crud import delete_chunks_by_document, update_document_status
    
    delete_chunks_by_document(session, doc_id)
    update_document_status(session, doc_id, "pending", 0)
    
    background_tasks.add_task(
        process_document_async, doc_id, kb_id, current_user.oid
    )
    
    return {"message": "Document reprocessing started"}


# ==================== Search Endpoints ====================

class SearchRequest(BaseModel):
    query: str
    kb_ids: List[int]
    top_k: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.6


@router.post("/search")
async def search_kbs(
    session: SessionDep,
    current_user: CurrentUser,
    request: SearchRequest
):
    """Search across knowledge bases"""
    # Get embedding model
    embedding_model = EmbeddingModelCache.get_embedding_model()
    if not embedding_model:
        raise HTTPException(status_code=500, detail="Embedding model not available")
    
    # Generate query embedding
    query_embedding = embedding_model.embed_query(request.query)
    
    # Search
    results = search_knowledge_base(
        session=session,
        query_embedding=query_embedding,
        kb_ids=request.kb_ids,
        oid=current_user.oid,
        top_k=request.top_k,
        similarity_threshold=request.similarity_threshold
    )
    
    return {
        "query": request.query,
        "total": len(results),
        "results": [
            {
                "chunk_id": r.chunk_id,
                "document_id": r.document_id,
                "document_name": r.document_name,
                "kb_id": r.kb_id,
                "kb_name": r.kb_name,
                "content": r.content,
                "score": r.score,
                "page_number": r.page_number
            }
            for r in results
        ]
    }


# ==================== Supported Types Endpoint ====================

@router.get("/supported-types")
async def get_supported_types():
    """Get list of supported document types"""
    return {
        "types": DocumentProcessor.SUPPORTED_TYPES,
        "chunking_strategies": ["recursive", "fixed_size", "paragraph", "sentence", "semantic"]
    }
