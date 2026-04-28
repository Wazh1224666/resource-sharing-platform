<template>
  <div class="statistics-container">
    <header class="header">
      <div class="header-inner">
        <div class="brand">
          <div class="brand-mark" aria-hidden="true"></div>
          <div class="brand-text">
            <div class="logo">资源统计中心</div>
            <div class="tagline">数据洞察 · 趋势分析 · 管理决策</div>
          </div>
        </div>

        <div class="user-info">
          <el-avatar :size="34" icon="UserFilled" />
          <span class="username">{{ userDisplayName }}</span>
          <el-tag size="small" effect="light">{{ roleText }}</el-tag>
          <el-button link @click="goToHome">返回首页</el-button>
          <el-button link @click="handleLogout">退出</el-button>
        </div>
      </div>
    </header>

    <div class="main-content">
      <el-card class="content-card" shadow="never">
        <!-- 概览卡片 -->
        <div class="overview-section">
          <div class="section-title">
            <el-icon><DataAnalysis /></el-icon>
            <span>数据概览</span>
          </div>
          <div class="overview-cards">
            <el-card class="overview-card" shadow="hover">
              <div class="card-content">
                <div class="card-icon" style="background: linear-gradient(135deg, #3b82f6, #8b5cf6);">
                  <el-icon><Folder /></el-icon>
                </div>
                <div class="card-info">
                  <div class="card-value">{{ formatNumber(statistics.totalResources) }}</div>
                  <div class="card-label">资源总数</div>
                </div>
              </div>
            </el-card>

            <el-card class="overview-card" shadow="hover">
              <div class="card-content">
                <div class="card-icon" style="background: linear-gradient(135deg, #10b981, #34d399);">
                  <el-icon><DataBoard /></el-icon>
                </div>
                <div class="card-info">
                  <div class="card-value">{{ formatFileSize(statistics.totalFileSize) }}</div>
                  <div class="card-label">总文件大小</div>
                </div>
              </div>
            </el-card>

            <el-card class="overview-card" shadow="hover">
              <div class="card-content">
                <div class="card-icon" style="background: linear-gradient(135deg, #f59e0b, #fbbf24);">
                  <el-icon><Download /></el-icon>
                </div>
                <div class="card-info">
                  <div class="card-value">{{ formatNumber(statistics.totalDownloads) }}</div>
                  <div class="card-label">总下载量</div>
                </div>
              </div>
            </el-card>

            <el-card class="overview-card" shadow="hover">
              <div class="card-content">
                <div class="card-icon" style="background: linear-gradient(135deg, #ef4444, #f87171);">
                  <el-icon><View /></el-icon>
                </div>
                <div class="card-info">
                  <div class="card-value">{{ formatNumber(statistics.totalViews) }}</div>
                  <div class="card-label">总浏览量</div>
                </div>
              </div>
            </el-card>
          </div>
        </div>

        <!-- 图表区域：文件类型分布 + 文件大小分布 -->
        <div class="charts-grid">
          <!-- 文件类型分布 -->
          <div class="chart-section">
            <div class="section-title">
              <el-icon><PieChart /></el-icon>
              <span>文件类型分布</span>
            </div>
            <div ref="fileTypeChartRef" class="chart-container"></div>
          </div>

          <!-- 文件大小分布 -->
          <div class="chart-section">
            <div class="section-title">
              <el-icon><Box /></el-icon>
              <span>文件大小分布</span>
            </div>
            <div ref="fileSizeChartRef" class="chart-container"></div>
          </div>
        </div>

        <!-- 最近30天趋势 -->
        <div class="chart-section chart-full">
          <div class="section-title">
            <el-icon><TrendCharts /></el-icon>
            <span>最近30天趋势</span>
          </div>
          <div ref="trendChartRef" class="chart-container chart-tall"></div>
        </div>

        <!-- 热门资源 -->
        <div class="chart-section chart-full">
          <div class="section-title">
            <el-icon><Star /></el-icon>
            <span>热门资源（下载量TOP10）</span>
          </div>
          <el-table :data="statistics.popularResources" stripe class="data-table">
              <el-table-column prop="title" label="资源名称" min-width="160" show-overflow-tooltip />
              <el-table-column prop="fileType" label="类型" width="80">
                <template #default="scope">
                  <el-tag size="small" :type="getTagType(scope.row.fileType)">
                    {{ scope.row.fileType ? scope.row.fileType.toUpperCase() : '未知' }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="fileSize" label="大小" width="90">
                <template #default="scope">
                  {{ formatFileSize(scope.row.fileSize) }}
                </template>
              </el-table-column>
              <el-table-column prop="downloadCount" label="下载" width="70" sortable />
              <el-table-column prop="viewCount" label="浏览" width="70" sortable />
              <el-table-column prop="uploaderName" label="上传者" width="90" />
            </el-table>
          </div>

        <!-- 操作按钮 -->
        <div class="action-section">
          <el-button type="primary" icon="Refresh" @click="fetchStatistics" :loading="loading">
            刷新数据
          </el-button>
          <el-button type="info" icon="Download" @click="exportStatistics">
            导出统计
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis, Folder, DataBoard, Download, View,
  PieChart, Box, TrendCharts, Star,
  UserFilled, Refresh
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import request from '../utils/request'

const router = useRouter()
const loading = ref(false)

// 用户信息
const userInfo = ref({ id: null, username: '', role: 'STUDENT' })

// 统计数据结构
const statistics = reactive({
  totalResources: 0,
  totalFileSize: 0,
  totalDownloads: 0,
  totalViews: 0,
  fileTypeStats: [],
  uploaderStats: [],
  dailyStats: [],
  popularResources: [],
  fileSizeDistribution: {
    smallCount: 0,
    mediumCount: 0,
    largeCount: 0,
    hugeCount: 0
  }
})

// DOM 引用
const fileTypeChartRef = ref(null)
const fileSizeChartRef = ref(null)
const trendChartRef = ref(null)

// 图表实例
let fileTypeChart = null
let fileSizeChart = null
let trendChart = null
// Resize observers
const resizeObservers = []

const roleText = computed(() => {
  const roleMap = { STUDENT: '学生', TEACHER: '教师', ADMIN: '管理员' }
  return roleMap[userInfo.value.role] || '访客'
})

const userDisplayName = computed(() => userInfo.value.username || '管理员')

// 设计系统色板（与 global.css 保持一致）
const COLORS = {
  primary: '#3b82f6',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  purple: '#8b5cf6',
  pink: '#ec4899',
  cyan: '#06b6d4',
  lime: '#84cc16',
  neutral: '#64748b'
}

const CHART_COLORS = [COLORS.primary, COLORS.success, COLORS.warning, COLORS.danger, COLORS.purple, COLORS.pink, COLORS.cyan, COLORS.lime]

// 文件类型图表调色板 — 每项使用独立色，避免混淆
const FILE_TYPE_PALETTE = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#14b8a6',
  '#6366f1', '#d946ef', '#22c55e', '#eab308', '#a855f7',
  '#0ea5e9', '#65a30d', '#fb7185', '#2dd4bf', '#c026d3'
]

const SIZE_CATEGORIES = [
  { key: 'smallCount', label: '小文件 (< 1MB)', color: '#10b981' },
  { key: 'mediumCount', label: '中等文件 (1-10MB)', color: '#3b82f6' },
  { key: 'largeCount', label: '大文件 (10-100MB)', color: '#f59e0b' },
  { key: 'hugeCount', label: '超大文件 (> 100MB)', color: '#ef4444' }
]

// ========== ECharts 工具函数 ==========
const initChart = (el) => {
  if (!el) return null
  const chart = echarts.init(el, null, { renderer: 'canvas' })
  const observer = new ResizeObserver(() => { chart.resize() })
  observer.observe(el)
  resizeObservers.push(observer)
  return chart
}

const disposeChart = (chart, observerIndex) => {
  if (chart) chart.dispose()
  if (resizeObservers[observerIndex]) {
    resizeObservers[observerIndex].disconnect()
  }
}

const disposeAllCharts = () => {
  [fileTypeChart, fileSizeChart, trendChart].forEach(c => {
    if (c) { try { c.dispose() } catch (e) { /* ignore */ } }
  })
  resizeObservers.forEach(o => o.disconnect())
  resizeObservers.length = 0
  fileTypeChart = fileSizeChart = trendChart = null
}

// ========== 图表更新函数 ==========
const updateFileTypeChart = () => {
  if (!fileTypeChartRef.value) return
  if (!fileTypeChart) fileTypeChart = initChart(fileTypeChartRef.value)
  if (!fileTypeChart) return

  const data = statistics.fileTypeStats || []
  const total = data.reduce((s, d) => s + d.count, 0)

  fileTypeChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${p.name}<br/>数量: ${p.value}${total > 0 ? ` (${p.percent}%)` : ''}`
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      type: 'scroll',
      textStyle: { fontSize: 12 }
    },
    color: data.map((_, i) => FILE_TYPE_PALETTE[i % FILE_TYPE_PALETTE.length]),
    series: [{
      type: 'pie',
      radius: ['0%', '65%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: true,
      label: {
        show: data.length <= 6,
        formatter: '{d}%',
        fontSize: 12,
        color: '#475569'
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
      },
      data: data.map(d => ({
        name: d.fileType ? d.fileType.toUpperCase() : '未知',
        value: d.count
      }))
    }]
  })
}

const updateFileSizeChart = () => {
  if (!fileSizeChartRef.value) return
  if (!fileSizeChart) fileSizeChart = initChart(fileSizeChartRef.value)
  if (!fileSizeChart) return

  const dist = statistics.fileSizeDistribution || {}
  const total = SIZE_CATEGORIES.reduce((s, c) => s + (dist[c.key] || 0), 0)

  fileSizeChart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p) => `${p.name}<br/>数量: ${p.value}${total > 0 ? ` (${p.percent}%)` : ''}`
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { fontSize: 12 }
    },
    color: SIZE_CATEGORIES.map(c => c.color),
    series: [{
      type: 'pie',
      radius: ['45%', '70%'],
      center: ['38%', '50%'],
      avoidLabelOverlap: true,
      label: {
        show: total > 0,
        formatter: '{d}%',
        fontSize: 12,
        color: '#475569'
      },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.15)' }
      },
      data: SIZE_CATEGORIES.map(c => ({
        name: c.label,
        value: dist[c.key] || 0
      }))
    }]
  })
}

const updateTrendChart = () => {
  if (!trendChartRef.value) return
  if (!trendChart) trendChart = initChart(trendChartRef.value)
  if (!trendChart) return

  const data = statistics.dailyStats || []
  const dates = data.map(d => {
    const parts = d.date.split('-')
    return `${parts[1]}/${parts[2]}`
  })

  trendChart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.95)',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      textStyle: { color: '#1e293b', fontSize: 12 },
      formatter: (params) => {
        const dateStr = data[params[0].dataIndex]?.date || ''
        let html = `<div style="font-weight:600;margin-bottom:4px">${dateStr}</div>`
        params.forEach(p => {
          html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
            <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color}"></span>
            ${p.seriesName}: <strong>${p.value}</strong>
          </div>`
        })
        return html
      }
    },
    legend: {
      data: ['新增资源', '下载量', '浏览量'],
      bottom: 0,
      textStyle: { fontSize: 12 }
    },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: {
        color: '#64748b',
        fontSize: 11,
        interval: Math.max(0, Math.floor(data.length / 8) - 1)
      },
      axisTick: { show: false }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLabel: { color: '#64748b', fontSize: 11 }
    },
    color: [COLORS.primary, COLORS.success, COLORS.warning],
    series: [
      {
        name: '新增资源',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59,130,246,0.25)' },
              { offset: 1, color: 'rgba(59,130,246,0.02)' }
            ]
          }
        },
        data: data.map(d => d.resourceCount || 0)
      },
      {
        name: '下载量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(16,185,129,0.2)' },
              { offset: 1, color: 'rgba(16,185,129,0.02)' }
            ]
          }
        },
        data: data.map(d => d.downloadCount || 0)
      },
      {
        name: '浏览量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2.5 },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(245,158,11,0.18)' },
              { offset: 1, color: 'rgba(245,158,11,0.02)' }
            ]
          }
        },
        data: data.map(d => d.viewCount || 0)
      }
    ]
  })
}

const updateAllCharts = () => {
  nextTick(() => {
    updateFileTypeChart()
    updateFileSizeChart()
    updateTrendChart()
  })
}

// 初始化用户信息
const initUserInfo = () => {
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    if (userInfoStr) {
      const localUser = JSON.parse(userInfoStr)
      if (localUser && localUser.id) {
        userInfo.value = {
          id: localUser.id,
          username: localUser.username || '',
          role: localUser.role || 'STUDENT'
        }

        fetchStatistics()
      }
    } else {
      router.push('/')
    }
  } catch (e) {
    console.error('Error parsing user info:', e)
    router.push('/')
  }
}

// 获取统计信息
const fetchStatistics = async () => {
  loading.value = true
  try {
    const res = await request.get('/resource/statistics')
    if (res.data.code === 200) {
      Object.assign(statistics, res.data.data)
      updateAllCharts()
      ElMessage.success('数据已更新')
    } else {
      ElMessage.error(res.data.msg || '获取统计信息失败')
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
    ElMessage.error('获取统计信息失败，请检查网络连接')
  } finally {
    loading.value = false
  }
}

// ========== 格式化函数 ==========
const formatNumber = (num) => {
  if (!num) return '0'
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

const formatFileSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  const decimals = size < 10 ? 2 : size < 100 ? 1 : 0
  return size.toFixed(decimals) + ' ' + units[unitIndex]
}

const getTagType = (type) => {
  if (!type) return 'info'
  const t = type.toLowerCase()
  if (['pdf', 'docx', 'doc', 'txt'].includes(t)) return 'warning'
  if (['zip', 'rar', '7z'].includes(t)) return 'success'
  if (['jpg', 'png', 'gif', 'jpeg'].includes(t)) return 'primary'
  return 'info'
}

// ========== 导航 ==========
const goToHome = () => router.push('/home')

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  router.push('/')
}

const exportStatistics = () => {
  const dataStr = JSON.stringify(statistics, null, 2)
  const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr)
  const exportFileDefaultName = `resource-statistics-${new Date().toISOString().split('T')[0]}.json`
  const linkElement = document.createElement('a')
  linkElement.setAttribute('href', dataUri)
  linkElement.setAttribute('download', exportFileDefaultName)
  linkElement.click()
  ElMessage.success('统计数据已导出')
}

onMounted(() => {
  initUserInfo()
})

onUnmounted(() => {
  disposeAllCharts()
})
</script>

<style scoped>
.statistics-container {
  min-height: 100vh;
  animation: fadeIn var(--app-transition-normal) ease-out;
}

/* Header */
.header {
  position: sticky;
  top: 0;
  z-index: var(--app-z-sticky);
  backdrop-filter: blur(20px);
  background: var(--app-bg-overlay);
  border-bottom: 1px solid var(--app-border);
  box-shadow: var(--app-shadow-sm);
  transition: var(--app-transition-normal);
}

.header:hover {
  background: var(--app-bg-card);
  border-bottom-color: var(--app-border-hover);
}

.header-inner {
  height: 68px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 var(--app-spacing-5);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-3);
  cursor: pointer;
  transition: var(--app-transition-normal);
}

.brand:hover {
  transform: translateX(2px);
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: var(--app-radius-lg);
  background: linear-gradient(135deg,
    var(--app-color-primary-500) 0%,
    var(--app-color-primary-400) 55%,
    var(--app-color-success) 100%);
  box-shadow: 0 12px 28px rgba(59, 130, 246, 0.25);
  transition: var(--app-transition-normal);
}

.brand:hover .brand-mark {
  transform: rotate(5deg) scale(1.05);
  box-shadow: 0 16px 32px rgba(59, 130, 246, 0.35);
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: var(--app-line-height-tight);
}

.logo {
  font-size: var(--app-font-size-lg);
  font-weight: var(--app-font-weight-bold);
  letter-spacing: 0.3px;
  background: linear-gradient(135deg, var(--app-color-primary-600), var(--app-color-primary-800));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.tagline {
  margin-top: var(--app-spacing-1);
  font-size: var(--app-font-size-xs);
  color: var(--app-text-muted);
  font-weight: var(--app-font-weight-medium);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-3);
  padding: var(--app-spacing-2) var(--app-spacing-3);
  background: var(--app-color-neutral-50);
  border-radius: var(--app-radius-full);
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
}

.user-info:hover {
  background: var(--app-color-neutral-100);
  border-color: var(--app-border-hover);
  transform: translateY(-1px);
  box-shadow: var(--app-shadow-sm);
}

.username {
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text);
}

/* Main Content */
.main-content {
  padding: var(--app-spacing-6) var(--app-spacing-5) var(--app-spacing-8);
  max-width: 1280px;
  margin: 0 auto;
}

.content-card {
  border-radius: var(--app-radius-xl);
  background: var(--app-bg-card);
  backdrop-filter: blur(20px);
  box-shadow: var(--app-shadow-lg);
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
  overflow: hidden;
}

.content-card:hover {
  box-shadow: var(--app-shadow-xl);
  border-color: var(--app-border-hover);
}

:deep(.el-card__body) {
  padding: var(--app-spacing-5) !important;
}

/* Section Styles */
.section-title {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-2);
  font-weight: var(--app-font-weight-bold);
  font-size: var(--app-font-size-lg);
  color: var(--app-text);
  margin-bottom: var(--app-spacing-4);
}

.section-title .el-icon {
  color: var(--app-color-primary-600);
}

.overview-section {
  margin-bottom: var(--app-spacing-6);
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--app-spacing-4);
  margin-top: var(--app-spacing-4);
}

.overview-card {
  border-radius: var(--app-radius-lg);
  transition: var(--app-transition-normal);
}

.overview-card:hover {
  transform: translateY(-4px);
}

.card-content {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-4);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--app-radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
}

.card-info {
  flex: 1;
}

.card-value {
  font-size: var(--app-font-size-2xl);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text);
  line-height: 1.2;
}

.card-label {
  font-size: var(--app-font-size-sm);
  color: var(--app-text-muted);
  margin-top: var(--app-spacing-1);
}

/* Chart Layout */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--app-spacing-5);
  margin-bottom: var(--app-spacing-6);
}

.chart-section {
  background: var(--app-color-neutral-50);
  border-radius: var(--app-radius-lg);
  padding: var(--app-spacing-4);
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
}

.chart-section:hover {
  border-color: var(--app-border-hover);
  box-shadow: var(--app-shadow-sm);
}

.chart-full {
  margin-bottom: var(--app-spacing-6);
}

.chart-container {
  width: 100%;
  height: 320px;
}

.chart-tall {
  height: 380px;
}

/* Data Table */
.data-table {
  border-radius: var(--app-radius-lg);
  overflow: hidden;
  border: 1px solid var(--app-border);
}

.data-table :deep(.el-table__header-wrapper th) {
  background-color: var(--app-color-neutral-50) !important;
  font-weight: var(--app-font-weight-semibold) !important;
  color: var(--app-text) !important;
}

.data-table :deep(.el-table__row) {
  transition: var(--app-transition-fast);
}

.data-table :deep(.el-table__row:hover) {
  background-color: var(--app-color-neutral-50) !important;
}

/* Action Section */
.action-section {
  display: flex;
  justify-content: center;
  gap: var(--app-spacing-4);
  margin-top: var(--app-spacing-6);
  padding-top: var(--app-spacing-6);
  border-top: 1px solid var(--app-border);
}

/* Responsive */
@media (max-width: 900px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .header-inner {
    height: 60px;
    padding: 0 var(--app-spacing-3);
  }

  .brand-mark {
    width: 32px;
    height: 32px;
  }

  .logo {
    font-size: var(--app-font-size-base);
  }

  .tagline {
    font-size: 0.7rem;
  }

  .user-info {
    padding: var(--app-spacing-1) var(--app-spacing-2);
    gap: var(--app-spacing-2);
  }

  .username {
    display: none;
  }

  .main-content {
    padding: var(--app-spacing-4) var(--app-spacing-3) var(--app-spacing-6);
  }

  .overview-cards {
    grid-template-columns: 1fr;
  }

  .action-section {
    flex-direction: column;
  }

  .chart-container {
    height: 280px;
  }

  .chart-tall {
    height: 300px;
  }
}

@media (max-width: 480px) {
  .brand-text {
    display: none;
  }

  .user-info .el-tag {
    display: none;
  }
}

/* Animation */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
