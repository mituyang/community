<template>
  <div class="notification-container">
    <el-card class="notification-card">
      <template #header>
        <div class="notification-header">
          <span>消息通知</span>
          <el-button 
            type="primary" 
            size="small" 
            @click="markAllAsRead"
            :disabled="!hasUnread"
          >
            全部标为已读
          </el-button>
        </div>
      </template>

      <div class="notification-list" v-loading="loading">
        <div v-if="notifications.length === 0" class="no-notifications">
          暂无消息通知
        </div>
        
        <template v-else>
          <div 
            v-for="notification in notifications" 
            :key="notification.id" 
            class="notification-item"
            :class="{ 'unread': !notification.is_read }"
            @click="goToTarget(notification)"
          >
            <div class="notification-content">
              <router-link 
                :to="`/user/${notification.sender.id}`"
                class="sender-name"
                @click.stop
              >
                {{ notification.sender.username }}
              </router-link>
              {{ getActionText(notification.type) }}
              <span v-if="notification.type !== 'follow'" class="target-text">
                {{ getTargetText(notification) }}
              </span>
            </div>
            
            <div class="notification-meta">
              <span class="notification-time">{{ formatTime(notification.created_at) }}</span>
              <el-button 
                v-if="!notification.is_read"
                link
                type="primary"
                size="small"
                @click.stop="markAsRead(notification.id)"
              >
                标为已读
              </el-button>
            </div>
          </div>
          
          <div v-if="hasMore" class="load-more">
            <el-button 
              text 
              @click="loadMore"
              :loading="loadingMore"
            >
              加载更多
            </el-button>
          </div>
        </template>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const notifications = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const hasMore = ref(true)
const router = useRouter()

// 计算是否有未读消息
const hasUnread = computed(() => {
  return notifications.value.some(notification => !notification.is_read)
})

// 获取动作文本
const getActionText = (type) => {
  const actionMap = {
    'like': '点赞了你的',
    'comment': '评论了你的',
    'share': '转发了你的',
    'reply': '回复了你的',
    'follow': '关注了你'
  }
  return actionMap[type] || '互动了你的'
}

// 获取目标文本
const getTargetText = (notification) => {
  if (notification.type === 'follow') {
    return ''
  }
  
  // 如果是评论的回复、点赞或转发，显示评论内容
  if (notification.comment_id) {
    const match = notification.content.match(/'([^']*)'/)
    if (match && match[1]) {
      const commentContent = match[1]
      return commentContent.length > 20 ? commentContent.substring(0, 20) + '...' : commentContent + ' 评论'
    }
    return '评论'
  }
  
  // 如果是帖子的评论、点赞或转发，显示帖子标题
  const match = notification.content.match(/'([^']*)'/)
  if (match && match[1]) {
    const title = match[1]
    return title.length > 20 ? title.substring(0, 20) + '...' : title + ' 帖子'
  }
  
  return '帖子'
}

// 获取通知列表
const fetchNotifications = async () => {
  if (!userStore.isLoggedIn()) return
  
  try {
    loading.value = true
    const response = await fetch(`https://api.searchsomething.top/api/notifications?page=${currentPage.value}&page_size=${pageSize.value}`, {
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    const data = await response.json()
    
    if (response.ok) {
      if (currentPage.value === 1) {
        // 如果是第一页，重置通知列表
        notifications.value = data.notifications
      } else {
        // 如果是加载更多，追加新的通知
        notifications.value = notifications.value.concat(data.notifications)
      }
      hasMore.value = data.has_more
      
      // 计算所有通知中未读的数量
      const unreadCount = notifications.value.filter(n => !n.is_read).length
      userStore.setUnreadCount(unreadCount)
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('获取通知失败:', error)
    ElMessage.error('获取通知失败')
  } finally {
    loading.value = false
  }
}

// 加载更多
const loadMore = async () => {
  if (loadingMore.value || !hasMore.value) return
  
  loadingMore.value = true
  currentPage.value++
  await fetchNotifications()
  loadingMore.value = false
}

// 标记单个通知为已读
const markAsRead = async (notificationId) => {
  try {
    const response = await fetch(`https://api.searchsomething.top/api/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    if (response.ok) {
      // 更新本地通知状态
      const notification = notifications.value.find(n => n.id === notificationId)
      if (notification) {
        notification.is_read = true
      }
      
      // 立即获取最新的未读数量
      const countResponse = await fetch('https://api.searchsomething.top/api/notifications/unread-count', {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      })
      
      if (countResponse.ok) {
        const data = await countResponse.json()
        userStore.setUnreadCount(data.count)
      }
      
      // 强制更新视图
      notifications.value = [...notifications.value]
    } else {
      throw new Error('标记已读失败')
    }
  } catch (error) {
    console.error('标记已读失败:', error)
    ElMessage.error('标记已读失败')
  }
}

// 标记所有通知为已读
const markAllAsRead = async () => {
  try {
    const response = await fetch('https://api.searchsomething.top/api/notifications/read-all', {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    if (response.ok) {
      // 更新所有通知的状态
      notifications.value.forEach(notification => {
        notification.is_read = true
      })
      
      // 立即获取最新的未读数量
      const countResponse = await fetch('https://api.searchsomething.top/api/notifications/unread-count', {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      })
      
      if (countResponse.ok) {
        const data = await countResponse.json()
        userStore.setUnreadCount(data.count)
      }
      
      // 强制更新视图
      notifications.value = [...notifications.value]
      
      ElMessage.success('已全部标记为已读')
    } else {
      throw new Error('标记全部已读失败')
    }
  } catch (error) {
    console.error('标记全部已读失败:', error)
    ElMessage.error('标记全部已读失败')
  }
}

// 格式化时间
const formatTime = (timeStr) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚'
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  // 大于24小时
  return timeStr.split('T')[0]
}

// 点击通知跳转到目标
const goToTarget = (notification) => {
  // 如果是关注通知，跳转到用户主页
  if (notification.type === 'follow') {
    router.push(`/user/${notification.sender.id}`)
  } 
  // 如果有评论ID，跳转到对应的评论位置
  else if (notification.comment_id) {
    router.push(`/posts/${notification.post_id}#comment-${notification.comment_id}`)
  }
  // 如果只有帖子ID，跳转到帖子
  else if (notification.post_id) {
    router.push(`/posts/${notification.post_id}`)
  }

  // 标记通知为已读
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
}

// 初始化
onMounted(() => {
  // 重置页码并获取通知
  currentPage.value = 1
  fetchNotifications()
})
</script>

<style scoped>
.notification-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-item {
  padding: 16px;
  border-bottom: 1px solid #EBEEF5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.notification-item:hover {
  background-color: #F5F7FA;
}

.notification-item.unread {
  background-color: #ecf5ff;
}

.notification-item.follow {
  background-color: #f0f9ff;
}

.notification-content {
  font-size: 14px;
  line-height: 1.4;
}

.sender-name {
  color: #409EFF;
  font-weight: 500;
  text-decoration: none;
}

.sender-name:hover {
  text-decoration: underline;
}

.target-text {
  color: #606266;
}

.notification-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-time {
  color: #909399;
  font-size: 12px;
}

.no-notifications {
  text-align: center;
  padding: 40px 0;
  color: #909399;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}
</style> 