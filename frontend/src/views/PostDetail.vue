<template>
  <div class="post-detail-container">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="10" animated />
    </div>
    
    <!-- 主要内容 -->
    <div v-else-if="post" v-show="contentReady" class="content-wrapper" ref="detailContainer">
      <el-card class="post-detail">
        <div class="post-header" ref="titleRef">
          <h1 class="post-title">{{ post.title }}</h1>
          <div class="post-meta">
            <div class="author-info">
              <span>作者: 
                <router-link :to="`/user/${post.author?.id}`">{{ post.author?.username }}</router-link>
              </span>
              
              <!-- 关注按钮，放在作者名字旁边 -->
              <el-button 
                v-if="userStore.isLoggedIn() && post.author && post.author.id && userStore.user && userStore.user.id !== post.author.id"
                size="small"
                :type="isFollowingAuthor ? 'info' : 'primary'"
                @click="toggleFollowAuthor"
                style="margin-left: 10px;"
              >
                {{ isFollowingAuthor ? '已关注' : '关注' }}
              </el-button>
            </div>
            
            <!-- 打印调试信息 - 开发时使用，发布前删除 -->
            <!-- <div v-if="isDev" style="background-color: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 4px;">
              <p>作者ID: {{ post.author?.id }}</p>
              <p>当前用户ID: {{ userStore.user?.id }}</p>
              <p>是否已登录: {{ userStore.isLoggedIn() }}</p>
              <p>是否已关注: {{ isFollowingAuthor }}</p>
              <p>是否应显示关注按钮: {{ userStore.isLoggedIn() && post.author?.id && userStore.user?.id !== post.author?.id }}</p>
            </div> -->
            
            <span>发布时间: {{ post.created_at }}</span>
            <span>浏览: {{ post.view_count || 0 }}</span>
          </div>
        </div>
        
        <div class="post-content">
          {{ post.content }}
        </div>
        
        <div class="post-actions">
          <el-button 
            :class="{ 'is-active': post.isCommented }"
            @click="handleComment"
          >
            <el-icon><ChatLineRound /></el-icon>
            评论 {{ post.comment_count || 0 }}
          </el-button>
          <el-button 
            :class="{ 'is-active': post.isShared }"
            @click="toggleShare"
          >
            <el-icon><Share /></el-icon>
            转发 {{ post.share_count || 0 }}
          </el-button>
          <el-button 
            :class="{ 'is-active': post.isLiked }"
            @click="handleLike"
          >
            <el-icon><Star /></el-icon>
            点赞 {{ post.like_count || 0 }}
          </el-button>
          
          <!-- 删除按钮 - 只有作者才能看到 -->
          <el-button 
            v-if="isAuthor"
            type="danger"
            @click="handleDelete"
          >
            <el-icon><Delete /></el-icon>
            删除
          </el-button>
        </div>
      </el-card>

      <!-- 评论区 -->
      <el-card class="comments-section">
        <template #header>
          <div class="comments-header">
            <span>评论 ({{ post.comment_count || 0 }})</span>
            <el-button type="primary" @click="handleComment">
              写评论
            </el-button>
          </div>
        </template>
        
        <div class="comments-list" v-loading="loadingComments">
          <div v-if="comments.length === 0" class="no-comments">
            暂无评论，来发表第一条评论吧
          </div>
          <div v-else v-for="comment in comments" :key="comment.id" class="comment-item" :data-id="comment.id">
            <div class="comment-header">
              <router-link 
                :to="`/user/${comment.author_id}`" 
                class="comment-author"
              >
                {{ comment.author_name }}
              </router-link>
              <span class="comment-time">{{ comment.created_at }}</span>
            </div>
            <div class="comment-content">{{ comment.content }}</div>
            
            <!-- 评论操作按钮 -->
            <div class="comment-actions">
              <el-button 
                size="small"
                :class="{ 'is-active': comment.isLiked }"
                @click="handleCommentLike(comment)"
              >
                <el-icon><Star /></el-icon>
                {{ comment.isLiked ? '已点赞' : '点赞' }} {{ comment.like_count || 0 }}
              </el-button>
              
              <el-button 
                size="small"
                :class="{ 'is-active': comment.isShared }"
                @click="handleCommentShare(comment)"
              >
                <el-icon><Share /></el-icon>
                {{ comment.isShared ? '已转发' : '转发' }} {{ comment.share_count || 0 }}
              </el-button>
              
              <el-button 
                size="small"
                @click="showReplyForm(comment)"
              >
                <el-icon><ChatLineRound /></el-icon>
                回复 {{ comment.reply_count || 0 }}
              </el-button>
            </div>
            
            <!-- 评论回复列表 -->
            <div v-if="comment.showReplies" class="comment-replies">
              <div v-if="comment.loadingReplies" class="loading-replies">
                <el-icon class="is-loading"><Loading /></el-icon> 加载回复中...
              </div>
              <div v-else-if="comment.replies && comment.replies.length > 0" class="replies-list">
                <div v-for="reply in comment.replies" :key="reply.id" class="reply-item">
                  <div class="reply-header">
                    <router-link :to="`/user/${reply.user_id}`" class="reply-author">
                      {{ reply.username }}
                    </router-link>
                    <span class="reply-time">{{ reply.created_at }}</span>
                  </div>
                  <div class="reply-content">{{ reply.content }}</div>
                </div>
                
                <div v-if="comment.hasMoreReplies" class="load-more-replies">
                  <el-button link @click="loadMoreReplies(comment)">加载更多回复</el-button>
                </div>
              </div>
              <div v-else class="no-replies">
                暂无回复
              </div>
              
              <!-- 回复评论的表单 -->
              <div v-if="comment.showReplyForm" class="reply-form">
                <el-input
                  v-model="comment.replyContent"
                  type="textarea"
                  :rows="2"
                  placeholder="写下你的回复..."
                  maxlength="200"
                  show-word-limit
                />
                <div class="reply-form-actions">
                  <el-button size="small" @click="cancelReply(comment)">取消</el-button>
                  <el-button 
                    size="small" 
                    type="primary" 
                    @click="submitReply(comment)"
                    :loading="comment.submittingReply"
                    :disabled="!comment.replyContent || comment.replyContent.trim() === ''"
                  >
                    发表回复
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="load-more" v-if="hasMoreComments">
            <el-button text @click="loadMoreComments">加载更多评论</el-button>
          </div>
        </div>
      </el-card>

      <!-- 评论对话框 -->
      <el-dialog
        v-model="showCommentDialog"
        title="发表评论"
        width="500px"
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
            <el-button @click="showCommentDialog = false">取消</el-button>
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
    </div>
    
    <!-- 错误状态 -->
    <el-empty 
      v-else 
      description="帖子不存在或已被删除"
      :image-size="200"
    >
      <template #extra>
        <el-button type="primary" @click="router.push('/')">返回首页</el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatLineRound, Share, Star, Delete, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '../stores/user'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const post = ref(null)
const comments = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const hasMoreComments = ref(true)
const loadingComments = ref(false)
const showCommentDialog = ref(false)
const showDeleteDialog = ref(false)
const submitting = ref(false)
const deleting = ref(false)
const isFollowingAuthor = ref(false)

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

const isAuthor = computed(() => {
  return userStore.isLoggedIn() && 
         post.value && 
         post.value.author && 
         post.value.author.id && 
         userStore.user && 
         userStore.user.id === post.value.author.id;
});

const detailContainer = ref(null)
const titleRef = ref(null)
const contentReady = ref(false)
const loading = ref(true)

// 创建一个带有基本配置的 axios 实例
const api = axios.create({
  baseURL: 'https://api.searchsomething.top/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加开发环境标志
const isDev = process.env.NODE_ENV === 'development';

const fetchPostDetail = async () => {
  loading.value = true
  contentReady.value = false
  
  try {
    console.log('获取帖子详情...');
    const response = await api.get(`/posts/${route.params.id}`, {
      headers: userStore.isLoggedIn() ? {
        'Authorization': userStore.getAuthHeader()
      } : {}
    });
    
    console.log('帖子详情API响应:', response.data);
    post.value = response.data;
    
    // 确保作者信息存在且用户已登录
    if (userStore.isLoggedIn() && post.value.author && post.value.author.id) {
      console.log('检查作者关注状态...');
      console.log('作者ID:', post.value.author.id);
      console.log('当前用户ID:', userStore.user.id);
      
      if (post.value.author.id !== userStore.user.id) {
        console.log('准备检查关注状态...');
        await checkAuthorFollowStatus();
      } else {
        console.log('用户查看自己的帖子，不显示关注按钮');
      }
    } else {
      console.log('无法检查关注状态:', {
        isLoggedIn: userStore.isLoggedIn(),
        hasAuthor: !!post.value.author,
        authorId: post.value.author?.id
      });
    }
  } catch (error) {
    console.error('获取帖子详情失败:', error);
    ElMessage.error('获取帖子详情失败');
  } finally {
    loading.value = false
  }
};

// 获取评论
const fetchComments = async () => {
  try {
    loadingComments.value = true
    const response = await api.get(`/posts/${route.params.id}/comments`, {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      },
      headers: userStore.isLoggedIn() ? {
        'Authorization': userStore.getAuthHeader()
      } : {}
    })
    
    if (response.data.comments) {
      // 初始化每个评论的回复相关属性
      response.data.comments.forEach(comment => {
        comment.showReplies = false;
        comment.showReplyForm = false;
        comment.replyContent = '';
        comment.submittingReply = false;
        comment.replies = [];
        comment.currentReplyPage = 1;
        comment.hasMoreReplies = false;
        comment.loadingReplies = false;
      });
    }
    
    comments.value = response.data.comments;
    hasMoreComments.value = response.data.total > (currentPage.value * pageSize.value);
  } catch (error) {
    console.error('获取评论失败:', error)
    ElMessage.error('获取评论失败')
  } finally {
    loadingComments.value = false
  }
}

const loadMoreComments = () => {
  fetchComments()
}

const handleComment = () => {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  showCommentDialog.value = true
}

const toggleShare = async () => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    return;
  }
  
  try {
    console.log(`转发前状态: ${post.value.isShared}`);
    const response = await fetch(`https://api.searchsomething.top/api/posts/${post.value.id}/share`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    });
    
    const result = await response.json();
    console.log('转发API返回:', result);
    
    if (response.ok) {
      // 确保使用响应中的布尔值
      post.value.isShared = !!result.isShared;
      post.value.share_count = result.shares_count;
      
      console.log(`转发后状态: ${post.value.isShared}`);
      ElMessage.success(post.value.isShared ? '转发成功' : '已取消转发');
    } else {
      ElMessage.error(result.error || '操作失败');
    }
  } catch (error) {
    console.error('转发失败:', error);
    ElMessage.error('操作失败，请稍后再试');
  }
};

const handleLike = async () => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    return;
  }
  
  try {
    console.log(`点赞前状态: ${post.value.isLiked}`);
    const response = await fetch(`https://api.searchsomething.top/api/posts/${post.value.id}/like`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    });
    
    const result = await response.json();
    console.log('点赞API返回:', result);
    
    if (response.ok) {
      // 确保使用响应中的布尔值
      post.value.isLiked = !!result.isLiked;
      post.value.like_count = result.likes_count;
      
      console.log(`点赞后状态: ${post.value.isLiked}`);
      ElMessage.success(post.value.isLiked ? '点赞成功' : '已取消点赞');
    } else {
      ElMessage.error(result.error || '操作失败');
    }
  } catch (error) {
    console.error('点赞失败:', error);
    ElMessage.error('操作失败，请稍后再试');
  }
};

const handleDelete = () => {
  if (!isAuthor.value) {
    ElMessage.error('只有作者才能删除帖子');
    return;
  }
  
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!post.value || !post.value.id) {
    ElMessage.error('帖子信息不完整，无法删除');
    return;
  }
  
  deleting.value = true;
  
  try {
    console.log(`准备删除帖子 ID: ${post.value.id}`);
    const response = await fetch(`https://api.searchsomething.top/api/posts/${post.value.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || '删除失败');
    }
    
    const result = await response.json();
    console.log('删除成功:', result);
    
    ElMessage.success('帖子已删除');
    showDeleteDialog.value = false;
    
    // 删除成功后跳转到首页
    router.push('/');
  } catch (error) {
    console.error('删除帖子失败:', error);
    ElMessage.error(error.message || '删除帖子失败，请重试');
  } finally {
    deleting.value = false;
  }
};

const submitComment = async () => {
  if (!commentFormRef.value) return
  
  try {
    await commentFormRef.value.validate()
    submitting.value = true
    
    const response = await api.post(`/posts/${post.value.id}/comment`, {
      content: commentForm.value.content.trim()
    }, {
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    })
    
    post.value.comment_count = response.data.comment_count
    showCommentDialog.value = false
    commentForm.value.content = ''
    ElMessage.success('评论成功')
    // 重新加载评论列表
    currentPage.value = 1
    comments.value = []
    hasMoreComments.value = true
    fetchComments()
  } catch (error) {
    console.error('评论失败:', error)
    ElMessage.error(error.response?.data?.error || '评论失败')
  } finally {
    submitting.value = false
  }
}

// 更新浏览量
const updateViewCount = async () => {
  if (!userStore.isLoggedIn()) return;  // 未登录用户不更新浏览量
  
  try {
    console.log("准备更新浏览量...")
    const response = await fetch(`https://api.searchsomething.top/api/posts/${route.params.id}/view`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    });
    
    const data = await response.json();
    console.log("浏览量更新结果:", data);
    
    // 更新本地数据
    if (data.view_count !== undefined) {
      post.value.view_count = data.view_count;
      console.log("更新后的浏览量:", post.value.view_count);
    }
  } catch (error) {
    console.error('更新浏览量失败:', error);
  }
}

// 检查是否已关注帖子作者
const checkAuthorFollowStatus = async () => {
  if (!post.value.author || !post.value.author.id) {
    console.log('无法检查关注状态：作者ID不存在');
    return;
  }
  
  try {
    const backendUrl = 'https://api.searchsomething.top';
    const response = await axios.get(`${backendUrl}/api/users/${post.value.author.id}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    if (response.data) {
      isFollowingAuthor.value = response.data.is_following;
      console.log('当前关注状态:', isFollowingAuthor.value);
    }
  } catch (err) {
    console.error('检查关注状态失败:', err);
  }
};

// 关注/取消关注帖子作者
const toggleFollowAuthor = async () => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    router.push('/login');
    return;
  }
  
  // 检查作者ID是否存在
  if (!post.value.author || !post.value.author.id) {
    console.error('作者ID不存在');
    ElMessage.error('作者信息不完整，无法执行操作');
    return;
  }
  
  try {
    const backendUrl = 'https://api.searchsomething.top';
    const endpoint = isFollowingAuthor.value 
      ? `${backendUrl}/api/users/${post.value.author.id}/unfollow` 
      : `${backendUrl}/api/users/${post.value.author.id}/follow`;
    
    const response = await axios.post(endpoint, {}, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    });
    
    isFollowingAuthor.value = !isFollowingAuthor.value;
    ElMessage.success(isFollowingAuthor.value ? '关注成功' : '取消关注成功');
  } catch (err) {
    console.error('关注/取消关注操作失败:', err);
    ElMessage.error(err.response?.data?.error || '操作失败');
  }
};

// 评论点赞功能
const handleCommentLike = async (comment) => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    return;
  }
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/comments/${comment.id}/like`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    });
    
    const result = await response.json();
    
    if (response.ok) {
      comment.isLiked = !!result.isLiked;
      comment.like_count = result.likes_count;
      ElMessage.success(comment.isLiked ? '点赞评论成功' : '已取消点赞评论');
    } else {
      ElMessage.error(result.error || '操作失败');
    }
  } catch (error) {
    console.error('评论点赞失败:', error);
    ElMessage.error('操作失败，请稍后再试');
  }
};

// 评论转发功能
const handleCommentShare = async (comment) => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    return;
  }
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/comments/${comment.id}/share`, {
      method: 'POST',
      headers: {
        'Authorization': userStore.getAuthHeader()
      }
    });
    
    const result = await response.json();
    
    if (response.ok) {
      comment.isShared = !!result.isShared;
      comment.share_count = result.shares_count;
      ElMessage.success(comment.isShared ? '转发评论成功' : '已取消转发评论');
    } else {
      ElMessage.error(result.error || '操作失败');
    }
  } catch (error) {
    console.error('评论转发失败:', error);
    ElMessage.error('操作失败，请稍后再试');
  }
};

// 显示回复表单
const showReplyForm = async (comment) => {
  if (!userStore.isLoggedIn()) {
    ElMessage.warning('请先登录');
    return;
  }
  
  // 初始化回复相关属性
  if (!comment.showReplies) {
    comment.showReplies = true;
    comment.replies = [];
    comment.currentReplyPage = 1;
    comment.hasMoreReplies = false;
    await fetchCommentReplies(comment);
  }
  
  // 显示回复表单
  comment.showReplyForm = true;
  comment.replyContent = '';
  
  // 确保UI更新后聚焦输入框
  await nextTick();
  const textareaEl = document.querySelector(`.comment-item[data-id="${comment.id}"] .reply-form textarea`);
  if (textareaEl) textareaEl.focus();
};

// 取消回复
const cancelReply = (comment) => {
  comment.showReplyForm = false;
  comment.replyContent = '';
};

// 提交回复
const submitReply = async (comment) => {
  if (!comment.replyContent || comment.replyContent.trim() === '') {
    ElMessage.warning('回复内容不能为空');
    return;
  }
  
  comment.submittingReply = true;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/comments/${comment.id}/reply`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': userStore.getAuthHeader()
      },
      body: JSON.stringify({
        content: comment.replyContent.trim()
      })
    });
    
    const result = await response.json();
    
    if (response.ok) {
      // 成功提交回复
      ElMessage.success('回复成功');
      
      // 更新回复计数
      comment.reply_count = (comment.reply_count || 0) + 1;
      
      // 重新加载回复列表
      comment.currentReplyPage = 1;
      await fetchCommentReplies(comment);
      
      // 清空回复表单
      comment.replyContent = '';
      comment.showReplyForm = false;
    } else {
      ElMessage.error(result.error || '回复失败');
    }
  } catch (error) {
    console.error('评论回复提交失败:', error);
    ElMessage.error('操作失败，请稍后再试');
  } finally {
    comment.submittingReply = false;
  }
};

// 获取评论的回复列表
const fetchCommentReplies = async (comment) => {
  comment.loadingReplies = true;
  
  try {
    const response = await fetch(`https://api.searchsomething.top/api/comments/${comment.id}/replies?page=${comment.currentReplyPage}&page_size=5`, {
      headers: userStore.isLoggedIn() ? {
        'Authorization': userStore.getAuthHeader()
      } : {}
    });
    
    const result = await response.json();
    
    if (response.ok) {
      // 如果是第一页，替换回复列表；否则追加
      if (comment.currentReplyPage === 1) {
        comment.replies = result.replies;
      } else {
        comment.replies = [...comment.replies, ...result.replies];
      }
      
      comment.hasMoreReplies = result.has_more;
    } else {
      console.error('获取评论回复失败:', result.error);
      ElMessage.error(result.error || '获取回复失败');
    }
  } catch (error) {
    console.error('获取评论回复失败:', error);
    ElMessage.error('获取回复失败，请稍后再试');
  } finally {
    comment.loadingReplies = false;
  }
};

// 加载更多回复
const loadMoreReplies = async (comment) => {
  if (comment.loadingReplies || !comment.hasMoreReplies) return;
  
  comment.currentReplyPage += 1;
  await fetchCommentReplies(comment);
};

onMounted(async () => {
  try {
    // 1. 先重置滚动位置
    window.scrollTo({
      top: 0,
      behavior: 'instant'
    })
    
    // 2. 获取数据
    await fetchPostDetail()
    await updateViewCount()
    await fetchComments()
    
    // 3. 等待 DOM 更新
    await nextTick()
    
    // 4. 显示内容
    contentReady.value = true
    
    // 5. 如果 URL 中有评论 ID，滚动到对应评论
    await nextTick() // 再次等待 DOM 更新
    const commentId = window.location.hash.replace('#comment-', '')
    if (commentId) {
      const commentElement = document.querySelector(`[data-id="${commentId}"]`)
      if (commentElement) {
        // 滚动到评论位置，并添加高亮效果
        commentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        commentElement.classList.add('highlight')
        // 3秒后移除高亮效果
        setTimeout(() => {
          commentElement.classList.remove('highlight')
        }, 3000)
      }
    }
    
  } catch (error) {
    console.error('组件加载失败:', error)
  }
})

// 在组件卸载时清除浏览记录，这样用户下次访问时可以重新计数
onUnmounted(() => {
  localStorage.removeItem(`post_viewed_${route.params.id}`)
})
</script>

<style scoped>
.post-detail-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
  min-height: 80vh; /* 确保容器有最小高度 */
}

.content-wrapper {
  opacity: 1;
  transition: opacity 0.3s ease;
}

.content-wrapper[v-show="false"] {
  opacity: 0;
}

.loading-state {
  padding: 20px;
}

/* 优化骨架屏样式 */
:deep(.el-skeleton) {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

/* 调整标题样式 */
.post-title {
  font-size: 1.5rem; /* 从默认的 2rem 减小到 1.5rem */
  font-weight: 500; /* 稍微减轻字重 */
  color: #2c3e50; /* 更柔和的颜色 */
  margin: 0 0 16px 0; /* 调整下边距 */
  line-height: 1.4; /* 优化行高 */
}

.post-header {
  padding-top: 16px;
  border-bottom: 1px solid #ebeef5; /* 添加一个淡色边框分隔线 */
  margin-bottom: 20px;
}

/* 添加渐变背景，提升视觉效果 */
.post-detail {
  background: linear-gradient(to bottom, #ffffff, #fafafa);
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.post-meta {
  margin: 10px 0 20px;
  color: #909399;
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  align-items: center;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.post-content {
  margin: 20px 0;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
}

.post-actions {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  border-top: 1px solid #EBEEF5;
  padding-top: 20px;
}

.post-actions .el-button {
  display: flex;
  align-items: center;
  gap: 5px;
}

.post-actions .el-button.is-active {
  color: #409EFF;
}

.comments-section {
  margin-top: 20px;
}

.comments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.comment-item {
  padding: 15px 0;
  border-bottom: 1px solid #EBEEF5;
  transition: background-color 0.3s ease;  /* 添加过渡效果 */
}

/* 添加高亮样式 */
.comment-item.highlight {
  background-color: #ecf5ff;
  border-radius: 4px;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.2);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-header {
  margin-bottom: 8px;
}

.comment-author {
  font-weight: bold;
  margin-right: 10px;
}

.comment-time {
  color: #909399;
  font-size: 12px;
}

.comment-content {
  color: #606266;
  line-height: 1.5;
}

.no-comments {
  text-align: center;
  color: #909399;
  padding: 20px 0;
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

/* 添加样式使用户名链接更明显 */
.comment-author {
  font-weight: bold;
  color: #409EFF;
  text-decoration: none;
}

.comment-author:hover {
  text-decoration: underline;
}

.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.comment-time {
  color: #909399;
  font-size: 12px;
}

.comment-item {
  padding: 15px 0;
  border-bottom: 1px solid #EBEEF5;
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.comments-list {
  margin-top: 20px;
}

.no-comments {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}

.load-more {
  text-align: center;
  margin-top: 15px;
}

.comment-actions {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.comment-actions .el-button {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}

.comment-actions .el-button.is-active {
  color: #409EFF;
}

.comment-replies {
  margin-left: 20px;
  margin-top: 10px;
  padding-left: 15px;
  border-left: 2px solid #EBEEF5;
}

.reply-item {
  padding: 8px 0;
  border-bottom: 1px solid #F5F7FA;
}

.reply-item:last-child {
  border-bottom: none;
}

.reply-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 5px;
}

.reply-author {
  font-weight: bold;
  color: #409EFF;
  text-decoration: none;
}

.reply-author:hover {
  text-decoration: underline;
}

.reply-time {
  color: #909399;
  font-size: 12px;
}

.reply-content {
  color: #606266;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.reply-form {
  margin-top: 10px;
  padding: 10px;
  background-color: #F5F7FA;
  border-radius: 4px;
}

.reply-form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  gap: 10px;
}

.loading-replies {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 0;
  color: #909399;
}

.no-replies {
  text-align: center;
  padding: 10px 0;
  color: #909399;
}

.load-more-replies {
  text-align: center;
  padding: 5px 0;
}
</style>
