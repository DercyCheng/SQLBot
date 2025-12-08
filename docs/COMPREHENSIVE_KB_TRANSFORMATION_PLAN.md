# SQLBot 综合性知识库改造方案

## 一、项目现状分析

### 当前架构
- **核心定位**：基于大模型和RAG的智能问数系统（Text-to-SQL）
- **主要功能**：
  - 多数据源支持（MySQL、PostgreSQL、SQL Server等数据库）
  - 术语库管理（Terminology）
  - 数据训练（Data Training）
  - 知识库基础（Knowledge Base模块）
  - AI模型管理
  - ChatBI对话分析

### 现有知识库能力
1. **Document处理**：PDF、DOCX、Excel等
2. **向量化**：使用LangChain + Sentence Transformers + pgvector
3. **Embedding存储**：PostgreSQL + pgvector扩展
4. **术语管理**：业务术语的定义和标准化

---

## 二、综合性知识库改造方向

### 2.1 数据源扩展架构

```
┌─────────────────────────────────────────────────────┐
│          综合知识库统一入口 (Knowledge Store)        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │数据库源  │  │代码仓库  │  │文档源   │  ...     │
│  │(Database)│  │(Git Repo)│  │(Docs)   │         │
│  └────┬─────┘  └────┬─────┘  └────┬────┘         │
│       │             │             │              │
│  ┌────────────────────────────────────────────┐  │
│  │        统一提取/转换层 (ETL Layer)         │  │
│  │  • Schema解析 • Code解析 • Doc解析      │  │
│  │  • 关系提取 • 块划分 • 元数据生成        │  │
│  └────────────────────────────────────────────┘  │
│       │                                          │
│  ┌────────────────────────────────────────────┐  │
│  │        向量化与索引层 (Embedding Layer)    │  │
│  │  • 多种Embedding模型支持                   │  │
│  │  • 混合索引（向量+关键词）                │  │
│  │  • 增量更新机制                          │  │
│  └────────────────────────────────────────────┘  │
│       │                                          │
│  ┌────────────────────────────────────────────┐  │
│  │    存储层 (Persistence Layer)              │  │
│  │  • PostgreSQL (结构化 + pgvector)         │  │
│  │  • Redis (缓存)                          │  │
│  │  • 可选：Milvus/Weaviate等向量DB         │  │
│  └────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 支持的数据源类型

#### A. 数据库源（已支持）
- MySQL、PostgreSQL、SQL Server、Oracle等
- 提取Schema、表关系、数据统计

#### B. 代码仓库源（新增）
- **Git仓库**：GitHub、GitLab、Gitee等
  - 提取代码文件树
  - 解析代码注释和文档字符串
  - 识别函数/类/模块关系
  - 提取README、Wiki等
  
- **本地代码目录**：扫描本地路径
  - 支持多种语言（Python、Java、Go、JavaScript等）
  - 代码行级索引

#### C. 文档源（增强）
- **文档库**：Markdown、Wiki、Notion等
- **API文档**：Swagger/OpenAPI、PostMan集合
- **知识库平台**：Confluence、语雀等

#### D. 其他源
- **数据文件**：CSV、JSON、XML
- **结构化数据**：API端点、数据集
- **实时源**：日志、事件流（可选）

---

## 三、具体改造方案

### Phase 1: 数据库层扩展（基础）

#### 新增表结构

```sql
-- 知识源管理表
CREATE TABLE kb_source (
    id BIGSERIAL PRIMARY KEY,
    oid BIGINT NOT NULL,
    name VARCHAR(128) NOT NULL,
    source_type VARCHAR(32) NOT NULL,  -- 'database', 'git', 'document', 'api', 'local_code'
    description TEXT,
    configuration JSONB,  -- 根据source_type存储不同配置
    status VARCHAR(32),
    create_time TIMESTAMP,
    create_by BIGINT,
    update_time TIMESTAMP,
    update_by BIGINT
);

-- 知识块表（统一）
CREATE TABLE kb_document (
    id BIGSERIAL PRIMARY KEY,
    kb_source_id BIGINT NOT NULL,  -- 关联kb_source
    doc_type VARCHAR(32),  -- 'schema', 'code', 'doc', 'data'
    content TEXT,
    metadata JSONB,  -- 存储源信息：文件路径、行号、语言等
    embedding vector(1536),  -- pgvector嵌入
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY(kb_source_id) REFERENCES kb_source(id)
);

-- 知识关系表（追踪源间联系）
CREATE TABLE kb_relation (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    relation_type VARCHAR(32),  -- 'references', 'depends_on', 'related_to'
    metadata JSONB,
    FOREIGN KEY(source_id) REFERENCES kb_document(id),
    FOREIGN KEY(target_id) REFERENCES kb_document(id)
);

-- 同步记录表
CREATE TABLE kb_sync_log (
    id BIGSERIAL PRIMARY KEY,
    kb_source_id BIGINT NOT NULL,
    sync_type VARCHAR(32),  -- 'full', 'incremental'
    status VARCHAR(32),  -- 'pending', 'running', 'success', 'failed'
    message TEXT,
    stats JSONB,  -- {docs_added: X, docs_updated: Y, docs_deleted: Z}
    start_time TIMESTAMP,
    end_time TIMESTAMP
);
```

### Phase 2: 后端服务扩展

#### 2.1 新增模块结构

```
backend/apps/knowledge_base/
├── __init__.py
├── api/
│   ├── kb_source.py          # 知识源管理API
│   ├── kb_document.py        # 知识块管理API
│   ├── kb_search.py          # 统一搜索API
│   └── kb_sync.py            # 同步API
├── models/
│   ├── kb_source.py
│   ├── kb_document.py
│   ├── kb_relation.py
│   └── kb_sync_log.py
├── services/
│   ├── __init__.py
│   ├── kb_service.py         # 核心知识库服务
│   ├── sync_service.py       # 数据同步服务
│   └── search_service.py     # 搜索服务
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py     # 基础提取器
│   ├── database_extractor.py # 数据库源提取
│   ├── git_extractor.py      # Git仓库提取
│   ├── code_extractor.py     # 本地代码提取
│   ├── document_extractor.py # 文档提取
│   └── parser/
│       ├── code_parser.py    # 代码解析（支持多语言）
│       ├── doc_parser.py     # 文档解析
│       └── sql_parser.py     # SQL解析
├── crud/
│   ├── kb_source.py
│   ├── kb_document.py
│   └── kb_relation.py
└── utils/
    ├── chunk_util.py         # 文本分块
    ├── embedding_util.py     # 向量化
    └── sync_util.py          # 同步工具
```

#### 2.2 核心服务实现框架

**kb_service.py** - 知识库核心服务
```python
class KnowledgeBaseService:
    def __init__(self, session_maker, cache):
        self.session_maker = session_maker
        self.cache = cache
    
    # 源管理
    async def create_source(self, source_config: KBSourceConfig) -> KBSource
    async def update_source(self, source_id: int, config: KBSourceConfig)
    async def delete_source(self, source_id: int)
    async def list_sources(self, oid: int) -> List[KBSource]
    
    # 同步管理
    async def trigger_sync(self, source_id: int, sync_type: str = 'full')
    async def get_sync_status(self, sync_id: int)
    async def cancel_sync(self, sync_id: int)
    
    # 搜索
    async def search(self, query: str, oid: int, filters: Optional[Dict]) -> List[SearchResult]
    async def hybrid_search(self, query: str, oid: int, top_k: int = 10) -> List[SearchResult]
    
    # 内部方法
    async def _extract_and_index(self, source: KBSource)
    async def _update_relations(self, source_id: int)
    async def _refresh_embeddings(self, source_id: int)
```

**sync_service.py** - 同步引擎
```python
class SyncService:
    async def sync_database_source(self, source: GitRepoSource)
    async def sync_git_source(self, source: GitRepoSource)
    async def sync_code_source(self, source: LocalCodeSource)
    async def sync_document_source(self, source: DocumentSource)
    
    # 支持增量更新
    async def incremental_sync(self, source: KBSource, last_sync: datetime)
```

#### 2.3 提取器实现

**extractors/git_extractor.py** - Git仓库提取
```python
class GitExtractor(BaseExtractor):
    async def extract(self, config: GitRepoConfig) -> List[DocumentChunk]:
        """
        1. Clone/Pull仓库
        2. 递归扫描目录
        3. 识别代码文件和文档
        4. 解析README、Wiki
        5. 提取代码结构和注释
        6. 构建关系图
        """
        
    async def parse_code_file(self, file_path: str, language: str) -> CodeStructure
        # 使用tree-sitter或language-specific parser
        # 提取：函数/类定义、注释、文档字符串
        # 构建：符号表、调用图
        
    async def detect_language(self, file_path: str) -> str
        # 根据扩展名和文件内容识别语言
```

**extractors/code_parser.py** - 代码解析器
```python
class CodeParser:
    """支持多语言代码解析"""
    
    async def parse(self, file_path: str) -> CodeStructure:
        # Python、Java、Go、JavaScript等
        # 返回：符号表、注释、依赖
        
    def extract_docstring(self, node) -> str
    def extract_type_hints(self, node) -> Dict
    def build_dependency_graph(self, code_nodes) -> Graph
```

### Phase 3: 前端页面扩展

#### 新增页面路由

```
/knowledge-base/
├── sources/           # 知识源管理
│   ├── index          # 源列表
│   ├── create         # 新建源
│   └── [id]/detail    # 源详情和同步管理
├── documents/         # 知识块浏览
├── search/            # 统一搜索
├── graph/             # 知识图谱可视化
└── settings/          # 知识库配置
```

#### 主要组件

- **KnowledgeSourceManager**: 源管理组件
- **GitRepoConfig**: Git配置表单
- **CodeRepoConfig**: 本地代码配置表单
- **SyncMonitor**: 同步监控面板
- **KnowledgeGraph**: 知识关系可视化（使用D3/Cytoscape）
- **UnifiedSearch**: 统一搜索界面

---

## 四、实现优先级与时间表

### Sprint 1（2周）：基础设施
- [ ] 数据库表设计和迁移
- [ ] Git提取器实现（基础版）
- [ ] 代码解析器框架
- [ ] 后端API框架

### Sprint 2（2周）：核心功能
- [ ] Git提取器完善（支持增量同步）
- [ ] 本地代码提取器实现
- [ ] 向量化和索引优化
- [ ] 搜索服务实现

### Sprint 3（1周）：前端和集成
- [ ] 前端UI实现
- [ ] 知识图谱可视化
- [ ] 集成到现有Chat界面
- [ ] 测试和文档

### Sprint 4（可选增强）
- [ ] API文档源支持
- [ ] 实时同步机制
- [ ] 知识图谱关系学习
- [ ] 性能优化

---

## 五、技术栈建议

### 新增依赖

```python
# Git操作
gitpython>=3.1.0

# 代码解析
tree-sitter>=0.20.0
tree-sitter-python>=0.20.0
tree-sitter-javascript>=0.20.0
# 其他语言tree-sitter绑定

# Python特定解析
ast-parser>=0.1.0
libcst>=0.4.0  # 详细AST解析

# API文档
pyyaml>=6.0  # OpenAPI/Swagger解析

# 图形库（可视化）
networkx>=3.0

# 文件操作
GitPython>=3.1.0
python-dotenv>=0.19.0

# 异步任务
celery>=5.3.0  # 可选，用于后台同步任务
```

### 前端新增

```json
{
  "cytoscape": "^3.28.0",
  "cytoscape-dagre": "^2.5.0",
  "monaco-editor": "^0.44.0"
}
```

---

## 六、关键特性设计

### 6.1 混合搜索策略

```python
class HybridSearch:
    """结合向量搜索和关键词搜索"""
    
    async def search(self, query: str, top_k: int = 10):
        # 1. 向量相似度搜索 (70%)
        vector_results = await self.vector_search(query)
        
        # 2. 关键词搜索 (30%)
        keyword_results = await self.keyword_search(query)
        
        # 3. 排序融合
        merged = self.merge_results(vector_results, keyword_results)
        
        # 4. 多步推理（可选）
        # 使用LLM对结果进行排序优化
        ranked = await self.rerank_with_llm(merged, query)
        
        return ranked[:top_k]
```

### 6.2 增量同步机制

```python
class IncrementalSync:
    """支持高效增量更新"""
    
    async def sync(self, source: KBSource):
        # 1. 获取上次同步时间戳
        last_sync = await self.get_last_sync_time(source.id)
        
        # 2. 检测变化
        changes = await self._detect_changes(source, last_sync)
        
        # 3. 仅处理变化的内容
        if changes['added']:
            await self._add_documents(changes['added'])
        if changes['modified']:
            await self._update_documents(changes['modified'])
        if changes['deleted']:
            await self._delete_documents(changes['deleted'])
        
        # 4. 重新计算affected embeddings
        await self._update_related_embeddings(source.id)
```

### 6.3 知识关系图

```
自动构建：
  代码文件 -> 函数/类 -> 注释/文档
  数据表 -> 字段 -> 约束/关系
  API端点 -> 参数 -> 响应示例
  
支持操作：
  - 关系可视化
  - 跳转导航
  - 双向链接
  - 标签云
```

---

## 七、使用示例

### 示例1: 添加Git仓库知识源

```python
# 后端API调用
POST /knowledge-base/sources

{
  "name": "My Project Repo",
  "source_type": "git",
  "configuration": {
    "repo_url": "https://github.com/user/project.git",
    "branch": "main",
    "paths": ["src/", "README.md"],  # 可选：只扫描特定路径
    "file_patterns": ["*.py", "*.md"],  # 文件过滤
    "depth": 3,  # 目录深度
    "sync_interval": 3600  # 自动同步间隔（秒）
  }
}

# 自动触发同步
POST /knowledge-base/sources/{id}/sync

# 查询知识库
POST /knowledge-base/search

{
  "query": "如何实现异步处理",
  "source_type": "git",  # 可选：按类型过滤
  "top_k": 10
}

# 返回结果包含：
{
  "results": [
    {
      "id": 123,
      "source_id": 45,
      "source_name": "My Project Repo",
      "source_type": "git",
      "content": "async def process_data()...",
      "metadata": {
        "file_path": "src/async_handler.py",
        "language": "python",
        "line_range": [10, 25],
        "type": "function"
      },
      "similarity": 0.92,
      "preview": "async def process_data()..."
    }
  ]
}
```

### 示例2: 从Chat中利用多源知识

```python
# Chat提问
query = "如何配置数据库连接？"

# 系统搜索流程
1. 搜索所有知识源
   - 数据库源：查找connection相关的Schema
   - 代码库：查找config文件和示例代码
   - 文档源：查找教程和最佳实践
   
2. 融合结果后传给LLM
   context = f"""
   代码示例（来自GitHub）：
   {code_snippet}
   
   文档说明（来自Docs）：
   {doc_content}
   
   系统配置（来自Database）：
   {db_schema}
   """

3. LLM生成综合回答
```

---

## 八、维护和扩展

### 持续集成建议
- 定期同步计划任务
- 版本控制for Knowledge（记录更新历史）
- A/B测试搜索结果排序
- 用户反馈循环优化

### 可选增强
- 知识质量评分
- 热门知识排行
- 个性化推荐
- 知识过期检测

---

## 九、安全性考虑

1. **代码安全**：不执行提取的代码，仅解析结构
2. **访问控制**：遵守现有workspace隔离机制
3. **敏感信息**：过滤密钥、密码等敏感内容
4. **数据隐私**：支持私有知识源（企业内网Git等）

---

## 十、预期收益

✅ **知识覆盖**：从数据库 → 多维度知识源  
✅ **查询体验**：单一入口搜索所有资源  
✅ **质量提升**：ChatBI回答更准确、上下文更丰富  
✅ **易用性**：零配置同步，自动增量更新  
✅ **可视化**：知识关系图助力理解和导航  
✅ **可集成性**：支持嵌入更多业务系统  

---

## 附录A: Git仓库配置示例

```json
{
  "public_repos": [
    {
      "url": "https://github.com/kubernetes/kubernetes",
      "name": "Kubernetes",
      "paths": ["docs/", "README.md"]
    },
    {
      "url": "https://github.com/tensorflow/tensorflow",
      "name": "TensorFlow",
      "paths": ["tensorflow/", "README.md"],
      "exclude": ["*.pb", "*.so"]
    }
  ],
  "private_repos": [
    {
      "url": "ssh://git@github.com/company/internal-project.git",
      "auth": "ssh_key",
      "key_path": "/home/user/.ssh/id_rsa"
    }
  ]
}
```

---

## 附录B: API文档支持示例

```python
class OpenAPIExtractor(BaseExtractor):
    """从OpenAPI/Swagger规范提取知识"""
    
    async def extract(self, spec_file: str):
        # 解析spec.json或spec.yaml
        # 提取：
        # - API端点及方法
        # - 请求/响应模式
        # - 认证方式
        # - 示例代码
        pass
```

---

这个方案完全向后兼容，可以逐步实现。推荐先从Git仓库支持开始，因为这对开发团队最有价值。
