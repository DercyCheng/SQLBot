import request from '@/utils/request'

// ==================== Knowledge Base APIs ====================

export interface KnowledgeBaseInfo {
    id?: number
    name: string
    description?: string
    embedding_model?: string
    chunk_size?: number
    chunk_overlap?: number
    chunking_strategy?: string
    similarity_threshold?: number
    top_k?: number
    datasource_ids?: number[]
    enabled?: boolean
    document_count?: number
    chunk_count?: number
    create_time?: string
    update_time?: string
}

export interface DocumentInfo {
    id?: number
    kb_id: number
    name: string
    original_filename: string
    file_size?: number
    file_type: string
    mime_type?: string
    index_status: string
    chunk_count?: number
    error_message?: string
    metadata?: Record<string, any>
    enabled?: boolean
    create_time?: string
    update_time?: string
    processed_time?: string
}

export interface SearchResult {
    chunk_id: number
    document_id: number
    document_name: string
    kb_id: number
    kb_name: string
    content: string
    score: number
    page_number?: number
    metadata?: Record<string, any>
}

// Get all knowledge bases
export const getAllKnowledgeBases = () => {
    return request({
        url: '/api/v1/system/knowledge-base/list',
        method: 'get'
    })
}

// Get paginated knowledge bases
export const getKnowledgeBases = (
    currentPage: number,
    pageSize: number,
    params?: { name?: string }
) => {
    return request({
        url: `/api/v1/system/knowledge-base/page/${currentPage}/${pageSize}`,
        method: 'get',
        params
    })
}

// Get knowledge base detail
export const getKnowledgeBase = (kbId: number) => {
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}`,
        method: 'get'
    })
}

// Create knowledge base
export const createKnowledgeBase = (data: KnowledgeBaseInfo) => {
    return request({
        url: '/api/v1/system/knowledge-base',
        method: 'post',
        data
    })
}

// Update knowledge base
export const updateKnowledgeBase = (kbId: number, data: KnowledgeBaseInfo) => {
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}`,
        method: 'put',
        data
    })
}

// Delete knowledge bases
export const deleteKnowledgeBases = (kbIds: number[]) => {
    return request({
        url: '/api/v1/system/knowledge-base',
        method: 'delete',
        data: kbIds
    })
}

// Get documents in a knowledge base
export const getDocuments = (
    kbId: number,
    currentPage: number,
    pageSize: number,
    params?: { name?: string; status?: string }
) => {
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}/documents/page/${currentPage}/${pageSize}`,
        method: 'get',
        params
    })
}

// Upload document
export const uploadDocument = (kbId: number, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}/documents/upload`,
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        data: formData
    })
}

// Batch upload documents
export const batchUploadDocuments = (kbId: number, files: File[]) => {
    const formData = new FormData()
    files.forEach(file => {
        formData.append('files', file)
    })
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}/documents/batch-upload`,
        method: 'post',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        data: formData
    })
}

// Delete documents
export const deleteDocuments = (kbId: number, docIds: number[]) => {
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}/documents`,
        method: 'delete',
        data: docIds
    })
}

// Reprocess document
export const reprocessDocument = (kbId: number, docId: number) => {
    return request({
        url: `/api/v1/system/knowledge-base/${kbId}/documents/${docId}/reprocess`,
        method: 'post'
    })
}

// Search knowledge bases
export const searchKnowledgeBase = (data: {
    query: string
    kb_ids: number[]
    top_k?: number
    similarity_threshold?: number
}) => {
    return request({
        url: '/api/v1/system/knowledge-base/search',
        method: 'post',
        data
    })
}

// Get supported document types
export const getSupportedTypes = () => {
    return request({
        url: '/api/v1/system/knowledge-base/supported-types',
        method: 'get'
    })
}
