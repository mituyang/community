<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">登录</h2>
      <el-form :model="loginForm" @submit.prevent="handleLogin" label-position="top">
        <el-form-item label="用户名或邮箱">
          <el-input 
            v-model="loginForm.username"
            placeholder="请输入用户名或邮箱"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input 
            v-model="loginForm.password" 
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            native-type="submit"
            class="submit-button"
          >
            登录
          </el-button>
          <div class="register-link">
            <el-button type="text" @click="forgotPasswordDialogVisible = true">
              忘记密码？
            </el-button>
            <div class="register-text">
              还没有账号？<router-link to="/register">立即注册</router-link>
            </div>
          </div>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="forgotPasswordDialogVisible"
      title="重置密码"
      width="30%"
      class="reset-dialog"
    >
      <el-form :model="resetForm" label-position="top">
        <el-form-item label="邮箱">
          <div class="email-group">
            <el-input 
              v-model="resetForm.email" 
              type="email"
              placeholder="请输入注册时使用的邮箱"
            />
            <el-button 
              type="primary" 
              :disabled="countdown > 0"
              @click="handleSendCode"
              class="verify-button"
            >
              {{ countdown > 0 ? `${countdown}秒后重试` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="验证码" v-if="showVerificationCode">
          <el-input 
            v-model="resetForm.verificationCode" 
            placeholder="请输入验证码"
            maxlength="6"
            class="verification-input"
          />
        </el-form-item>

        <el-form-item label="新密码" v-if="showNewPassword">
          <el-input 
            v-model="resetForm.newPassword" 
            type="password"
            placeholder="请输入新密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="forgotPasswordDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleResetPassword">
            {{ showNewPassword ? '重置密码' : '下一步' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { login, sendCode, verifyCode, resetPassword } from '../api'  // 修改导入
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()

const loginForm = ref({
  username: '',
  password: ''
})

const forgotPasswordDialogVisible = ref(false)
const showVerificationCode = ref(false)
const showNewPassword = ref(false)
const countdown = ref(0)

const resetForm = ref({
  email: '',
  verificationCode: '',
  newPassword: ''
})

const handleLogin = async () => {
  try {
    if (!loginForm.value.username || !loginForm.value.password) {
      ElMessage.warning('请输入用户名和密码')
      return
    }

    const response = await fetch('https://api.searchsomething.top/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: loginForm.value.username,
        password: loginForm.value.password
      })
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error || '登录失败')
    }

    console.log('Login response:', data) // 调试日志
    userStore.login(data.token, data.user)
    console.log('Auth token after login:', userStore.getAuthToken) // 调试日志

    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    console.error('Login error:', error)
    ElMessage.error(error.message || '登录失败')
  }
}

const handleSendCode = async () => {  // 改名
  if (!resetForm.value.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  
  try {
    // 调用后端发送验证码API
    await sendCode(resetForm.value.email)  // 使用新的函数名
    showVerificationCode.value = true
    ElMessage.success('验证码已发送到您的邮箱')
    
    // 开始倒计时
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '验证码发送失败')
    return
  }
}

const handleResetPassword = async () => {
  if (!resetForm.value.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }

  if (showVerificationCode.value && !resetForm.value.verificationCode) {
    ElMessage.warning('请输入验证码')
    return
  }

  try {
    if (!showVerificationCode.value) {
      // 第一步：发送验证码
      await handleSendCode()  // 使用新的函数名
      return
    }

    if (!showNewPassword.value) {
      // 第二步：验证验证码
      await verifyCode(resetForm.value.email, resetForm.value.verificationCode)
      showNewPassword.value = true
      return
    }

    // 第三步：重置密码
    await resetPassword({
      email: resetForm.value.email,
      verificationCode: resetForm.value.verificationCode,
      newPassword: resetForm.value.newPassword
    })

    ElMessage.success('密码重置成功，请使用新密码登录')
    forgotPasswordDialogVisible.value = false
    resetForm.value = { email: '', verificationCode: '', newPassword: '' }
    showVerificationCode.value = false
    showNewPassword.value = false
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '操作失败')
  }
}

// 检查是否已登录
if (userStore.isLoggedIn()) {
  console.log('Already logged in, redirecting...') // 调试日志
  router.push('/')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90vh;  /* 改为90vh，让整体向上移动 */
  background-color: #f5f7fa;
  padding: 20px;
  padding-top: 0;  /* 移除顶部内边距 */
}

.login-card {
  width: 440px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-top: -60px;  /* 添加负的上边距，使卡片向上移动 */
}

.login-title {
  text-align: center;
  color: #303133;
  margin-bottom: 30px;
  font-size: 24px;
}

.submit-button {
  width: 100%;
  margin-top: 10px;
  height: 40px;
  font-size: 16px;
}

.register-link {
  text-align: center;
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;  /* 移除内边距 */
}

.register-text {
  margin-left: auto;  /* 将注册文本推到最右边 */
  padding-right: 0;  /* 移除右侧内边距 */
}

.register-link a {
  color: #409EFF;
  text-decoration: none;
  margin-left: 5px;
}

.register-link a:hover {
  color: #79bbff;
}

/* 重置密码对话框样式 */
.reset-dialog {
  border-radius: 8px;
}

.email-group {
  display: flex;
  gap: 10px;
  align-items: center;
}

.email-group .el-input {
  flex: 1;
}

.verify-button {
  white-space: nowrap;
  min-width: 120px;
}

.verification-input {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  padding-bottom: 8px;
}

:deep(.el-input__inner) {
  height: 40px;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-dialog__body) {
  padding: 20px 30px;
}

:deep(.el-dialog__header) {
  margin-right: 0;
  padding: 20px 30px 10px;
  text-align: center;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 500;
}

:deep(.el-dialog__footer) {
  padding: 10px 30px 20px;
  border-top: 1px solid #dcdfe6;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .login-card {
    width: 100%;
  }
  
  .email-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .verify-button {
    width: 100%;
  }
  
  :deep(.el-dialog) {
    width: 90% !important;
    margin: 0 auto;
  }
}
</style>