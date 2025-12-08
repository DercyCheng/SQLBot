# 综合知识库改造 - 开发者清单

快速参考清单，包含实施过程中的关键点。

---

## 📋 前置检查

- [ ] 团队成员已阅读 COMPREHENSIVE_SUMMARY.md
- [ ] 技术负责人已阅读 COMPREHENSIVE_KB_TRANSFORMATION_PLAN.md
- [ ] 后端开发者已准备好环境
- [ ] 前端开发者已准备好环境
- [ ] 已有PostgreSQL环境（带pgvector）
- [ ] Git仓库已创建，团队成员有访问权限

---

## 🗂️ 项目结构搭建

### 后端文件结构

```
backend/apps/knowledge_base/
├── __init__.py
├── kb_framework.py                    [✅ 已创建]
├── git_extractor_impl.py              [✅ 已创建]
│
├── models/
│   ├── __init__.py
│   ├── kb_source.py                   [ ] TODO
│   ├── kb_document.py                 [ ] TODO
│   ├── kb_relation.py                 [ ] TODO
│   └── kb_sync.py                     [ ] TODO
│
├── crud/
│   ├── __init__.py
│   ├── kb_source.py                   [ ] TODO
│   ├── kb_document.py                 [ ] TODO
│   └── kb_relation.py                 [ ] TODO
│
├── services/
│   ├── __init__.py
│   ├── kb_service.py                  [ ] TODO
│   ├── sync_service.py                [ ] TODO
│   ├── search_service.py              [ ] TODO
│   └── scheduler_sync.py              [ ] TODO
│
├── extractors/
│   ├── __init__.py
│   ├── git_extractor.py               [ ] TODO
│   ├── code_extractor.py              [ ] TODO
│   ├── database_extractor.py          [ ] TODO
│   ├── document_extractor.py          [ ] TODO
│   └── parser/
│       ├── code_parser.py             [ ] TODO
│       ├── doc_parser.py              [ ] TODO
│       └── sql_parser.py              [ ] TODO
│
├── api/
│   ├── __init__.py
│   ├── kb_source.py                   [ ] TODO
│   ├── kb_document.py                 [ ] TODO
│   ├── kb_search.py                   [ ] TODO
│   └── kb_sync.py                     [ ] TODO
│
└── utils/
    ├── __init__.py
    ├── chunk_util.py                  [ ] TODO
    ├── embedding_util.py              [ ] TODO
    └── sync_util.py                   [ ] TODO
```

### 前端文件结构

```
frontend/src/
├── api/
│   └── knowledge-base.ts              [ ] TODO
│
├── views/knowledge-base/
│   ├── Layout.vue                     [ ] TODO
│   ├── Sources.vue                    [ ] TODO
│   ├── CreateSource.vue               [ ] TODO
│   ├── SourceDetail.vue               [ ] TODO
│   ├── Search.vue                     [ ] TODO
│   ├── Graph.vue                      [ ] TODO
│   ├── Documents.vue                  [ ] TODO
│   │
│   ├── components/
│   │   ├── SourceCard.vue             [ ] TODO
│   │   ├── SyncMonitor.vue            [ ] TODO
│   │   ├── ResultCard.vue             [ ] TODO
│   │   ├── SourceTypeIcon.vue         [ ] TODO
│   │   └── LoadingState.vue           [ ] TODO
│   │
│   └── forms/
│       ├── GitRepoForm.vue            [ ] TODO
│       ├── LocalCodeForm.vue          [ ] TODO
│       ├── DatabaseForm.vue           [ ] TODO
│       └── DocumentForm.vue           [ ] TODO
│
└── router/
    └── index.ts                       [ ] 修改现有路由
```

---

## 📦 依赖管理

### 后端新增依赖

```bash
# 在 backend/pyproject.toml 中添加

# Git操作
gitpython>=3.1.0                          [ ] 确认添加

# 代码解析（多语言）
tree-sitter>=0.20.0                       [ ] 确认添加
tree-sitter-python>=0.20.0                [ ] 确认添加
tree-sitter-javascript>=0.20.0            [ ] 确认添加

# 文档处理
pdfplumber>=0.10.0                        [ ] 确认添加（已有）
python-docx>=1.1.0                        [ ] 确认添加（已有）

# 图处理
networkx>=3.0                             [ ] 确认添加

# 其他
python-dotenv>=0.19.0                     [ ] 确认添加
```

### 前端新增依赖

```bash
# 在 frontend/package.json 中添加

npm install cytoscape cytoscape-dagre     [ ] 知识图谱可视化
npm install monaco-editor                 [ ] 代码查看（可选）
npm install prismjs                       [ ] 代码高亮
```

---

## 🗄️ 数据库迁移

### Alembic迁移文件

- [ ] 创建 `backend/alembic/versions/XXX_add_knowledge_base.py`
- [ ] 包含以下表:
  - [ ] `kb_source` - 知识源
  - [ ] `kb_document` - 知识块
  - [ ] `kb_relation` - 关系
  - [ ] `kb_sync_log` - 同步日志
- [ ] 创建向量索引: `CREATE INDEX ON kb_document USING ivfflat (embedding)`
- [ ] 运行迁移: `alembic upgrade head`
- [ ] 验证表创建成功

### 数据库检查清单

```sql
-- 运行这些查询验证

-- 1. 检查表是否存在
SELECT tablename FROM pg_tables WHERE tablename LIKE 'kb_%';

-- 2. 检查向量索引
SELECT * FROM pg_indexes WHERE tablename = 'kb_document';

-- 3. 检查pgvector是否可用
CREATE EXTENSION IF NOT EXISTS vector;

-- 4. 测试向量操作
SELECT '[1,2,3]'::vector <-> '[4,5,6]'::vector;
```

---

## 🔧 Week 1: 基础设施

### 任务分配

**后端开发者A - 数据库和模型**
- [ ] 创建并运行Alembic迁移
- [ ] 在 `models/` 目录实现:
  - [ ] `kb_source.py` - KBSource SQLModel
  - [ ] `kb_document.py` - KBDocument SQLModel
  - [ ] `kb_relation.py` - KBRelation SQLModel
  - [ ] `kb_sync.py` - KBSyncLog SQLModel

**后端开发者B - 核心框架**
- [ ] 复制 `kb_framework.py` 并完善:
  - [ ] 实现 `BaseExtractor` 抽象类
  - [ ] 实现 `ExtractorFactory` 工厂
  - [ ] 实现 `KnowledgeBaseService` 框架
  - [ ] 补充TODO部分

**后端开发者C - CRUD操作**
- [ ] 在 `crud/` 目录实现:
  - [ ] `kb_source.py` - 源的CRUD
  - [ ] `kb_document.py` - 文档的CRUD
  - [ ] `kb_relation.py` - 关系的CRUD

### Week 1 验收标准

- [ ] 所有模型类已定义
- [ ] 数据库表已成功创建
- [ ] CRUD操作可正常执行
- [ ] 单元测试通过 (Models层)
- [ ] 可以创建/更新/删除知识源

---

## 🔍 Week 2: 核心功能

### Git提取器实现

**任务**
- [ ] 复制 `git_extractor_impl.py` 为参考
- [ ] 完成以下模块:
  - [ ] `git_extractor.py` - GitExtractor 类完整实现
  - [ ] 支持clone/pull仓库
  - [ ] 支持增量同步
  - [ ] 完善错误处理

**代码检查清单**
```python
# git_extractor.py 中应该有
- [ ] async def extract(config) -> List[DocumentChunk]
- [ ] async def validate_config(config) -> bool  
- [ ] async def _setup_repository()
- [ ] async def _scan_directory()
- [ ] async def _process_file()
```

### 代码解析器

**任务**
- [ ] `parser/code_parser.py` - 多语言代码解析
  - [ ] Python 解析器
  - [ ] JavaScript/TypeScript 解析器
  - [ ] Java 解析器（简化版）
  - [ ] 通用解析器（降级方案）

**功能检查**
```python
# code_parser.py 应该支持
- [ ] 函数/类定义提取
- [ ] 注释和docstring提取
- [ ] import 语句识别
- [ ] 符号表构建
```

### 搜索服务

**任务**
- [ ] `search_service.py` - 搜索引擎实现
  - [ ] 向量搜索实现
  - [ ] 关键词搜索实现
  - [ ] 混合搜索融合
  - [ ] 可选LLM排序

**性能目标**
- [ ] 搜索响应 < 200ms
- [ ] 支持 > 100K 文档

### API端点

**任务**
- [ ] `api/kb_source.py` - 源管理API
  - [ ] POST /sources 创建
  - [ ] GET /sources 列表
  - [ ] GET /sources/{id} 详情
  - [ ] PUT /sources/{id} 更新
  - [ ] DELETE /sources/{id} 删除
  - [ ] POST /sources/test 测试连接

- [ ] `api/kb_search.py` - 搜索API
  - [ ] POST /search 搜索
  - [ ] POST /search/hybrid 混合搜索

- [ ] `api/kb_sync.py` - 同步API
  - [ ] POST /sources/{id}/sync 触发同步
  - [ ] GET /sync/{id} 状态查询
  - [ ] POST /sync/{id}/cancel 取消同步

### Week 2 验收标准

- [ ] Git提取器可成功提取仓库
- [ ] 代码解析准确率 > 90%
- [ ] 搜索响应时间 < 200ms
- [ ] 所有API端点可用
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试通过

---

## 🎨 Week 3: 前端实现

### 页面创建

**任务**
- [ ] 创建 `/frontend/src/views/knowledge-base/` 目录

**Sources.vue**
- [ ] 源列表展示
- [ ] 搜索和过滤
- [ ] 创建/删除操作
- [ ] 同步状态显示

**CreateSource.vue**
- [ ] 表单验证
- [ ] 配置保存
- [ ] 连接测试
- [ ] 错误处理

**Search.vue**
- [ ] 搜索输入框
- [ ] 结果展示
- [ ] 结果卡片
- [ ] 高亮匹配

**SourceDetail.vue**
- [ ] 源信息展示
- [ ] 同步历史
- [ ] 手动同步按钮
- [ ] 文档浏览

**Graph.vue**
- [ ] 知识图谱可视化
- [ ] 节点交互
- [ ] 关系展示

### 组件创建

**共通组件**
- [ ] `SourceCard.vue` - 源卡片
- [ ] `SyncMonitor.vue` - 同步监控
- [ ] `ResultCard.vue` - 搜索结果卡
- [ ] `LoadingState.vue` - 加载状态
- [ ] `EmptyState.vue` - 空状态

### API集成

**任务**
- [ ] 创建 `/frontend/src/api/knowledge-base.ts`
- [ ] 实现所有API调用
- [ ] 添加TypeScript类型定义
- [ ] 错误处理

### 路由配置

**任务**
- [ ] 在路由表中添加知识库路由
- [ ] 配置子路由
- [ ] 面包屑导航

### Week 3 验收标准

- [ ] 所有页面可正常渲染
- [ ] API调用成功
- [ ] 错误提示完善
- [ ] 响应式设计正确
- [ ] 移动端适配

---

## 🔗 Week 4: Chat集成与测试

### Chat集成

**任务**
- [ ] 在Chat组件中集成知识库搜索
- [ ] 修改提示词生成逻辑
- [ ] 将搜索结果格式化为上下文
- [ ] 测试回答质量提升

**具体步骤**
```python
# 在Chat中添加
1. 用户提问时调用: kbApi.search(question)
2. 格式化搜索结果为prompt上下文
3. 传给LLM: llm.complete(enhanced_prompt)
4. 返回带引用的答案
```

### 完整测试

**单元测试**
- [ ] 提取器单元测试
- [ ] 搜索服务单元测试
- [ ] CRUD操作单元测试
- [ ] 工具函数单元测试

**集成测试**
- [ ] 端到端的同步流程
- [ ] 搜索准确性验证
- [ ] Chat集成验证
- [ ] 权限隔离验证

**性能测试**
- [ ] 大仓库同步时间
- [ ] 搜索响应时间
- [ ] 并发处理能力
- [ ] 内存占用

**UI测试**
- [ ] 页面功能验收
- [ ] 错误提示验证
- [ ] 状态转换验证
- [ ] 移动端测试

### 优化和打磨

**性能优化**
- [ ] 查询优化
- [ ] 缓存优化
- [ ] 索引优化
- [ ] 增量更新优化

**用户体验**
- [ ] 界面打磨
- [ ] 加载状态反馈
- [ ] 错误提示友好化
- [ ] 帮助文本补充

### Week 4 验收标准

- [ ] 所有测试通过
- [ ] Chat集成工作正常
- [ ] 性能指标达成:
  - [ ] 搜索响应 < 200ms
  - [ ] 同步速度 > 1MB/s
  - [ ] 并发搜索 > 100qps
- [ ] 代码质量 (可选):
  - [ ] 代码审查通过
  - [ ] 测试覆盖 > 80%
  - [ ] 无关键问题
- [ ] 文档完整
- [ ] 可部署到生产

---

## 🧪 测试检查清单

### 单元测试

```python
# test_extractors.py
- [ ] test_git_extractor_extract()
- [ ] test_code_parser_python()
- [ ] test_code_parser_javascript()
- [ ] test_language_detector()

# test_search.py
- [ ] test_vector_search()
- [ ] test_keyword_search()
- [ ] test_hybrid_search()
- [ ] test_merge_results()

# test_crud.py
- [ ] test_create_source()
- [ ] test_update_source()
- [ ] test_delete_source()
- [ ] test_list_sources()
```

### 集成测试

```python
# test_integration.py
- [ ] test_git_sync_flow()         # 完整的Git同步流程
- [ ] test_search_accuracy()       # 搜索准确性
- [ ] test_chat_integration()      # Chat集成
- [ ] test_concurrent_sync()       # 并发同步
- [ ] test_permission_isolation()  # 权限隔离
```

### 功能验收

- [ ] 创建Git源成功
- [ ] 同步仓库成功
- [ ] 搜索功能有效
- [ ] Chat回答改进
- [ ] 错误处理完善
- [ ] 性能满足要求

---

## 🚀 部署检查清单

### 预部署检查

**代码**
- [ ] 所有代码已review
- [ ] 所有测试通过
- [ ] 没有TODO注释（除了future work）
- [ ] 文档已更新
- [ ] README中有使用说明

**环境**
- [ ] PostgreSQL已安装pgvector
- [ ] Python版本符合要求（3.11+）
- [ ] 所有依赖已安装
- [ ] 环境变量已配置

**数据库**
- [ ] Alembic迁移已运行
- [ ] 所有表已创建
- [ ] 向量索引已生成
- [ ] 数据一致性检查通过

### 部署步骤

```bash
# 1. 数据库迁移
cd backend
alembic upgrade head

# 2. 后端服务重启
docker restart sqlbot-backend
# 或
systemctl restart sqlbot-backend

# 3. 前端构建（如果有更改）
cd frontend
npm run build

# 4. 清理缓存
redis-cli FLUSHDB  # 可选

# 5. 验证
curl http://localhost:8000/knowledge-base/sources
```

### 部署后验证

- [ ] 后端服务正常运行
- [ ] 前端页面可访问
- [ ] 可创建知识源
- [ ] 可执行搜索
- [ ] Chat功能正常
- [ ] 监控告警正常

---

## 📊 质量指标

### 代码质量

| 指标 | 目标值 | 当前值 | 状态 |
|------|--------|--------|------|
| 测试覆盖 | > 80% | - | [ ] |
| 代码审查 | 100% | - | [ ] |
| Bug率 | 0 (P1) | - | [ ] |
| 技术债 | 0 | - | [ ] |

### 功能质量

| 功能 | 完成度 | 测试 | 文档 |
|------|--------|------|------|
| Git提取器 | [ ] | [ ] | [ ] |
| 代码解析 | [ ] | [ ] | [ ] |
| 搜索服务 | [ ] | [ ] | [ ] |
| Chat集成 | [ ] | [ ] | [ ] |
| 前端UI | [ ] | [ ] | [ ] |

### 性能指标

| 指标 | 目标 | 当前 | 状态 |
|------|------|------|------|
| 搜索响应 | < 200ms | - | [ ] |
| Git同步 | 10MB < 3分钟 | - | [ ] |
| 并发搜索 | > 100qps | - | [ ] |
| 向量计算 | 1000/min | - | [ ] |

---

## 🎓 知识转移

### 培训计划

- [ ] Week 1: 架构和设计培训
- [ ] Week 2: 代码实现培训
- [ ] Week 3: 前端开发培训
- [ ] Week 4: 部署运维培训

### 文档

- [ ] API文档完整
- [ ] 部署指南完整
- [ ] 故障排查指南
- [ ] 扩展开发指南

### 知识转移验收

- [ ] 新加入者可独立操作
- [ ] 文档可自助查阅
- [ ] 常见问题有记录
- [ ] 最佳实践已总结

---

## 🎉 最终交付清单

### 代码提交

- [ ] 所有分支已合并到main
- [ ] Tag已创建 (v1.0.0或类似)
- [ ] 变更日志已更新
- [ ] Release notes已准备

### 文档交付

- [ ] README.md已更新
- [ ] API文档已完成
- [ ] 部署指南已完成
- [ ] 最佳实践文档已完成

### 功能交付

- [ ] 所有计划功能已实现
- [ ] 性能目标已达成
- [ ] 用户体验已验证
- [ ] Chat集成已测试

### 运维交付

- [ ] 监控告警已配置
- [ ] 日志收集已配置
- [ ] 备份策略已制定
- [ ] 灾难恢复已测试

---

## 📞 关键联系

### 项目角色

| 角色 | 姓名 | 联系 | 职责 |
|------|------|------|------|
| 项目经理 | - | - | [ ] 分配 |
| 技术负责人 | - | - | [ ] 分配 |
| 后端负责 | - | - | [ ] 分配 |
| 前端负责 | - | - | [ ] 分配 |
| QA负责 | - | - | [ ] 分配 |

### 关键决策

- [ ] 向量模型已选定: _______
- [ ] 同步间隔已确定: _______
- [ ] 搜索权重已调整: _______
- [ ] 部署时间已确定: _______

---

## 🏁 项目完成标志

✅ **项目成功标志** (全部勾选)

- [ ] 所有计划任务已完成
- [ ] 所有测试已通过
- [ ] 所有质量指标已达成
- [ ] 所有文档已完成
- [ ] 团队培训已完成
- [ ] 系统已部署到生产
- [ ] 用户反馈已收集
- [ ] 项目总结已完成

---

**使用说明**: 
- 打印此清单，贴在团队工作区
- 每日更新进度
- 每周进行检查
- 遇到阻碍项立即反馈

**预计完成时间**: 4周  
**最后更新**: 2024-12-06  
**维护者**: Project Team
