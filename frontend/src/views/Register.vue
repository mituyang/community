<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">注册</h2>
      <el-form :model="registerForm" @submit.prevent="handleRegister" label-position="top">
        <el-form-item 
          label="用户名" 
          :error="usernameError"
          :class="{ 'is-error': usernameError }"
        >
          <el-input 
            v-model="registerForm.username"
            placeholder="请输入3-20个字符的用户名"
            :status="usernameError ? 'error' : ''"
          />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <div class="email-group">
            <el-input 
              v-model="registerForm.email" 
              type="email"
              placeholder="请输入邮箱"
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
            v-model="registerForm.verificationCode"
            placeholder="请输入验证码"
            maxlength="6"
            class="verification-input"
          />
        </el-form-item>

        <el-form-item label="密码">
          <el-input 
            v-model="registerForm.password" 
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
            注册
          </el-button>
          <div class="login-link">
            已有账号？
            <router-link to="/login">立即登录</router-link>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { register, sendRegisterCode, checkUsername } from '../api'
import { ElMessage } from 'element-plus'
import { debounce } from 'lodash'  // 需要安装 lodash: npm install lodash

const router = useRouter()
const countdown = ref(0)
const showVerificationCode = ref(false)
const usernameError = ref('')

const registerForm = ref({
  username: '',
  email: '',
  password: '',
  verificationCode: ''
})

// 使用 debounce 防止频繁请求
const checkUsernameAvailability = debounce(async (username) => {
  if (username.length < 3) {
    usernameError.value = '用户名长度至少为3个字符'
    return
  }
  if (username.length > 20) {
    usernameError.value = '用户名长度不能超过20个字符'
    return
  }
  
  try {
    await checkUsername(username)
    usernameError.value = ''  // 清除错误信息
  } catch (error) {
    usernameError.value = error.response?.data?.error || '检查用户名失败'
  }
}, 500)  // 500ms 的防抖延迟

// 监听用户名变化
watch(() => registerForm.value.username, (newUsername) => {
  if (newUsername) {
    checkUsernameAvailability(newUsername)
  } else {
    usernameError.value = ''
  }
})

const handleSendCode = async () => {
  if (!registerForm.value.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }
  
  try {
    await sendRegisterCode(registerForm.value.email)
    showVerificationCode.value = true
    ElMessage.success('验证码已发送到您的邮箱')
    
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error) {
    ElMessage.error(error.response?.data?.error || '验证码发送失败')
  }
}

const handleRegister = async () => {
  if (!registerForm.value.username || !registerForm.value.email || !registerForm.value.password) {
    ElMessage.warning('请填写所有必填项')
    return
  }

  if (!registerForm.value.verificationCode) {
    ElMessage.warning('请输入验证码')
    return
  }

  if (registerForm.value.username.length < 3 || registerForm.value.username.length > 20) {
    ElMessage.warning('用户名长度应在3-20个字符之间')
    return
  }

  if (registerForm.value.password.length < 6) {
    ElMessage.warning('密码长度不能少于6个字符')
    return
  }

  try {
    await register({
      username: registerForm.value.username,
      email: registerForm.value.email,
      password: registerForm.value.password,
      verificationCode: registerForm.value.verificationCode
    })
    ElMessage.success('注册成功')
    router.push('/login')
  } catch (error) {
    const errorMessage = error.response?.data?.error || '注册失败'
    ElMessage.error(errorMessage)
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 90vh;
  background-color: #f5f7fa;
  padding: 20px;
  padding-top: 10px;
}

.register-card {
  width: 440px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  margin-top: 0;
}

.register-title {
  text-align: center;
  color: #303133;
  margin-bottom: 30px;
  font-size: 24px;
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

.submit-button {
  width: 100%;
  margin-top: 10px;
  height: 40px;
  font-size: 16px;
}

.login-link {
  text-align: center;
  margin-top: 15px;
  color: #606266;
  font-size: 14px;
}

.login-link a {
  color: #409EFF;
  text-decoration: none;
  margin-left: 5px;
}

.login-link a:hover {
  color: #79bbff;
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

/* 响应式调整 */
@media (max-width: 480px) {
  .register-card {
    width: 100%;
  }
  
  .email-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .verify-button {
    width: 100%;
  }
}

.is-error .el-input__inner {
  border-color: #f56c6c;
}

.el-form-item.is-error .el-input__inner:focus {
  border-color: #f56c6c;
}

.el-form-item__error {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 4px;
}
</style> 