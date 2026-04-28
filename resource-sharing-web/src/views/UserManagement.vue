<template>
  <div class="user-mgr-container">
    <header class="mgr-header">
      <div class="mgr-header-inner">
        <div class="mgr-header-left">
          <el-button class="back-btn" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回首页
          </el-button>
          <div class="mgr-title">
            <el-icon size="24"><User /></el-icon>
            <span>用户管理</span>
          </div>
        </div>
        <div class="mgr-header-right">
          <el-tag effect="dark" type="warning">管理员</el-tag>
        </div>
      </div>
    </header>

    <div class="mgr-content">
      <el-card class="mgr-card" shadow="never">
        <!-- 角色筛选 -->
        <div class="role-filter-bar">
          <span class="filter-label">角色筛选</span>
          <div class="role-tabs">
            <div
              v-for="tab in roleTabs"
              :key="tab.value"
              class="role-tab"
              :class="{ active: activeRole === tab.value }"
              @click="switchRole(tab.value)"
            >
              <el-icon v-if="tab.icon"><component :is="tab.icon" /></el-icon>
              <span>{{ tab.label }}</span>
            </div>
          </div>
        </div>

        <!-- 用户表格 -->
        <el-table
          :data="userList"
          row-key="id"
          stripe
          v-loading="userLoading"
          class="user-table"
        >
          <template #empty>
            <el-empty description="没有找到相关用户" />
          </template>

          <el-table-column prop="username" label="用户名" min-width="120" />
          <el-table-column prop="nickname" label="昵称" min-width="120">
            <template #default="scope">
              {{ scope.row.nickname || '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
          <el-table-column prop="role" label="角色" width="130">
            <template #default="scope">
              <el-tag
                :type="roleTagType(scope.row.role)"
                effect="dark"
                size="small"
              >
                <el-icon style="margin-right: 4px; vertical-align: middle;">
                  <component :is="roleIcon(scope.row.role)" />
                </el-icon>
                {{ roleLabel(scope.row.role) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope">
              <el-tag :type="scope.row.status === 1 ? 'success' : 'info'" size="small">
                {{ scope.row.status === 1 ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="注册时间" width="180">
            <template #default="scope">
              {{ formatDate(scope.row.createTime) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="scope">
              <el-button
                link
                type="danger"
                size="small"
                :disabled="scope.row.id === userInfo.id"
                @click="handleDeleteUser(scope.row)"
              >
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="mgr-footer">
          <div class="mgr-stats">
            <span>共 <strong>{{ total }}</strong> 个用户</span>
          </div>
          <el-pagination
            :current-page="currentPage"
            :page-size="pageSize"
            :page-sizes="[10, 15, 20, 50]"
            :total="total"
            layout="total, sizes, prev, pager, next, jumper"
            background
            @current-change="onCurrentPageChange"
            @size-change="onPageSizeChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft, User, UserFilled,
  School, Suitcase, Monitor
} from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const userList = ref([])
const userLoading = ref(false)
const activeRole = ref('')
const userInfo = ref({ id: null, username: '', role: '' })
const currentPage = ref(1)
const pageSize = ref(15)
const total = ref(0)

const roleTabs = [
  { label: '全部', value: '', icon: 'UserFilled' },
  { label: '学生', value: 'STUDENT', icon: 'School' },
  { label: '教师', value: 'TEACHER', icon: 'Suitcase' },
  { label: '管理员', value: 'ADMIN', icon: 'Monitor' }
]

const roleLabel = (role) => {
  const map = { STUDENT: '学生', TEACHER: '教师', ADMIN: '管理员' }
  return map[role] || role
}

const roleTagType = (role) => {
  const map = { STUDENT: 'primary', TEACHER: 'success', ADMIN: 'warning' }
  return map[role] || 'info'
}

const roleIcon = (role) => {
  const map = { STUDENT: 'School', TEACHER: 'Suitcase', ADMIN: 'Monitor' }
  return map[role] || 'User'
}

const formatDate = (isoStr) => {
  if (!isoStr) return '-'
  const d = new Date(isoStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const fetchUsers = async (role, page, size) => {
  userLoading.value = true
  try {
    const params = {
      current: page || currentPage.value,
      size: size || pageSize.value
    }
    if (role) params.role = role
    const res = await request.get('/user/list', { params })
    if (res.data.code === 200) {
      const d = res.data.data
      userList.value = d.records || []
      total.value = Number(d.total) || 0
      currentPage.value = Number(d.current) || currentPage.value
      pageSize.value = Number(d.size) || pageSize.value
    } else {
      ElMessage.error(res.data.msg || '获取用户列表失败')
    }
  } catch (e) {
    ElMessage.error('获取用户列表失败')
  } finally {
    userLoading.value = false
  }
}

const switchRole = (role) => {
  activeRole.value = role
  currentPage.value = 1
  fetchUsers(role, 1, pageSize.value)
}

const onCurrentPageChange = (page) => {
  currentPage.value = page
  fetchUsers(activeRole.value, page, pageSize.value)
}

const onPageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers(activeRole.value, 1, size)
}

const handleDeleteUser = (row) => {
  ElMessageBox.confirm(
    `确定删除用户【${row.username}】（${roleLabel(row.role)}）吗？`,
    '管理员操作确认',
    { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      const res = await request.delete(`/user/delete/${row.id}`)
      if (res.data.code === 200) {
        ElMessage.success('用户删除成功')
        // 刷新当前列表
        const currentTotal = total.value
        const afterDelete = currentTotal - 1
        // 如果当前页只有一条且不是第一页，回退一页
        if (afterDelete > 0 && afterDelete % pageSize.value === 0 && currentPage.value > 1) {
          currentPage.value -= 1
        }
        await fetchUsers(activeRole.value, currentPage.value, pageSize.value)
      } else {
        ElMessage.error(res.data.msg || '删除用户失败')
      }
    } catch (e) {
      ElMessage.error('删除用户失败')
    }
  }).catch(() => {})
}

const goBack = () => {
  router.push('/home')
}

onMounted(async () => {
  // 获取当前登录用户信息
  try {
    const userInfoStr = localStorage.getItem('userInfo')
    const localUser = JSON.parse(userInfoStr || '{}')
    if (localUser && localUser.id) {
      userInfo.value = localUser
    } else {
      const res = await request.get('/auth/me')
      if (res.data.code === 200) {
        userInfo.value = res.data.data
      }
    }
  } catch (e) {
    // ignore
  }

  // 获取当前角色筛选数据
  await fetchUsers('', 1, pageSize.value)
})
</script>

<style scoped>
.user-mgr-container {
  min-height: 100vh;
  background: var(--app-bg, #f5f7fa);
  animation: fadeIn 0.3s ease-out;
}

/* Header */
.mgr-header {
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(20px);
  background: rgba(255, 255, 255, 0.85);
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.mgr-header-inner {
  height: 68px;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mgr-header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mgr-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.back-btn {
  font-weight: 600;
}

/* Content */
.mgr-content {
  padding: 24px;
  max-width: 1280px;
  margin: 0 auto;
}

.mgr-card {
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

/* Role Filter Bar */
.role-filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 1px solid #e5e7eb;
}

.filter-label {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}

.role-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.role-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
  background: #fff;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.role-tab:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  background: #eff6ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.role-tab.active {
  border-color: #3b82f6;
  color: #fff;
  background: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

/* Table */
.user-table {
  border-radius: 0;
}

.user-table :deep(.el-table__header-wrapper th) {
  background-color: #f8fafc !important;
  font-weight: 600 !important;
  color: #1e293b !important;
}

.user-table :deep(.el-table__row:hover) {
  background-color: #f0f7ff !important;
}

.user-table :deep(.el-table__cell) {
  padding: 12px 16px !important;
}

/* Footer */
.mgr-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-top: 1px solid #e5e7eb;
  background: #fafbfc;
  flex-wrap: wrap;
  gap: 12px;
}

.mgr-stats {
  font-size: 13px;
  color: #64748b;
}

.mgr-stats strong {
  color: #1e293b;
  font-size: 15px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 768px) {
  .mgr-header-inner {
    height: 60px;
    padding: 0 16px;
  }

  .mgr-title {
    font-size: 17px;
  }

  .mgr-content {
    padding: 16px;
  }

  .role-filter-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .role-tabs {
    width: 100%;
  }

  .role-tab {
    flex: 1;
    justify-content: center;
    padding: 8px 10px;
    font-size: 13px;
  }
}
</style>
