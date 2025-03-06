<template>
  <div class="user-profile-container">
    <!-- 用户资料卡片 -->
    <el-card class="profile-card">
      <template #header>
        <div class="card-header">
          <h2>{{ isCurrentUser ? '个人主页' : `${userData?.username || '用户'} 的主页` }}</h2>
          <div class="header-actions">
            <!-- 如果是当前用户查看自己的主页，显示编辑按钮 -->
            <el-button v-if="isCurrentUser" type="primary" @click="goToEditProfile">编辑资料</el-button>
            
            <!-- 如果是查看其他用户的主页，显示关注/取消关注按钮 -->
            <el-button 
              v-else-if="userStore.isLoggedIn()" 
              :type="isFollowing ? 'info' : 'primary'" 
              @click="toggleFollow"
            >
              {{ isFollowing ? '已关注' : '关注' }}
            </el-button>
            
            <!-- 未登录用户查看他人主页，显示需要登录的关注按钮 -->
            <el-button 
              v-else 
              type="primary" 
              @click="router.push('/login')"
            >
              关注
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="loading" class="loading">
        <el-skeleton :rows="10" animated />
      </div>
      
      <div v-else-if="error" class="error">
        {{ error }}
      </div>
      
      <div v-else-if="userData" class="profile-info">
        <div class="avatar-section">
          <el-avatar 
            :size="100" 
            :src="userData.avatar || 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'"
          />
          <h2 class="user-name">{{ userData.username }}</h2>
          <p v-if="userData.nickname" class="user-nickname">{{ userData.nickname }}</p>
        </div>

        <div class="user-stats">
          <div class="stat-item">
            <div class="stat-number">{{ userData.post_count || 0 }}</div>
            <div class="stat-label">帖子</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ userData.follower_count || 0 }}</div>
            <div class="stat-label">粉丝</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ userData.following_count || 0 }}</div>
            <div class="stat-label">关注</div>
          </div>
        </div>

        <div v-if="userData.bio" class="user-bio">
          <p>{{ userData.bio }}</p>
        </div>

        <div class="user-details">
          <div class="detail-item" v-if="userData.location">
            <el-icon><Location /></el-icon>
            <span>{{ userData.location }}</span>
          </div>
          <div class="detail-item" v-if="userData.website">
            <el-icon><Link /></el-icon>
            <a :href="userData.website" target="_blank">{{ userData.website }}</a>
          </div>
          <div class="detail-item">
            <el-icon><Calendar /></el-icon>
            <span>加入于 {{ formatDate(userData.created_at) }}</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 用户内容选项卡 -->
    <el-card class="content-card">
      <el-tabs v-model="activeTab" @tab-click="handleTabClick">
        <!-- 帖子选项卡 -->
        <el-tab-pane label="帖子" name="posts">
          <div class="tab-header" v-if="isCurrentUser">
            <el-button type="primary" @click="showCreateDialog = true">
              发布新帖子
            </el-button>
          </div>

          <div class="posts-list" v-loading="loadingPosts">
            <el-empty v-if="posts.length === 0" description="暂无帖子" />
            <el-card v-else v-for="post in posts" :key="post.id" class="post-card">
              <div class="post-header">
                <h3 class="post-title" @click="goToPost(post.id)">{{ post.title }}</h3>
              </div>
              <p class="post-content">{{ truncateContent(post.content) }}</p>
              <div class="post-footer">
                <div class="post-meta">
                  <span>发布时间: {{ formatTime(post.created_at) }}</span>
                  <span>浏览: {{ post.view_count || 0 }}</span>
                  <span>评论: {{ post.comment_count || 0 }}</span>
                  <span>点赞: {{ post.like_count || 0 }}</span>
                </div>
                <div class="post-actions" v-if="isCurrentUser">
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
            
            <div v-if="hasMorePosts" class="load-more">
              <el-button text @click="loadMorePosts">加载更多</el-button>
            </div>
          </div>
        </el-tab-pane>

        <!-- 仅当查看自己的主页时显示以下选项卡 -->
        <template v-if="isCurrentUser">
          <!-- 评论选项卡 -->
          <el-tab-pane label="评论" name="comments">
            <div class="comments-list" v-loading="loadingComments">
              <el-empty v-if="comments.length === 0" description="暂无评论" />
              <el-card v-else v-for="comment in comments" :key="comment.id" class="comment-card">
                <div class="comment-content">{{ comment.content }}</div>
                <div class="comment-meta">
                  <div class="post-info">
                    评论于：<el-link type="primary" @click="goToPost(comment.post_id)">{{ comment.post_title }}</el-link>
                    <span class="post-author">作者：{{ comment.post_author }}</span>
                  </div>
                  <div class="comment-time">{{ formatTime(comment.created_at) }}</div>
                </div>
              </el-card>
              
              <div v-if="hasMoreComments" class="load-more">
                <el-button text @click="loadMoreComments">加载更多</el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 点赞选项卡 -->
          <el-tab-pane label="点赞" name="likes">
            <div class="likes-list" v-loading="loadingLikes">
              <el-empty v-if="likes.length === 0" description="暂无点赞" />
              <el-card v-else v-for="like in likes" :key="like.id" class="like-card">
                <div class="like-meta">
                  <div class="post-info">
                    点赞了：<el-link type="primary" @click="goToPost(like.post_id)">{{ like.post_title }}</el-link>
                    <span class="post-author">作者：{{ like.post_author }}</span>
                  </div>
                  <div class="like-time">{{ formatTime(like.created_at) }}</div>
                </div>
              </el-card>
              
              <div v-if="hasMoreLikes" class="load-more">
                <el-button text @click="loadMoreLikes">加载更多</el-button>
              </div>
            </div>
          </el-tab-pane>

          <!-- 转发选项卡 -->
          <el-tab-pane label="转发" name="shares">
            <div class="shares-list" v-loading="loadingShares">
              <el-empty v-if="shares.length === 0" description="暂无转发" />
              <el-card v-else v-for="share in shares" :key="share.id" class="share-card">
                <div class="share-meta">
                  <div class="post-info">
                    转发了：<el-link type="primary" @click="goToPost(share.post_id)">{{ share.post_title }}</el-link>
                    <span class="post-author">作者：{{ share.post_author }}</span>
                  </div>
                  <div class="share-time">{{ formatTime(share.created_at) }}</div>
                </div>
              </el-card>
              
              <div v-if="hasMoreShares" class="load-more">
                <el-button text @click="loadMoreShares">加载更多</el-button>
              </div>
            </div>
          </el-tab-pane>
        </template>
      </el-tabs>
    </el-card>

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
import { ref, onMounted, computed, watch, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useUserStore } from '../stores/user';
import axios from 'axios';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Location, Link, Calendar, Delete } from '@element-plus/icons-vue';

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const postFormRef = ref(null);

// 后端API基础URL
const backendUrl = 'https://api.searchsomething.top';

// 用户数据
const userId = computed(() => route.params.id);
const userData = ref(null);
const loading = ref(true);
const error = ref('');
const isFollowing = ref(false);

// 选项卡状态
const activeTab = ref('posts');

// 帖子数据
const posts = ref([]);
const loadingPosts = ref(false);
const hasMorePosts = ref(true);
const currentPage = ref(1);

// 评论数据
const comments = ref([]);
const loadingComments = ref(false);
const hasMoreComments = ref(true);
const commentsPage = ref(1);

// 点赞数据
const likes = ref([]);
const loadingLikes = ref(false);
const hasMoreLikes = ref(true);
const likesPage = ref(1);

// 转发数据
const shares = ref([]);
const loadingShares = ref(false);
const hasMoreShares = ref(true);
const sharesPage = ref(1);

const perPage = ref(10);
const showCreateDialog = ref(false);
const postForm = ref({
  title: '',
  content: ''
});

// 表单验证规则
const rules = {
  title: [
    { required: true, message: '请输入标题', trigger: 'blur' },
    { min: 2, max: 100, message: '标题长度在2到100个字符之间', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入内容', trigger: 'blur' },
    { min: 2, max: 1000, message: '内容长度在2到1000个字符之间', trigger: 'blur' }
  ]
};

// 是否是当前登录用户
const isCurrentUser = computed(() => {
  return userStore.isLoggedIn() && userStore.user.id === parseInt(userId.value);
});

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '未知';
  const date = new Date(dateString);
  return date.toLocaleDateString('zh-CN');
};

// 截断内容
const truncateContent = (content) => {
  if (!content) return '';
  // 移除HTML标签
  const plainText = content.replace(/<[^>]+>/g, '');
  return plainText.length > 100 ? plainText.substring(0, 100) + '...' : plainText;
};

// 格式化时间
const formatTime = (time) => {
  if (!time) return '';
  const date = new Date(time);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 获取用户信息
const fetchUserData = async () => {
  loading.value = true;
  error.value = '';
  userData.value = null;
  
  try {
    console.log(`开始请求用户数据: ${backendUrl}/api/users/${userId.value}`);
    const response = await axios.get(`${backendUrl}/api/users/${userId.value}`);
    console.log('用户数据API响应:', response);
    
    if (response.data && response.data.user) {
      userData.value = response.data.user;
      isFollowing.value = response.data.is_following;
    } else {
      error.value = '获取用户数据格式不正确';
      console.error('API返回的数据格式不正确:', response.data);
    }
  } catch (err) {
    console.error('获取用户信息失败:', err);
    // 显示更详细的错误信息
    if (err.response) {
      console.error('状态码:', err.response.status);
      console.error('响应数据:', err.response.data);
      error.value = `错误 ${err.response.status}: ${err.response.data.error || '服务器错误'}`;
    } else if (err.request) {
      console.error('请求已发送但没有收到响应:', err.request);
      error.value = '无法连接到服务器，请检查网络或后端服务是否运行';
    } else {
      console.error('请求配置错误:', err.message);
      error.value = `请求错误: ${err.message}`;
    }
  } finally {
    loading.value = false;
  }
};

// 获取用户发布的帖子
const fetchUserPosts = async (refresh = false) => {
  if (loadingPosts.value || (!hasMorePosts.value && !refresh)) return;
  
  if (refresh) {
    currentPage.value = 1;
    hasMorePosts.value = true;
    posts.value = [];
  }
  
  loadingPosts.value = true;
  
  try {
    // 构建API路径
    let apiPath = isCurrentUser.value 
      ? `${backendUrl}/api/users/posts` // 当前用户查看自己的帖子
      : `${backendUrl}/api/users/${userId.value}/posts`; // 查看其他用户的帖子
    
    const params = {
      page: currentPage.value,
      per_page: perPage.value
    };
    
    const headers = userStore.isLoggedIn() 
      ? { 'Authorization': `Bearer ${userStore.token}` } 
      : {};
    
    const response = await axios.get(apiPath, { params, headers });
    
    console.log('帖子API响应:', response);
    
    if (currentPage.value === 1) {
      posts.value = response.data.posts || [];
    } else {
      posts.value = [...posts.value, ...(response.data.posts || [])];
    }
    
    hasMorePosts.value = response.data.has_more || false;
    currentPage.value++;
  } catch (err) {
    console.error('获取用户帖子失败:', err);
    ElMessage.error('获取帖子列表失败');
  } finally {
    loadingPosts.value = false;
  }
};

// 加载更多帖子
const loadMorePosts = () => {
  fetchUserPosts();
};

// 我的评论获取
const fetchMyComments = async () => {
  if (loadingComments.value) return;
  
  loadingComments.value = true;
  
  try {
    const response = await axios.get(`${backendUrl}/api/users/comments`, {
      params: {
        page: commentsPage.value,
        per_page: perPage.value
      },
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    console.log('评论API响应:', response);
    
    if (commentsPage.value === 1) {
      comments.value = response.data.comments || [];
    } else {
      comments.value = [...comments.value, ...(response.data.comments || [])];
    }
    
    hasMoreComments.value = response.data.has_more || false;
  } catch (err) {
    console.error('获取评论失败:', err);
    ElMessage.error('获取评论失败');
  } finally {
    loadingComments.value = false;
  }
};

// 加载更多评论
const loadMoreComments = () => {
  commentsPage.value++;
  fetchMyComments();
};

// 我的点赞获取
const fetchMyLikes = async () => {
  if (loadingLikes.value) return;
  
  loadingLikes.value = true;
  
  try {
    const response = await axios.get(`${backendUrl}/api/users/likes`, {
      params: {
        page: likesPage.value,
        per_page: perPage.value
      },
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    console.log('点赞API响应:', response);
    
    if (likesPage.value === 1) {
      likes.value = response.data.likes || [];
    } else {
      likes.value = [...likes.value, ...(response.data.likes || [])];
    }
    
    hasMoreLikes.value = response.data.has_more || false;
  } catch (err) {
    console.error('获取点赞失败:', err);
    ElMessage.error('获取点赞失败');
  } finally {
    loadingLikes.value = false;
  }
};

// 加载更多点赞
const loadMoreLikes = () => {
  likesPage.value++;
  fetchMyLikes();
};

// 我的转发获取
const fetchMyShares = async () => {
  if (loadingShares.value) return;
  
  loadingShares.value = true;
  
  try {
    const response = await axios.get(`${backendUrl}/api/users/shares`, {
      params: {
        page: sharesPage.value,
        per_page: perPage.value
      },
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    console.log('转发API响应:', response);
    
    if (sharesPage.value === 1) {
      shares.value = response.data.shares || [];
    } else {
      shares.value = [...shares.value, ...(response.data.shares || [])];
    }
    
    hasMoreShares.value = response.data.has_more || false;
  } catch (err) {
    console.error('获取转发失败:', err);
    ElMessage.error('获取转发失败');
  } finally {
    loadingShares.value = false;
  }
};

// 加载更多转发
const loadMoreShares = () => {
  sharesPage.value++;
  fetchMyShares();
};

// 处理选项卡切换
const handleTabClick = () => {
  if (!isCurrentUser.value) return;
  
  switch (activeTab.value) {
    case 'comments':
      if (comments.value.length === 0) fetchMyComments();
      break;
    case 'likes':
      if (likes.value.length === 0) fetchMyLikes();
      break;
    case 'shares':
      if (shares.value.length === 0) fetchMyShares();
      break;
  }
};

// 跳转到帖子详情
const goToPost = (postId) => {
  router.push(`/posts/${postId}`);
};

// 删除帖子
const handleDelete = async (postId) => {
  try {
    await ElMessageBox.confirm('确定要删除这篇帖子吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    const response = await axios.delete(`${backendUrl}/api/posts/${postId}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });

    ElMessage.success('删除成功');
    fetchUserPosts(true); // 刷新帖子列表
  } catch (err) {
    if (err !== 'cancel') {
      console.error('删除帖子失败:', err);
      ElMessage.error('删除失败');
    }
  }
};

// 发布新帖子
const submitPost = async () => {
  try {
    await postFormRef.value.validate();
    
    const response = await axios.post(`${backendUrl}/api/posts`, postForm.value, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    ElMessage.success('发布成功');
    showCreateDialog.value = false;
    postForm.value = { title: '', content: '' };
    fetchUserPosts(true); // 刷新帖子列表
  } catch (err) {
    if (err !== 'cancel') {
      console.error('发布帖子失败:', err);
      ElMessage.error('发布失败');
    }
  }
};

// 跳转到编辑个人资料页面
const goToEditProfile = () => {
  router.push('/settings/profile');
};

// 关注/取消关注用户
const toggleFollow = async () => {
  if (!userStore.isLoggedIn()) {
    router.push('/login');
    return;
  }
  
  try {
    const endpoint = isFollowing.value 
      ? `${backendUrl}/api/users/${userId.value}/unfollow` 
      : `${backendUrl}/api/users/${userId.value}/follow`;
      
    const response = await axios.post(endpoint, {}, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    });
    
    isFollowing.value = !isFollowing.value;
    if (userData.value) {
      userData.value.follower_count = response.data.follower_count;
    }
    
    ElMessage.success(isFollowing.value ? '关注成功' : '取消关注成功');
  } catch (err) {
    console.error('关注/取消关注操作失败:', err);
    ElMessage.error(err.response?.data?.error || '操作失败');
  }
};

// 检查滚动位置加载更多
const checkScroll = () => {
  const scrollHeight = document.documentElement.scrollHeight;
  const scrollTop = window.scrollY;
  const clientHeight = document.documentElement.clientHeight;
  
  if (scrollHeight - scrollTop - clientHeight < 100) {
    if (activeTab.value === 'posts') {
      loadMorePosts();
    }
  }
};

// 节流函数
const throttle = (fn, delay) => {
  let lastCall = 0;
  return function (...args) {
    const now = Date.now();
    if (now - lastCall >= delay) {
      fn.apply(this, args);
      lastCall = now;
    }
  };
};

const throttledCheckScroll = throttle(checkScroll, 200);

// 在组件挂载时获取数据
onMounted(() => {
  fetchUserData();
  fetchUserPosts();
  window.addEventListener('scroll', throttledCheckScroll);
});

// 移除事件监听
onUnmounted(() => {
  window.removeEventListener('scroll', throttledCheckScroll);
});

// 当用户ID变化时重新获取数据
watch(() => userId.value, () => {
  fetchUserData();
  currentPage.value = 1;
  fetchUserPosts(true);
  
  // 如果是当前用户并且选项卡已激活，也重新获取其他数据
  if (isCurrentUser.value) {
    if (activeTab.value === 'comments') {
      commentsPage.value = 1;
      fetchMyComments();
    } else if (activeTab.value === 'likes') {
      likesPage.value = 1;
      fetchMyLikes();
    } else if (activeTab.value === 'shares') {
      sharesPage.value = 1;
      fetchMyShares();
    }
  }
});
</script>

<style scoped>
.user-profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.profile-card {
  margin-bottom: 20px;
}

.content-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.user-name {
  margin: 10px 0 5px;
  font-size: 22px;
}

.user-nickname {
  margin: 0;
  color: #606266;
  font-size: 16px;
}

.user-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
  margin: 20px 0;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.user-bio {
  margin: 15px 0;
  text-align: center;
  color: #303133;
  line-height: 1.5;
}

.user-details {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #606266;
}

.tab-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 15px;
}

.post-card, .comment-card, .like-card, .share-card {
  margin-bottom: 15px;
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
  line-height: 1.6;
}

.post-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 15px;
}

.post-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  color: #909399;
  font-size: 14px;
}

.post-actions {
  display: flex;
  gap: 10px;
}

.comment-content {
  color: #303133;
  margin-bottom: 10px;
}

.comment-meta, .like-meta, .share-meta {
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

.loading {
  padding: 20px 0;
}

.error {
  color: #f56c6c;
  text-align: center;
  padding: 20px;
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
