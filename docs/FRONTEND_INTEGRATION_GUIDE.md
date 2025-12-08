# 综合知识库 - 前端集成指南

## 一、新增页面结构

### 路由配置

```typescript
// frontend/src/router/index.ts 中新增

const knowledgeBaseRoutes = [
  {
    path: '/knowledge-base',
    component: () => import('@/views/knowledge-base/Layout.vue'),
    children: [
      {
        path: 'sources',
        name: 'KBSources',
        component: () => import('@/views/knowledge-base/Sources.vue'),
        meta: { title: '知识源管理' }
      },
      {
        path: 'sources/create/:type',
        name: 'CreateSource',
        component: () => import('@/views/knowledge-base/CreateSource.vue'),
        meta: { title: '创建知识源' }
      },
      {
        path: 'sources/:id',
        name: 'SourceDetail',
        component: () => import('@/views/knowledge-base/SourceDetail.vue'),
        meta: { title: '知识源详情' }
      },
      {
        path: 'search',
        name: 'KBSearch',
        component: () => import('@/views/knowledge-base/Search.vue'),
        meta: { title: '知识库搜索' }
      },
      {
        path: 'graph',
        name: 'KnowledgeGraph',
        component: () => import('@/views/knowledge-base/Graph.vue'),
        meta: { title: '知识图谱' }
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/knowledge-base/Documents.vue'),
        meta: { title: '知识文档' }
      }
    ]
  }
]
```

## 二、核心组件

### 1. Sources.vue - 知识源列表

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus-secondary'
import { kbApi } from '@/api/knowledge-base'
import SourceCard from '@/views/knowledge-base/components/SourceCard.vue'
import SyncMonitor from '@/views/knowledge-base/components/SyncMonitor.vue'

interface KBSource {
  id: number
  oid: number
  name: string
  source_type: 'database' | 'git' | 'local_code' | 'document' | 'api'
  description: string
  configuration: Record<string, any>
  status: string
  create_time: string
  create_by: number
  sync_info?: {
    last_sync_time: string
    status: 'running' | 'success' | 'failed' | 'pending'
    sync_count: number
    doc_count: number
  }
}

const sources = ref<KBSource[]>([])
const loading = ref(false)
const selectedType = ref('')
const searchKeyword = ref('')

const filteredSources = computed(() => {
  return sources.value.filter(source => {
    const matchType = !selectedType.value || source.source_type === selectedType.value
    const matchKeyword = !searchKeyword.value || 
      source.name.toLowerCase().includes(searchKeyword.value.toLowerCase()) ||
      source.description.toLowerCase().includes(searchKeyword.value.toLowerCase())
    return matchType && matchKeyword
  })
})

const sourceTypes = [
  { value: 'database', label: '数据库源', icon: 'icon_database' },
  { value: 'git', label: 'Git仓库', icon: 'icon_git' },
  { value: 'local_code', label: '本地代码', icon: 'icon_folder' },
  { value: 'document', label: '文档源', icon: 'icon_doc' },
  { value: 'api', label: 'API源', icon: 'icon_api' }
]

onMounted(async () => {
  await loadSources()
})

async function loadSources() {
  loading.value = true
  try {
    const response = await kbApi.listSources()
    sources.value = response.data
  } finally {
    loading.value = false
  }
}

async function handleDelete(sourceId: number) {
  try {
    await ElMessageBox.confirm(
      '确定删除该知识源及其所有数据吗？此操作不可撤销。',
      '警告',
      { type: 'warning' }
    )
    
    await kbApi.deleteSource(sourceId)
    ElMessage.success('删除成功')
    await loadSources()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

async function handleSync(sourceId: number, syncType: 'full' | 'incremental' = 'full') {
  try {
    const response = await kbApi.triggerSync(sourceId, syncType)
    ElMessage.success('同步已启动')
    // 通过WebSocket监听同步进度
  } catch (err) {
    ElMessage.error('启动同步失败')
  }
}

function handleAddSource(type: string) {
  useRouter().push({
    name: 'CreateSource',
    params: { type }
  })
}
</script>

<template>
  <div class="kb-sources-container">
    <!-- 头部 -->
    <div class="header">
      <h1>知识源管理</h1>
      <p>管理和同步多种类型的知识源</p>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索知识源..."
        class="search-input"
      >
        <template #prefix>
          <icon_search />
        </template>
      </el-input>

      <el-select
        v-model="selectedType"
        placeholder="筛选类型"
        clearable
        class="type-filter"
      >
        <el-option
          v-for="type in sourceTypes"
          :key="type.value"
          :value="type.value"
          :label="type.label"
        />
      </el-select>

      <!-- 创建按钮组 -->
      <el-dropdown @command="handleAddSource">
        <el-button type="primary">
          <template #icon><icon_add /></template>
          新建知识源
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item
                v-for="type in sourceTypes"
                :key="type.value"
                :command="type.value"
              >
                {{ type.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-button>
      </el-dropdown>
    </div>

    <!-- 源卡片网格 -->
    <div v-if="!loading" class="sources-grid">
      <SourceCard
        v-for="source in filteredSources"
        :key="source.id"
        :source="source"
        @delete="handleDelete"
        @sync="handleSync"
        @refresh="loadSources"
      />
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="!loading && filteredSources.length === 0"
      description="暂无知识源，点击新建按钮添加"
    />

    <!-- 加载中 -->
    <div v-if="loading" class="loading">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 同步监控面板（可选，使用抽屉展示） -->
    <SyncMonitor v-if="sources.length > 0" />
  </div>
</template>

<style scoped lang="less">
.kb-sources-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  .header {
    margin-bottom: 24px;

    h1 {
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: bold;
    }

    p {
      margin: 0;
      color: #666;
    }
  }

  .toolbar {
    display: flex;
    gap: 12px;
    margin-bottom: 24px;
    background: white;
    padding: 16px;
    border-radius: 4px;

    .search-input {
      width: 300px;
    }

    .type-filter {
      width: 150px;
    }
  }

  .sources-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }

  .loading {
    padding: 20px;
    background: white;
    border-radius: 4px;
  }
}
</style>
```

### 2. CreateSource.vue - 创建/编辑知识源

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus-secondary'
import { kbApi } from '@/api/knowledge-base'

import GitRepoForm from '@/views/knowledge-base/forms/GitRepoForm.vue'
import LocalCodeForm from '@/views/knowledge-base/forms/LocalCodeForm.vue'
import DatabaseForm from '@/views/knowledge-base/forms/DatabaseForm.vue'
import DocumentForm from '@/views/knowledge-base/forms/DocumentForm.vue'

const route = useRoute()
const router = useRouter()

const sourceType = computed(() => route.params.type as string)

const form = ref({
  name: '',
  description: '',
  source_type: sourceType.value,
  configuration: {} as Record<string, any>
})

const loading = ref(false)
const testing = ref(false)

async function handleSubmit() {
  loading.value = true
  try {
    // 验证配置
    if (!form.value.name.trim()) {
      ElMessage.error('请输入知识源名称')
      return
    }

    await kbApi.createSource({
      name: form.value.name,
      description: form.value.description,
      source_type: sourceType.value,
      configuration: form.value.configuration
    })

    ElMessage.success('知识源创建成功')
    router.push({ name: 'KBSources' })
  } catch (err) {
    ElMessage.error('创建失败')
  } finally {
    loading.value = false
  }
}

async function handleTest() {
  testing.value = true
  try {
    const result = await kbApi.testSource({
      source_type: sourceType.value,
      configuration: form.value.configuration
    })

    if (result.data.success) {
      ElMessage.success('连接测试成功！')
    } else {
      ElMessage.error(`测试失败: ${result.data.message}`)
    }
  } finally {
    testing.value = false
  }
}
</script>

<template>
  <div class="create-source-container">
    <el-card>
      <template #header>
        <div class="header">
          <h2>创建 {{ sourceTypeLabel }} 知识源</h2>
        </div>
      </template>

      <el-form :model="form" label-width="120px">
        <!-- 基本信息 -->
        <el-form-item label="源名称" required>
          <el-input
            v-model="form.name"
            placeholder="输入知识源名称"
            maxlength="128"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="描述">
          <el-input
            v-model="form.description"
            type="textarea"
            placeholder="输入知识源描述"
            maxlength="512"
            show-word-limit
            :rows="3"
          />
        </el-form-item>

        <!-- 根据类型显示不同的表单 -->
        <GitRepoForm
          v-if="sourceType === 'git'"
          v-model:configuration="form.configuration"
        />

        <LocalCodeForm
          v-if="sourceType === 'local_code'"
          v-model:configuration="form.configuration"
        />

        <DatabaseForm
          v-if="sourceType === 'database'"
          v-model:configuration="form.configuration"
        />

        <DocumentForm
          v-if="sourceType === 'document'"
          v-model:configuration="form.configuration"
        />

        <!-- 按钮 -->
        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            创建知识源
          </el-button>

          <el-button @click="handleTest" :loading="testing">
            测试连接
          </el-button>

          <el-button @click="$router.back()">
            取消
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped lang="less">
.create-source-container {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;

  :deep(.el-card) {
    max-width: 800px;
    margin: 0 auto;
  }
}
</style>
```

### 3. Search.vue - 统一搜索

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { kbApi } from '@/api/knowledge-base'
import ResultCard from '@/views/knowledge-base/components/ResultCard.vue'

interface SearchResult {
  document: {
    id: number
    content: string
    metadata: Record<string, any>
  }
  source_name: string
  source_type: string
  similarity: number
}

const query = ref('')
const searching = ref(false)
const results = ref<SearchResult[]>([])
const selectedSourceType = ref('')
const topK = ref(10)

const sourceTypes = ['database', 'git', 'local_code', 'document', 'api']

async function handleSearch() {
  if (!query.value.trim()) return

  searching.value = true
  try {
    const response = await kbApi.search({
      query: query.value,
      top_k: topK.value,
      source_type: selectedSourceType.value || undefined
    })

    results.value = response.data.results
  } finally {
    searching.value = false
  }
}

// 高亮匹配的文本
function highlightText(text: string, query: string): string {
  const regex = new RegExp(`(${query})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

// 预览处理
function getPreview(content: string, maxLen: number = 200): string {
  return content.length > maxLen ? content.substring(0, maxLen) + '...' : content
}
</script>

<template>
  <div class="kb-search-container">
    <!-- 搜索框 -->
    <div class="search-section">
      <h1>知识库搜索</h1>

      <div class="search-box">
        <el-input
          v-model="query"
          placeholder="输入问题或关键词..."
          @keyup.enter="handleSearch"
          clearable
          size="large"
        >
          <template #prefix>
            <icon_search />
          </template>
        </el-input>

        <el-button
          type="primary"
          size="large"
          @click="handleSearch"
          :loading="searching"
        >
          搜索
        </el-button>
      </div>

      <!-- 高级选项 -->
      <div class="advanced-options">
        <el-select
          v-model="selectedSourceType"
          placeholder="所有源类型"
          clearable
          class="source-type-filter"
        >
          <el-option
            v-for="type in sourceTypes"
            :key="type"
            :value="type"
            :label="type"
          />
        </el-select>

        <el-select v-model="topK" placeholder="结果数量">
          <el-option value="5" label="5条" />
          <el-option value="10" label="10条" />
          <el-option value="20" label="20条" />
          <el-option value="50" label="50条" />
        </el-select>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="results.length > 0" class="results-section">
      <div class="result-count">
        找到 <strong>{{ results.length }}</strong> 条相关结果
      </div>

      <div class="results-list">
        <ResultCard
          v-for="(result, index) in results"
          :key="result.document.id"
          :result="result"
          :index="index + 1"
        />
      </div>
    </div>

    <!-- 空状态 -->
    <el-empty
      v-if="!searching && results.length === 0 && query"
      description="未找到相关结果"
    />
  </div>
</template>

<style scoped lang="less">
.kb-search-container {
  padding: 40px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e9ecf1 100%);
  min-height: 100vh;

  .search-section {
    max-width: 900px;
    margin: 0 auto 40px;

    h1 {
      text-align: center;
      font-size: 32px;
      margin-bottom: 30px;
      color: #333;
    }

    .search-box {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;

      :deep(.el-input) {
        flex: 1;
      }
    }

    .advanced-options {
      display: flex;
      gap: 12px;
      justify-content: center;

      select {
        min-width: 150px;
      }
    }
  }

  .results-section {
    max-width: 900px;
    margin: 0 auto;

    .result-count {
      padding: 12px 0;
      margin-bottom: 20px;
      color: #666;
    }

    .results-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
  }
}
</style>
```

## 三、API调用层

### knowledge-base.ts API定义

```typescript
// frontend/src/api/knowledge-base.ts

import { request } from '@/utils/request'

export const kbApi = {
  // 知识源管理
  listSources: () => request.get('/knowledge-base/sources'),
  
  createSource: (data: any) => 
    request.post('/knowledge-base/sources', data),
  
  updateSource: (id: number, data: any) => 
    request.put(`/knowledge-base/sources/${id}`, data),
  
  deleteSource: (id: number) => 
    request.delete(`/knowledge-base/sources/${id}`),
  
  getSourceDetail: (id: number) => 
    request.get(`/knowledge-base/sources/${id}`),
  
  testSource: (data: any) => 
    request.post('/knowledge-base/sources/test', data),
  
  // 同步管理
  triggerSync: (sourceId: number, syncType: string = 'full') => 
    request.post(`/knowledge-base/sources/${sourceId}/sync`, { sync_type: syncType }),
  
  getSyncStatus: (syncId: number) => 
    request.get(`/knowledge-base/sync/${syncId}`),
  
  cancelSync: (syncId: number) => 
    request.post(`/knowledge-base/sync/${syncId}/cancel`),
  
  getSyncLogs: (sourceId: number) => 
    request.get(`/knowledge-base/sources/${sourceId}/sync-logs`),
  
  // 搜索
  search: (params: any) => 
    request.post('/knowledge-base/search', params),
  
  hybridSearch: (params: any) => 
    request.post('/knowledge-base/search/hybrid', params),
  
  // 知识图谱
  getKnowledgeGraph: (sourceId: number) => 
    request.get(`/knowledge-base/sources/${sourceId}/graph`),
  
  // 文档管理
  listDocuments: (sourceId: number, params?: any) => 
    request.get(`/knowledge-base/sources/${sourceId}/documents`, { params }),
  
  getDocument: (documentId: number) => 
    request.get(`/knowledge-base/documents/${documentId}`),
  
  deleteDocument: (documentId: number) => 
    request.delete(`/knowledge-base/documents/${documentId}`)
}
```

## 四、在Chat中集成知识库

修改现有的Chat组件以支持知识库搜索：

```typescript
// 在chat消息生成流程中，在生成LLM prompt前：

async function generatePromptWithKnowledge(userQuery: string, aiModel: any) {
  // 1. 搜索知识库
  const searchResults = await kbApi.search({
    query: userQuery,
    top_k: 5
  })
  
  // 2. 格式化知识上下文
  const knowledgeContext = formatKnowledgeContext(searchResults)
  
  // 3. 构建增强提示词
  const enhancedPrompt = `
根据以下知识库信息回答用户问题：

【知识库信息】
${knowledgeContext}

【用户问题】
${userQuery}

请基于上述知识库信息提供准确、详细的回答。
`
  
  return enhancedPrompt
}

function formatKnowledgeContext(results: SearchResult[]): string {
  return results.map((r, i) => `
[来源 ${i + 1}: ${r.source_name} (${r.source_type})] 
相似度: ${(r.similarity * 100).toFixed(0)}%
${r.document.content.substring(0, 300)}...
`).join('\n')
}
```

## 五、主题和样式

推荐使用统一的设计系统，参考现有DataEase设计语言。

## 六、性能优化

1. **虚拟滚动**：对于大量搜索结果使用虚拟滚动
2. **图片懒加载**：源卡片上的图标和预览
3. **缓存**：缓存热门搜索和最近访问的源
4. **分页**：搜索结果分页加载

## 七、可访问性

- 确保所有交互元素都可通过键盘访问
- 添加适当的ARIA标签
- 确保颜色对比满足WCAG标准
