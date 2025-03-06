<template>
  <div class="home-container">
    <!-- 搜索框 -->
    <div class="search-container">
      <el-input
        v-model="searchQuery"
        placeholder="搜索帖子和用户"
        class="search-input"
        @keyup.enter="handleSearch"
      >
        <template #append>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card class="community-info">
          <template #header>
            <div class="card-header">
              <span>社区信息</span>
            </div>
          </template>
          <div class="info-container">
            <div class="info-item">
              <span class="info-value">{{ communityStats.userCount || 0 }}</span>
              <span class="info-label">社区成员</span>
            </div>
            <div class="info-item">
              <span class="info-value">{{ communityStats.postCount || 0 }}</span>
              <span class="info-label">帖子数量</span>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="18">
        <div class="posts-section">
          <div class="section-header">
            <div class="header-left">
              <h2>帖子列表</h2>
              <el-radio-group v-model="currentTab" @change="handleTabChange">
                <el-radio-button label="latest">最新帖子</el-radio-button>
                <el-radio-button label="hot">最热帖子</el-radio-button>
              </el-radio-group>
            </div>
            <el-button type="primary" @click="showCreateDialog = true">
              发布新帖子
            </el-button>
          </div>
          
          <post-list
            :posts="posts"
            :loading="loading"
            :has-more="hasMore"
            @refresh="refreshPosts"
            @load-more="loadMore"
          />
        </div>
      </el-col>
    </el-row>

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
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import PostList from '../components/PostList.vue'
import { Search } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const currentTab = ref('latest')
const loading = ref(false)
const posts = ref([])
const hasMore = ref(true)
const currentPage = ref(1)
const pageSize = 10

const communityStats = ref({
  userCount: 0,
  postCount: 0
})

const showCreateDialog = ref(false)
const postForm = ref({
  title: '',
  content: ''
})

const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在2-100个字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '内容长度在2-1000个字符之间', trigger: 'blur' }
  ]
}

const debug = ref(true) // 临时添加调试模式

const searchQuery = ref('')

const fetchPosts = async () => {
  try {
    loading.value = true
    console.log('【fetchPosts】开始获取帖子列表...', {
      page: currentPage.value,
      tab: currentTab.value,
      pageSize
    })
    
    const response = await fetch(
      `https://api.searchsomething.top/api/posts?page=${currentPage.value}&page_size=${pageSize}&sort_by=${currentTab.value}`,
      {
        headers: userStore.isLoggedIn ? { 'Authorization': userStore.getAuthHeader() } : {},
        cache: 'no-store'
      }
    )
    
    if (!response.ok) {
      throw new Error('获取帖子失败')
    }
    
    const data = await response.json()
    
    // 如果是第一页，直接替换数据
    // 如果不是第一页，则追加数据
    if (currentPage.value === 1) {
      posts.value = data.posts
    } else {
      posts.value = [...posts.value, ...data.posts]
    }
    
    hasMore.value = data.total > (currentPage.value * pageSize)
    
  } catch (error) {
    console.error('【fetchPosts】获取帖子失败:', error)
    ElMessage.error('获取帖子失败，请重新登录')
  } finally {
    loading.value = false
  }
}

const handleTabChange = async () => {
  console.log('【handleTabChange】切换标签:', currentTab.value)
  currentPage.value = 1
  posts.value = []
  await fetchPosts()
}

const refreshPosts = async () => {
  console.log('【refreshPosts】开始刷新帖子列表')
  currentPage.value = 1
  posts.value = []
  await fetchPosts()
  console.log('【refreshPosts】刷新完成')
}

const loadMore = () => {
  if (!loading.value && hasMore.value) {
    currentPage.value++
    fetchPosts()
  }
}

const fetchCommunityStats = async () => {
  try {
    const response = await fetch('https://api.searchsomething.top/api/community-stats')
    if (!response.ok) {
      throw new Error('获取社区统计失败')
    }
    const data = await response.json()
    communityStats.value = data
    console.log('社区统计数据:', data)  // 添加调试日志
  } catch (error) {
    console.error('获取社区统计失败:', error)
    ElMessage.error('获取社区统计失败')
  }
}

const submitPost = async () => {
  if (!postFormRef.value) return
  
  try {
    await postFormRef.value.validate()
    console.log('【submitPost】开始发布帖子:', {
      title: postForm.value.title,
      content: postForm.value.content
    })
    
    const response = await fetch('https://api.searchsomething.top/api/posts', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify({
        title: postForm.value.title.trim(),
        content: postForm.value.content.trim()
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.error || '发布失败')
    }
    
    console.log('【submitPost】发布成功，准备刷新列表')
    ElMessage.success('发布成功')
    showCreateDialog.value = false
    postForm.value.title = ''
    postForm.value.content = ''
    
    // 重置页码
    currentPage.value = 1
    // 强制刷新数据
    posts.value = []
    await fetchPosts()
    
    console.log('【submitPost】刷新完成，当前帖子列表:', {
      postsLength: posts.value.length,
      firstPost: posts.value[0]
    })
    
  } catch (error) {
    console.error('【submitPost】发布帖子失败:', error)
    ElMessage.error(error.message || '发布失败')
  }
}

// 添加 postFormRef
const postFormRef = ref(null)

// 检查滚动位置
const checkScroll = () => {
  // 获取滚动容器（文档或指定容器）的高度信息
  const scrollHeight = Math.max(
    document.documentElement.scrollHeight,
    document.body.scrollHeight
  )
  const scrollTop = Math.max(
    document.documentElement.scrollTop,
    document.body.scrollTop,
    window.scrollY
  )
  const clientHeight = document.documentElement.clientHeight
  
  // 提前 200px 触发加载，并确保当前没有正在加载的请求
  if (!loading.value && hasMore.value && (scrollHeight - scrollTop - clientHeight < 200)) {
    loadMore()
  }
}

// 优化节流函数的间隔时间
const throttle = (fn, delay) => {
  let lastCall = 0
  let timeout = null
  
  return function (...args) {
    const now = Date.now()
    
    // 清除之前的延迟执行
    if (timeout) {
      clearTimeout(timeout)
    }
    
    if (now - lastCall >= delay) {
      fn.apply(this, args)
      lastCall = now
    } else {
      // 如果距离上次执行还没到间隔时间，则延迟执行
      timeout = setTimeout(() => {
        fn.apply(this, args)
        lastCall = Date.now()
      }, delay)
    }
  }
}

// 减小节流时间间隔，使响应更及时
const throttledCheckScroll = throttle(checkScroll, 100)

const goToPostDetail = (postId) => {
  // 设置路由状态，标记来源为首页
  router.push({
    name: 'post-detail',
    params: { id: postId },
    state: { from: 'home' }
  })
}

// 处理搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    router.push({
      name: 'SearchResults',
      query: { q: searchQuery.value }
    });
  }
};

onMounted(async () => {
  console.log('【onMounted】组件挂载，开始获取数据')
  await fetchPosts()
  await fetchCommunityStats()
  window.addEventListener('scroll', throttledCheckScroll)
  // 添加 resize 事件监听，窗口大小改变时也检查是否需要加载
  window.addEventListener('resize', throttledCheckScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', throttledCheckScroll)
  window.removeEventListener('resize', throttledCheckScroll)
})
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.community-info {
  margin-bottom: 20px;
}

.card-header {
  font-weight: bold;
}

.info-container {
  display: flex;
  flex-direction: column;
  gap: 15px;
  padding: 0 20px;  /* 添加左右内边距 */
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: flex-start;  /* 向右对齐 */
  padding-left: 20px;  /* 额外的左边距 */
}

.info-value {
  font-size: 28px;  /* 增大字体 */
  font-weight: bold;
  color: #409EFF;
}

.info-label {
  font-size: 16px;  /* 增大字体 */
  color: #606266;
}

.posts-section {
  background: #fff;
  padding: 20px;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-left h2 {
  margin: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.search-container {
  margin: 20px auto;
  max-width: 600px;
  padding: 0 20px;
}

.search-input {
  width: 100%;
}
</style> 