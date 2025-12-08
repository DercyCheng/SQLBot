# 综合知识库改造 - 快速开始指南

## 项目概述

将SQLBot从**SQL专用问数系统**改造为**综合知识库系统**，支持多种数据源（数据库、Git仓库、本地代码、文档等），实现统一搜索和智能问答。

### 核心价值
- 📚 **知识覆盖**：从单一数据库 → 代码、文档、API等多维度知识源
- 🔍 **智能搜索**：混合搜索 + 向量检索 + LLM排序
- 🎯 **使用场景**：开发文档查询、代码理解、技术问答、知识管理
- 🔌 **易集成**：可嵌入现有Chat界面和API

---

## 快速开始（4周实施计划）

### 🏁 **Week 1: 基础设施建设**

#### 1.1 数据库迁移 (1天)
```bash
cd backend
python -m alembic revision --autogenerate -m "Add knowledge base tables"
python -m alembic upgrade head
```

需要创建的表：
- `kb_source` - 知识源管理
- `kb_document` - 知识块存储
- `kb_relation` - 知识关系
- `kb_sync_log` - 同步日志

参考: `backend/alembic/versions/XXX_add_knowledge_base.py`

#### 1.2 模型定义 (1天)
创建文件结构：
```
backend/apps/knowledge_base/
├── models/
│   ├── __init__.py
│   ├── kb_source.py      # KBSource, KBSourceConfig
│   ├── kb_document.py    # KBDocument, DocumentChunk
│   ├── kb_relation.py    # KBRelation
│   └── kb_sync.py        # KBSyncLog
├── crud/
│   ├── __init__.py
│   ├── kb_source.py      # CRUD操作
│   ├── kb_document.py
│   └── kb_relation.py
└── ...
```

#### 1.3 框架代码 (1天)
- 提取器基类: `BaseExtractor`
- 提取器工厂: `ExtractorFactory`
- 知识库服务: `KnowledgeBaseService`

参考实现: `backend/apps/knowledge_base/kb_framework.py`

### 📦 **Week 2: 核心功能实现**

#### 2.1 Git提取器 (2天)
```python
# 实现步骤
1. GitExtractor 类
   - 支持仓库克隆/更新
   - 递归扫描文件
   - 支持增量同步

2. CodeParser 类
   - Python/JavaScript/Java等多语言支持
   - 符号表提取（函数、类等）
   - 注释和文档字符串提取

3. 依赖处理
   - 安装: pip install gitpython tree-sitter
   - 配置tree-sitter语言绑定
```

参考实现: `backend/apps/knowledge_base/git_extractor_impl.py`

#### 2.2 搜索服务 (2天)
```python
# SearchService 实现
- 向量搜索: 使用pgvector相似度查询
- 关键词搜索: PostgreSQL全文搜索
- 混合搜索: 权重融合 (向量70% + 关键词30%)
- 结果排序: 可选LLM重排序
```

#### 2.3 API端点 (1天)
```python
# 核心API
POST   /knowledge-base/sources              # 创建源
PUT    /knowledge-base/sources/{id}         # 更新源
DELETE /knowledge-base/sources/{id}         # 删除源
GET    /knowledge-base/sources              # 列表
GET    /knowledge-base/sources/{id}         # 详情

POST   /knowledge-base/sources/{id}/sync    # 触发同步
GET    /knowledge-base/sync/{sync_id}       # 同步状态
POST   /knowledge-base/sources/{id}/test    # 测试连接

POST   /knowledge-base/search               # 搜索
POST   /knowledge-base/search/hybrid        # 混合搜索
GET    /knowledge-base/sources/{id}/graph   # 知识图谱
```

### 🎨 **Week 3: 前端实现**

#### 3.1 核心页面 (2天)
```
src/views/knowledge-base/
├── Layout.vue              # 主布局
├── Sources.vue             # 源列表
├── CreateSource.vue        # 创建源
├── SourceDetail.vue        # 源详情
├── Search.vue              # 搜索页
├── Graph.vue               # 知识图谱
├── Documents.vue           # 文档浏览
├── components/
│   ├── SourceCard.vue      # 源卡片
│   ├── SyncMonitor.vue     # 同步监控
│   ├── ResultCard.vue      # 搜索结果卡
│   └── ...
└── forms/
    ├── GitRepoForm.vue
    ├── LocalCodeForm.vue
    ├── DatabaseForm.vue
    └── DocumentForm.vue
```

#### 3.2 API集成 (1天)
```typescript
// src/api/knowledge-base.ts
export const kbApi = {
  listSources: () => request.get('/knowledge-base/sources'),
  createSource: (data) => request.post('/knowledge-base/sources', data),
  search: (params) => request.post('/knowledge-base/search', params),
  // ... 其他API
}
```

### 🔗 **Week 4: Chat集成 + 测试**

#### 4.1 Chat集成 (1天)
在现有Chat组件中：
1. 获取用户问题
2. 调用知识库搜索
3. 格式化搜索结果为上下文
4. 传给LLM生成更准确的回答

```python
# 伪代码
async def chat_with_kb_context(user_question):
    # 搜索知识库
    kb_results = await kbApi.search(user_question)
    
    # 构建prompt
    prompt = build_prompt(user_question, kb_results)
    
    # 调用LLM
    response = await llm.complete(prompt)
    
    return response
```

#### 4.2 测试 + 优化 (2天)
- 单元测试：各提取器、搜索服务
- 集成测试：端到端流程
- 性能优化：缓存、索引优化
- UI/UX验收测试

---

## 核心技术实现细节

### 📝 Git提取器配置示例

```json
{
  "name": "My Project",
  "source_type": "git",
  "configuration": {
    "repo_url": "https://github.com/user/project.git",
    "branch": "main",
    "auth_type": "https",  // 或 "ssh"
    "paths": ["src/", "docs/", "README.md"],  // 可选：只扫描特定路径
    "file_patterns": ["*.py", "*.md", "*.txt"],
    "exclude_patterns": ["test_*.py", "*.pyc"],
    "max_depth": 5,
    "sync_interval": 3600  // 自动同步间隔（秒），0 = 不自动同步
  }
}
```

### 🔄 同步流程

```
1. 触发同步 (用户点击或定时任务)
   ↓
2. 创建 SyncLog 记录 (状态: pending)
   ↓
3. 根据 source_type 创建相应 Extractor
   ↓
4. 执行 extractor.extract()
   - 对于Git: clone/pull → 扫描 → 解析 → 返回chunks
   - 对于LocalCode: 扫描 → 解析 → 返回chunks
   - 对于Database: 获取schema → 返回chunks
   ↓
5. 保存 chunks 到 kb_document 表
   ↓
6. 计算 embeddings (异步任务)
   ↓
7. 构建 relation 图 (可选)
   ↓
8. 更新 SyncLog (状态: success/failed)
```

### 🧠 搜索流程

```
用户输入: "如何实现异步处理?"
   ↓
┌─────────────────────────────────────┐
│ 1. 向量搜索                         │
│    - 对query计算embedding           │
│    - pgvector相似度查询             │
│    - 获取 Top 10 结果               │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 2. 关键词搜索                       │
│    - PostgreSQL全文搜索             │
│    - 匹配关键词                     │
│    - 获取 Top 10 结果               │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 3. 结果融合                         │
│    - 向量结果权重：70%              │
│    - 关键词结果权重：30%            │
│    - 计算最终分数                   │
│    - 排序并去重                     │
└─────────────────────────────────────┘
   ↓
┌─────────────────────────────────────┐
│ 4. 可选：LLM重排序                  │
│    - 用LLM评分结果相关性            │
│    - 微调最终排序                   │
└─────────────────────────────────────┘
   ↓
返回: Top K 结果 (包含source信息)
```

---

## 依赖安装

### 后端依赖

```bash
# 核心
pip install gitpython>=3.1.0
pip install tree-sitter>=0.20.0

# 多语言支持
pip install tree-sitter-python>=0.20.0
pip install tree-sitter-javascript>=0.20.0

# 其他
pip install pygments>=2.15.0  # 语法高亮
pip install networkx>=3.0     # 图操作
pip install python-dotenv>=0.19.0
```

### 前端依赖

```bash
cd frontend
npm install cytoscape cytoscape-dagre  # 知识图谱可视化
npm install monaco-editor               # 代码编辑器（可选）
npm install prismjs                     # 代码高亮
```

---

## 文件清单

### 需要创建的文件

```
📦 backend/apps/knowledge_base/
├── __init__.py
├── kb_framework.py                    ✅ (已创建)
├── git_extractor_impl.py              ✅ (已创建)
├── models/
│   ├── __init__.py
│   ├── kb_source.py                   🚧 TODO
│   ├── kb_document.py                 🚧 TODO
│   ├── kb_relation.py                 🚧 TODO
│   └── kb_sync.py                     🚧 TODO
├── crud/
│   ├── __init__.py
│   ├── kb_source.py                   🚧 TODO
│   ├── kb_document.py                 🚧 TODO
│   └── kb_relation.py                 🚧 TODO
├── services/
│   ├── __init__.py
│   ├── kb_service.py                  🚧 TODO
│   ├── sync_service.py                🚧 TODO
│   ├── search_service.py              🚧 TODO
│   └── scheduler_sync.py              🚧 TODO (定时同步)
├── extractors/
│   ├── __init__.py
│   ├── base_extractor.py              ✅ (在kb_framework.py中)
│   ├── git_extractor.py               🚧 TODO
│   ├── code_extractor.py              🚧 TODO
│   ├── database_extractor.py          🚧 TODO
│   ├── document_extractor.py          🚧 TODO
│   └── parser/
│       ├── code_parser.py             ✅ (git_extractor_impl.py中)
│       ├── doc_parser.py              🚧 TODO
│       └── sql_parser.py              🚧 TODO (可选)
├── api/
│   ├── __init__.py
│   ├── kb_source.py                   🚧 TODO
│   ├── kb_document.py                 🚧 TODO
│   ├── kb_search.py                   🚧 TODO
│   └── kb_sync.py                     🚧 TODO
└── utils/
    ├── __init__.py
    ├── chunk_util.py                  🚧 TODO
    ├── embedding_util.py              🚧 TODO
    └── sync_util.py                   🚧 TODO

📦 backend/alembic/versions/
├── XXX_add_knowledge_base.py          🚧 TODO

📦 frontend/src/
├── api/knowledge-base.ts              🚧 TODO
├── views/knowledge-base/
│   ├── Layout.vue                     🚧 TODO
│   ├── Sources.vue                    🚧 TODO
│   ├── CreateSource.vue               🚧 TODO
│   ├── SourceDetail.vue               🚧 TODO
│   ├── Search.vue                     🚧 TODO
│   ├── Graph.vue                      🚧 TODO
│   ├── Documents.vue                  🚧 TODO
│   ├── components/
│   │   ├── SourceCard.vue             🚧 TODO
│   │   ├── SyncMonitor.vue            🚧 TODO
│   │   ├── ResultCard.vue             🚧 TODO
│   │   └── ...
│   └── forms/
│       ├── GitRepoForm.vue            🚧 TODO
│       ├── LocalCodeForm.vue          🚧 TODO
│       ├── DatabaseForm.vue           🚧 TODO
│       └── DocumentForm.vue           🚧 TODO

📄 docs/
├── COMPREHENSIVE_KB_TRANSFORMATION_PLAN.md     ✅ (已创建)
├── FRONTEND_INTEGRATION_GUIDE.md               ✅ (已创建)
├── QUICK_START_GUIDE.md                        ✅ (本文件)
├── KB_API_REFERENCE.md                        🚧 TODO
└── DEPLOYMENT_GUIDE.md                        🚧 TODO
```

---

## 数据库迁移脚本示例

```python
# backend/alembic/versions/XXX_add_knowledge_base.py

"""Add knowledge base tables

Revision ID: abc123def456
Revises: <previous_migration>
Create Date: 2024-12-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

revision = 'abc123def456'
down_revision = '<previous_migration>'

def upgrade():
    # kb_source 表
    op.create_table('kb_source',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('oid', sa.BigInteger(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=128), nullable=False),
        sa.Column('source_type', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('configuration', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column('create_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('create_by', sa.BigInteger(), nullable=True),
        sa.Column('update_time', sa.DateTime(timezone=False), nullable=True),
        sa.Column('update_by', sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('oid', 'name')
    )
    op.create_index('ix_kb_source_oid', 'kb_source', ['oid'])
    
    # kb_document 表
    op.create_table('kb_document',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=True), nullable=False),
        sa.Column('kb_source_id', sa.BigInteger(), nullable=False),
        sa.Column('doc_type', sqlmodel.sql.sqltypes.AutoString(length=32), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('embedding', postgresql.VECTOR(dim=1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=False), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['kb_source_id'], ['kb_source.id'], ondelete='CASCADE')
    )
    op.create_index('ix_kb_document_source', 'kb_document', ['kb_source_id'])
    op.create_index('ix_kb_document_embedding', 'kb_document', ['embedding'], postgresql_using='ivfflat')
    
    # ... 其他表定义

def downgrade():
    op.drop_table('kb_document')
    op.drop_table('kb_source')
    # ... 其他表删除
```

---

## 测试清单

### 单元测试
- [ ] GitExtractor 提取功能
- [ ] CodeParser 解析各种语言
- [ ] SearchService 搜索逻辑
- [ ] 分块和embedding计算

### 集成测试
- [ ] 完整的Git同步流程
- [ ] 搜索结果准确性
- [ ] Chat集成功能
- [ ] 并发同步处理

### 性能测试
- [ ] 大型仓库同步时间
- [ ] 搜索响应时间
- [ ] 向量计算效率

### UI/UX测试
- [ ] 表单验证
- [ ] 错误提示
- [ ] 加载状态反馈
- [ ] 移动端适配

---

## 常见问题

### Q1: 如何处理私有Git仓库？
A: 支持SSH密钥认证或HTTPS令牌。配置中提供 `auth_type` 和认证凭据。

### Q2: 大型仓库同步会很慢吗？
A: 
- 首次全量同步会较慢（10MB仓库约2-5分钟）
- 后续增量同步非常快（仅处理变化）
- 可配置 `sync_interval` 自动增量同步

### Q3: 搜索结果的准确性如何保证？
A:
- 向量搜索 + 关键词搜索混合
- 支持LLM重排序
- 可配置权重比例
- 用户反馈循环优化

### Q4: 系统扩展性如何？
A:
- PostgreSQL pgvector 支持百万级向量
- 支持分片存储（可选）
- 可选Milvus等专业向量数据库

### Q5: 如何监控同步状态？
A:
- UI中的 SyncMonitor 组件实时显示
- WebSocket 推送同步进度
- 同步日志记录详细信息

---

## 后续增强方向

1. **知识质量评分**：用户反馈 → 搜索结果优化
2. **个性化推荐**：基于用户查询历史推荐相关知识
3. **知识版本管理**：追踪源的变化历史
4. **智能摘要**：使用LLM为搜索结果生成摘要
5. **多语言支持**：支持代码和文档的多语言标注
6. **实时源**：支持日志、事件流等实时数据源

---

## 联系与支持

- 📖 完整文档: 见 `docs/` 目录
- 🐛 问题反馈: GitHub Issues
- 💬 讨论交流: GitHub Discussions

---

**开始改造，让SQLBot成为综合知识库！** 🚀
