<template>
  <div class="my-posts-container">
    <el-tabs v-model="activeTab" @tab-click="handleTabClick">
      <el-tab-pane label="我的帖子" name="posts">
        <div class="page-header">
          <h2>我的帖子</h2>
          <el-button type="primary" @click="showCreateDialog = true">
            发布新帖子
          </el-button>
        </div>

        <div class="posts-list" v-loading="loading">
          <el-empty v-if="posts.length === 0" description="暂无帖子" />
          <el-card v-else v-for="post in posts" :key="post.id" class="post-card">
            <div class="post-header">
              <h3 class="post-title" @click="goToPost(post.id)">{{ post.title }}</h3>
            </div>
            <p class="post-content">{{ post.content }}</p>
            <div class="post-footer">
              <div class="post-meta">
                <span>发布时间: {{ post.created_at }}</span>
                <span>浏览: {{ post.view_count || 0 }}</span>
                <span>评论: {{ post.comment_count || 0 }}</span>
                <span>点赞: {{ post.like_count || 0 }}</span>
                <span>转发: {{ post.share_count || 0 }}</span>
              </div>
              <div class="post-actions">
                <el-button 
                  type="danger" 
                  text
                  @click="handleDelete(post.id)"
                >
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </div>
            </div>
          </el-card>
          <div v-if="hasMore" class="load-more">
            <el-button text @click="loadMore">加载更多</el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的评论" name="comments">
        <div class="comments-list" v-loading="loadingComments">
          <el-empty v-if="comments.length === 0" description="暂无评论" />
          <el-card v-else v-for="comment in comments" :key="comment.id" class="comment-card">
            <div class="comment-content">{{ comment.content }}</div>
            <div class="comment-meta">
              <div class="post-info">
                评论于：<el-link type="primary" @click="goToPost(comment.post_id)">{{ comment.post_title }}</el-link>
                <span class="post-author">作者：{{ comment.post_author }}</span>
              </div>
              <div class="comment-time">{{ comment.created_at }}</div>
            </div>
          </el-card>
          <div v-if="hasMoreComments" class="load-more">
            <el-button text @click="loadMoreComments">加载更多</el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的点赞" name="likes">
        <div class="likes-list" v-loading="loadingLikes">
          <el-empty v-if="likes.length === 0" description="暂无点赞" />
          <el-card v-else v-for="like in likes" :key="like.id" class="like-card">
            <div class="like-meta">
              <div class="post-info">
                点赞了：<el-link type="primary" @click="goToPost(like.post_id)">{{ like.post_title }}</el-link>
                <span class="post-author">作者：{{ like.post_author }}</span>
              </div>
              <div class="like-time">{{ like.created_at }}</div>
            </div>
          </el-card>
          <div v-if="hasMoreLikes" class="load-more">
            <el-button text @click="loadMoreLikes">加载更多</el-button>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的转发" name="shares">
        <div class="shares-list" v-loading="loadingShares">
          <el-empty v-if="shares.length === 0" description="暂无转发" />
          <el-card v-else v-for="share in shares" :key="share.id" class="share-card">
            <div class="share-meta">
              <div class="post-info">
                转发了：<el-link type="primary" @click="goToPost(share.post_id)">{{ share.post_title }}</el-link>
                <span class="post-author">作者：{{ share.post_author }}</span>
              </div>
              <div class="share-time">{{ share.created_at }}</div>
            </div>
          </el-card>
          <div v-if="hasMoreShares" class="load-more">
            <el-button text @click="loadMoreShares">加载更多</el-button>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 发帖对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="发布新帖子"
      width="500px"
    >
      <el-form :model="postForm" :rules="rules" ref="postFormRef">
        <el-form-item prop="title" label="标题">
          <el-input v-model="postForm.title" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item prop="content" label="内容">
          <el-input
            v-model="postForm.content"
            type="textarea"
            :rows="6"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">取消</el-button>
          <el-button type="primary" @click="submitPost">发布</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('posts')
const loading = ref(false)
const loadingComments = ref(false)
const loadingLikes = ref(false)
const loadingShares = ref(false)

const posts = ref([])
const comments = ref([])
const likes = ref([])
const shares = ref([])

const hasMore = ref(true)
const hasMoreComments = ref(true)
const hasMoreLikes = ref(true)
const hasMoreShares = ref(true)

const currentPage = ref(1)
const commentsPage = ref(1)
const likesPage = ref(1)
const sharesPage = ref(1)

const pageSize = 10
const showCreateDialog = ref(false)
const postForm = ref({
  title: '',
  content: ''
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在2到100个字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '内容长度在2到1000个字符之间', trigger: 'blur' }
  ]
}

const fetchMyPosts = async () => {
  if (loading.value || !hasMore.value) return
  
  try {
    loading.value = true
    const response = await fetch(
      `https://api.searchsomething.top/api/users/posts?page=${currentPage.value}&page_size=${pageSize.value}`,
      {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      }
    )
    const data = await response.json()
    if (response.ok) {
      if (currentPage.value === 1) {
        posts.value = data.posts
      } else {
        posts.value = [...posts.value, ...data.posts]
      }
      hasMore.value = data.posts.length === pageSize.value
      currentPage.value++
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('获取我的帖子失败:', error)
    ElMessage.error('获取帖子列表失败')
  } finally {
    loading.value = false
  }
}

const refreshPosts = () => {
  currentPage.value = 1
  hasMore.value = true
  fetchMyPosts()
}

const submitPost = async () => {
  try {
    const response = await fetch('https://api.searchsomething.top/api/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify(postForm.value)
    })
    
    const data = await response.json()
    if (response.ok) {
      ElMessage.success('发布成功')
      showCreateDialog.value = false
      postForm.value = { title: '', content: '' }
      refreshPosts()
    } else {
      throw new Error(data.error)
    }
  } catch (error) {
    console.error('发布帖子失败:', error)
    ElMessage.error('发布失败')
  }
}

const fetchComments = async () => {
  try {
    loadingComments.value = true
    const response = await fetch(
      `https://api.searchsomething.top/api/users/${userStore.user.id}/comments?page=${commentsPage.value}&per_page=${pageSize}`,
      {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      }
    )
    
    if (!response.ok) {
      throw new Error('获取评论失败')
    }
    
    const data = await response.json()
    if (commentsPage.value === 1) {
      comments.value = data.comments
    } else {
      comments.value = [...comments.value, ...data.comments]
    }
    
    hasMoreComments.value = comments.value.length < data.total
  } catch (error) {
    console.error('获取评论失败:', error)
    ElMessage.error('获取评论失败')
  } finally {
    loadingComments.value = false
  }
}

const fetchLikes = async () => {
  try {
    loadingLikes.value = true
    const response = await fetch(
      `https://api.searchsomething.top/api/users/${userStore.user.id}/likes?page=${likesPage.value}&per_page=${pageSize}`,
      {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      }
    )
    
    if (!response.ok) {
      throw new Error('获取点赞失败')
    }
    
    const data = await response.json()
    if (likesPage.value === 1) {
      likes.value = data.likes
    } else {
      likes.value = [...likes.value, ...data.likes]
    }
    
    hasMoreLikes.value = likes.value.length < data.total
  } catch (error) {
    console.error('获取点赞失败:', error)
    ElMessage.error('获取点赞失败')
  } finally {
    loadingLikes.value = false
  }
}

const fetchShares = async () => {
  try {
    loadingShares.value = true
    const response = await fetch(
      `https://api.searchsomething.top/api/users/${userStore.user.id}/shares?page=${sharesPage.value}&per_page=${pageSize}`,
      {
        headers: {
          'Authorization': userStore.getAuthHeader()
        }
      }
    )
    
    if (!response.ok) {
      throw new Error('获取转发失败')
    }
    
    const data = await response.json()
    if (sharesPage.value === 1) {
      shares.value = data.shares
    } else {
      shares.value = [...shares.value, ...data.shares]
    }
    
    hasMoreShares.value = shares.value.length < data.total
  } catch (error) {
    console.error('获取转发失败:', error)
    ElMessage.error('获取转发失败')
  } finally {
    loadingShares.value = false
  }
}

const loadMoreComments = () => {
  commentsPage.value++
  fetchComments()
}

const loadMoreLikes = () => {
  likesPage.value++
  fetchLikes()
}

const loadMoreShares = () => {
  sharesPage.value++
  fetchShares()
}

const handleTabClick = () => {
  switch (activeTab.value) {
    case 'comments':
      if (comments.value.length === 0) fetchComments()
      break
    case 'likes':
      if (likes.value.length === 0) fetchLikes()
      break
    case 'shares':
      if (shares.value.length === 0) fetchShares()
      break
  }
}

const goToPost = (postId) => {
  router.push(`/posts/${postId}`)
}

const handleDelete = async (postId) => {
  try {
    await ElMessageBox.confirm('确定要删除这篇帖子吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    const response = await fetch(`https://api.searchsomething.top/api/posts/${postId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })

    if (!response.ok) {
      throw new Error('删除失败')
    }

    ElMessage.success('删除成功')
    refreshPosts() // 刷新帖子列表
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除帖子失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

// 检查滚动位置
const checkScroll = () => {
  const scrollHeight = document.documentElement.scrollHeight
  const scrollTop = window.scrollY
  const clientHeight = document.documentElement.clientHeight
  
  if (scrollHeight - scrollTop - clientHeight < 100) {
    fetchMyPosts()
  }
}

const throttle = (fn, delay) => {
  let lastCall = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastCall >= delay) {
      fn.apply(this, args)
      lastCall = now
    }
  }
}

const throttledCheckScroll = throttle(checkScroll, 200)

onMounted(() => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  fetchMyPosts()
  window.addEventListener('scroll', throttledCheckScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', throttledCheckScroll)
})
</script>

<style scoped>
.my-posts-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

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
  gap: 10px;
}

.post-actions .el-button {
  display: flex;
  align-items: center;
  gap: 5px;
}

.comment-card,
.like-card,
.share-card {
  margin-bottom: 15px;
}

.comment-content {
  color: #303133;
  margin-bottom: 10px;
}

.comment-meta,
.like-meta,
.share-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #909399;
  font-size: 14px;
}

.post-info {
  display: flex;
  gap: 10px;
  align-items: center;
}

.post-author {
  color: #606266;
}

.load-more {
  text-align: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 
