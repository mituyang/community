<template>
  <div class="app-container">
    <el-header class="header">
      <div class="nav">
        <div class="nav-left">
          <router-link to="/" class="nav-item">首页</router-link>
          <router-link 
            v-if="userStore.isLoggedIn()" 
            to="/my-posts" 
            class="nav-item"
          >
            我的帖子
          </router-link>
          <router-link 
            v-if="userStore.isLoggedIn()" 
            :to="`/user/${userStore.user.id}`" 
            class="nav-item"
          >
            个人主页
          </router-link>
        </div>
        <div class="nav-right">
          <template v-if="userStore.isLoggedIn()">
            <router-link to="/notifications" class="nav-item notification-icon">
              <el-badge :value="userStore.unreadCount" :max="99" :hidden="userStore.unreadCount === 0">
                <el-icon><Bell /></el-icon>
              </el-badge>
            </router-link>
            
            <el-dropdown>
              <span class="username">
                {{ userStore.user.username }}
                <el-icon class="el-icon--right">
                  <arrow-down />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item>
                    <router-link to="/profile" class="dropdown-link">个人资料</router-link>
                  </el-dropdown-item>
                  <el-dropdown-item>
                    <router-link to="/notifications" class="dropdown-link">
                      消息通知
                      <el-badge 
                        v-if="userStore.unreadCount > 0" 
                        :value="userStore.unreadCount" 
                        :max="99" 
                        class="notification-badge"
                      />
                    </router-link>
                  </el-dropdown-item>
                  <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <router-link to="/login" class="nav-item">登录</router-link>
            <router-link to="/register" class="nav-item">注册</router-link>
          </template>
        </div>
      </div>
    </el-header>
    
    <router-view></router-view>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useUserStore } from './stores/user'
import { useRouter } from 'vue-router'
import { ArrowDown, Bell } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()
let updateInterval = null

// 获取未读消息数量
const fetchUnreadCount = async () => {
  if (!userStore.isLoggedIn()) return
  
  try {
    const response = await fetch('https://api.searchsomething.top/api/notifications/unread-count', {
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      userStore.setUnreadCount(data.count)
    }
  } catch (error) {
    console.error('获取未读消息数量失败:', error)
  }
}

const handleLogout = () => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (userStore.isLoggedIn()) {
    // 初始化时获取一次
    fetchUnreadCount()
    
    // 启动定时获取
    updateInterval = setInterval(fetchUnreadCount, 5000) // 每10秒更新一次
    
    // 初始化 WebSocket
    userStore.initializeWebSocket()
  }
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
    updateInterval = null
  }
})
</script>

<style scoped>
.app-container {
  min-height: 100vh;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #eee;
  padding: 0 20px;
}

.nav {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-left {
  display: flex;
  gap: 20px;
}

.nav-item {
  color: #333;
  text-decoration: none;
  font-size: 16px;
  padding: 0 10px;
  height: 60px;
  display: flex;
  align-items: center;
  position: relative;
}

.nav-item:hover {
  color: #409EFF;
}

/* 激活状态的导航项样式 */
.nav-item.router-link-active {
  color: #409EFF;
}

.nav-item.router-link-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background-color: #409EFF;
}

.nav-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.username {
  cursor: pointer;
  display: flex;
  align-items: center;
  color: #666;
}

.username:hover {
  color: #409EFF;
}

.dropdown-link {
  text-decoration: none;
  color: inherit;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.notification-icon {
  font-size: 20px;
  padding: 0 10px;
}

.notification-badge {
  margin-left: 8px;
}

:deep(.el-dropdown-menu__item) {
  padding: 5px 20px;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: #f5f7fa;
}

:deep(.el-dropdown-menu__item a) {
  color: inherit;
}

:deep(.el-badge__content) {
  transform: translateY(-50%) translateX(100%);
}
</style>