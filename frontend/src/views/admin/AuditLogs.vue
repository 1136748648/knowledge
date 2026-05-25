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
