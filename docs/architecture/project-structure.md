# 项目结构文档（Wiki）

> 最后更新：2026-05-20
> 本文档供 Claude Code 快速了解项目全貌，避免每次扫描整个代码库。

---

## 顶层目录

```
knowledge-platform/
├── backend/          # FastAPI 后端（Python 3.11+）
├── frontend/         # Vue3 + Vite 前端
├── infra/            # Docker Compose + 数据库初始化
└── docs/             # 项目文档（需求/架构/API）
```

---

## Backend 结构 (`backend/app/`)

### 入口与配置
| 文件 | 用途 |
|------|------|
| `main.py` | FastAPI 应用入口，注册路由/中间件，系统初始化状态管理 |
| `config.py` | Pydantic Settings，从 `.env` 加载配置，`get_settings()` + `reload_settings()` |

### API 路由 (`api/`)
| 文件 | 路由前缀 | 功能 |
|------|----------|------|
| `auth.py` | `/api/auth` | 登录/登出/改密/用户信息（本地 JWT） |
| `wiki.py` | `/api/wiki` | Wiki CRUD + 版本历史 + 搜索 |
| `qa.py` | `/api/qa` | 智能问答入口 → RouterAgent |
| `knowledge.py` | `/api/knowledge` | 知识导航树 CRUD + 内容关联 |
| `admin.py` | `/api/admin` | 审计日志/用户列表/权限策略（大部分 TODO） |
| `system.py` | `/api/system` | 系统配置/连接测试/初始化 |

### Agent 层 (`agents/`)
| 文件 | Agent | 状态 | 职责 |
|------|-------|------|------|
| `router.py` | RouterAgent | ✅ | 意图分类 + SQL 注入检测 + 路由分发 |
| `coordinator.py` | CoordinatorAgent | ⚠️ | 任务编排（DB查询可用，KB/混合查询 TODO） |
| `permission.py` | PermissionAgent | ⚠️ | RBAC 鉴权 + 敏感字段脱敏 |
| `wiki_agent.py` | WikiAgent | ✅ | Wiki 搜索 + 内容获取 |
| `vector.py` | VectorAgent | ✅ | 语义搜索 + 向量存储（含权限过滤） |
| `db_agent.py` | DBAgent | ✅ | 员工查询 + 统计 |
| `navigation.py` | NavigationAgent | ✅ | 关键词 + LLM 分类 |
| `review.py` | ReviewAgent | ✅ | 敏感词检查 + MD 格式修正 |
| `mindmap.py` | MindMapAgent | ✅ | 思维导图 JSON/Mermaid 生成 |

### Service 层 (`services/`)
| 文件 | 用途 |
|------|------|
| `wiki_service.py` | Wiki CRUD + 版本管理 + 全文搜索 + 权限过滤 |
| `db_service.py` | 员工档案查询 + 行级访问控制 |
| `nav_service.py` | 知识导航树 CRUD + 内容关联 |
| `vector_service.py` | Milvus REST API 封装（insert/search/delete） |
| `llm_service.py` | LLM 多提供商架构（chat/embed/classify_intent） |
| `config_service.py` | 配置管理（环境变量 > 数据库 > 默认值）+ CONFIG_SCHEMA |
| `cache_service.py` | Redis 缓存封装 |
| `encryption.py` | Fernet 加密/解密（敏感配置字段） |

### LLM 提供商 (`services/llm_providers/`)
| 文件 | 提供商 | Embedding 支持 |
|------|--------|---------------|
| `base.py` | BaseLLMProvider 抽象基类 | - |
| `openai_provider.py` | OpenAI 兼容 | ✅ |
| `deepseek_provider.py` | DeepSeek | ✅ |
| `zhipu_provider.py` | 智谱 AI | ✅ |
| `ollama_provider.py` | Ollama 本地 | ❌ |
| `__init__.py` | ProviderRegistry 注册表 | - |

### 数据模型 (`models/`)
| 文件 | 表/模型 | 说明 |
|------|---------|------|
| `wiki.py` | wiki_pages + wiki_page_versions | Wiki 文档 + 版本历史 |
| `employee.py` | employees | 员工档案 |
| `conversation.py` | conversations | 会话记录 |
| `navigation.py` | knowledge_nav + nav_content_links | 知识导航树（ltree） |
| `local_user.py` | local_users | 本地用户（非 Keycloak） |
| `system_config.py` | system_configs | 系统配置键值对 |
| `audit.py` | audit_logs | 审计日志 |
| `casbin.py` | casbin_rule | Casbin 策略持久化 |
| `schemas.py` | Pydantic schemas | 所有请求/响应模型 |

### 核心模块 (`core/`)
| 文件 | 用途 |
|------|------|
| `security.py` | JWT 校验 + 密码哈希 + 本地 token 生成 |
| `casbin_policy.py` | Casbin RBAC 策略加载 + 权限检查 |
| `middleware.py` | 审计日志中间件 |
| `encryption.py` | Fernet 加密/解密 |
| `logging.py` | 日志配置（文件 + 控制台） |

### 数据库 (`db/`)
| 文件 | 用途 |
|------|------|
| `session.py` | AsyncSession 管理 + `recreate_engine()` 热重载 |
| `migrations/env.py` | Alembic 迁移配置 |

---

## Frontend 结构 (`frontend/src/`)

### 入口
| 文件 | 用途 |
|------|------|
| `main.js` | Vue 应用入口，注册 Element Plus + i18n + Router |
| `App.vue` | 根组件，el-config-provider + Element Plus 多语言联动 |

### 路由 (`router/`)
| 文件 | 说明 |
|------|------|
| `index.js` | 路由定义 + 登录守卫 + 初始化跳转 |

### API 封装 (`api/`)
| 文件 | 对应后端 |
|------|----------|
| `request.js` | Axios 实例 + token 拦截器 |
| `wiki.js` | `/api/wiki` CRUD |
| `qa.js` | `/api/qa/ask` |
| `knowledge.js` | `/api/knowledge/nav` CRUD |
| `system.js` | `/api/system` 配置 + 测试 + 初始化 |

### 状态管理 (`stores/`)
| 文件 | 用途 |
|------|------|
| `user.js` | 用户登录状态 + token 管理 |
| `system.js` | 系统初始化状态 |

### 页面视图 (`views/`)
| 文件 | 页面 | 状态 |
|------|------|------|
| `Login.vue` | 登录页 | ✅ |
| `Dashboard.vue` | 仪表盘 | ✅ |
| `Wiki.vue` | Wiki 文档（编辑器+预览+编辑删除） | ✅ |
| `QA.vue` | 智能问答 | ⚠️ 需对接实际向量搜索 |
| `Knowledge.vue` | 知识导航 | ✅ |
| `layout/MainLayout.vue` | 主布局（侧边栏+顶栏+语言切换） | ✅ |
| `setup/SetupLayout.vue` | 初始化向导（5步） | ✅ |
| `admin/Settings.vue` | 系统设置（6 Tab） | ✅ |

### 国际化 (`i18n/`)
| 文件 | 用途 |
|------|------|
| `index.js` | createI18n 实例 + Element Plus locale 联动 |
| `zh-CN/*.js` | 中文语言包（8个模块） |
| `en-US/*.js` | 英文语言包（8个模块） |

语言包模块：`common` / `login` / `dashboard` / `wiki` / `qa` / `knowledge` / `setup` / `settings`

---

## Infra 结构 (`infra/`)

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | PostgreSQL 15 + Milvus + Etcd + MinIO + Keycloak + Redis |
| `init-db.sql` | 数据库初始化（表结构 + ltree 扩展 + 预设数据） |

---

## 关键数据流

### 智能问答流程
```
用户提问 → QA API → RouterAgent
    → 意图分类（关键词 + LLM）
    → PURE_DB: CoordinatorAgent → DBAgent → DBService（PostgreSQL）
    → PURE_KB: VectorAgent → VectorService（Milvus）+ WikiAgent
    → HYBRID: 两者结合
    → 返回 answer + sources + intent + confidence
```

### 配置加载链
```
.env 文件 → pydantic Settings（config.py）
    ↓
CONFIG_SCHEMA（config_service.py）→ 数据库 system_configs 表
    ↓
优先级：环境变量 > 数据库 > 代码默认值
```

### 权限校验流程
```
JWT Token → security.py 解析 → UserContext（user_id, roles, dept_id）
    ↓
CasbinPolicy（casbin_policy.py）→ check_permission(roles, resource, action, scope)
    ↓
Service 层：WHERE 过滤 + 敏感字段脱敏
```

---

## 环境变量（`.env`）

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://knowledge:knowledge123@localhost:5432/knowledge

# Redis
REDIS_URL=redis://localhost:6379/0

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=knowledge_vectors

# Keycloak
KEYCLOAK_SERVER_URL=http://localhost:8080
KEYCLOAK_REALM=knowledge-platform
KEYCLOAK_CLIENT_ID=knowledge-backend
KEYCLOAK_CLIENT_SECRET=

# LLM
LLM_PROVIDER=openai
LLM_API_KEY=
LLM_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4
LLM_EMBEDDING_MODEL=text-embedding-3-small
LLM_EMBEDDING_DIM=1536

# 安全
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
ENCRYPTION_KEY=
JWT_ALGORITHM=RS256

# 审计
AUDIT_LOG_ENABLED=true
```

---

## 启动命令

```bash
# 基础设施
cd knowledge-platform/infra && docker compose up -d

# 后端
cd knowledge-platform/backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000

# 前端
cd knowledge-platform/frontend && npm install && npm run dev

# 测试
cd knowledge-platform/backend && python -m pytest tests/ -v

# 数据库迁移
cd knowledge-platform/backend && alembic upgrade head
```
