<template>
  <div class="home-container">
    <header class="header">
      <div class="header-inner">
        <div class="brand">
          <div class="brand-mark" aria-hidden="true"></div>
          <div class="brand-text">
            <div class="logo">高校资源共享平台</div>
            <div class="tagline">资源检索 · 上传 · 下载</div>
          </div>
        </div>

        <div class="user-info">
          <el-avatar :size="34" icon="UserFilled" />
          <span class="username">{{ userDisplayName }}</span>
          <el-tag size="small" effect="light">{{ roleText }}</el-tag>
          <el-button link @click="handleLogout">退出</el-button>
        </div>
      </div>
    </header>

    <div class="main-content">
      <el-card class="content-card" shadow="never">
        <!-- 推荐区域 -->
        <div class="recommendation-section" v-if="showRecommendations">
          <div class="recommendation-header">
            <div class="recommendation-title">
              <el-icon><Star /></el-icon>
              <span>为你推荐</span>
            </div>
            <div class="recommendation-toolbar">
              <div class="algorithm-row">
                <span class="algorithm-label">推荐算法</span>
                <el-select
                  v-model="recommendationAlgorithm"
                  class="algorithm-select"
                  size="small"
                  :disabled="recommendationLoading"
                  @change="onRecommendationAlgorithmChange"
                >
                  <el-option label="Item-CF（基于物品）" value="item_cf" />
                  <el-option label="User-CF（基于用户）" value="user_cf" />
                  <el-option label="SVD（矩阵分解）" value="svd" />
                </el-select>
              </div>
              <div class="recommendation-actions">
                <el-button link @click="toggleRecommendations">
                  <el-icon><Close /></el-icon>
                  隐藏
                </el-button>
              </div>
            </div>
          </div>
          <div class="recommendation-list" v-if="recommendationList.length > 0">
            <div class="recommendation-item" v-for="item in visibleRecommendations" :key="item.resourceId">
              <div class="recommendation-item-content" @click="handleRecommendationClick(item)">
                <div class="recommendation-item-title">{{ item.title }}</div>
                <div class="recommendation-item-meta">
                  <el-tag size="small" :type="getTagType(item.fileType)">
                    {{ item.fileType ? item.fileType.toUpperCase() : '未知' }}
                  </el-tag>
                  <span class="recommendation-item-size">{{ item.fileSize ? formatFileSize(item.fileSize) : '大小未知' }}</span>
                  <span class="recommendation-item-reason" v-if="item.recommendationReason">{{ item.recommendationReason }}</span>
                </div>
              </div>
              <el-button link type="primary" @click="handleDownload(item)">下载</el-button>
            </div>
            <div class="recommendation-more" v-if="hasMoreRecommendations">
              <el-button link @click="toggleShowAllRecommendations">
                <el-icon><ArrowDown v-if="!showAllRecommendations" /><ArrowUp v-else /></el-icon>
                {{ showAllRecommendations ? '收起' : '展示更多' }}
              </el-button>
            </div>
          </div>
          <div v-else class="recommendation-empty">
            <el-empty description="暂时没有可推荐资源" :image-size="80" />
            <el-button type="primary" plain @click="refreshRecommendations" :loading="recommendationLoading">
              重新获取推荐
            </el-button>
          </div>
        </div>

        <div class="action-bar">
          <div class="left-tools">
            <el-input
                v-model="searchQuery"
                placeholder="输入关键字搜索..."
                class="search-input"
                prefix-icon="Search"
                clearable
                @input="handleSearch"
            />
            <el-checkbox
                v-model="showOnlyMine"
                label="只看我的上传"
                border
                class="filter-checkbox"
                @change="handleSearch"
            />
            <el-select
                v-model="sortOption"
                class="sort-select"
                size="default"
                placeholder="排序方式"
                @change="handleSearch"
                style="width: 180px"
            >
                <el-option label="按创建时间（最新）" value="create_time_desc" />
                <el-option label="按创建时间（最早）" value="create_time_asc" />
                <el-option label="按文件大小（最大）" value="file_size_desc" />
                <el-option label="按文件大小（最小）" value="file_size_asc" />
            </el-select>
            <el-button v-if="!showRecommendations" link @click="toggleRecommendations" class="show-recommendations-btn">
              <el-icon><Star /></el-icon>
              显示推荐
            </el-button>
          </div>
          <div class="right-tools">
            <el-button v-if="isAdmin" type="warning" icon="User" @click="goToUserManagement">用户管理</el-button>
            <el-button type="info" icon="DataAnalysis" @click="goToStatistics">资源统计</el-button>
            <el-button v-if="canUpload" type="primary" icon="Plus" @click="openUploadDialog">上传资源</el-button>
          </div>
        </div>

        <el-tabs v-model="activeCategory" @tab-click="handleTabClick" class="category-tabs">
          <el-tab-pane label="全部资源" name="all"></el-tab-pane>
          <el-tab-pane label="文档" name="pdf,docx,doc,txt"></el-tab-pane>
          <el-tab-pane label="图片" name="jpg,png,gif,jpeg"></el-tab-pane>
          <el-tab-pane label="压缩包" name="zip,rar,7z"></el-tab-pane>
          <el-tab-pane label="其他" name="other"></el-tab-pane>
        </el-tabs>

        <el-table :data="resourceList" row-key="id" class="res-table" stripe v-loading="loading" @row-click="handleRowClick">
          <template #empty>
            <el-empty description="没有找到相关资源" />
          </template>

          <el-table-column prop="title" label="资源名称" min-width="250" show-overflow-tooltip />
          <el-table-column prop="fileType" label="类型" width="110">
            <template #default="scope">
              <el-tag size="small" effect="dark" :type="getTagType(scope.row.fileType)">
                {{ scope.row.fileType ? scope.row.fileType.toUpperCase() : '未知' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fileSize" label="大小" width="130">
            <template #default="scope">
              {{ formatFileSize(scope.row.fileSize) }}
            </template>
          </el-table-column>
          <el-table-column label="上传时间" width="180">
            <template #default="scope">
              <div class="time-display">
                <div class="time-date">{{ formatDateTime(scope.row.createTime).date }}</div>
                <div class="time-time">{{ formatDateTime(scope.row.createTime).time }}</div>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="190" fixed="right">
            <template #default="scope">
              <el-button link type="primary" @click.stop="handleDownload(scope.row)">下载</el-button>
              <el-button v-if="canDelete(scope.row)" link type="danger" @click.stop="handleDelete(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="table-pagination">
          <el-pagination
            :current-page="pagination.current"
            :page-size="pagination.size"
            :page-sizes="[10, 15, 20, 50]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @current-change="onCurrentPageChange"
            @size-change="onPageSizeChange"
          />
        </div>
      </el-card>
    </div>

    <el-dialog v-model="uploadDialogVisible" title="上传新资源" width="450px" @close="resetUploadForm">
      <el-form label-position="top">
        <el-form-item label="自定义资源标题 (可选)">
          <el-input v-model="uploadForm.title" placeholder="不填则使用原始文件名" />
        </el-form-item>
        <el-form-item v-if="canUpload" label="可见范围">
          <el-radio-group v-model="uploadForm.visibility">
            <el-radio value="PUBLIC">公开</el-radio>
            <el-radio value="PRIVATE">仅自己可见</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload
              class="upload-area"
              drag
              action="#"
              :auto-upload="false"
              :on-change="onFileChange"
              :limit="1"
              :on-exceed="handleExceed"
              ref="uploadRef"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitUpload" :loading="uploading">确认上传</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="resourceDetailVisible" title="资源详情" width="600px">
      <div v-if="currentResource" class="resource-detail">
        <div class="detail-section">
          <h3>{{ currentResource.title }}</h3>
          <div class="detail-info">
            <div class="info-row">
              <span class="label">文件类型：</span>
              <el-tag size="small" :type="getTagType(currentResource.fileType)">
                {{ currentResource.fileType ? currentResource.fileType.toUpperCase() : '未知' }}
              </el-tag>
            </div>
            <div class="info-row">
              <span class="label">文件大小：</span>
              <span>{{ formatFileSize(currentResource.fileSize) }}</span>
            </div>
            <div class="info-row">
              <span class="label">上传时间：</span>
              <span class="time-stack">
                <span>{{ formatDateTime(currentResource.createTime).date }}</span>
                <span class="time-sep">{{ formatDateTime(currentResource.createTime).time }}</span>
              </span>
            </div>
            <div class="info-row">
              <span class="label">上传者ID：</span>
              <span>{{ currentResource.uploaderId }}</span>
            </div>
          </div>
          <div class="detail-actions">
            <el-button type="primary" @click="handleDownload(currentResource)">下载文件</el-button>
            <el-button v-if="canDelete(currentResource)" type="danger" @click="handleDelete(currentResource)">删除资源</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, UserFilled, UploadFilled, Star, Refresh, Close, ArrowDown, ArrowUp, DataAnalysis, PieChart } from '@element-plus/icons-vue'
import request from '../utils/request'
import axios from 'axios'

// --- 状态定义 ---
const loading = ref(false)
const uploading = ref(false)
const uploadDialogVisible = ref(false)
const resourceDetailVisible = ref(false)
const resourceList = ref([])
const currentResource = ref(null)
const pagination = reactive({
  current: 1,
  size: 15,
  total: 0
})
const searchQuery = ref('')
const showOnlyMine = ref(false)
const activeCategory = ref('all')
const sortOption = ref('create_time_desc') // 默认按创建时间降序

const selectedFile = ref(null)
const uploadForm = ref({ title: '', visibility: 'PUBLIC' })
const uploadRef = ref(null)
const userInfo = ref({ id: null, username: '', role: 'STUDENT' })
const router = useRouter()

const REC_ALGO_STORAGE_KEY = 'recommendationAlgorithm'

// 推荐相关状态
const showRecommendations = ref(true)
const recommendationList = ref([])
const recommendationLoading = ref(false)
const recommendationAlgorithm = ref(
  typeof localStorage !== 'undefined'
    ? (localStorage.getItem(REC_ALGO_STORAGE_KEY) || 'item_cf')
    : 'item_cf'
)

// 推荐显示控制
const showAllRecommendations = ref(false)
const visibleRecommendations = computed(() => {
  if (showAllRecommendations.value) {
    return recommendationList.value
  }
  return recommendationList.value.slice(0, 3)
})
const hasMoreRecommendations = computed(() => recommendationList.value.length > 3)

const roleText = computed(() => {
  const roleMap = {
    STUDENT: '学生',
    TEACHER: '教师',
    ADMIN: '管理员'
  }
  return roleMap[userInfo.value.role] || '访客'
})

const userDisplayName = computed(() => userInfo.value.username || '我的空间')
const isAdmin = computed(() => userInfo.value.role === 'ADMIN')
const canUpload = computed(() => ['TEACHER', 'ADMIN'].includes(userInfo.value.role))
const canDelete = (row) => {
  if (userInfo.value.role === 'ADMIN') return true
  if (userInfo.value.role === 'TEACHER') return row.uploaderId === userInfo.value.id
  return false
}

// --- 核心方法 ---

/**
 * 修复 Bug：Tab 点击处理
 * 使用 nextTick 确保 activeCategory 的值在请求发出前已经完成同步
 */
const handleTabClick = async () => {
  await nextTick()
  pagination.current = 1
  fetchResourceList()
}

const fetchResourceList = async () => {
  console.log('fetchResourceList called with params:', {
    query: searchQuery.value,
    onlyMine: showOnlyMine.value,
    type: activeCategory.value === 'all' ? null : activeCategory.value,
    sort: sortOption.value,
    current: pagination.current,
    size: pagination.size
  })
  loading.value = true
  try {
    const res = await request.get('/resource/list', {
      params: {
        query: searchQuery.value,
        onlyMine: showOnlyMine.value,
        type: activeCategory.value === 'all' ? null : activeCategory.value,
        sort: sortOption.value,
        current: pagination.current,
        size: pagination.size
      }
    })
    if (res.data.code === 200) {
      const d = res.data.data
      resourceList.value = d.records || []
      pagination.total = Number(d.total) || 0
      pagination.current = Number(d.current) || pagination.current
      pagination.size = Number(d.size) || pagination.size
    } else {
      ElMessage.error(res.data.msg || '获取列表失败')
    }
  } catch (error) {
    ElMessage.error('获取列表失败')
  } finally {
    loading.value = false
  }
}

/** 筛选条件变化时从第一页重新加载 */
const handleSearch = () => {
  console.log('handleSearch called, sortOption:', sortOption.value)
  pagination.current = 1
  fetchResourceList()
}

const onCurrentPageChange = (page) => {
  pagination.current = page
  fetchResourceList()
}

const onPageSizeChange = (size) => {
  pagination.size = size
  pagination.current = 1
  fetchResourceList()
}

onMounted(() => {
  initUserInfo()
  fetchResourceList()
})

const initUserInfo = async () => {
  console.log('initUserInfo called')
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    console.log('LocalStorage userInfo:', userInfoStr)
    const localUser = JSON.parse(userInfoStr || '{}')
    console.log('Parsed localUser:', localUser)

    if (localUser && localUser.id) {
      console.log('Using cached user info, id:', localUser.id)
      userInfo.value = {
        id: localUser.id,
        username: localUser.username || '',
        role: localUser.role || 'STUDENT'
      }
      // 获取推荐
      fetchRecommendations()
      return
    } else {
      console.log('No cached user info found')
    }
  } catch (e) {
    console.error('Error parsing localStorage userInfo:', e)
    // ignore parse error and fallback to /auth/me
  }

  try {
    console.log('Fetching user info from /auth/me')
    const res = await request.get('/auth/me')
    console.log('/auth/me response:', res.data)
    if (res.data.code === 200) {
      userInfo.value = res.data.data
      localStorage.setItem('userInfo', JSON.stringify(res.data.data))
      console.log('User info saved to localStorage')
      // 获取推荐
      fetchRecommendations()
    } else {
      console.error('/auth/me returned error:', res.data.msg)
    }
  } catch (e) {
    console.error('/auth/me request failed:', e)
    // 401 交给拦截器处理
  }
}

// --- 推荐相关逻辑 ---
const fetchRecommendations = async () => {
  console.log('fetchRecommendations called, userInfo:', userInfo.value)
  if (!userInfo.value.id) {
    console.log('No user ID, skipping recommendations')
    return
  }

  recommendationLoading.value = true
  try {
    console.log('Fetching recommendations for user:', userInfo.value.id)
    const res = await request.get('/recommendation/personalized', {
      params: {
        limit: 5,
        algorithm: recommendationAlgorithm.value
      }
    })
    console.log('Recommendations API response:', res.data)
    if (res.data.code === 200) {
      recommendationList.value = res.data.data || []
      console.log('Recommendations set:', recommendationList.value)
      // 重置显示状态，默认只显示3个
      showAllRecommendations.value = false
    } else {
      console.error('Recommendations API error:', res.data.msg)
      ElMessage.error(res.data.msg || '获取推荐失败')
    }
  } catch (error) {
    console.error('获取推荐失败:', error)
    console.error('Error details:', error.response || error.message)
    // 静默失败，不显示错误信息
  } finally {
    recommendationLoading.value = false
  }
}

const refreshRecommendations = () => {
  fetchRecommendations()
}

const onRecommendationAlgorithmChange = () => {
  try {
    localStorage.setItem(REC_ALGO_STORAGE_KEY, recommendationAlgorithm.value)
  } catch (_) {
    /* ignore */
  }
  if (userInfo.value.id) {
    fetchRecommendations()
  }
}

const toggleRecommendations = () => {
  showRecommendations.value = !showRecommendations.value
  if (showRecommendations.value && recommendationList.value.length === 0) {
    fetchRecommendations()
  }
}

const toggleShowAllRecommendations = () => {
  showAllRecommendations.value = !showAllRecommendations.value
}

const handleRecommendationClick = (item) => {
  // 可以跳转到资源详情页，这里先简单处理
  console.log('点击推荐资源:', item)
  // 记录浏览行为
  recordView(item.resourceId || item.id)
  // 可以在这里触发下载或查看详情
}

const handleRowClick = (row) => {
  // 记录资源浏览行为
  recordView(row.id)
  // 显示资源详情对话框
  currentResource.value = row
  resourceDetailVisible.value = true
}

const recordView = async (resourceId) => {
  try {
    await request.get(`/resource/view/${resourceId}`)
    console.log('记录浏览行为成功:', resourceId)
  } catch (error) {
    console.error('记录浏览行为失败:', error)
    // 静默失败，不影响用户体验
  }
}

// --- 上传相关逻辑 ---
const openUploadDialog = () => { uploadDialogVisible.value = true }
const goToUserManagement = () => {
  router.push('/users')
}

const onFileChange = (file) => { selectedFile.value = file.raw }

const handleExceed = (files) => {
  uploadRef.value.clearFiles()
  const file = files[0]
  uploadRef.value.handleStart(file)
}

const submitUpload = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择一个文件')
    return
  }
  uploading.value = true
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('title', uploadForm.value.title)
  formData.append('visibility', uploadForm.value.visibility || 'PUBLIC')

  try {
    const res = await request.post('/resource/upload', formData)
    if (res.data.code === 200) {
      ElMessage.success('上传成功！')
      uploadDialogVisible.value = false
      handleSearch()
    } else {
      ElMessage.error(res.data.msg || '上传失败')
    }
  } catch (error) {
    ElMessage.error('网络错误，上传失败')
  } finally {
    uploading.value = false
  }
}

const resetUploadForm = () => {
  uploadForm.value.title = ''
  uploadForm.value.visibility = 'PUBLIC'
  selectedFile.value = null
  if (uploadRef.value) uploadRef.value.clearFiles()
}

// --- 下载与删除 ---
const handleDownload = async (row) => {
  try {
    // 支持两种格式：常规资源有id字段，推荐资源有resourceId字段
    const resourceId = row.id || row.resourceId
    console.log('开始下载资源:', resourceId, row.title)

    // 获取token
    const token = localStorage.getItem('token')
    console.log('Token exists:', !!token)

    // 使用独立的axios实例下载文件，避免拦截器干扰
    const response = await axios.get(`http://localhost:8080/api/resource/download/${resourceId}`, {
      responseType: 'blob', // 重要：指定响应类型为blob
      headers: token ? { 'Authorization': token } : {},
      timeout: 30000 // 30秒超时
    })

    console.log('响应状态:', response.status, response.statusText)
    console.log('响应头:', response.headers)
    console.log('响应数据类型:', typeof response.data, response.data.constructor.name)
    console.log('响应数据大小:', response.data.size)

    // 检查响应状态 - 接受200和206（部分内容）
    if (response.status !== 200 && response.status !== 206) {
      throw new Error(`下载失败，状态码: ${response.status}`)
    }

    // 从响应头获取文件名，如果不存在则使用资源标题
    let filename = row.title
    const contentDisposition = response.headers['content-disposition']
    console.log('Content-Disposition header:', contentDisposition)

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch) {
        // 解码URL编码的文件名
        filename = decodeURIComponent(filenameMatch[1])
        console.log('从filename*获取文件名:', filename)
      } else {
        const filenameMatch2 = contentDisposition.match(/filename="(.+)"/)
        if (filenameMatch2) {
          filename = filenameMatch2[1]
          console.log('从filename获取文件名:', filename)
        }
      }
    }

    // 确保文件名有扩展名
    if (!filename.includes('.') && row.fileType) {
      filename = `${filename}.${row.fileType}`
      console.log('添加文件扩展名:', filename)
    }

    // 直接使用响应数据作为blob（已经是blob类型）
    const blob = response.data
    const url = window.URL.createObjectURL(blob)
    console.log('创建的URL:', url)

    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    link.style.display = 'none'
    document.body.appendChild(link)

    console.log('开始触发下载...')
    link.click()

    // 延迟清理，确保下载开始
    setTimeout(() => {
      window.URL.revokeObjectURL(url)
      document.body.removeChild(link)
      console.log('清理完成')
    }, 1000)

    console.log('下载流程完成')

  } catch (error) {
    console.error('下载失败详情:', error)
    console.error('错误堆栈:', error.stack)

    if (error.response) {
      console.error('错误响应:', error.response)

      // 尝试读取blob错误消息
      if (error.response.data && error.response.data instanceof Blob) {
        try {
          const errorText = await error.response.data.text()
          console.error('后端错误消息:', errorText)
          ElMessage.error(`下载失败: ${errorText}`)
        } catch (e) {
          console.error('读取错误消息失败:', e)
          if (error.response.status === 401) {
            ElMessage.error('登录已过期，请重新登录')
          } else if (error.response.status === 403) {
            ElMessage.error('无权限访问该文件')
          } else if (error.response.status === 404) {
            ElMessage.error('文件不存在')
          } else if (error.response.status === 500) {
            ElMessage.error('服务器内部错误，请稍后重试')
          } else {
            ElMessage.error(`下载失败，状态码: ${error.response.status}`)
          }
        }
      } else if (error.response.status === 401) {
        ElMessage.error('登录已过期，请重新登录')
      } else if (error.response.status === 403) {
        ElMessage.error('无权限访问该文件')
      } else if (error.response.status === 404) {
        ElMessage.error('文件不存在')
      } else if (error.response.status === 500) {
        ElMessage.error('服务器内部错误，请稍后重试')
      } else {
        ElMessage.error(`下载失败，状态码: ${error.response.status}`)
      }
    } else if (error.request) {
      console.error('没有收到响应:', error.request)
      ElMessage.error('网络错误，请检查网络连接或后端服务')
    } else {
      console.error('其他错误:', error.message)
      ElMessage.error('下载失败: ' + error.message)
    }
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
      `确定要永久删除资源【${row.title}】吗？`,
      '安全警告',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'error' }
  ).then(async () => {
    try {
      const res = await request.delete(`/resource/delete/${row.id}`)
      if (res.data.code === 200) {
        ElMessage.success('已删除')
        if (resourceList.value.length === 1 && pagination.current > 1) {
          pagination.current -= 1
        }
        fetchResourceList()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

const getTagType = (type) => {
  if (!type) return 'info'
  const t = type.toLowerCase()
  if (['pdf', 'docx', 'doc', 'txt'].includes(t)) return 'warning'
  if (['zip', 'rar', '7z'].includes(t)) return 'success'
  if (['jpg', 'png', 'gif', 'jpeg'].includes(t)) return 'primary'
  return 'info'
}

/**
 * 格式化文件大小，自动选择合适的单位
 * @param {number} bytes 文件大小（字节）
 * @returns {string} 格式化后的文件大小字符串
 */
const formatDateTime = (isoStr) => {
  if (!isoStr) return { date: '-', time: '-' }
  const [date, time] = isoStr.split('T')
  return { date, time: time ? time.split('.')[0] : '-' }
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

  // 对于小于10的单位，显示2位小数；对于10-100，显示1位小数；大于100显示整数
  let decimals = 0
  if (size < 10) {
    decimals = 2
  } else if (size < 100) {
    decimals = 1
  }

  return size.toFixed(decimals) + ' ' + units[unitIndex]
}

const goToStatistics = () => {
  router.push('/statistics')
}

const handleLogout = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  window.location.href = '/'
}
</script>

<style scoped>
/* ==================== Layout & Structure ==================== */
.home-container {
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

/* Brand */
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
  color: var(--app-text);
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

/* User Info */
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

/* ==================== Recommendation Section ==================== */
.recommendation-section {
  background: linear-gradient(135deg,
    rgba(248, 250, 252, 0.95) 0%,
    rgba(241, 245, 249, 0.95) 100%);
  border-radius: var(--app-radius-lg);
  padding: var(--app-spacing-4);
  margin-bottom: var(--app-spacing-5);
  border: 1px solid var(--app-border);
  animation: slideInRight var(--app-transition-normal) ease-out;
}

.recommendation-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--app-spacing-3);
  flex-wrap: wrap;
  margin-bottom: var(--app-spacing-4);
}

.recommendation-title {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-2);
  font-weight: var(--app-font-weight-bold);
  font-size: var(--app-font-size-lg);
  color: var(--app-text);
}

.recommendation-title .el-icon {
  color: var(--app-color-warning);
  animation: pulse 2s var(--app-transition-bounce) infinite;
}

.recommendation-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-spacing-3) var(--app-spacing-4);
}

.algorithm-row {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-2);
}

.algorithm-label {
  font-size: var(--app-font-size-sm);
  color: var(--app-text-muted);
  white-space: nowrap;
  font-weight: var(--app-font-weight-medium);
}

.algorithm-select {
  width: 200px;
}

.recommendation-actions {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-2);
}

/* Recommendation List */
.recommendation-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-spacing-3);
}

.recommendation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--app-spacing-3);
  background: var(--app-bg-overlay);
  border-radius: var(--app-radius-md);
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
  cursor: pointer;
}

.recommendation-item:hover {
  border-color: var(--app-color-primary-400);
  background: var(--app-color-primary-50);
  transform: translateX(4px);
  box-shadow: var(--app-shadow-md);
}

.recommendation-item-content {
  flex: 1;
}

.recommendation-item-title {
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text);
  margin-bottom: var(--app-spacing-2);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: var(--app-line-height-tight);
}

.recommendation-item-meta {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-3);
  font-size: var(--app-font-size-xs);
  color: var(--app-text-light);
}

.recommendation-item-size {
  font-family: var(--app-font-mono);
  background: var(--app-color-neutral-100);
  padding: 1px var(--app-spacing-1);
  border-radius: var(--app-radius-sm);
}

.recommendation-item-reason {
  background: rgba(59, 130, 246, 0.1);
  color: var(--app-color-primary-600);
  padding: var(--app-spacing-1) var(--app-spacing-2);
  border-radius: var(--app-radius-sm);
  font-size: var(--app-font-size-xs);
  font-weight: var(--app-font-weight-medium);
}

.recommendation-empty {
  padding: var(--app-spacing-4) 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--app-spacing-3);
}

.recommendation-more {
  display: flex;
  justify-content: center;
  padding-top: var(--app-spacing-3);
  border-top: 1px dashed var(--app-border);
  margin-top: var(--app-spacing-3);
}

.show-recommendations-btn {
  color: var(--app-color-warning) !important;
  font-weight: var(--app-font-weight-semibold) !important;
}

.show-recommendations-btn .el-icon {
  margin-right: var(--app-spacing-1);
}

/* ==================== Action Bar ==================== */
.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--app-spacing-3);
  margin-bottom: var(--app-spacing-4);
  flex-wrap: wrap;
}

.right-tools {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-3);
}

.left-tools {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-4);
  flex-wrap: wrap;
}

.search-input {
  width: min(480px, 72vw);
}

.search-input :deep(.el-input__wrapper) {
  border-radius: var(--app-radius-full) !important;
  padding-left: var(--app-spacing-4) !important;
}

.filter-checkbox {
  background-color: var(--app-bg-overlay);
}

/* ==================== Tabs ==================== */
.category-tabs {
  margin-bottom: var(--app-spacing-5);
}

:deep(.el-tabs__item) {
  font-size: var(--app-font-size-sm);
  font-weight: var(--app-font-weight-semibold) !important;
  padding: 0 var(--app-spacing-3) !important;
  height: 40px !important;
}

:deep(.el-tabs__item:hover) {
  color: var(--app-color-primary-600) !important;
}

:deep(.el-tabs__item.is-active) {
  color: var(--app-color-primary-600) !important;
}

:deep(.el-tabs__active-bar) {
  background-color: var(--app-color-primary-600) !important;
  height: 3px !important;
  border-radius: var(--app-radius-full) !important;
}

/* ==================== Table ==================== */
.res-table {
  border-radius: var(--app-radius-lg);
  overflow: hidden;
  border: 1px solid var(--app-border);
}

.res-table :deep(.el-table__header-wrapper th) {
  background-color: var(--app-color-neutral-50) !important;
  font-weight: var(--app-font-weight-semibold) !important;
  color: var(--app-text) !important;
}

.res-table :deep(.el-table__row) {
  transition: var(--app-transition-fast);
}

.res-table :deep(.el-table__row:hover) {
  background-color: var(--app-color-neutral-50) !important;
  transform: translateY(-1px);
  box-shadow: var(--app-shadow-sm);
}

.res-table :deep(.el-table__cell) {
  padding: var(--app-spacing-3) var(--app-spacing-4) !important;
}

/* Time display */
.time-display {
  line-height: 1.4;
}
.time-date {
  font-size: var(--app-font-size-sm);
  color: var(--app-text);
}
.time-time {
  font-size: var(--app-font-size-xs);
  color: var(--app-text-muted);
  font-family: var(--app-font-mono);
}
.time-stack {
  display: inline-flex;
  flex-direction: column;
  line-height: 1.4;
}
.time-sep {
  font-size: var(--app-font-size-xs);
  color: var(--app-text-muted);
  font-family: var(--app-font-mono);
}

/* ==================== Pagination ==================== */
.table-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--app-spacing-5);
  flex-wrap: wrap;
  gap: var(--app-spacing-2);
}

/* ==================== Dialogs ==================== */
.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  border-radius: var(--app-radius-lg) !important;
  border: 2px dashed var(--app-border) !important;
  padding: var(--app-spacing-6) var(--app-spacing-4) !important;
  transition: var(--app-transition-normal) !important;
}

.upload-area :deep(.el-upload-dragger:hover) {
  border-color: var(--app-color-primary-400) !important;
  background-color: var(--app-color-primary-50) !important;
  transform: translateY(-2px);
  box-shadow: var(--app-shadow-md) !important;
}

/* Resource Detail */
.resource-detail {
  padding: var(--app-spacing-1);
}

.detail-section h3 {
  margin-top: 0;
  margin-bottom: var(--app-spacing-4);
  font-size: var(--app-font-size-xl);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text);
}

.detail-info {
  display: flex;
  flex-direction: column;
  gap: var(--app-spacing-3);
  margin-bottom: var(--app-spacing-5);
}

.info-row {
  display: flex;
  align-items: center;
  gap: var(--app-spacing-3);
}

.info-row .label {
  font-weight: var(--app-font-weight-medium);
  color: var(--app-text-muted);
  min-width: 80px;
}

.detail-actions {
  display: flex;
  gap: var(--app-spacing-3);
  margin-top: var(--app-spacing-5);
}

/* ==================== Responsive Design ==================== */
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

  .action-bar {
    flex-direction: column;
    align-items: stretch;
    gap: var(--app-spacing-3);
  }

  .left-tools, .right-tools {
    width: 100%;
    justify-content: center;
  }

  .search-input {
    width: 100%;
  }

  .recommendation-header {
    flex-direction: column;
    align-items: stretch;
    gap: var(--app-spacing-3);
  }

  .recommendation-toolbar {
    justify-content: space-between;
  }

  .algorithm-row {
    width: 100%;
    justify-content: space-between;
  }

  .algorithm-select {
    flex: 1;
  }

  .detail-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .brand-text {
    display: none;
  }

  .user-info .el-tag {
    display: none;
  }

  .category-tabs :deep(.el-tabs__item) {
    padding: 0 var(--app-spacing-2) !important;
    font-size: var(--app-font-size-xs) !important;
  }

  .table-pagination {
    justify-content: center;
  }
}

/* ==================== Animation Keyframes ==================== */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(24px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}
</style>