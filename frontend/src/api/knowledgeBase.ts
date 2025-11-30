import { request } from '@/utils/request'

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

const buildQueryString = (params?: Record<string, any>): string => {
  if (!params) return ''
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })
  const queryString = searchParams.toString()
  return queryString ? `?${queryString}` : ''
}

export const knowledgeBaseApi = {
  // Get all knowledge bases
  list: () => request.get('/system/knowledge-base/list'),

  // Get paginated knowledge bases
  page: (currentPage: number, pageSize: number, params?: { name?: string }) =>
    request.get(`/system/knowledge-base/page/${currentPage}/${pageSize}${buildQueryString(params)}`),

  // Get knowledge base detail
  get: (kbId: number) => request.get(`/system/knowledge-base/${kbId}`),

  // Create knowledge base
  create: (data: KnowledgeBaseInfo) => request.post('/system/knowledge-base', data),

  // Update knowledge base
  update: (kbId: number, data: KnowledgeBaseInfo) => request.put(`/system/knowledge-base/${kbId}`, data),

  // Delete knowledge bases
  delete: (kbIds: number[]) => request.post('/system/knowledge-base/batch-delete', kbIds),

  // Get documents in a knowledge base
  getDocuments: (kbId: number, currentPage: number, pageSize: number, params?: { name?: string; status?: string }) =>
    request.get(`/system/knowledge-base/${kbId}/documents/page/${currentPage}/${pageSize}${buildQueryString(params)}`),

  // Upload document
  uploadDocument: (kbId: number, file: File) => request.upload(`/system/knowledge-base/${kbId}/documents/upload`, file),

  // Batch upload documents - upload one by one
  batchUpload: async (kbId: number, files: File[]) => {
    const results = []
    for (const file of files) {
      const result = await request.upload(`/system/knowledge-base/${kbId}/documents/upload`, file)
      results.push(result)
    }
    return results
  },

  // Delete documents
  deleteDocuments: (kbId: number, docIds: number[]) =>
    request.post(`/system/knowledge-base/${kbId}/documents/batch-delete`, docIds),

  // Reprocess document
  reprocessDocument: (kbId: number, docId: number) =>
    request.post(`/system/knowledge-base/${kbId}/documents/${docId}/reprocess`),

  // Search knowledge bases
  search: (data: { query: string; kb_ids: number[]; top_k?: number; similarity_threshold?: number }) =>
    request.post('/system/knowledge-base/search', data),

  // Get supported document types
  getSupportedTypes: () => request.get('/system/knowledge-base/supported-types'),
}
