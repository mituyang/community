<template>
  <router-link to="/notifications" class="notification-link">
    <el-badge
      :value="userStore.unreadCount"
      :hidden="userStore.unreadCount === 0"
      class="notification-badge"
    >
      <el-icon><Bell /></el-icon>
    </el-badge>
  </router-link>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const userStore = useUserStore()

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

// 定期更新未读消息数量
let updateInterval
onMounted(() => {
  fetchUnreadCount()
  // 每分钟更新一次
  updateInterval = setInterval(fetchUnreadCount, 60000)
})

onUnmounted(() => {
  if (updateInterval) {
    clearInterval(updateInterval)
  }
})
</script>

<style scoped>
.notification-link {
  color: inherit;
  text-decoration: none;
  display: flex;
  align-items: center;
}

.notification-badge {
  margin-right: 16px;
  font-size: 20px;
}

:deep(.el-badge__content) {
  transform: translate(50%, -50%);
}
</style> 