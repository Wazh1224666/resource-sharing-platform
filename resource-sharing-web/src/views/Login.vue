<template>
  <div class="login-page">
    <div class="bg-decoration ball-1"></div>
    <div class="bg-decoration ball-2"></div>
    <div class="bg-decoration ball-3"></div>

    <div class="login-container">
      <el-card class="login-card">
        <div class="login-header">
          <div class="logo-area">
            <el-icon :size="32"><School /></el-icon>
          </div>
          <h2 class="title">高校资源共享平台</h2>
          <p class="subtitle">Academic Resource Sharing Platform</p>
        </div>

        <el-form :model="loginForm" class="login-form">
          <el-form-item>
            <el-input v-model="loginForm.username" placeholder="用户名" prefix-icon="User" size="large" />
          </el-form-item>
          <el-form-item>
            <el-input v-model="loginForm.password" type="password" placeholder="密码" show-password prefix-icon="Lock" size="large" />
          </el-form-item>
          <div class="form-options">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
            <el-link type="primary" :underline="false" @click="openForgotPassword">忘记密码？</el-link>
          </div>
          <el-button type="primary" class="login-button" @click="handleLogin" :loading="loading">登 录</el-button>
          <div class="register-link">
            还没有账号？<el-link type="primary" :underline="false" @click="openRegister">立即注册</el-link>
          </div>
        </el-form>
      </el-card>
    </div>

    <el-dialog v-model="registerDialogVisible" title="新用户注册" width="420px" center destroy-on-close>
      <el-form
          :model="registerForm"
          :rules="registerRules"
          ref="registerFormRef"
          label-position="top"
          status-icon
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="3-15位字母或数字" />
        </el-form-item>

        <el-form-item label="设置密码" prop="password">
          <el-input
              v-model="registerForm.password"
              type="password"
              show-password
              placeholder="至少6位，需包含字母和数字"
          />
        </el-form-item>

        <el-form-item label="绑定邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="用于找回密码，例如：name@example.com" />
        </el-form-item>

        <el-form-item label="账号角色" prop="role">
          <el-select v-model="registerForm.role" placeholder="请选择角色">
            <el-option label="学生" value="STUDENT" />
            <el-option label="教师" value="TEACHER" />
            <el-option label="管理员" value="ADMIN" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="registerForm.role !== 'STUDENT'" label="管理密钥" prop="adminKey">
          <el-input
              v-model="registerForm.adminKey"
              type="password"
              show-password
              placeholder="创建教师/管理员账号必须输入"
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
              v-model="registerForm.confirmPassword"
              type="password"
              show-password
              placeholder="请再次输入密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="registerDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleRegister" :loading="registerLoading">提交注册</el-button>
        </span>
      </template>
    </el-dialog>

    <el-dialog v-model="forgotDialogVisible" title="找回密码" width="420px" center destroy-on-close>
      <el-form
          :model="forgotForm"
          :rules="forgotRules"
          ref="forgotFormRef"
          label-position="top"
          status-icon
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="forgotForm.username" placeholder="请输入注册用户名" />
        </el-form-item>
        <el-form-item label="绑定邮箱" prop="email">
          <el-input v-model="forgotForm.email" placeholder="请输入注册时绑定的邮箱" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
              v-model="forgotForm.newPassword"
              type="password"
              show-password
              placeholder="至少6位，且包含字母和数字"
          />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmNewPassword">
          <el-input
              v-model="forgotForm.confirmNewPassword"
              type="password"
              show-password
              placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="forgotDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleForgotPassword" :loading="forgotLoading">重置密码</el-button>
        </span>
      </template>
    </el-dialog>

    <div class="footer">
      <p>© 2026 高校资源共享平台 | 技术支持：SpringBoot + Vue3</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { School, User, Lock } from '@element-plus/icons-vue'
import request from '../utils/request'

const router = useRouter()
const loading = ref(false)
const rememberMe = ref(false)

// --- 登录逻辑 ---
const loginForm = ref({ username: '', password: '' })

const handleLogin = async () => {
  if (!loginForm.value.username || !loginForm.value.password) {
    return ElMessage.warning('请填写账号和密码')
  }
  loading.value = true
  try {
    const res = await request.post('/auth/login', loginForm.value)
    if (res.data.code === 200) {
      const loginData = res.data.data
      // 兼容老格式（仅 token 字符串）和新格式（token + userInfo）
      const token = typeof loginData === 'string' ? loginData : loginData?.token
      const userInfo = typeof loginData === 'object' ? loginData?.userInfo : null
      localStorage.setItem('token', token || '')
      if (userInfo) {
        localStorage.setItem('userInfo', JSON.stringify(userInfo))
      } else {
        // 如果没有userInfo，清空可能存在的旧数据
        localStorage.removeItem('userInfo')
      }
      ElMessage.success('登录成功')
      setTimeout(() => router.push('/home'), 200)
    } else {
      ElMessage.error(res.data.msg)
    }
  } catch (error) {
    ElMessage.error('连接服务器失败')
  } finally {
    loading.value = false
  }
}

// --- 注册逻辑 (带强校验) ---
const registerDialogVisible = ref(false)
const registerLoading = ref(false)
const registerFormRef = ref(null)

const registerForm = reactive({
  username: '',
  password: '',
  email: '',
  role: 'STUDENT',
  adminKey: '',
  confirmPassword: ''
})

// 定义复杂的校验规则
const registerRules = {
  username: [
    { required: true, message: '用户名不能为空', trigger: 'blur' },
    { min: 3, max: 15, message: '长度需在 3 到 15 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '密码不能为空', trigger: 'blur' },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$/,
      message: '密码至少6位，且必须同时包含字母和数字',
      trigger: 'blur'
    }
  ],
  email: [
    { required: true, message: '邮箱不能为空', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$/,
      message: '请输入有效邮箱地址',
      trigger: 'blur'
    }
  ],
  role: [{ required: true, message: '请选择账号角色', trigger: 'change' }],
  adminKey: [
    {
      validator: (rule, value, callback) => {
        if (registerForm.role !== 'STUDENT' && !value) {
          callback(new Error('创建教师/管理员账号必须填写管理密钥'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码确认', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致！'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const openRegister = () => {
  registerDialogVisible.value = true
}

const handleRegister = async () => {
  if (!registerFormRef.value) return

  // 核心：提交前执行表单验证
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      registerLoading.value = true
      try {
        const res = await request.post('/auth/register', {
          username: registerForm.username,
          password: registerForm.password,
          email: registerForm.email,
          role: registerForm.role,
          // 后端暂借 nickname 字段传递注册密钥，避免新增 DTO
          nickname: registerForm.adminKey
        })
        if (res.data.code === 200) {
          ElMessage.success('注册成功，请登录')
          registerDialogVisible.value = false
          loginForm.value.username = registerForm.username // 自动填充刚才注册的用户名
        } else {
          ElMessage.error(res.data.msg)
        }
      } catch (error) {
        ElMessage.error('注册接口调用失败')
      } finally {
        registerLoading.value = false
      }
    } else {
      ElMessage.error('请检查输入内容是否符合要求')
    }
  })
}

// --- 找回密码逻辑 ---
const forgotDialogVisible = ref(false)
const forgotLoading = ref(false)
const forgotFormRef = ref(null)
const forgotForm = reactive({
  username: '',
  email: '',
  newPassword: '',
  confirmNewPassword: ''
})

const forgotRules = {
  username: [{ required: true, message: '用户名不能为空', trigger: 'blur' }],
  email: [
    { required: true, message: '邮箱不能为空', trigger: 'blur' },
    {
      pattern: /^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$/,
      message: '请输入有效邮箱地址',
      trigger: 'blur'
    }
  ],
  newPassword: [
    { required: true, message: '新密码不能为空', trigger: 'blur' },
    {
      pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{6,}$/,
      message: '密码至少6位，且必须同时包含字母和数字',
      trigger: 'blur'
    }
  ],
  confirmNewPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== forgotForm.newPassword) {
          callback(new Error('两次输入的新密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const openForgotPassword = () => {
  forgotDialogVisible.value = true
}

const handleForgotPassword = async () => {
  if (!forgotFormRef.value) return
  await forgotFormRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请先修正表单错误')
      return
    }
    forgotLoading.value = true
    try {
      const res = await request.post('/auth/forgot-password', {
        username: forgotForm.username,
        email: forgotForm.email,
        newPassword: forgotForm.newPassword
      })
      if (res.data.code === 200) {
        ElMessage.success('密码已重置，请使用新密码登录')
        forgotDialogVisible.value = false
        loginForm.value.username = forgotForm.username
        loginForm.value.password = ''
      } else {
        ElMessage.error(res.data.msg || '重置密码失败')
      }
    } catch (e) {
      ElMessage.error('重置密码请求失败')
    } finally {
      forgotLoading.value = false
    }
  })
}
</script>

<style scoped>
/* ==================== Login Page ==================== */
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background: var(--app-bg);
  position: relative;
  overflow: hidden;
  animation: fadeIn var(--app-transition-slow) ease-out;
}

/* Background Decorations */
.bg-decoration {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  z-index: 0;
  opacity: 0.7;
  animation: float 20s ease-in-out infinite;
}

.ball-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle,
    rgba(59, 130, 246, 0.25) 0%,
    rgba(59, 130, 246, 0.1) 40%,
    transparent 70%);
  top: -150px;
  right: -150px;
  animation-delay: 0s;
}

.ball-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle,
    rgba(16, 185, 129, 0.2) 0%,
    rgba(16, 185, 129, 0.05) 40%,
    transparent 70%);
  bottom: -100px;
  left: -100px;
  animation-delay: 5s;
}

.ball-3 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle,
    rgba(245, 158, 11, 0.15) 0%,
    rgba(245, 158, 11, 0.05) 40%,
    transparent 70%);
  top: 50%;
  left: 10%;
  animation-delay: 10s;
}

/* Login Container */
.login-container {
  z-index: var(--app-z-modal);
  width: 100%;
  max-width: 440px;
  padding: var(--app-spacing-5);
}

.login-card {
  border: none;
  border-radius: var(--app-radius-xl);
  box-shadow: var(--app-shadow-2xl) !important;
  background: var(--app-bg-card);
  backdrop-filter: blur(30px);
  padding: var(--app-spacing-6);
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
  animation: slideInRight var(--app-transition-normal) ease-out 0.2s both;
}

.login-card:hover {
  box-shadow: var(--app-shadow-2xl), 0 0 0 1px rgba(59, 130, 246, 0.1) !important;
  border-color: var(--app-border-hover);
  transform: translateY(-4px);
}

/* Login Header */
.login-header {
  text-align: center;
  margin-bottom: var(--app-spacing-6);
}

.logo-area {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg,
    var(--app-color-primary-500),
    var(--app-color-primary-600));
  border-radius: var(--app-radius-lg);
  margin-bottom: var(--app-spacing-4);
  box-shadow: 0 12px 28px rgba(59, 130, 246, 0.3);
  transition: var(--app-transition-normal);
}

.login-card:hover .logo-area {
  transform: rotate(10deg) scale(1.1);
  box-shadow: 0 16px 36px rgba(59, 130, 246, 0.4);
}

.logo-area .el-icon {
  color: white;
  font-size: 32px;
}

.title {
  margin: 0;
  font-size: var(--app-font-size-3xl);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text);
  background: linear-gradient(135deg,
    var(--app-color-primary-600),
    var(--app-color-primary-800));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--app-spacing-2);
}

.subtitle {
  margin: 0;
  font-size: var(--app-font-size-sm);
  color: var(--app-text-muted);
  font-weight: var(--app-font-weight-medium);
  letter-spacing: 1px;
  text-transform: uppercase;
}

/* Login Form */
.login-form {
  margin-top: var(--app-spacing-5);
}

.login-form :deep(.el-form-item) {
  margin-bottom: var(--app-spacing-4);
}

.login-form :deep(.el-input__wrapper) {
  border-radius: var(--app-radius-lg) !important;
  padding: 0 var(--app-spacing-4) !important;
  height: 48px;
  border: 1px solid var(--app-border);
  transition: var(--app-transition-normal);
  background: var(--app-bg-overlay);
}

.login-form :deep(.el-input__wrapper:hover),
.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: var(--app-color-primary-400) !important;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
  transform: translateY(-1px);
}

.login-form :deep(.el-input__prefix) {
  margin-right: var(--app-spacing-2);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--app-spacing-5);
}

.login-button {
  width: 100%;
  height: 52px;
  font-size: var(--app-font-size-base);
  font-weight: var(--app-font-weight-semibold);
  border-radius: var(--app-radius-lg);
  background: linear-gradient(135deg,
    var(--app-color-primary-500),
    var(--app-color-primary-600));
  border: none;
  transition: var(--app-transition-normal) !important;
  margin-top: var(--app-spacing-2);
}

.login-button:hover {
  background: linear-gradient(135deg,
    var(--app-color-primary-600),
    var(--app-color-primary-700));
  transform: translateY(-2px);
  box-shadow: var(--app-shadow-lg) !important;
}

.login-button:active {
  transform: translateY(0);
}

.register-link {
  margin-top: var(--app-spacing-5);
  text-align: center;
  font-size: var(--app-font-size-sm);
  color: var(--app-text-muted);
}

.register-link .el-link {
  font-weight: var(--app-font-weight-semibold);
}

/* Dialog Styles */
:deep(.el-dialog) {
  border-radius: var(--app-radius-xl) !important;
  background: var(--app-bg-card) !important;
  backdrop-filter: blur(30px) !important;
  border: 1px solid var(--app-border) !important;
}

:deep(.el-dialog__header) {
  padding: var(--app-spacing-5) var(--app-spacing-5) 0 !important;
  margin-bottom: var(--app-spacing-4) !important;
}

:deep(.el-dialog__title) {
  font-size: var(--app-font-size-xl) !important;
  font-weight: var(--app-font-weight-bold) !important;
  color: var(--app-text) !important;
}

:deep(.el-dialog__body) {
  padding: var(--app-spacing-5) !important;
}

:deep(.el-dialog__footer) {
  padding: 0 var(--app-spacing-5) var(--app-spacing-5) !important;
}

/* Footer */
.footer {
  position: absolute;
  bottom: var(--app-spacing-4);
  color: var(--app-text-light);
  font-size: var(--app-font-size-xs);
  z-index: var(--app-z-modal);
  text-align: center;
  width: 100%;
  padding: 0 var(--app-spacing-4);
}

/* ==================== Animations ==================== */
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -30px) scale(1.05); }
  66% { transform: translate(-20px, 20px) scale(0.95); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInRight {
  from { opacity: 0; transform: translateX(40px); }
  to { opacity: 1; transform: translateX(0); }
}

/* ==================== Responsive Design ==================== */
@media (max-width: 640px) {
  .login-container {
    padding: var(--app-spacing-3);
    max-width: 90%;
  }

  .login-card {
    padding: var(--app-spacing-5);
  }

  .title {
    font-size: var(--app-font-size-2xl);
  }

  .logo-area {
    width: 56px;
    height: 56px;
  }

  .logo-area .el-icon {
    font-size: 28px;
  }

  .login-form :deep(.el-input__wrapper) {
    height: 44px;
  }

  .login-button {
    height: 48px;
  }

  .bg-decoration {
    filter: blur(40px);
  }

  .ball-1, .ball-2, .ball-3 {
    display: none;
  }
}

@media (max-width: 480px) {
  .form-options {
    flex-direction: column;
    gap: var(--app-spacing-3);
    align-items: flex-start;
  }

  .footer {
    font-size: 0.7rem;
  }
}
</style>