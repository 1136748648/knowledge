# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repo contains a multi-Agent dynamic knowledge base system (`knowledge-platform/`). The system integrates Wiki documents, vectorized conversation records, and relational employee data with RBAC permissions, knowledge navigation, and mind map generation.

## Repository Structure

```
knowledge-platform/
├── backend/                        # FastAPI 后端
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # Pydantic Settings 配置
│   │   ├── api/                    # API 路由
│   │   │   ├── auth.py             # 认证（Keycloak JWT）
│   │   │   ├── wiki.py             # Wiki CRUD + 搜索
│   │   │   ├── qa.py               # 智能问答入口
│   │   │   ├── knowledge.py        # 知识导航管理
│   │   │   └── admin.py            # 管理后台（审计日志、权限）
│   │   ├── agents/                 # Agent 实现
│   │   │   ├── router.py           # 路由Agent（意图识别 + SQL注入检测）
│   │   │   ├── coordinator.py      # 协调Agent（任务编排）
│   │   │   ├── permission.py       # 权限管控Agent
│   │   │   ├── wiki_agent.py       # Wiki Agent
│   │   │   ├── vector.py           # 向量Agent（Milvus）
│   │   │   ├── db_agent.py         # 轻库Agent（PostgreSQL）
│   │   │   ├── navigation.py       # 分类与导航Agent
│   │   │   ├── review.py           # 审核优化Agent
│   │   │   └── mindmap.py          # 思维导图Agent
│   │   ├── services/               # 业务服务层
│   │   │   ├── wiki_service.py     # Wiki CRUD + 版本历史
│   │   │   ├── vector_service.py   # Milvus 连接 + 向量操作
│   │   │   ├── db_service.py       # 员工档案查询（参数化SQL）
│   │   │   ├── nav_service.py      # 知识导航树 CRUD
│   │   │   └── llm_service.py      # LLM 调用封装（OpenAI兼容）
│   │   ├── core/                   # 核心模块
│   │   │   ├── security.py         # JWT 校验（Keycloak公钥）
│   │   │   ├── casbin_policy.py    # Casbin RBAC 策略引擎
│   │   │   └── middleware.py       # 审计日志中间件
│   │   ├── models/                 # SQLAlchemy ORM + Pydantic schemas
│   │   └── db/
│   │       ├── session.py          # AsyncSession 管理
│   │       └── migrations/         # Alembic 迁移
│   ├── tests/
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/                       # Vue3 + Vite 前端（待开发）
├── infra/
│   ├── docker-compose.yml          # PostgreSQL + Milvus + Keycloak + Redis
│   ├── init-db.sql                 # 数据库初始化脚本（表结构 + 预设数据）
│   └── keycloak/                   # Keycloak realm 配置
└── docs/
```

## Key Commands

```bash
# 启动基础设施
cd knowledge-platform/infra && docker compose up -d

# 安装后端依赖
cd knowledge-platform/backend && pip install -r requirements.txt

# 复制环境变量
cp .env.example .env

# 运行后端
cd knowledge-platform/backend && uvicorn app.main:app --reload --port 8000

# 运行测试
cd knowledge-platform/backend && python -m pytest tests/ -v

# 数据库迁移
cd knowledge-platform/backend && alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Tech Stack

- **Backend:** Python 3.11+ / FastAPI / SQLAlchemy 2.0 (async) / asyncpg
- **Database:** PostgreSQL 15 (关系数据 + ltree 导航树)
- **Vector DB:** Milvus 2.4
- **Auth:** Keycloak 24 (OAuth2/OIDC)
- **Permission:** Casbin (RBAC)
- **LLM:** OpenAI-compatible API
- **Frontend:** Vue3 + Vite + Element Plus (planned)

## Architecture

**Agent 通信模式：**
```
用户请求 → FastAPI 接口
    → 路由Agent（意图识别 + 权限预检）
        → 权限Agent（校验操作许可）
        → 协调Agent（任务分解）
            → Wiki Agent / 向量Agent / 轻库Agent（执行）
            → 结果聚合
        → 审核优化Agent（格式化 + 来源标注）
    → 返回用户
```

**权限数据流：**
```
JWT Token → 解析 user_id, roles, dept_id
    → Casbin enforcer 校验策略
    → Agent 查询时注入可见数据范围
    → Milvus filter: dept_id IN (visible_depts)
    → SQL WHERE: dept_id IN (visible_depts) AND sensitivity <= clearance
    → 敏感字段脱敏（根据角色）
```

## Database Schema

- **wiki_pages** — Wiki 文档（带 ACL、敏感度分级）
- **wiki_page_versions** — 版本历史
- **employees** — 员工档案（带密级、部门隔离）
- **conversations** — 会话问答记录（向量ID关联 Milvus）
- **knowledge_nav** — 知识导航树（ltree 物化路径）
- **nav_content_links** — 导航节点与内容关联
- **casbin_rule** — Casbin 策略持久化
- **audit_logs** — 操作审计日志

## Key Constraints

- All SQL must use parameterized queries (SQLAlchemy ORM) — string concatenation is forbidden.
- Every data access goes through permission check (Casbin RBAC).
- Sensitive fields (salary, phone) are masked based on user role.
- All answers must cite sources.
- All API operations are logged to audit_logs.
