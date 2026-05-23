# 检索热力图功能设计文档

> 创建日期：2026-05-23
> 状态：待审核

---

## 一、功能概述

### 1.1 目标

为知识库平台新增检索热力图功能，实现：
- **用户推荐**（主要）：向用户展示热门知识，帮助发现高价值内容
- **管理员监控**（次要）：实时监控平台使用情况，发现热门知识和异常查询
- **数据分析**（次要）：长期数据分析，优化知识库结构和内容质量

### 1.2 核心能力

1. **热门查询词榜单** - 展示高频检索词
2. **热门文档榜单** - 展示频繁命中的知识文档
3. **时间热力图** - 可视化展示不同时段的检索热度
4. **知识导航热度** - 在知识导航树上标注热点节点

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户请求                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VectorService.search()                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. 执行向量检索                                          │   │
│  │ 2. 异步调用 HeatmapService.record_search()              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    HeatmapService (新增)                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ record_search() - 异步记录检索事件                       │   │
│  │   ├─ Redis: ZINCRBY 实时热度计数                        │   │
│  │   └─ PostgreSQL: INSERT 埋点数据                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              后台任务 (APScheduler, 每5分钟)                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ 1. 从Redis读取实时热榜                                   │   │
│  │ 2. 从PostgreSQL聚合历史统计                              │   │
│  │ 3. 更新知识导航树热度标记                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┬───────────────────────────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    热力图API (新增)                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ GET /api/heatmap/queries     - 热门查询词榜单            │   │
│  │ GET /api/heatmap/documents   - 热门文档榜单              │   │
│  │ GET /api/heatmap/timeline    - 时间热力图数据            │   │
│  │ GET /api/heatmap/navigation  - 知识导航热度              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 核心组件

| 组件 | 职责 |
|------|------|
| HeatmapService | 新增服务层，负责埋点记录和热度计算 |
| search_events表 | PostgreSQL存储完整埋点数据 |
| Redis Sorted Set | 存储实时热度排名 |
| 后台定时任务 | 每5分钟聚合计算 |
| 热力图API | 提供前端展示数据 |

---

## 三、数据埋点设计

### 3.1 埋点字段（完整埋点方案）

| 字段 | 类型 | 说明 |
|------|------|------|
| query_text | VARCHAR(500) | 查询词 |
| query_embedding | VECTOR(1536) | 查询向量（用于相似查询聚合） |
| user_id | VARCHAR(128) | 用户ID |
| dept_id | VARCHAR(64) | 部门ID |
| hit_doc_ids | TEXT[] | 命中文档ID列表 |
| hit_scores | FLOAT[] | 命中文档得分列表 |
| filter_conditions | JSONB | 过滤条件 |
| search_duration_ms | INTEGER | 检索耗时(毫秒) |
| created_at | TIMESTAMP | 时间戳 |

### 3.2 埋点位置

在 `VectorService.search()` 方法中埋点，异步写入数据存储。

---

## 四、数据库设计

### 4.1 PostgreSQL表结构

**search_events表 - 检索事件埋点数据**

```sql
CREATE TABLE search_events (
    id SERIAL PRIMARY KEY,
    query_text VARCHAR(500) NOT NULL,
    query_embedding VECTOR(1536),
    user_id VARCHAR(128),
    dept_id VARCHAR(64),
    hit_doc_ids TEXT[],
    hit_scores FLOAT[],
    filter_conditions JSONB,
    search_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_search_events_created_at ON search_events(created_at);
CREATE INDEX idx_search_events_user_id ON search_events(user_id);
CREATE INDEX idx_search_events_query_text ON search_events(query_text);
```

**heatmap_stats表 - 聚合统计结果**

```sql
CREATE TABLE heatmap_stats (
    id SERIAL PRIMARY KEY,
    stat_type VARCHAR(20) NOT NULL,  -- 'query' | 'document' | 'hour'
    stat_key VARCHAR(500) NOT NULL,
    stat_date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    avg_duration_ms FLOAT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_heatmap_stats_type_date ON heatmap_stats(stat_type, stat_date);
CREATE UNIQUE INDEX idx_heatmap_stats_unique ON heatmap_stats(stat_type, stat_key, stat_date);
```

### 4.2 Redis数据结构

```
# 实时热门查询词（24小时滚动）
ZSET heatmap:queries:24h
  member: "查询词文本"
  score: 检索次数

# 实时热门文档（24小时滚动）
ZSET heatmap:documents:24h
  member: "文档ID"
  score: 命中次数

# 小时热度计数器（用于时间热力图）
STRING heatmap:hour:{YYYY-MM-DD:HH}
  value: 该小时检索次数
  TTL: 7天
```

---

## 五、API接口设计

### 5.1 热门查询词榜单

```
GET /api/heatmap/queries

Query参数:
  - time_range: string (可选) - "24h" | "7d" | "30d"，默认"24h"
  - limit: int (可选) - 返回数量，默认10，最大50

响应:
{
  "time_range": "24h",
  "data": [
    {
      "rank": 1,
      "query": "如何申请年假",
      "count": 156,
      "trend": "up"
    }
  ],
  "updated_at": "2026-05-23T14:30:00Z"
}
```

### 5.2 热门文档榜单

```
GET /api/heatmap/documents

Query参数:
  - time_range: string (可选) - "24h" | "7d" | "30d"
  - limit: int (可选) - 返回数量，默认10

响应:
{
  "time_range": "24h",
  "data": [
    {
      "rank": 1,
      "doc_id": "wiki-123",
      "doc_title": "年假申请流程",
      "doc_type": "wiki",
      "hit_count": 89,
      "avg_score": 0.92
    }
  ]
}
```

### 5.3 时间热力图数据

```
GET /api/heatmap/timeline

Query参数:
  - date: string (可选) - 日期，格式YYYY-MM-DD，默认今天
  - granularity: string - "hour" | "day"，默认"hour"

响应:
{
  "date": "2026-05-23",
  "granularity": "hour",
  "data": [
    {"hour": 0, "count": 12},
    {"hour": 1, "count": 5}
  ],
  "peak_hour": 14,
  "total_count": 523
}
```

### 5.4 知识导航热度

```
GET /api/heatmap/navigation

响应:
{
  "data": [
    {
      "node_id": "nav-001",
      "node_name": "人事制度",
      "path": "/人事制度",
      "hit_count": 234,
      "hot_level": "hot"
    }
  ]
}
```

---

## 六、核心实现细节

### 6.1 HeatmapService实现

```python
# app/services/heatmap_service.py

class HeatmapService:
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session
    
    async def record_search(
        self,
        query_text: str,
        query_embedding: list[float],
        user_id: str | None,
        dept_id: str | None,
        hit_docs: list[dict],
        filter_conditions: dict,
        duration_ms: int
    ):
        """异步记录检索事件（Fire-and-forget）"""
        import asyncio
        asyncio.create_task(self._record_async(...))
    
    async def _record_async(self, ...):
        # 1. 写入PostgreSQL
        # 2. 更新Redis热度计数
        # 3. 更新小时计数器
        pass
    
    async def get_hot_queries(self, time_range: str, limit: int) -> list[dict]:
        """获取热门查询词"""
        pass
    
    async def get_hot_documents(self, time_range: str, limit: int) -> list[dict]:
        """获取热门文档"""
        pass
    
    async def get_timeline(self, date: str, granularity: str) -> dict:
        """获取时间热力图数据"""
        pass
    
    async def get_navigation_heat(self) -> list[dict]:
        """获取知识导航热度"""
        pass
```

### 6.2 VectorService埋点改造

```python
# app/services/vector_service.py

async def search(
    self,
    query_embedding: list[float],
    query_text: str = "",  # 新增参数
    user_id: str | None = None,
    visible_dept_ids: list[str] | None = None,
    allowed_sensitivities: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    import time
    start_time = time.time()
    
    # 执行检索
    results = await self._execute_search(...)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # 异步记录检索事件
    await self.heatmap_service.record_search(
        query_text=query_text,
        query_embedding=query_embedding,
        user_id=user_id,
        dept_id=...,
        hit_docs=results,
        filter_conditions={...},
        duration_ms=duration_ms
    )
    
    return results
```

### 6.3 后台定时任务

```python
# app/tasks/heatmap_aggregator.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

async def aggregate_heatmap_stats():
    """每5分钟聚合热度统计"""
    # 1. 从Redis读取实时数据
    # 2. 写入heatmap_stats表
    # 3. 更新知识导航热度标记
    pass

scheduler.add_job(aggregate_heatmap_stats, 'interval', minutes=5)
```

### 6.4 错误处理策略

| 场景 | 处理方式 |
|------|----------|
| 埋点失败 | 记录日志，不影响主流程返回结果 |
| Redis不可用 | 降级为仅写入PostgreSQL |
| PostgreSQL写入失败 | 记录日志，Redis继续工作 |

---

## 七、测试策略

### 7.1 单元测试

- **HeatmapService测试**：Mock Redis和PostgreSQL，测试各个方法
- **VectorService埋点测试**：验证异步记录是否正确触发
- **API接口测试**：测试各个热力图接口的响应格式

### 7.2 集成测试

- **端到端流程测试**：执行检索 → 验证埋点数据 → 查询热力图API
- **定时任务测试**：验证聚合逻辑正确性

### 7.3 性能测试

- **埋点性能影响**：验证异步记录不影响检索响应时间（目标：<5ms额外开销）
- **Redis写入性能**：验证高并发下的写入稳定性
- **查询性能**：验证热力图API响应时间（目标：<100ms）

---

## 八、部署注意事项

### 8.1 依赖项

- **Redis**：已在infra/docker-compose.yml中配置，需确保运行
- **APScheduler**：新增依赖，需添加到requirements.txt
- **PostgreSQL扩展**：如需存储向量，需安装pgvector扩展（可选）

### 8.2 配置项

```env
# .env 新增配置
HEATMAP_ENABLED=true
HEATMAP_REDIS_TTL=86400
HEATMAP_AGGREGATE_INTERVAL=5
```

### 8.3 数据迁移

- 创建`search_events`表和`heatmap_stats`表
- 创建相关索引

### 8.4 监控指标

- 检索埋点成功率
- Redis写入延迟
- PostgreSQL写入延迟
- 定时任务执行状态

---

## 九、实现优先级

### Phase 1（核心功能）

1. 数据库表创建
2. HeatmapService基础实现
3. VectorService埋点改造
4. 热门查询词/文档榜单API

### Phase 2（完善功能）

5. 时间热力图API
6. 知识导航热度API
7. 后台聚合任务

### Phase 3（优化增强）

8. 前端展示界面
9. 性能优化
10. 监控告警
