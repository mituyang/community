<template>
  <div class="post-list" v-loading="loading">

      <div class="posts-container">
        <post-card
          v-for="post in posts"
          :key="post.id"
          :post="post"
          @refresh="$emit('refresh')"
        />
      </div>
      
      <div class="load-more-status" v-if="!loading">
        <el-divider v-if="posts.length > 0">
          <span class="load-more-text">{{ hasMore ? '滚动加载更多' : '没有更多帖子了' }}</span>
        </el-divider>
      </div>

  </div>
</template>

<script setup>
// import { defineProps, defineEmits } from 'vue'
import PostCard from './PostCard.vue'

defineProps({
  posts: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  hasMore: {
    type: Boolean,
    default: false
  }
})

defineEmits(['refresh', 'loadMore'])
</script>

<style scoped>
.post-list {
  min-height: 200px;
}

.posts-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.load-more-status {
  text-align: center;
  margin: 20px 0;
}

.load-more-text {
  font-size: 14px;
  color: #909399;
}
</style> 