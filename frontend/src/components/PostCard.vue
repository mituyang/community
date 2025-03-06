<template>
  <el-card class="post-card" shadow="hover">


    <div class="post-header">
      <h3 class="post-title" @click="goToPostDetail(post.id)">
        {{ post.title }}
      </h3>
    </div>
    <p class="post-content">{{ truncateContent(post.content) }}</p>
    <div class="post-footer">
      <div class="post-meta">
        <span>作者: {{ post.author }}</span>
        <span>发布时间: {{ post.created_at }}</span>
        <span>浏览: {{ post.view_count || 0 }}</span>
      </div>
      <div class="post-actions">
        <el-button 
          text 
          :class="{ 'is-active': post.isCommented }"
          @click="handleComment"
        >
          <el-icon><ChatLineRound /></el-icon>
          评论 {{ post.comment_count || 0 }}
        </el-button>
        <el-button 
          text 
          :class="{ 'is-active': post.isShared }"
          @click="handleShare"
        >
          <el-icon><Share /></el-icon>
          转发 {{ post.share_count || 0 }}
        </el-button>
        <el-button 
          text 
          :class="{ 'is-active': post.isLiked }"
          @click="handleLike"
        >
          <el-icon><Star /></el-icon>
          点赞 {{ post.like_count || 0 }}
        </el-button>
        
        <!-- 只在帖子属于当前用户时显示删除按钮 -->
        <el-button 
          v-if="isCurrentUserPost"
          text 
          type="danger"
          @click="handleDelete"
        >
          <el-icon><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <!-- 评论对话框 -->
    <el-dialog
      v-model="showCommentDialog"
      title="发表评论"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="commentForm" :rules="commentRules" ref="commentFormRef">
        <el-form-item prop="content">
          <el-input
            v-model="commentForm.content"
            type="textarea"
            :rows="3"
            placeholder="写下你的评论..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cancelComment">取消</el-button>
          <el-button type="primary" @click="submitComment" :loading="submitting">
            发表评论
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="showDeleteDialog"
      title="确认删除"
      width="300px"
    >
      <p>确定要删除这篇帖子吗？此操作不可恢复。</p>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDeleteDialog = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete" :loading="deleting">
            确定删除
          </el-button>
        </span>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatLineRound, Share, Star, Delete } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const props = defineProps({
  post: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const showCommentDialog = ref(false)
const showDeleteDialog = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const commentFormRef = ref(null)
const commentForm = ref({
  content: ''
})

const commentRules = {
  content: [
    { required: true, message: '请输入评论内容', trigger: 'blur' },
    { min: 2, max: 500, message: '评论长度在2到500个字符之间', trigger: 'blur' }
  ]
}

// 判断帖子是否属于当前用户
const isCurrentUserPost = computed(() => {
  return userStore.isLoggedIn && userStore.user && props.post.user_id === userStore.user.id
})

const goToPostDetail = (postId) => {
  router.push({
    path: `/posts/${postId}`,
    state: { fromList: true }
  })
}

const handleComment = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  showCommentDialog.value = true
}

const cancelComment = () => {
  commentForm.value.content = ''
  showCommentDialog.value = false
}

const handleShare = async (event) => {
  event.stopPropagation();
  
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/posts/${props.post.id}/share`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    const data = await response.json();
    console.log('转发API返回数据:', data);
    
    if (response.ok) {
      // 使用API返回的状态
      props.post.isShared = data.isShared;  // 使用isShared而不是is_shared
      props.post.share_count = data.shares_count;
      ElMessage.success(data.isShared ? '转发成功' : '已取消转发');
    } else {
      ElMessage.error(data.error || '操作失败');
    }
  } catch (error) {
    console.error('转发操作失败:', error);
    ElMessage.error('操作失败');
  }
};

const handleLike = async (event) => {
  event.stopPropagation();
  
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/posts/${props.post.id}/like`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    const data = await response.json();
    console.log('点赞API返回数据:', data);
    
    if (response.ok) {
      // 使用API返回的状态
      props.post.isLiked = data.isLiked;  // 使用isLiked而不是is_liked
      props.post.like_count = data.likes_count;
      ElMessage.success(data.isLiked ? '点赞成功' : '已取消点赞');
    } else {
      ElMessage.error(data.error || '操作失败');
    }
  } catch (error) {
    console.error('点赞操作失败:', error);
    ElMessage.error('操作失败');
  }
};

const handleDelete = () => {
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  try {
    deleting.value = true
    const response = await fetch(`https://api.searchsomething.top/api/posts/${props.post.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    if (response.ok) {
      ElMessage.success('删除成功')
      showDeleteDialog.value = false
      emit('refresh') // 通知父组件刷新列表
    } else {
      const data = await response.json()
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('删除帖子失败:', error)
    ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}

// 优化后的提交评论方法
const submitComment = async () => {
  if (!commentFormRef.value) return
  
  try {
    await commentFormRef.value.validate()
    submitting.value = true
    
    const response = await fetch(`https://api.searchsomething.top/api/posts/${props.post.id}/comment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify({
        content: commentForm.value.content.trim()
      })
    })
    
    const data = await response.json()
    if (response.ok) {
      props.post.comment_count = data.comment_count
      props.post.isCommented = true
      showCommentDialog.value = false
      commentForm.value.content = ''
      ElMessage.success('评论成功')
      emit('refresh') // 可选：刷新帖子列表以获取最新状态
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    } else {
      console.error('评论失败:', error)
      ElMessage.error('评论失败')
    }
  } finally {
    submitting.value = false
  }
}

const truncateContent = (content) => {
  if (!content) return ''
  return content.length > 100 ? content.slice(0, 100) + '...' : content
}
</script>

<style scoped>
.post-card {
  margin-bottom: 20px;
}

.post-header {
  margin-bottom: 10px;
}

.post-title {
  margin: 0;
  cursor: pointer;
  color: #303133;
}

.post-title:hover {
  color: #409EFF;
}

.post-content {
  color: #606266;
  margin: 10px 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.post-meta {
  display: flex;
  gap: 20px;
  color: #909399;
  font-size: 14px;
}

.post-actions {
  display: flex;
  gap: 20px;
}

.post-actions .el-button {
  display: flex;
  align-items: center;
  gap: 5px;
}

.post-actions .el-button.is-active {
  color: #409EFF;
  font-weight: bold;
}

.post-actions .el-button.el-button--danger {
  color: #F56C6C;
}

.post-actions .el-button.el-button--danger:hover {
  color: #f89898;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.debug-info {
  background: #f5f7fa;
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
}
</style> 