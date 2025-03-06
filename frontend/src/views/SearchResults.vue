<template>
  <div class="search-results-container">
    <!-- 搜索框 -->
    <div class="search-header">
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

    <!-- 搜索结果 -->
    <div class="search-results" v-if="searchQuery">
      <el-tabs v-model="activeTab" class="search-tabs">
        <el-tab-pane label="热门" name="hot">
          <div v-if="loading.hot" class="tab-loading">加载中...</div>
          <post-list
            v-else
            :posts="results.hot"
            :loading="loading.hot"
            :has-more="hasMore.hot"
            @refresh="fetchHotResults"
            @load-more="loadMoreHotResults"
          />
          <el-empty v-if="!loading.hot && results.hot.length === 0" description="没有找到相关帖子" />
        </el-tab-pane>
        
        <el-tab-pane label="最新" name="latest">
          <div v-if="loading.latest" class="tab-loading">加载中...</div>
          <post-list
            v-else
            :posts="results.latest"
            :loading="loading.latest"
            :has-more="hasMore.latest"
            @refresh="fetchLatestResults"
            @load-more="loadMoreLatestResults"
          />
          <el-empty v-if="!loading.latest && results.latest.length === 0" description="没有找到相关帖子" />
        </el-tab-pane>
        
        <el-tab-pane label="用户" name="users">
          <div v-if="loading.users" class="tab-loading">加载中...</div>
          <div v-else class="user-results">
            <div v-for="user in results.users" :key="user.id" class="user-card">
              <div class="user-avatar">
                <el-avatar :size="50" :src="user.avatar || 'https://via.placeholder.com/50'"></el-avatar>
              </div>
              <div class="user-info">
                <h3 class="user-name">{{ user.username }}</h3>
                <p class="user-bio">{{ user.bio || '这个用户很懒，还没有写简介' }}</p>
              </div>
              <div class="user-action">
                <el-button type="primary" size="small" @click="goToUserProfile(user.id)">查看主页</el-button>
              </div>
            </div>
            <el-empty v-if="results.users.length === 0" description="没有找到相关用户" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Search } from '@element-plus/icons-vue';
import PostList from '../components/PostList.vue';
import { ElMessage } from 'element-plus';

const route = useRoute();
const router = useRouter();
const searchQuery = ref('');
const activeTab = ref('hot');

// 搜索结果
const results = reactive({
  hot: [],
  latest: [],
  users: []
});

// 加载状态
const loading = reactive({
  hot: false,
  latest: false,
  users: false
});

// 是否有更多结果
const hasMore = reactive({
  hot: false,
  latest: false
});

// 分页参数
const page = reactive({
  hot: 1,
  latest: 1,
  users: 1
});

// 初始化
onMounted(() => {
  if (route.query.q) {
    searchQuery.value = route.query.q;
    fetchResults();
  }
});

// 监听路由变化
watch(() => route.query.q, (newVal) => {
  if (newVal) {
    searchQuery.value = newVal;
    fetchResults();
  }
});

// 处理新搜索
const handleSearch = () => {
  if (searchQuery.value.trim()) {
    // 重置页码
    page.hot = 1;
    page.latest = 1;
    page.users = 1;
    
    // 更新URL但不重新加载页面
    router.replace({
      query: { q: searchQuery.value }
    });
    
    // 获取搜索结果
    fetchResults();
  }
};

// 获取搜索结果
const fetchResults = () => {
  fetchHotResults();
  fetchLatestResults();
  fetchUserResults();
};

// 获取热门帖子
const fetchHotResults = async () => {
  if (!searchQuery.value.trim()) return;
  
  loading.hot = true;
  page.hot = 1;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/search/posts?q=${encodeURIComponent(searchQuery.value)}&sort=hot&page=${page.hot}`);
    const data = await response.json();
    
    if (response.ok) {
      results.hot = data.posts;
      hasMore.hot = data.has_more;
    } else {
      ElMessage.error(data.error || '获取热门搜索结果失败');
    }
  } catch (error) {
    console.error('获取热门搜索结果出错:', error);
    ElMessage.error('获取热门搜索结果失败');
  } finally {
    loading.hot = false;
  }
};

// 加载更多热门帖子
const loadMoreHotResults = async () => {
  if (loading.hot || !hasMore.hot) return;
  
  loading.hot = true;
  page.hot++;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/search/posts?q=${encodeURIComponent(searchQuery.value)}&sort=hot&page=${page.hot}`);
    const data = await response.json();
    
    if (response.ok) {
      results.hot = [...results.hot, ...data.posts];
      hasMore.hot = data.has_more;
    } else {
      ElMessage.error(data.error || '加载更多热门搜索结果失败');
    }
  } catch (error) {
    console.error('加载更多热门搜索结果出错:', error);
    ElMessage.error('加载更多热门搜索结果失败');
  } finally {
    loading.hot = false;
  }
};

// 获取最新帖子
const fetchLatestResults = async () => {
  if (!searchQuery.value.trim()) return;
  
  loading.latest = true;
  page.latest = 1;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/search/posts?q=${encodeURIComponent(searchQuery.value)}&sort=latest&page=${page.latest}`);
    const data = await response.json();
    
    if (response.ok) {
      results.latest = data.posts;
      hasMore.latest = data.has_more;
    } else {
      ElMessage.error(data.error || '获取最新搜索结果失败');
    }
  } catch (error) {
    console.error('获取最新搜索结果出错:', error);
    ElMessage.error('获取最新搜索结果失败');
  } finally {
    loading.latest = false;
  }
};

// 加载更多最新帖子
const loadMoreLatestResults = async () => {
  if (loading.latest || !hasMore.latest) return;
  
  loading.latest = true;
  page.latest++;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/search/posts?q=${encodeURIComponent(searchQuery.value)}&sort=latest&page=${page.latest}`);
    const data = await response.json();
    
    if (response.ok) {
      results.latest = [...results.latest, ...data.posts];
      hasMore.latest = data.has_more;
    } else {
      ElMessage.error(data.error || '加载更多最新搜索结果失败');
    }
  } catch (error) {
    console.error('加载更多最新搜索结果出错:', error);
    ElMessage.error('加载更多最新搜索结果失败');
  } finally {
    loading.latest = false;
  }
};

// 获取用户搜索结果
const fetchUserResults = async () => {
  if (!searchQuery.value.trim()) return;
  
  loading.users = true;
  page.users = 1;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/search/users?q=${encodeURIComponent(searchQuery.value)}&page=${page.users}`);
    const data = await response.json();
    
    if (response.ok) {
      results.users = data.users;
    } else {
      ElMessage.error(data.error || '获取用户搜索结果失败');
    }
  } catch (error) {
    console.error('获取用户搜索结果出错:', error);
    ElMessage.error('获取用户搜索结果失败');
  } finally {
    loading.users = false;
  }
};

// 跳转到用户主页
const goToUserProfile = (userId) => {
  router.push(`/user/${userId}`);
};
</script>

<style scoped>
.search-results-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.search-header {
  margin-bottom: 20px;
}

.search-input {
  width: 100%;
}

.search-tabs {
  margin-top: 20px;
}

.tab-loading {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.user-results {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-top: 10px;
}

.user-card {
  display: flex;
  align-items: center;
  padding: 15px;
  border-radius: 8px;
  background-color: #f5f7fa;
  transition: all 0.3s ease;
}

.user-card:hover {
  background-color: #e6e8eb;
}

.user-avatar {
  margin-right: 15px;
}

.user-info {
  flex: 1;
}

.user-name {
  margin: 0 0 5px 0;
  font-size: 16px;
}

.user-bio {
  margin: 0;
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  max-height: 2.6em; /* 兼容性替代方案 */
}

.user-action {
  margin-left: 15px;
}
</style> 