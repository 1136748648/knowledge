<template>
  <div class="dashboard fade-in">
    <div class="page-header">
      <h1>{{ t('dashboard.title') }}</h1>
      <p>{{ t('dashboard.subtitle') }}</p>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: var(--color-primary-100); color: var(--color-primary)">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.wikiCount }}</div>
            <div class="stat-label">{{ t('dashboard.stats.wiki') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #FEF3C7; color: #D97706">
            <el-icon :size="24"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.qaCount }}</div>
            <div class="stat-label">{{ t('dashboard.stats.qa') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #D1FAE5; color: #059669">
            <el-icon :size="24"><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">{{ t('dashboard.stats.users') }}</div>
          </div>
        </div>
      </el-col>
      <el-col :xs="12" :sm="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: #EDE9FE; color: #7C3AED">
            <el-icon :size="24"><Compass /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.navCount }}</div>
            <div class="stat-label">{{ t('dashboard.stats.nav') }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20">
      <el-col :xs="24" :md="16">
        <div class="card">
          <h3>{{ t('dashboard.quickActions.title') }}</h3>
          <div class="quick-actions">
            <div class="action-item" @click="router.push('/wiki')">
              <el-icon :size="32" color="#7C3AED"><Document /></el-icon>
              <span>{{ t('dashboard.quickActions.createDoc') }}</span>
            </div>
            <div class="action-item" @click="router.push('/qa')">
              <el-icon :size="32" color="#F97316"><ChatDotRound /></el-icon>
              <span>{{ t('dashboard.quickActions.smartQA') }}</span>
            </div>
            <div class="action-item" @click="router.push('/knowledge')">
              <el-icon :size="32" color="#10B981"><Compass /></el-icon>
              <span>{{ t('dashboard.quickActions.knowledgeNav') }}</span>
            </div>
            <div class="action-item" @click="router.push('/admin/settings')">
              <el-icon :size="32" color="#6B7280"><Setting /></el-icon>
              <span>{{ t('dashboard.quickActions.systemSettings') }}</span>
            </div>
          </div>
        </div>
      </el-col>
      <el-col :xs="24" :md="8">
        <div class="card">
          <h3>{{ t('dashboard.systemStatus.title') }}</h3>
          <div class="status-list">
            <div class="status-item">
              <span class="status-dot status-online" />
              <span>{{ t('dashboard.systemStatus.database') }}</span>
              <el-tag size="small" type="success">{{ t('common.status.normal') }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-dot status-online" />
              <span>{{ t('dashboard.systemStatus.milvus') }}</span>
              <el-tag size="small" type="success">{{ t('common.status.normal') }}</el-tag>
            </div>
            <div class="status-item">
              <span class="status-dot status-online" />
              <span>{{ t('dashboard.systemStatus.llm') }}</span>
              <el-tag size="small" type="success">{{ t('common.status.normal') }}</el-tag>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 热门推荐入口 -->
    <div class="heatmap-entry-card" @click="router.push('/heatmap')">
      <div class="entry-icon">
        <el-icon :size="32"><TrendCharts /></el-icon>
      </div>
      <div class="entry-content">
        <h3>{{ t('heatmap.dashboardCard.title') }}</h3>
        <p>{{ t('heatmap.dashboardCard.subtitle') }}</p>
        <div v-if="topQueries.length > 0" class="entry-tags">
          <el-tag
            v-for="(query, index) in topQueries"
            :key="index"
            size="small"
            :type="index === 0 ? 'danger' : index === 1 ? 'warning' : 'info'"
          >
            {{ query.query }}
          </el-tag>
        </div>
      </div>
      <div class="entry-arrow">
        <el-icon :size="24"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { TrendCharts, ArrowRight, Document, ChatDotRound, User, Compass, Setting } from '@element-plus/icons-vue'
import { heatmapApi } from '@/api/heatmap'

const { t } = useI18n()
const router = useRouter()

const stats = ref({
  wikiCount: 0,
  qaCount: 0,
  userCount: 0,
  navCount: 0,
})

const topQueries = ref([])

onMounted(async () => {
  try {
    const res = await heatmapApi.getHotQueries('24h', 3)
    topQueries.value = res.data || []
  } catch (error) {
    console.error('Failed to load top queries:', error)
  }
})
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: var(--font-size-2xl);
  margin-bottom: 4px;
}

.page-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all var(--transition-base);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all var(--transition-base);
}

.action-item:hover {
  border-color: var(--color-primary-200);
  background: var(--color-primary-50);
  transform: translateY(-2px);
}

.action-item span {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text);
}

.status-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-sm);
}

.status-item .el-tag {
  margin-left: auto;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-online {
  background: var(--color-success);
}

.status-offline {
  background: var(--color-error);
}

@media (max-width: 768px) {
  .quick-actions {
    grid-template-columns: repeat(2, 1fr);
  }
}

.heatmap-entry-card {
  display: flex;
  align-items: center;
  gap: 20px;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  padding: 24px;
  margin-top: 20px;
  cursor: pointer;
  transition: all var(--transition-base);
}

.heatmap-entry-card:hover {
  border-color: var(--color-cta);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.entry-icon {
  width: 64px;
  height: 64px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, var(--color-cta) 0%, #F97316 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.entry-content {
  flex: 1;
  min-width: 0;
}

.entry-content h3 {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.entry-content p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0 0 12px 0;
}

.entry-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.entry-arrow {
  color: var(--color-text-muted);
  flex-shrink: 0;
  transition: all var(--transition-base);
}

.heatmap-entry-card:hover .entry-arrow {
  color: var(--color-cta);
  transform: translateX(4px);
}
</style>
