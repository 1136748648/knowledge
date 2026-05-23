# 项目结构解耦优化设计方案

**日期**: 2025-05-23
**状态**: 已批准

## 一、目标

1. **分层架构**: API Layer → Server Layer → DAL Layer，禁止越级调用
2. **依赖注入**: 使用 FastAPI Depends 模式，禁止直接实例化

## 二、目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│                   (app/api/*.py)                           │
│              请求/响应处理，参数校验                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ Depends()
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Server Layer                             │
│                  (app/server/*.py)                         │
│           业务逻辑，权限校验，事务编排                         │
└─────────────────────────┬───────────────────────────────────┘
                          │ 构造函数注入
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       DAL Layer                              │
│               (app/dal/repositories.py)                     │
│              数据访问，CRUD 封装                             │
└─────────────────────────────────────────────────────────────┘
```

## 三、目录结构

```
app/
├── api/                    # API Layer (不变)
│   ├── __init__.py
│   ├── wiki.py           # 只做请求路由，调用 Server
│   ├── auth.py
│   ├── qa.py
│   └── ...
│
├── server/                # 新建 Server Layer
│   ├── __init__.py       # 导出所有 Server 和 DI 工厂
│   ├── wiki_server.py    # Wiki 业务逻辑
│   ├── auth_server.py    # 认证业务逻辑
│   ├── qa_server.py      # 问答业务逻辑
│   ├── admin_server.py   # 管理业务逻辑
│   ├── heatmap_server.py # 热力图业务逻辑
│   └── knowledge_server.py # 知识导航业务逻辑
│
├── services/              # 基础设施服务层 (不变)
│   ├── llm_service.py    # LLM 调用
│   ├── cache_service.py   # 缓存
│   ├── nav_service.py     # 导航服务
│   ├── db_service.py      # 数据库服务
│   └── ...
│
├── dal/                   # DAL Layer (不变)
│   ├── base.py           # 抽象基类
│   ├── postgres.py       # PostgreSQL 适配器
│   ├── repositories.py   # Repository 实现
│   └── registry.py       # Repository 注册表
│
└── main.py               # 入口 (更新路由引用)
```

## 四、DI 设计

### 4.1 Server 获取 Repository 的方式

使用构造函数注入：

```python
class WikiServer:
    def __init__(
        self,
        page_repo: WikiPageRepository,
        version_repo: WikiPageVersionRepository,
    ):
        self.page_repo = page_repo
        self.version_repo = version_repo
```

### 4.2 API 获取 Server 的方式

使用 FastAPI Depends：

```python
def get_wiki_server(
    page_repo: WikiPageRepository = Depends(get_wiki_page_repo),
    version_repo: WikiPageVersionRepository = Depends(get_wiki_version_repo),
) -> WikiServer:
    return WikiServer(page_repo, version_repo)
```

### 4.3 DI 工厂 (app/server/__init__.py)

```python
from functools import lru_cache
from fastapi import Depends
from app.dal import get_adapter
from app.dal.repositories import WikiPageRepository, WikiPageVersionRepository
from .wiki_server import WikiServer

@lru_cache()
def get_wiki_page_repo() -> WikiPageRepository:
    adapter = get_adapter()
    return WikiPageRepository(adapter)

@lru_cache()
def get_wiki_version_repo() -> WikiPageVersionRepository:
    adapter = get_adapter()
    return WikiPageVersionRepository(adapter)

def get_wiki_server(
    page_repo: WikiPageRepository = Depends(get_wiki_page_repo),
    version_repo: WikiPageVersionRepository = Depends(get_wiki_version_repo),
) -> WikiServer:
    return WikiServer(page_repo, version_repo)
```

## 五、调用规则

### 5.1 允许的调用链

```
✅ API → Server → DAL
✅ API → Server → Services (基础设施服务如 LLM)
✅ API → Core (security, config)
✅ Server → Services (基础设施服务)
✅ Server → DAL
```

### 5.2 禁止的调用

```
❌ API → DAL (越级)
❌ API → Services (越级)
❌ Server → API (反向)
❌ DAL → Server (反向)
❌ DAL → API (反向)
```

## 六、迁移清单

### 6.1 创建 Server Layer

- [ ] 创建 `app/server/` 目录
- [ ] 创建 `__init__.py`
- [ ] WikiServer
- [ ] AuthServer
- [ ] QAServer
- [ ] AdminServer
- [ ] HeatmapServer
- [ ] KnowledgeServer

### 6.2 更新 API Layer

- [ ] 更新 `app/api/wiki.py`
- [ ] 更新 `app/api/auth.py`
- [ ] 更新 `app/api/qa.py`
- [ ] 更新 `app/api/admin.py`
- [ ] 更新 `app/api/heatmap.py`
- [ ] 更新 `app/api/knowledge.py`

### 6.3 更新 main.py

- [ ] 更新导入语句

### 6.4 验证

- [ ] 运行测试
- [ ] 手动验证功能

## 七、测试策略

- 单元测试：Mock Server 依赖的 Repository
- 集成测试：通过 API 端点测试完整流程
- 保持现有测试结构，只需更新 mock 对象
