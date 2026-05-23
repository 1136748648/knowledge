<template>
  <div class="heatmap-page fade-in">
    <div class="page-header">
      <div class="header-content">
        <h1>{{ t('heatmap.title') }}</h1>
        <p>{{ t('heatmap.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="timeRange" size="default" @change="handleTimeRangeChange">
          <el-radio-button value="24h">{{ t('heatmap.timeRanges.24h') }}</el-radio-button>
          <el-radio-button value="7d">{{ t('heatmap.timeRanges.7d') }}</el-radio-button>
          <el-radio-button value="30d">{{ t('heatmap.timeRanges.30d') }}</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-row :gutter="20" class="top-row">
      <el-col :xs="24" :md="12">
        <div class="card hot-card">
          <div class="card-header">
            <h3>
              <el-icon :size="20" color="var(--color-cta)"><TrendCharts /></el-icon>
              {{ t('heatmap.hotQueries') }}
            </h3>
          </div>
          <div class="list-container">
            <div
              v-for="(item, index) in hotQueries"
              :key="index"
              class="list-item"
              @click="handleQueryClick(item.query)"
            >
              <div class="item-rank">
                <el-tag :type="getRankType(index)" size="small">{{ index + 1 }}</el-tag>
              </div>
              <div class="item-content">
                <div class="item-title">{{ item.query }}</div>
                <div class="item-meta">
                  <span class="item-count">{{ item.count }} {{ t('heatmap.times') }}</span>
                  <span class="item-trend" :class="item.trend > 0 ? 'trend-up' : 'trend-down'">
                    <el-icon :size="12">
                      <Top v-if="item.trend > 0" />
                      <Bottom v-else />
                    </el-icon>
                    {{ Math.abs(item.trend) }}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :md="12">
        <div class="card hot-card">
          <div class="card-header">
            <h3>
              <el-icon :size="20" color="var(--color-primary)"><Document /></el-icon>
              {{ t('heatmap.hotDocuments') }}
            </h3>
          </div>
          <div class="list-container">
            <div
              v-for="(item, index) in hotDocuments"
              :key="index"
              class="list-item"
              @click="handleDocumentClick(item.id)"
            >
              <div class="item-rank">
                <el-tag :type="getRankType(index)" size="small">{{ index + 1 }}</el-tag>
              </div>
              <div class="item-content">
                <div class="item-title">{{ item.title }}</div>
                <div class="item-meta">
                  <span class="item-count">{{ item.views }} {{ t('heatmap.views') }}</span>
                  <el-tag :type="getSensitivityType(item.sensitivity)" size="small">
                    {{ t(`heatmap.sensitivity.${item.sensitivity}`) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <div class="card timeline-card">
      <div class="card-header">
        <h3>
          <el-icon :size="20" color="var(--color-info)"><DataAnalysis /></el-icon>
          {{ t('heatmap.timeline') }}
        </h3>
        <el-radio-group v-model="chartType" size="small" @change="handleChartTypeChange">
          <el-radio-button value="bar">{{ t('heatmap.chartTypes.bar') }}</el-radio-button>
          <el-radio-button value="line">{{ t('heatmap.chartTypes.line') }}</el-radio-button>
          <el-radio-button value="heatmap">{{ t('heatmap.chartTypes.heatmap') }}</el-radio-button>
        </el-radio-group>
      </div>
      <div ref="timelineChartRef" class="chart-container"></div>
    </div>

    <div class="card nav-heat-card">
      <div class="card-header">
        <h3>
          <el-icon :size="20" color="var(--color-success)"><Compass /></el-icon>
          {{ t('heatmap.navigationHeat') }}
        </h3>
      </div>
      <div ref="navHeatChartRef" class="chart-container"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { Document, TrendCharts, DataAnalysis, Compass, Top, Bottom } from '@element-plus/icons-vue'
import { heatmapApi } from '@/api/heatmap'

const { t } = useI18n()
const router = useRouter()

const timeRange = ref('24h')
const chartType = ref('bar')
const hotQueries = ref([])
const hotDocuments = ref([])
const timelineData = ref([])
const navigationData = ref([])

let timelineChart = null
let navHeatChart = null
const timelineChartRef = ref(null)
const navHeatChartRef = ref(null)

const getRankType = (index) => {
  const types = ['', 'danger', 'warning', '', 'info']
  return types[index] || ''
}

const getSensitivityType = (level) => {
  const types = {
    low: 'success',
    medium: 'warning',
    high: 'danger'
  }
  return types[level] || 'info'
}

const handleTimeRangeChange = async () => {
  await loadData()
}

const handleChartTypeChange = () => {
  renderTimelineChart()
}

const handleQueryClick = (query) => {
  router.push({ path: '/qa', query: { q: query } })
}

const handleDocumentClick = (id) => {
  router.push({ path: '/wiki', query: { id } })
}

const loadData = async () => {
  try {
    const [queriesRes, documentsRes, timelineRes, navRes] = await Promise.all([
      heatmapApi.getHotQueries(timeRange.value),
      heatmapApi.getHotDocuments(timeRange.value),
      heatmapApi.getTimeline(new Date().toISOString().split('T')[0]),
      heatmapApi.getNavigationHeat()
    ])

    hotQueries.value = queriesRes.data || []
    hotDocuments.value = documentsRes.data || []
    timelineData.value = timelineRes.data || []
    navigationData.value = navRes.data || []

    await nextTick()
    renderTimelineChart()
    renderNavHeatChart()
  } catch (error) {
    console.error('Failed to load heatmap data:', error)
  }
}

const renderTimelineChart = () => {
  if (!timelineChartRef.value) return

  if (timelineChart) {
    timelineChart.dispose()
  }

  timelineChart = echarts.init(timelineChartRef.value)

  let option = {}

  if (chartType.value === 'bar') {
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: timelineData.value.map(item => item.time),
        axisLabel: { color: 'var(--color-text-secondary)' }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: 'var(--color-text-secondary)' }
      },
      series: [{
        name: t('heatmap.visits'),
        type: 'bar',
        data: timelineData.value.map(item => item.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'var(--color-primary)' },
            { offset: 1, color: 'var(--color-primary-light)' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      }]
    }
  } else if (chartType.value === 'line') {
    option = {
      tooltip: {
        trigger: 'axis'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: timelineData.value.map(item => item.time),
        boundaryGap: false,
        axisLabel: { color: 'var(--color-text-secondary)' }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: 'var(--color-text-secondary)' }
      },
      series: [{
        name: t('heatmap.visits'),
        type: 'line',
        smooth: true,
        data: timelineData.value.map(item => item.count),
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(124, 58, 237, 0.3)' },
            { offset: 1, color: 'rgba(124, 58, 237, 0.05)' }
          ])
        },
        lineStyle: { color: 'var(--color-primary)', width: 2 },
        itemStyle: { color: 'var(--color-primary)' }
      }]
    }
  } else if (chartType.value === 'heatmap') {
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    const data = []
    for (let i = 0; i < days.length; i++) {
      for (let j = 0; j < hours.length; j++) {
        const baseValue = Math.floor(Math.random() * 100)
        data.push([j, i, baseValue])
      }
    }

    option = {
      tooltip: {
        formatter: (params) => `${days[params.value[1]]} ${hours[params.value[0]]}: ${params.value[2]} ${t('heatmap.visits')}`
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '10%',
        top: '5%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: hours,
        splitArea: { show: true },
        axisLabel: { color: 'var(--color-text-secondary)', interval: 3 }
      },
      yAxis: {
        type: 'category',
        data: days,
        splitArea: { show: true },
        axisLabel: { color: 'var(--color-text-secondary)' }
      },
      visualMap: {
        min: 0,
        max: 100,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '0%',
        inRange: {
          color: ['#EDE9FE', '#A78BFA', '#7C3AED', '#5B21B6']
        }
      },
      series: [{
        name: t('heatmap.visits'),
        type: 'heatmap',
        data: data,
        label: { show: false },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    }
  }

  timelineChart.setOption(option)
}

const renderNavHeatChart = () => {
  if (!navHeatChartRef.value) return

  if (navHeatChart) {
    navHeatChart.dispose()
  }

  navHeatChart = echarts.init(navHeatChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params) => `${params.name}: ${params.value} ${t('heatmap.visits')}`
    },
    series: [{
      type: 'treemap',
      data: navigationData.value.map(item => ({
        name: item.name,
        value: item.heat,
        children: item.children ? item.children.map(child => ({
          name: child.name,
          value: child.heat
        })) : undefined
      })),
      leafDepth: 2,
      label: {
        show: true,
        formatter: '{b}'
      },
      upperLabel: {
        show: true,
        height: 30
      },
      itemStyle: {
        borderColor: '#fff',
        borderWidth: 2,
        gapWidth: 2
      },
      color: ['#EDE9FE', '#DDD6FE', '#A78BFA', '#7C3AED', '#5B21B6', '#4C1D95']
    }]
  }

  navHeatChart.setOption(option)
}

const handleResize = () => {
  if (timelineChart) {
    timelineChart.resize()
  }
  if (navHeatChart) {
    navHeatChart.resize()
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (timelineChart) {
    timelineChart.dispose()
  }
  if (navHeatChart) {
    navHeatChart.dispose()
  }
})
</script>

<style scoped>
.heatmap-page {
  padding: var(--spacing-lg);
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-xl);
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.header-content h1 {
  font-size: var(--font-size-2xl);
  margin-bottom: var(--spacing-xs);
}

.header-content p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.top-row {
  margin-bottom: var(--spacing-xl);
}

.hot-card {
  height: 100%;
  min-height: 400px;
}

.list-container {
  margin-top: var(--spacing-md);
}

.list-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  border-bottom: 1px solid var(--color-border-light);
}

.list-item:last-child {
  border-bottom: none;
}

.list-item:hover {
  background: var(--color-primary-50);
  transform: translateX(4px);
}

.item-rank {
  flex-shrink: 0;
  min-width: 28px;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-title {
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: var(--spacing-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.item-count {
  color: var(--color-text-muted);
}

.item-trend {
  display: flex;
  align-items: center;
  gap: 2px;
  font-weight: 500;
}

.trend-up {
  color: var(--color-success);
}

.trend-down {
  color: var(--color-error);
}

.timeline-card {
  margin-bottom: var(--spacing-xl);
}

.nav-heat-card {
  margin-bottom: var(--spacing-xl);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-md);
}

.card-header h3 {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: var(--font-size-lg);
  margin: 0;
}

.chart-container {
  height: 300px;
  margin-top: var(--spacing-lg);
  width: 100%;
}

@media (max-width: 768px) {
  .heatmap-page {
    padding: var(--spacing-md);
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .el-radio-group {
    width: 100%;
    display: flex;
  }

  .header-actions .el-radio-button {
    flex: 1;
  }

  .chart-container {
    height: 250px;
  }

  .list-item {
    padding: var(--spacing-sm);
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .card-header .el-radio-group {
    width: 100%;
  }
}
</style>
