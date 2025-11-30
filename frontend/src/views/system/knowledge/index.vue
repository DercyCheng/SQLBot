<template>
  <div class="knowledge-base-container">
    <div class="left-panel">
      <div class="panel-header">
        <span class="title">{{ $t('knowledgeBase.title') }}</span>
        <el-button type="primary" size="small" @click="openCreateKbDialog">
          <el-icon><Plus /></el-icon>
        </el-button>
      </div>
      <el-input
        v-model="searchKb"
        :placeholder="$t('knowledgeBase.search_knowledge_base')"
        clearable
        size="small"
        style="margin-bottom: 12px"
        @clear="loadKnowledgeBases"
        @keyup.enter="loadKnowledgeBases"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <div v-loading="kbLoading" class="kb-list">
        <div
          v-for="kb in kbList"
          :key="kb.id"
          :class="['kb-item', { active: selectedKb?.id === kb.id }]"
          @click="selectKb(kb)"
        >
          <div class="kb-info">
            <div class="kb-name">{{ kb.name }}</div>
            <div class="kb-stats">
              {{ $t('knowledgeBase.document_count') }}: {{ kb.document_count }} |
              {{ $t('knowledgeBase.chunk_count') }}: {{ kb.chunk_count }}
            </div>
          </div>
          <div class="kb-actions">
            <el-dropdown trigger="click" @command="handleKbCommand($event, kb)">
              <el-icon><MoreFilled /></el-icon>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">{{ $t('common.edit') }}</el-dropdown-item>
                  <el-dropdown-item command="delete" style="color: #f56c6c">{{ $t('common.delete') }}</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
        <el-empty v-if="kbList.length === 0" :description="$t('knowledgeBase.no_knowledge_base')" />
      </div>
    </div>

    <div class="right-panel">
      <template v-if="selectedKb">
        <div class="panel-header">
          <div class="kb-title">
            <span>{{ selectedKb.name }}</span>
            <el-tag v-if="selectedKb.enabled" type="success" size="small">{{ $t('knowledgeBase.enabled') }}</el-tag>
          </div>
          <div class="actions">
            <el-upload
              ref="uploadRef"
              :show-file-list="false"
              :before-upload="beforeUpload"
              :http-request="uploadFile"
              multiple
              accept=".md,.pdf,.txt,.docx,.csv,.xlsx,.html,.json"
            >
              <el-button type="primary">
                <el-icon><Upload /></el-icon>
                {{ $t('knowledgeBase.upload_document') }}
              </el-button>
            </el-upload>
          </div>
        </div>

        <div class="kb-description" v-if="selectedKb.description">
          {{ selectedKb.description }}
        </div>

        <div class="documents-section">
          <div class="section-header">
            <span class="section-title">{{ $t('knowledgeBase.documents') }}</span>
            <el-input
              v-model="searchDoc"
              :placeholder="$t('common.search')"
              style="width: 200px"
              clearable
              size="small"
              @clear="loadDocuments"
              @keyup.enter="loadDocuments"
            />
          </div>

          <el-table
            v-loading="docLoading"
            :data="docList"
            style="width: 100%"
            @selection-change="handleDocSelection"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" :label="$t('knowledgeBase.file_name')" min-width="200" />
            <el-table-column prop="file_type" :label="$t('knowledgeBase.file_type')" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ getFileTypeLabel(row.file_type) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="file_size" :label="$t('knowledgeBase.file_size')" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column prop="index_status" :label="$t('knowledgeBase.index_status')" width="120">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.index_status)" size="small">
                  {{ getStatusLabel(row.index_status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="chunk_count" :label="$t('knowledgeBase.chunk_count')" width="100" />
            <el-table-column :label="$t('common.operation')" width="150" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" @click="reprocessDoc(row)">
                  {{ $t('knowledgeBase.reprocess') }}
                </el-button>
                <el-button link type="danger" @click="deleteDoc(row)">
                  {{ $t('common.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-container">
            <el-pagination
              v-model:current-page="docCurrentPage"
              v-model:page-size="docPageSize"
              :total="docTotalCount"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @size-change="loadDocuments"
              @current-change="loadDocuments"
            />
          </div>
        </div>
      </template>

      <el-empty v-else :description="$t('knowledgeBase.no_knowledge_base')" />
    </div>

    <!-- Create/Edit KB Dialog -->
    <el-dialog
      v-model="kbDialogVisible"
      :title="isEditKb ? $t('knowledgeBase.edit_kb') : $t('knowledgeBase.create_kb')"
      width="600px"
    >
      <el-form ref="kbFormRef" :model="kbForm" :rules="kbFormRules" label-width="120px">
        <el-form-item :label="$t('knowledgeBase.name')" prop="name">
          <el-input v-model="kbForm.name" />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.description')">
          <el-input v-model="kbForm.description" type="textarea" rows="2" />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.chunk_size')">
          <el-input-number v-model="kbForm.chunk_size" :min="100" :max="2000" />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.chunk_overlap')">
          <el-input-number v-model="kbForm.chunk_overlap" :min="0" :max="500" />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.chunking_strategy')">
          <el-select v-model="kbForm.chunking_strategy" style="width: 100%">
            <el-option value="recursive" :label="$t('knowledgeBase.recursive')" />
            <el-option value="fixed_size" :label="$t('knowledgeBase.fixed_size')" />
            <el-option value="paragraph" :label="$t('knowledgeBase.paragraph')" />
            <el-option value="sentence" :label="$t('knowledgeBase.sentence')" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.similarity_threshold')">
          <el-slider v-model="kbForm.similarity_threshold" :min="0" :max="1" :step="0.05" show-input />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.top_k')">
          <el-input-number v-model="kbForm.top_k" :min="1" :max="20" />
        </el-form-item>
        <el-form-item :label="$t('knowledgeBase.enabled')">
          <el-switch v-model="kbForm.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="kbDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitKbForm">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload, MoreFilled } from '@element-plus/icons-vue'
import { knowledgeBaseApi, type KnowledgeBaseInfo, type DocumentInfo } from '@/api/knowledgeBase'

const { t } = useI18n()

// Knowledge Base State
const kbLoading = ref(false)
const kbList = ref<KnowledgeBaseInfo[]>([])
const selectedKb = ref<KnowledgeBaseInfo | null>(null)
const searchKb = ref('')
const kbDialogVisible = ref(false)
const isEditKb = ref(false)
const kbFormRef = ref()

const kbForm = reactive<KnowledgeBaseInfo>({
  name: '',
  description: '',
  chunk_size: 500,
  chunk_overlap: 50,
  chunking_strategy: 'recursive',
  similarity_threshold: 0.6,
  top_k: 5,
  enabled: true
})

const kbFormRules = {
  name: [{ required: true, message: t('common.please_input', { msg: t('knowledgeBase.name') }), trigger: 'blur' }]
}

// Document State
const docLoading = ref(false)
const docList = ref<DocumentInfo[]>([])
const selectedDocs = ref<DocumentInfo[]>([])
const searchDoc = ref('')
const docCurrentPage = ref(1)
const docPageSize = ref(10)
const docTotalCount = ref(0)
const uploadRef = ref()

// Methods
const loadKnowledgeBases = async () => {
  kbLoading.value = true
  try {
    const res = await knowledgeBaseApi.page(1, 100, { name: searchKb.value || undefined })
    kbList.value = res.data?.data || []
    if (kbList.value.length > 0 && !selectedKb.value) {
      selectKb(kbList.value[0])
    }
  } finally {
    kbLoading.value = false
  }
}

const selectKb = async (kb: KnowledgeBaseInfo) => {
  selectedKb.value = kb
  docCurrentPage.value = 1
  await loadDocuments()
}

const loadDocuments = async () => {
  if (!selectedKb.value?.id) return
  
  docLoading.value = true
  try {
    const res = await knowledgeBaseApi.getDocuments(
      selectedKb.value.id,
      docCurrentPage.value,
      docPageSize.value,
      { name: searchDoc.value || undefined }
    )
    docList.value = res.data?.data || []
    docTotalCount.value = res.data?.total_count || 0
  } finally {
    docLoading.value = false
  }
}

const handleDocSelection = (selection: DocumentInfo[]) => {
  selectedDocs.value = selection
}

const openCreateKbDialog = () => {
  isEditKb.value = false
  Object.assign(kbForm, {
    id: undefined,
    name: '',
    description: '',
    chunk_size: 500,
    chunk_overlap: 50,
    chunking_strategy: 'recursive',
    similarity_threshold: 0.6,
    top_k: 5,
    enabled: true
  })
  kbDialogVisible.value = true
}

const handleKbCommand = async (command: string, kb: KnowledgeBaseInfo) => {
  if (command === 'edit') {
    isEditKb.value = true
    Object.assign(kbForm, kb)
    kbDialogVisible.value = true
  } else if (command === 'delete') {
    await ElMessageBox.confirm(
      t('knowledgeBase.confirm_delete_kb', { msg: '1' }),
      t('common.confirm')
    )
    if (kb.id) {
      await knowledgeBaseApi.delete([kb.id])
      ElMessage.success(t('dashboard.delete_success'))
      if (selectedKb.value?.id === kb.id) {
        selectedKb.value = null
      }
      loadKnowledgeBases()
    }
  }
}

const submitKbForm = async () => {
  await kbFormRef.value?.validate()

  if (isEditKb.value && kbForm.id) {
    await knowledgeBaseApi.update(kbForm.id, kbForm)
    ElMessage.success(t('common.update_success'))
  } else {
    await knowledgeBaseApi.create(kbForm)
    ElMessage.success(t('common.save_success'))
  }
  kbDialogVisible.value = false
  loadKnowledgeBases()
}

const beforeUpload = (file: File) => {
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('File size cannot exceed 50MB')
    return false
  }
  return true
}

const uploadFile = async (options: any) => {
  if (!selectedKb.value?.id) return
  
  try {
    await knowledgeBaseApi.uploadDocument(selectedKb.value.id, options.file)
    ElMessage.success(t('knowledgeBase.upload_success'))
    loadDocuments()
  } catch (error) {
    ElMessage.error(t('knowledgeBase.upload_failed'))
  }
}

const reprocessDoc = async (doc: DocumentInfo) => {
  if (!selectedKb.value?.id || !doc.id) return
  
  await knowledgeBaseApi.reprocessDocument(selectedKb.value.id, doc.id)
  ElMessage.success(t('knowledgeBase.processing_started'))
  loadDocuments()
}

const deleteDoc = async (doc: DocumentInfo) => {
  if (!selectedKb.value?.id || !doc.id) return
  
  await ElMessageBox.confirm(
    t('knowledgeBase.confirm_delete_doc', { msg: '1' }),
    t('common.confirm')
  )
  await knowledgeBaseApi.deleteDocuments(selectedKb.value.id, [doc.id])
  ElMessage.success(t('dashboard.delete_success'))
  loadDocuments()
}

const getFileTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    markdown: t('knowledgeBase.markdown'),
    pdf: t('knowledgeBase.pdf'),
    txt: t('knowledgeBase.txt'),
    docx: t('knowledgeBase.docx'),
    csv: t('knowledgeBase.csv'),
    xlsx: t('knowledgeBase.xlsx'),
    html: t('knowledgeBase.html'),
    json: t('knowledgeBase.json')
  }
  return labels[type] || type
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: t('scheduler.pending'),
    processing: t('knowledgeBase.processing'),
    completed: t('knowledgeBase.completed'),
    failed: t('scheduler.failed')
  }
  return labels[status] || status
}

const formatFileSize = (size: number | undefined) => {
  if (!size) return '-'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(() => {
  loadKnowledgeBases()
})
</script>

<style scoped lang="less">
.knowledge-base-container {
  display: flex;
  height: 100%;
  padding: 20px;
  gap: 20px;

  .left-panel {
    width: 300px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #ebeef5;
    padding-right: 20px;

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .title {
        font-size: 16px;
        font-weight: 600;
      }
    }

    .kb-list {
      flex: 1;
      overflow-y: auto;

      .kb-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        margin-bottom: 8px;
        border: 1px solid transparent;

        &:hover {
          background: #f5f7fa;
        }

        &.active {
          background: #ecf5ff;
          border-color: #409eff;
        }

        .kb-info {
          flex: 1;

          .kb-name {
            font-weight: 500;
            margin-bottom: 4px;
          }

          .kb-stats {
            font-size: 12px;
            color: #909399;
          }
        }

        .kb-actions {
          opacity: 0;
          transition: opacity 0.2s;
        }

        &:hover .kb-actions {
          opacity: 1;
        }
      }
    }
  }

  .right-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      .kb-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 18px;
        font-weight: 600;
      }
    }

    .kb-description {
      color: #606266;
      margin-bottom: 16px;
      padding: 12px;
      background: #f5f7fa;
      border-radius: 8px;
    }

    .documents-section {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;

      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;

        .section-title {
          font-size: 14px;
          font-weight: 500;
        }
      }

      .pagination-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 16px;
      }
    }
  }
}
</style>
