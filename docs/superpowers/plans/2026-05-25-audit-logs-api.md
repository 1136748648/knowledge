# FR-SYSTEM-004: 审计日志查询实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现审计日志查询API，支持按时间、用户、操作类型筛选，提供列表查询、详情查看和导出功能。

**Architecture:** 在现有审计日志中间件基础上，添加查询API端点。采用分层架构（API → Service → DAL），支持分页查询和多条件筛选。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, Vue3, Element Plus

---

## 文件结构

| 文件路径 | 职责 | 状态 |
|----------|------|------|
| `backend/app/dal/repositories.py` | 数据访问层，审计日志查询 | 修改 |
| `backend/app/services/admin_service.py` | 业务服务层 | 新增 |
| `backend/app/api/admin.py` | API路由层，新增审计日志端点 | 修改 |
| `backend/tests/test_audit_logs.py` | 审计日志API测试 | 新增 |
| `frontend/src/api/system.js` | 前端API调用 | 修改 |
| `frontend/src/views/admin/AuditLogs.vue` | 审计日志页面 | 新增 |
| `docs/requirements/detailed/FR-SYSTEM.md` | 更新需求状态 | 修改 |

---

## Task 1: 创建审计日志服务

**Files:**
- Create: `backend/app/services/admin_service.py`
- Modify: `backend/app/dal/repositories.py`

- [ ] **Step 1: 查看现有DAL层**

先检查 `dal/repositories.py` 是否已有审计日志相关方法。

- [ ] **Step 2: 在DAL层添加审计日志查询方法**

```python
# backend/app/dal/repositories.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wiki_storage import AuditLog

async def get_audit_logs(
    db: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> List[AuditLog]:
    """查询审计日志"""
    query = select(AuditLog)
    
    conditions = []
    if start_time:
        conditions.append(AuditLog.created_at >= start_time)
    if end_time:
        conditions.append(AuditLog.created_at <= end_time)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.order_by(AuditLog.created_at.desc())
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()

async def get_audit_log_count(
    db: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None
) -> int:
    """统计审计日志数量"""
    query = select(func.count(AuditLog.id))
    
    conditions = []
    if start_time:
        conditions.append(AuditLog.created_at >= start_time)
    if end_time:
        conditions.append(AuditLog.created_at <= end_time)
    if user_id:
        conditions.append(AuditLog.user_id == user_id)
    if action:
        conditions.append(AuditLog.action == action)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    result = await db.execute(query)
    return result.scalar()

async def get_audit_log_by_id(db: AsyncSession, log_id: int) -> Optional[AuditLog]:
    """根据ID获取审计日志详情"""
    query = select(AuditLog).where(AuditLog.id == log_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
```

- [ ] **Step 3: 创建Admin服务**

```python
# backend/app/services/admin_service.py
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.dal.repositories import get_audit_logs, get_audit_log_count, get_audit_log_by_id

class AdminService:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def query_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """查询审计日志列表"""
        skip = (page - 1) * page_size
        logs = await get_audit_logs(
            self.db_session,
            start_time,
            end_time,
            user_id,
            action,
            skip,
            page_size
        )
        
        total = await get_audit_log_count(
            self.db_session,
            start_time,
            end_time,
            user_id,
            action
        )
        
        return {
            "items": [log.to_dict() for log in logs],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def get_audit_log_detail(self, log_id: int):
        """获取审计日志详情"""
        log = await get_audit_log_by_id(self.db_session, log_id)
        if log:
            return log.to_dict()
        return None
    
    async def export_audit_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
        action: Optional[str] = None
    ) -> str:
        """导出审计日志为CSV"""
        logs = await get_audit_logs(
            self.db_session,
            start_time,
            end_time,
            user_id,
            action,
            skip=0,
            limit=10000
        )
        
        lines = ["user_id,username,action,resource,status,ip_address,created_at"]
        for log in logs:
            line = f'"{log.user_id}","{log.username}","{log.action}","{log.resource}","{log.status}","{log.ip_address}","{log.created_at}"'
            lines.append(line)
        
        return "\n".join(lines)
```

- [ ] **Step 4: Commit**

```bash
cd backend
git add app/dal/repositories.py app/services/admin_service.py
git commit -m "feat: add audit log repository and service"
```

---

## Task 2: 新增审计日志API端点

**Files:**
- Modify: `backend/app/api/admin.py`

- [ ] **Step 1: 添加审计日志端点**

```python
# backend/app/api/admin.py
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.schemas import UserContext
from app.services.admin_service import AdminService

router = APIRouter()

def get_admin_service(session: AsyncSession = Depends(get_db)) -> AdminService:
    return AdminService(session)

@router.get("/audit-logs")
async def get_audit_logs(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserContext = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """
    查询审计日志列表
    
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **user_id**: 用户ID
    - **action**: 操作类型
    - **page**: 页码
    - **page_size**: 每页数量
    """
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    return await service.query_audit_logs(
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        action=action,
        page=page,
        page_size=page_size
    )

@router.get("/audit-logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    current_user: UserContext = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """获取审计日志详情"""
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    log = await service.get_audit_log_detail(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")
    return log

@router.get("/audit-logs/export")
async def export_audit_logs(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    user_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    current_user: UserContext = Depends(get_current_active_user),
    service: AdminService = Depends(get_admin_service)
):
    """导出审计日志为CSV"""
    if "admin" not in current_user.roles and "audit" not in current_user.roles:
        raise HTTPException(status_code=403, detail="无审计权限")
    
    csv_content = await service.export_audit_logs(
        start_time=start_time,
        end_time=end_time,
        user_id=user_id,
        action=action
    )
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=csv_content,
        headers={
            "Content-Disposition": 'attachment; filename="audit_logs.csv"',
            "Content-Type": "text/csv; charset=utf-8"
        }
    )
```

- [ ] **Step 2: Commit**

```bash
cd backend
git add app/api/admin.py
git commit -m "feat: add audit logs API endpoints"
```

---

## Task 3: 更新前端API

**Files:**
- Modify: `frontend/src/api/system.js`

- [ ] **Step 1: 添加审计日志API调用**

```javascript
// frontend/src/api/system.js

// 审计日志相关
export const getAuditLogs = (params) => request.get('/admin/audit-logs', { params })
export const getAuditLogDetail = (id) => request.get(`/admin/audit-logs/${id}`)
export const exportAuditLogs = (params) => 
  request.get('/admin/audit-logs/export', { params, responseType: 'blob' })
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/api/system.js
git commit -m "feat: add audit logs API"
```

---

## Task 4: 创建审计日志页面

**Files:**
- Create: `frontend/src/views/admin/AuditLogs.vue`

- [ ] **Step 1: 创建页面组件**

```vue
<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h1>{{ t('admin.auditLogs.title') }}</h1>
      <p>{{ t('admin.auditLogs.subtitle') }}</p>
    </div>
    
    <div class="filter-section">
      <el-form :model="filters" inline class="filter-form">
        <el-form-item :label="t('admin.auditLogs.timeRange')">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            :disabled="loading"
          />
        </el-form-item>
        <el-form-item :label="t('admin.auditLogs.userId')">
          <el-input
            v-model="filters.user_id"
            :placeholder="t('admin.auditLogs.userIdPlaceholder')"
            :disabled="loading"
          />
        </el-form-item>
        <el-form-item :label="t('admin.auditLogs.action')">
          <el-select v-model="filters.action" :disabled="loading">
            <el-option :label="t('admin.auditLogs.all')" value="" />
            <el-option :label="t('admin.auditLogs.create')" value="create" />
            <el-option :label="t('admin.auditLogs.update')" value="update" />
            <el-option :label="t('admin.auditLogs.delete')" value="delete" />
            <el-option :label="t('admin.auditLogs.login')" value="login" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="search" :loading="loading">
            {{ t('common.btn.search') }}
          </el-button>
          <el-button @click="resetFilters">{{ t('common.btn.reset') }}</el-button>
          <el-button @click="handleExport" :loading="exporting">
            <el-icon><Download /></el-icon>
            {{ t('admin.auditLogs.export') }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <div class="table-section">
      <el-table :data="logs" border :loading="loading">
        <el-table-column prop="id" :label="t('admin.auditLogs.id')" width="80" />
        <el-table-column prop="username" :label="t('admin.auditLogs.user')" />
        <el-table-column prop="action" :label="t('admin.auditLogs.action')" />
        <el-table-column prop="resource" :label="t('admin.auditLogs.resource')" />
        <el-table-column prop="status" :label="t('admin.auditLogs.status')">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
              {{ scope.row.status === 'success' ? t('common.status.success') : t('common.status.failed') }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" :label="t('admin.auditLogs.ip')" />
        <el-table-column prop="created_at" :label="t('admin.auditLogs.time')" />
        <el-table-column :label="t('common.action.action')" width="100">
          <template #default="scope">
            <el-button text size="small" @click="showDetail(scope.row)">
              {{ t('common.action.detail') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <el-pagination
        :total="total"
        :page-size="filters.page_size"
        :current-page="filters.page"
        @current-change="handlePageChange"
        layout="total, prev, pager, next, jumper"
      />
    </div>
    
    <el-dialog :title="t('admin.auditLogs.detail')" :visible.sync="showDetailDialog" width="600px">
      <div v-if="selectedLog" class="detail-content">
        <el-descriptions title="" :column="2">
          <el-descriptions-item :label="t('admin.auditLogs.id')">{{ selectedLog.id }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.user')">{{ selectedLog.username }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.action')">{{ selectedLog.action }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.resource')">{{ selectedLog.resource }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.status')">
            <el-tag :type="selectedLog.status === 'success' ? 'success' : 'danger'">
              {{ selectedLog.status === 'success' ? t('common.status.success') : t('common.status.failed') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.ip')">{{ selectedLog.ip_address }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.time')" :span="2">{{ selectedLog.created_at }}</el-descriptions-item>
          <el-descriptions-item :label="t('admin.auditLogs.detailInfo')" :span="2">
            <pre class="detail-extra">{{ selectedLog.extra || '-' }}</pre>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { getAuditLogs, getAuditLogDetail, exportAuditLogs } from '@/api/system'

const { t } = useI18n()

const loading = ref(false)
const exporting = ref(false)
const logs = ref([])
const total = ref(0)
const showDetailDialog = ref(false)
const selectedLog = ref(null)
const dateRange = ref([])

const filters = reactive({
  user_id: '',
  action: '',
  page: 1,
  page_size: 20
})

watch(dateRange, (newVal) => {
  if (newVal && newVal.length === 2) {
    filters.start_time = newVal[0].toISOString()
    filters.end_time = newVal[1].toISOString()
  }
})

async function search() {
  await loadLogs()
}

async function loadLogs() {
  loading.value = true
  try {
    const params = { ...filters }
    delete params.start_time
    delete params.end_time
    if (dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }
    
    const result = await getAuditLogs(params)
    logs.value = result.items
    total.value = result.total
  } catch {
    ElMessage.error(t('admin.auditLogs.loadFailed'))
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.user_id = ''
  filters.action = ''
  filters.page = 1
  dateRange.value = []
}

function handlePageChange(page) {
  filters.page = page
  loadLogs()
}

async function showDetail(log) {
  try {
    selectedLog.value = await getAuditLogDetail(log.id)
    showDetailDialog.value = true
  } catch {
    ElMessage.error(t('admin.auditLogs.loadDetailFailed'))
  }
}

async function handleExport() {
  exporting.value = true
  try {
    const params = {}
    if (dateRange.value.length === 2) {
      params.start_time = dateRange.value[0].toISOString()
      params.end_time = dateRange.value[1].toISOString()
    }
    if (filters.user_id) params.user_id = filters.user_id
    if (filters.action) params.action = filters.action
    
    const response = await exportAuditLogs(params)
    const blob = new Blob([response], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `audit_logs_${new Date().toISOString().split('T')[0]}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    
    ElMessage.success(t('admin.auditLogs.exportSuccess'))
  } catch {
    ElMessage.error(t('admin.auditLogs.exportFailed'))
  } finally {
    exporting.value = false
  }
}

loadLogs()
</script>

<style scoped>
.audit-logs-page {
  padding: 24px;
}

.page-header h1 {
  font-size: var(--font-size-xl);
  margin-bottom: 8px;
}

.page-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.filter-section {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
  margin-bottom: 20px;
}

.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
  margin-right: 16px;
}

.table-section {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 16px;
}

.detail-content {
  padding: 16px;
}

.detail-extra {
  background: #1e1e2e;
  color: #cdd6f4;
  padding: 12px;
  border-radius: var(--radius-md);
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 13px;
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/views/admin/AuditLogs.vue
git commit -m "feat: add audit logs page"
```

---

## Task 5: 添加国际化翻译

**Files:**
- Modify: `frontend/src/i18n/zh-CN/admin.js`
- Modify: `frontend/src/i18n/en-US/admin.js`

- [ ] **Step 1: 添加中文翻译**

```javascript
// frontend/src/i18n/zh-CN/admin.js
auditLogs: {
  title: '审计日志',
  subtitle: '系统操作审计记录',
  timeRange: '时间范围',
  userId: '用户ID',
  userIdPlaceholder: '输入用户ID',
  action: '操作类型',
  all: '全部',
  create: '创建',
  update: '更新',
  delete: '删除',
  login: '登录',
  export: '导出',
  id: 'ID',
  user: '用户',
  resource: '资源',
  status: '状态',
  ip: 'IP地址',
  time: '时间',
  detail: '日志详情',
  detailInfo: '详细信息',
  loadFailed: '加载日志失败',
  loadDetailFailed: '加载日志详情失败',
  exportSuccess: '导出成功',
  exportFailed: '导出失败'
}
```

- [ ] **Step 2: 添加英文翻译**

```javascript
// frontend/src/i18n/en-US/admin.js
auditLogs: {
  title: 'Audit Logs',
  subtitle: 'System Operation Audit Records',
  timeRange: 'Time Range',
  userId: 'User ID',
  userIdPlaceholder: 'Enter user ID',
  action: 'Action',
  all: 'All',
  create: 'Create',
  update: 'Update',
  delete: 'Delete',
  login: 'Login',
  export: 'Export',
  id: 'ID',
  user: 'User',
  resource: 'Resource',
  status: 'Status',
  ip: 'IP Address',
  time: 'Time',
  detail: 'Detail',
  detailInfo: 'Detail Info',
  loadFailed: 'Failed to load logs',
  loadDetailFailed: 'Failed to load log detail',
  exportSuccess: 'Export successful',
  exportFailed: 'Export failed'
}
```

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/i18n/zh-CN/admin.js src/i18n/en-US/admin.js
git commit -m "feat: add audit logs i18n"
```

---

## Task 6: 更新需求文档

**Files:**
- Modify: `docs/requirements/detailed/FR-SYSTEM.md`

- [ ] **Step 1: 更新状态**

修改FR-SYSTEM-004状态从 `⚠️ 部分实现` 改为 `✅ 已完成`

- [ ] **Step 2: Commit**

```bash
git add docs/requirements/detailed/FR-SYSTEM.md
git commit -m "docs: update FR-SYSTEM-004 status"
```

---

## Self-Review

### 1. Spec Coverage

| 需求项 | 对应Task |
|--------|----------|
| 查询审计日志 | Task 1, Task 2 |
| 筛选日志（时间、用户、操作类型） | Task 2 |
| 查看日志详情 | Task 2, Task 4 |
| 导出日志 | Task 2, Task 4 |

### 2. Placeholder Scan

✅ 无占位符，所有步骤都有具体代码和命令

### 3. Type Consistency

✅ 类型和方法签名一致

---

**Plan complete.**