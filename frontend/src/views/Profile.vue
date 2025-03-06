<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h2>个人资料</h2>
          <el-button type="primary" @click="openEditDialog">编辑资料</el-button>
        </div>
      </template>
      
      <div class="profile-info">
        <div class="avatar-section">
          <el-avatar 
            :size="100" 
            :src="userInfo.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
          />
        </div>

        <div class="info-section">
          <div class="info-group">
            <div class="info-item">
              <span class="label">用户名：</span>
              <span>{{ userInfo.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">昵称：</span>
              <span>{{ userInfo.nickname || '未设置' }}</span>
            </div>
          </div>

          <div class="info-group">
            <div class="info-item">
              <span class="label">邮箱：</span>
              <span>{{ userInfo.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">性别：</span>
              <span>{{ formatGender(userInfo.gender) }}</span>
            </div>
          </div>

          <div class="info-group">
            <div class="info-item">
              <span class="label">生日：</span>
              <span>{{ userInfo.birthday || '未设置' }}</span>
            </div>
            <div class="info-item">
              <span class="label">所在地：</span>
              <span>{{ userInfo.location || '未设置' }}</span>
            </div>
          </div>

          <div class="info-item full-width">
            <span class="label">个人网站：</span>
            <a v-if="userInfo.website" :href="userInfo.website" target="_blank">{{ userInfo.website }}</a>
            <span v-else>未设置</span>
          </div>

          <div class="info-item full-width">
            <span class="label">个人简介：</span>
            <span class="bio">{{ userInfo.bio || '这个人很懒，什么都没写~' }}</span>
          </div>

          <div class="info-item">
            <span class="label">注册时间：</span>
            <span>{{ userInfo.created_at }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 编辑资料对话框 -->
    <el-dialog
      v-model="showEditDialog"
      title="编辑个人资料"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="editForm"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="头像">
          <el-upload
            class="avatar-uploader"
            :action="`${baseURL}/api/upload-avatar`"
            :headers="uploadHeaders"
            :show-file-list="false"
            :on-success="handleAvatarSuccess"
            :on-error="handleAvatarError"
            :before-upload="beforeAvatarUpload"
          >
            <img v-if="editForm.avatar" :src="baseURL + editForm.avatar" class="avatar" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>

        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" />
        </el-form-item>

        <el-form-item label="昵称" prop="nickname">
          <el-input v-model="editForm.nickname" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <div class="email-input-group">
            <el-input v-model="editForm.email" :disabled="!isChangingEmail" />
            <el-button 
              type="primary" 
              link
              @click="isChangingEmail = !isChangingEmail"
            >
              {{ isChangingEmail ? '取消修改' : '修改邮箱' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="性别" prop="gender">
          <el-select v-model="editForm.gender" placeholder="请选择性别">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="保密" value="secret" />
          </el-select>
        </el-form-item>

        <el-form-item label="生日" prop="birthday">
          <el-date-picker
            v-model="editForm.birthday"
            type="date"
            placeholder="选择生日"
            format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="所在地" prop="location">
          <el-input v-model="editForm.location" />
        </el-form-item>

        <el-form-item label="个人网站" prop="website">
          <el-input v-model="editForm.website" />
        </el-form-item>

        <el-form-item label="个人简介" prop="bio">
          <el-input
            v-model="editForm.bio"
            type="textarea"
            :rows="3"
            placeholder="写点什么介绍一下自己吧..."
          />
        </el-form-item>

        <!-- 验证码相关表单项保持不变 -->
        <el-form-item 
          v-if="needVerification"
          :label="isChangingEmail ? '原邮箱验证码' : '验证码'" 
          prop="verificationCode"
        >
          <div class="verification-input-group">
            <el-input v-model="editForm.verificationCode" />
            <el-button 
              type="primary" 
              :disabled="cooldown > 0"
              @click="sendVerificationCode(userInfo.email)"
            >
              {{ cooldown > 0 ? `${cooldown}秒后重试` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item 
          v-if="isChangingEmail"
          label="新邮箱验证码" 
          prop="newEmailCode"
        >
          <div class="verification-input-group">
            <el-input v-model="editForm.newEmailCode" />
            <el-button 
              type="primary" 
              :disabled="newEmailCooldown > 0"
              @click="sendVerificationCode(editForm.email, true)"
            >
              {{ newEmailCooldown > 0 ? `${newEmailCooldown}秒后重试` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">取消</el-button>
          <el-button type="primary" @click="handleUpdate">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import { Plus } from '@element-plus/icons-vue'

const baseURL = 'https://api.searchsomething.top'  // 配置后端基础URL
const userStore = useUserStore()
const userInfo = ref({})
const showEditDialog = ref(false)
const formRef = ref(null)
const isChangingEmail = ref(false)
const cooldown = ref(0)
const newEmailCooldown = ref(0)

const editForm = ref({
  username: '',
  email: '',
  verificationCode: '',
  newEmailCode: '',
  nickname: '',
  avatar: '',
  bio: '',
  location: '',
  website: '',
  gender: '',
  birthday: ''
})

const needVerification = computed(() => {
  return isChangingEmail.value || editForm.value.username !== userInfo.value.username
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  verificationCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ],
  newEmailCode: [
    { required: true, message: '请输入新邮箱验证码', trigger: 'blur' }
  ],
  nickname: [
    { max: 80, message: '昵称不能超过80个字符', trigger: 'blur' }
  ],
  website: [
    { type: 'url', message: '请输入正确的网址格式', trigger: 'blur' }
  ],
  bio: [
    { max: 500, message: '个人简介不能超过500个字符', trigger: 'blur' }
  ]
}

const formatGender = (gender) => {
  const genderMap = {
    male: '男',
    female: '女',
    secret: '保密'
  }
  return genderMap[gender] || '保密'
}

// 上传请求头
const uploadHeaders = computed(() => ({
  'Authorization': userStore.getAuthHeader()
}))

// 头像上传成功处理
const handleAvatarSuccess = (res) => {
  editForm.value.avatar = res.url
  ElMessage.success('头像上传成功')
}

// 头像上传失败处理
const handleAvatarError = (error) => {
  console.error('头像上传失败:', error)
  ElMessage.error('头像上传失败，请重试')
}

// 发送验证码
const sendVerificationCode = async (email, isNewEmail = false) => {
  try {
    const response = await fetch('https://api.searchsomething.top/api/send-verification', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify({
        email,
        type: isNewEmail ? 'new_email' : 'current_email'
      })
    })

    const data = await response.json()
    if (response.ok) {
      ElMessage.success('验证码已发送')
      // 设置冷却时间
      if (isNewEmail) {
        newEmailCooldown.value = 60
        const timer = setInterval(() => {
          newEmailCooldown.value--
          if (newEmailCooldown.value <= 0) clearInterval(timer)
        }, 1000)
      } else {
        cooldown.value = 60
        const timer = setInterval(() => {
          cooldown.value--
          if (cooldown.value <= 0) clearInterval(timer)
        }, 1000)
      }
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('发送验证码失败:', error)
    ElMessage.error(error.message || '发送验证码失败')
  }
}

// 更新用户信息
const handleUpdate = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await fetch('https://api.searchsomething.top/api/user/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': userStore.getAuthHeader()
          },
          body: JSON.stringify({
            username: editForm.value.username,
            email: isChangingEmail.value ? editForm.value.email : userInfo.value.email,
            verificationCode: editForm.value.verificationCode,
            newEmailCode: isChangingEmail.value ? editForm.value.newEmailCode : null,
            nickname: editForm.value.nickname,
            avatar: editForm.value.avatar,
            bio: editForm.value.bio,
            location: editForm.value.location,
            website: editForm.value.website,
            gender: editForm.value.gender,
            birthday: editForm.value.birthday
          })
        })
        
        const data = await response.json()
        if (response.ok) {
          ElMessage.success('更新成功')
          showEditDialog.value = false
          await fetchUserInfo()
          
          // 更新 store 中的用户信息
          userStore.updateUser({
            username: editForm.value.username,
            email: isChangingEmail.value ? editForm.value.email : userInfo.value.email,
            nickname: editForm.value.nickname,
            avatar: editForm.value.avatar,
            bio: editForm.value.bio,
            location: editForm.value.location,
            website: editForm.value.website,
            gender: editForm.value.gender,
            birthday: editForm.value.birthday
          })
          
          // 重置表单
          isChangingEmail.value = false
          editForm.value.verificationCode = ''
          editForm.value.newEmailCode = ''
        } else {
          throw new Error(data.error)
        }
      } catch (error) {
        console.error('更新用户信息失败:', error)
        ElMessage.error(error.message || '更新失败')
      }
    }
  })
}

// 打开编辑对话框时填充表单
const openEditDialog = () => {
  Object.keys(editForm.value).forEach(key => {
    if (key in userInfo.value) {
      editForm.value[key] = userInfo.value[key]
    }
  })
  isChangingEmail.value = false
  showEditDialog.value = true
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const response = await fetch('https://api.searchsomething.top/api/user/profile', {
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    const data = await response.json()
    if (response.ok) {
      userInfo.value = data.user
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  padding: 20px;
  max-width: 800px;
  margin: 0 auto;
}

.profile-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  color: #303133;
}

.profile-info {
  padding: 20px 0;
}

.avatar-section {
  text-align: center;
  margin-bottom: 30px;
}

.info-section {
  padding: 0 20px;
}

.info-group {
  display: flex;
  gap: 40px;
  margin-bottom: 20px;
}

.info-item {
  flex: 1;
  margin-bottom: 15px;
}

.info-item.full-width {
  flex: 0 0 100%;
}

.label {
  color: #909399;
  margin-right: 10px;
  display: inline-block;
  min-width: 80px;
}

.bio {
  color: #606266;
  white-space: pre-wrap;
}

.avatar-uploader {
  text-align: center;
}

.avatar-uploader .el-upload {
  border: 1px dashed #d9d9d9;
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.avatar-uploader .el-upload:hover {
  border-color: #409EFF;
}

.avatar-uploader-icon {
  font-size: 28px;
  color: #8c939d;
  width: 100px;
  height: 100px;
  line-height: 100px;
  text-align: center;
}

.avatar {
  width: 100px;
  height: 100px;
  display: block;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.email-input-group,
.verification-input-group {
  display: flex;
  gap: 10px;
}

.verification-input-group .el-input {
  flex: 1;
}
</style> 