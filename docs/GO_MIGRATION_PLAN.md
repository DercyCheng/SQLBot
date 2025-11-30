# SQLBot Go + 混合语言迁移规划

## 一、项目概述

### 1.1 当前技术栈
| 组件 | 当前技术 | 版本 |
|------|---------|------|
| 后端 | Python (FastAPI) | 3.11+ |
| ORM | SQLModel/SQLAlchemy | 2.x |
| 数据库 | PostgreSQL + pgvector | 16+ |
| 缓存 | Redis | 7.x |
| 前端 | Vue 3 + TypeScript | 3.x |
| UI框架 | Element Plus | 2.x |
| 图表SSR | Node.js (G2) | - |
| 部署 | Docker / Kubernetes | - |

### 1.2 迁移目标
- **核心服务**: Python → Go (高性能、低内存)
- **AI/ML模块**: 保持Python (成熟生态)
- **前端**: 保持Vue 3 (无需迁移)
- **图表SSR**: 保持Node.js (G2生态)

## 二、架构设计

### 2.1 目标架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (Vue 3 + TypeScript)                 │
└─────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API Gateway (Go - Gin/Fiber)                 │
│  - 认证/授权 (JWT)                                                │
│  - 限流/熔断                                                      │
│  - 请求路由                                                       │
│  - 统一日志                                                       │
└─────────────────────────────────────────────────────────────────┘
                    │                           │
         ┌──────────┴──────────┐     ┌──────────┴──────────┐
         ▼                      ▼     ▼                      ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│  Go 核心服务     │  │  Python AI服务   │  │  Node.js 图表SSR    │
│  ─────────────  │  │  ─────────────  │  │  ─────────────────  │
│  - 用户管理      │  │  - LLM集成       │  │  - G2图表渲染        │
│  - 数据源管理    │  │  - Embedding     │  │  - 图片生成          │
│  - 定时任务      │  │  - 知识库检索     │  │  - SSR服务          │
│  - 系统设置      │  │  - SQL生成       │  │                     │
│  - 权限控制      │  │  - 数据分析       │  │                     │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
         │                      │                     │
         └──────────────────────┴─────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    数据层 (PostgreSQL + Redis)                   │
│  - pgvector (向量存储)                                           │
│  - 关系数据                                                       │
│  - 会话缓存                                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 服务间通信

| 通信方式 | 场景 | 技术选型 |
|---------|------|---------|
| 同步HTTP | 前端-网关-服务 | REST API |
| gRPC | Go-Python服务间 | Protocol Buffers |
| 消息队列 | 异步任务 | Redis Streams / RabbitMQ |
| WebSocket | 实时推送 | Go原生支持 |

## 三、模块拆分规划

### 3.1 Go 核心服务 (sqlbot-core)

```
sqlbot-core/
├── cmd/
│   └── server/
│       └── main.go              # 入口
├── internal/
│   ├── config/                  # 配置管理
│   ├── middleware/              # 中间件
│   │   ├── auth.go             # JWT认证
│   │   ├── cors.go             # CORS
│   │   ├── logger.go           # 日志
│   │   └── ratelimit.go        # 限流
│   ├── handler/                 # HTTP处理器
│   │   ├── user.go
│   │   ├── datasource.go
│   │   ├── scheduler.go
│   │   └── system.go
│   ├── service/                 # 业务逻辑
│   ├── repository/              # 数据访问
│   ├── model/                   # 数据模型
│   └── pkg/                     # 工具包
│       ├── db/                  # 数据库连接
│       ├── cache/               # Redis封装
│       ├── logger/              # 日志封装
│       └── response/            # 统一响应
├── api/
│   └── proto/                   # gRPC定义
│       ├── ai.proto
│       └── chat.proto
├── migrations/                  # 数据库迁移
├── go.mod
└── go.sum
```

#### Go 技术选型

| 功能 | 推荐框架/库 | 备选 |
|------|------------|------|
| Web框架 | Gin | Fiber, Echo |
| ORM | GORM | Ent, sqlx |
| 配置 | Viper | Envconfig |
| 日志 | Zap | Logrus, Zerolog |
| 验证 | Validator | go-playground |
| JWT | jwt-go | - |
| gRPC | grpc-go | - |
| 调度器 | gocron | robfig/cron |
| 迁移 | golang-migrate | goose |

### 3.2 Python AI 服务 (sqlbot-ai)

```
sqlbot-ai/
├── app/
│   ├── main.py                  # FastAPI入口
│   ├── api/
│   │   ├── chat.py             # 对话API
│   │   ├── embedding.py        # 向量化API
│   │   └── knowledge.py        # 知识库API
│   ├── services/
│   │   ├── llm/                # LLM集成
│   │   │   ├── base.py
│   │   │   ├── openai.py
│   │   │   ├── deepseek.py
│   │   │   └── qianfan.py
│   │   ├── embedding/          # Embedding服务
│   │   ├── rag/                # RAG检索
│   │   └── sql_generator/      # SQL生成
│   ├── grpc/                   # gRPC服务
│   │   ├── server.py
│   │   └── handlers.py
│   └── models/                 # 数据模型
├── protos/                     # Proto文件
├── requirements.txt
└── Dockerfile
```

### 3.3 模块迁移优先级

| 阶段 | 模块 | 当前语言 | 目标 | 优先级 | 难度 |
|-----|------|---------|------|-------|------|
| 1 | 用户认证 | Python | Go | P0 | 低 |
| 1 | 系统设置 | Python | Go | P0 | 低 |
| 2 | 数据源管理 | Python | Go | P1 | 中 |
| 2 | 定时任务 | Python | Go | P1 | 中 |
| 2 | 权限管理 | Python | Go | P1 | 中 |
| 3 | Dashboard | Python | Go | P2 | 中 |
| 3 | 模板管理 | Python | Go | P2 | 低 |
| - | Chat/LLM | Python | Python | - | - |
| - | 知识库 | Python | Python | - | - |
| - | 向量检索 | Python | Python | - | - |

## 四、迁移步骤详解

### 4.1 第一阶段：基础设施 (2周)

#### Week 1: Go项目初始化
```bash
# 初始化Go模块
mkdir sqlbot-core && cd sqlbot-core
go mod init github.com/DercyCheng/sqlbot-core

# 安装核心依赖
go get github.com/gin-gonic/gin
go get gorm.io/gorm
go get gorm.io/driver/postgres
go get github.com/spf13/viper
go get go.uber.org/zap
go get github.com/golang-jwt/jwt/v5
```

#### Week 2: 基础框架搭建
- [ ] 项目结构创建
- [ ] 配置管理 (Viper)
- [ ] 数据库连接池 (GORM + pgx)
- [ ] Redis连接
- [ ] 日志系统 (Zap)
- [ ] 统一响应格式
- [ ] 错误处理
- [ ] Dockerfile

### 4.2 第二阶段：核心模块迁移 (4周)

#### Week 3-4: 用户 & 认证模块
```go
// internal/handler/auth.go
type AuthHandler struct {
    userService *service.UserService
    jwtService  *service.JWTService
}

func (h *AuthHandler) Login(c *gin.Context) {
    var req LoginRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.Error(c, http.StatusBadRequest, err.Error())
        return
    }
    
    token, err := h.userService.Login(req.Account, req.Password)
    if err != nil {
        response.Error(c, http.StatusUnauthorized, err.Error())
        return
    }
    
    response.Success(c, gin.H{"token": token})
}
```

迁移清单:
- [ ] User模型
- [ ] 登录/登出
- [ ] JWT认证中间件
- [ ] 密码加密
- [ ] 用户CRUD
- [ ] 权限校验

#### Week 5-6: 数据源 & 系统模块
- [ ] 数据源连接测试
- [ ] 数据源CRUD
- [ ] 表/字段元数据
- [ ] 系统设置
- [ ] AI模型配置

### 4.3 第三阶段：gRPC集成 (2周)

#### Proto定义
```protobuf
// api/proto/chat.proto
syntax = "proto3";

package sqlbot.chat;

option go_package = "github.com/DercyCheng/sqlbot-core/api/proto/chat";

service ChatService {
    rpc AskQuestion(QuestionRequest) returns (stream QuestionResponse);
    rpc GenerateSQL(SQLRequest) returns (SQLResponse);
}

message QuestionRequest {
    int64 chat_id = 1;
    string question = 2;
    int64 datasource_id = 3;
    map<string, string> context = 4;
}

message QuestionResponse {
    string content = 1;
    string sql = 2;
    bytes data = 3;
    bool finished = 4;
}
```

#### Go gRPC客户端
```go
// internal/grpc/client.go
type AIClient struct {
    conn *grpc.ClientConn
    chat chatpb.ChatServiceClient
}

func NewAIClient(addr string) (*AIClient, error) {
    conn, err := grpc.NewClient(addr,
        grpc.WithTransportCredentials(insecure.NewCredentials()),
    )
    if err != nil {
        return nil, err
    }
    
    return &AIClient{
        conn: conn,
        chat: chatpb.NewChatServiceClient(conn),
    }, nil
}
```

### 4.4 第四阶段：API网关整合 (2周)

```go
// cmd/gateway/main.go
func main() {
    r := gin.Default()
    
    // 中间件
    r.Use(middleware.CORS())
    r.Use(middleware.Logger())
    r.Use(middleware.RateLimit())
    
    // Go原生路由
    api := r.Group("/api/v1")
    {
        // 认证
        api.POST("/login", authHandler.Login)
        api.POST("/logout", authHandler.Logout)
        
        // 用户管理
        users := api.Group("/users", middleware.Auth())
        users.GET("", userHandler.List)
        users.POST("", userHandler.Create)
        
        // 数据源
        ds := api.Group("/datasource", middleware.Auth())
        ds.GET("/list", dsHandler.List)
        ds.POST("/add", dsHandler.Add)
    }
    
    // Python AI服务代理
    aiProxy := api.Group("/chat", middleware.Auth())
    aiProxy.Any("/*path", proxyHandler.ForwardToAI)
    
    r.Run(":8000")
}
```

## 五、数据库迁移策略

### 5.1 共享数据库方案

Go和Python服务共用同一PostgreSQL实例:

```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    # ...
    
  sqlbot-core:  # Go服务
    environment:
      DATABASE_URL: postgres://root:xxx@postgres:5432/sqlbot
      
  sqlbot-ai:    # Python服务
    environment:
      DATABASE_URL: postgres://root:xxx@postgres:5432/sqlbot
```

### 5.2 GORM模型定义

```go
// internal/model/user.go
type User struct {
    ID          int64      `gorm:"primaryKey;autoIncrement"`
    OID         string     `gorm:"size:36;not null;index"`
    Account     string     `gorm:"size:100;not null;uniqueIndex"`
    Name        string     `gorm:"size:100"`
    Email       string     `gorm:"size:255"`
    Password    string     `gorm:"size:255;not null"`
    Enabled     bool       `gorm:"default:true"`
    Language    string     `gorm:"size:20;default:zh-CN"`
    CreateTime  time.Time  `gorm:"autoCreateTime"`
    UpdateTime  time.Time  `gorm:"autoUpdateTime"`
}

func (User) TableName() string {
    return "core_user"
}
```

### 5.3 迁移工具

使用 `golang-migrate` 管理Go侧的数据库变更:

```bash
# 安装
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# 创建迁移
migrate create -ext sql -dir migrations -seq add_go_indexes

# 执行迁移
migrate -path migrations -database "$DATABASE_URL" up
```

## 六、部署架构

### 6.1 Docker Compose (开发环境)

```yaml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    # ...
    
  redis:
    image: redis:7-alpine
    # ...
    
  sqlbot-core:
    build:
      context: ./sqlbot-core
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    environment:
      - DATABASE_URL=postgres://root:xxx@postgres:5432/sqlbot
      - REDIS_URL=redis://redis:6379
      - AI_SERVICE_URL=sqlbot-ai:50051
      
  sqlbot-ai:
    build:
      context: ./sqlbot-ai
      dockerfile: Dockerfile
    ports:
      - "50051:50051"  # gRPC
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgres://root:xxx@postgres:5432/sqlbot
      
  sqlbot-ssr:
    build:
      context: ./g2-ssr
      dockerfile: Dockerfile
    ports:
      - "8001:8001"
```

### 6.2 Kubernetes (生产环境)

```yaml
# k8s/sqlbot-core-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sqlbot-core
  namespace: sqlbot
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sqlbot-core
  template:
    metadata:
      labels:
        app: sqlbot-core
    spec:
      containers:
        - name: sqlbot-core
          image: registry.example.com/sqlbot-core:latest
          ports:
            - containerPort: 8000
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
```

## 七、测试策略

### 7.1 单元测试

```go
// internal/service/user_test.go
func TestUserService_Login(t *testing.T) {
    db := setupTestDB(t)
    defer teardownTestDB(t, db)
    
    svc := NewUserService(db)
    
    tests := []struct {
        name     string
        account  string
        password string
        wantErr  bool
    }{
        {"valid login", "admin", "password123", false},
        {"invalid password", "admin", "wrong", true},
        {"user not found", "unknown", "password", true},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := svc.Login(tt.account, tt.password)
            if (err != nil) != tt.wantErr {
                t.Errorf("Login() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

### 7.2 集成测试

```go
// test/integration/api_test.go
func TestLoginAPI(t *testing.T) {
    router := setupRouter()
    
    w := httptest.NewRecorder()
    body := `{"account":"admin","password":"password123"}`
    req, _ := http.NewRequest("POST", "/api/v1/login", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    
    router.ServeHTTP(w, req)
    
    assert.Equal(t, 200, w.Code)
    
    var resp map[string]interface{}
    json.Unmarshal(w.Body.Bytes(), &resp)
    assert.NotEmpty(t, resp["data"].(map[string]interface{})["token"])
}
```

### 7.3 E2E测试

使用现有前端测试，验证API兼容性。

## 八、风险与对策

| 风险 | 影响 | 对策 |
|-----|------|------|
| API不兼容 | 前端无法工作 | 保持API签名一致，添加兼容层 |
| 数据不一致 | 数据损坏 | 共享数据库，统一迁移工具 |
| 性能回退 | 用户体验下降 | 充分压测，灰度发布 |
| 迁移周期长 | 项目延期 | 分阶段迁移，双系统并行 |

## 九、时间线

```mermaid
gantt
    title SQLBot Go迁移时间线
    dateFormat  YYYY-MM-DD
    section 阶段1
    基础设施搭建      :a1, 2024-01-01, 2w
    section 阶段2
    用户认证迁移      :a2, after a1, 2w
    数据源模块迁移    :a3, after a2, 2w
    section 阶段3
    gRPC集成         :a4, after a3, 2w
    section 阶段4
    API网关整合      :a5, after a4, 2w
    section 阶段5
    测试与优化       :a6, after a5, 2w
    灰度发布         :a7, after a6, 1w
```

## 十、参考资源

### Go学习资源
- [Go官方文档](https://go.dev/doc/)
- [Gin框架文档](https://gin-gonic.com/docs/)
- [GORM文档](https://gorm.io/docs/)

### 架构参考
- [Go微服务最佳实践](https://github.com/golang-standards/project-layout)
- [gRPC-Go示例](https://github.com/grpc/grpc-go/tree/master/examples)

### 工具
- [Air - Go热重载](https://github.com/cosmtrek/air)
- [Swag - Swagger生成](https://github.com/swaggo/swag)
- [Wire - 依赖注入](https://github.com/google/wire)
