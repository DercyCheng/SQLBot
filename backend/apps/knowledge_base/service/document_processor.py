import io
import logging
import os
import re
import traceback
from typing import List, Optional, Tuple
import hashlib

from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownTextSplitter
)

from apps.ai_model.embedding import EmbeddingModelCache
from apps.knowledge_base.models.knowledge_model import KnowledgeBase, Document, ChunkingStrategy
from common.core.config import settings
from common.utils.utils import SQLBotLogUtil

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process and chunk documents for knowledge base"""
    
    SUPPORTED_TYPES = {
        "markdown": [".md", ".markdown"],
        "pdf": [".pdf"],
        "txt": [".txt"],
        "docx": [".docx", ".doc"],
        "csv": [".csv"],
        "xlsx": [".xlsx", ".xls"],
        "html": [".html", ".htm"],
        "json": [".json"]
    }
    
    MIME_TYPES = {
        ".md": "text/markdown",
        ".markdown": "text/markdown",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".html": "text/html",
        ".htm": "text/html",
        ".json": "application/json"
    }
    
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.chunk_size = kb.chunk_size
        self.chunk_overlap = kb.chunk_overlap
        self.chunking_strategy = kb.chunking_strategy
    
    @classmethod
    def get_file_type(cls, filename: str) -> Optional[str]:
        """Determine file type from extension"""
        ext = os.path.splitext(filename)[1].lower()
        for file_type, extensions in cls.SUPPORTED_TYPES.items():
            if ext in extensions:
                return file_type
        return None
    
    @classmethod
    def get_mime_type(cls, filename: str) -> str:
        """Get MIME type from filename"""
        ext = os.path.splitext(filename)[1].lower()
        return cls.MIME_TYPES.get(ext, "application/octet-stream")
    
    def extract_text(self, file_path: str, file_type: str) -> str:
        """Extract text content from document"""
        try:
            if file_type == "markdown":
                return self._extract_markdown(file_path)
            elif file_type == "pdf":
                return self._extract_pdf(file_path)
            elif file_type == "txt":
                return self._extract_txt(file_path)
            elif file_type == "docx":
                return self._extract_docx(file_path)
            elif file_type == "csv":
                return self._extract_csv(file_path)
            elif file_type == "xlsx":
                return self._extract_xlsx(file_path)
            elif file_type == "html":
                return self._extract_html(file_path)
            elif file_type == "json":
                return self._extract_json(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            traceback.print_exc()
            raise
    
    def _extract_markdown(self, file_path: str) -> str:
        """Extract text from markdown file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_txt(self, file_path: str) -> str:
        """Extract text from plain text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            import fitz  # PyMuPDF
            
            text_parts = []
            with fitz.open(file_path) as pdf:
                for page_num in range(pdf.page_count):
                    page = pdf[page_num]
                    text = page.get_text()
                    if text.strip():
                        text_parts.append(f"[Page {page_num + 1}]\n{text}")
            
            return "\n\n".join(text_parts)
        except ImportError:
            # Fallback to pdfplumber if PyMuPDF not available
            import pdfplumber
            
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        text_parts.append(f"[Page {i + 1}]\n{text}")
            
            return "\n\n".join(text_parts)
    
    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        from docx import Document as DocxDocument
        
        doc = DocxDocument(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n\n".join(paragraphs)
    
    def _extract_csv(self, file_path: str) -> str:
        """Extract text from CSV file"""
        import pandas as pd
        
        df = pd.read_csv(file_path)
        return df.to_string(index=False)
    
    def _extract_xlsx(self, file_path: str) -> str:
        """Extract text from Excel file"""
        import pandas as pd
        
        # Read all sheets
        xl = pd.ExcelFile(file_path)
        text_parts = []
        
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name)
            text_parts.append(f"[Sheet: {sheet_name}]\n{df.to_string(index=False)}")
        
        return "\n\n".join(text_parts)
    
    def _extract_html(self, file_path: str) -> str:
        """Extract text from HTML file"""
        from bs4 import BeautifulSoup
        
        with open(file_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            return soup.get_text(separator='\n', strip=True)
    
    def _extract_json(self, file_path: str) -> str:
        """Extract text from JSON file"""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, indent=2, ensure_ascii=False)
    
    def chunk_text(self, text: str, file_type: str = "txt") -> List[dict]:
        """Split text into chunks"""
        splitter = self._get_text_splitter(file_type)
        
        # Split text
        chunks = splitter.split_text(text)
        
        # Create chunk data
        result = []
        current_pos = 0
        
        for i, chunk_text in enumerate(chunks):
            # Find position in original text
            start_char = text.find(chunk_text, current_pos)
            if start_char == -1:
                start_char = current_pos
            end_char = start_char + len(chunk_text)
            current_pos = end_char
            
            # Extract page number if present
            page_match = re.search(r'\[Page (\d+)\]', chunk_text)
            page_number = int(page_match.group(1)) if page_match else 0
            
            result.append({
                "content": chunk_text,
                "chunk_index": i,
                "start_char": start_char,
                "end_char": end_char,
                "page_number": page_number,
                "metadata": {}
            })
        
        return result
    
    def _get_text_splitter(self, file_type: str):
        """Get appropriate text splitter based on strategy and file type"""
        if self.chunking_strategy == ChunkingStrategy.RECURSIVE or self.chunking_strategy == "recursive":
            if file_type == "markdown":
                return MarkdownTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
            else:
                return RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
                )
        
        elif self.chunking_strategy == ChunkingStrategy.FIXED_SIZE or self.chunking_strategy == "fixed_size":
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator=""
            )
        
        elif self.chunking_strategy == ChunkingStrategy.PARAGRAPH or self.chunking_strategy == "paragraph":
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n\n"
            )
        
        elif self.chunking_strategy == ChunkingStrategy.SENTENCE or self.chunking_strategy == "sentence":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["。", "！", "？", ".", "!", "?", "\n"]
            )
        
        else:
            # Default to recursive
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
    
    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """Add embeddings to chunks"""
        embedding_model = EmbeddingModelCache.get_embedding_model()
        
        if not embedding_model:
            logger.warning("No embedding model available, skipping embeddings")
            return chunks
        
        texts = [chunk["content"] for chunk in chunks]
        
        try:
            embeddings = embedding_model.embed_documents(texts)
            
            for i, chunk in enumerate(chunks):
                chunk["embedding"] = embeddings[i]
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            traceback.print_exc()
        
        return chunks
    
    def process_document(self, file_path: str, file_type: str) -> List[dict]:
        """Full document processing pipeline: extract, chunk, embed"""
        # Extract text
        text = self.extract_text(file_path, file_type)
        
        if not text.strip():
            raise ValueError("Document is empty or could not be extracted")
        
        # Chunk text
        chunks = self.chunk_text(text, file_type)
        
        if not chunks:
            raise ValueError("No chunks created from document")
        
        # Add embeddings
        chunks = self.embed_chunks(chunks)
        
        SQLBotLogUtil.info(f"Processed document: {len(chunks)} chunks created")
        
        return chunks


def process_document_async(doc_id: int, kb_id: int, oid: int):
    """Background task to process a document"""
    from apps.db.db import engine
    from sqlmodel import Session
    from apps.knowledge_base.crud.knowledge_crud import (
        get_document, update_document_status, create_chunks, get_knowledge_base
    )
    
    with Session(engine) as session:
        doc = get_document(session, doc_id, oid)
        if not doc:
            logger.error(f"Document {doc_id} not found")
            return
        
        kb = get_knowledge_base(session, kb_id, oid)
        if not kb:
            logger.error(f"Knowledge base {kb_id} not found")
            return
        
        try:
            # Update status to processing
            update_document_status(session, doc_id, "processing")
            
            # Process document
            processor = DocumentProcessor(kb)
            chunks = processor.process_document(doc.file_path, doc.file_type)
            
            # Save chunks
            create_chunks(session, doc_id, kb_id, oid, chunks)
            
            SQLBotLogUtil.info(f"Document {doc_id} processed successfully: {len(chunks)} chunks")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing document {doc_id}: {error_msg}")
            traceback.print_exc()
            update_document_status(session, doc_id, "failed", 0, error_msg)
