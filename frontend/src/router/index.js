import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import PostDetail from '../views/PostDetail.vue'
import Profile from '../views/Profile.vue'
import { ElMessage } from 'element-plus'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'Home',
      component: Home,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'Login',
      component: Login
    },
    {
      path: '/posts/:id',
      name: 'PostDetail',
      component: () => import('../views/PostDetail.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('../views/Register.vue')
    },
    {
      path: '/home',
      redirect: '/'
    },
    {
      path: '/profile',
      name: 'Profile',
      component: Profile,
      meta: { requiresAuth: true }
    },
    {
      path: '/my-posts',
      name: 'MyPosts',
      component: () => import('../views/MyPosts.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/search',
      name: 'SearchResults',
      component: () => import('../views/SearchResults.vue')
    },
    {
      path: '/user/:id',
      name: 'UserProfile',
      component: () => import('../views/UserProfile.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/notifications',
      name: 'notifications',
      component: () => import('../views/NotificationView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// 导航守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 调试日志
  console.log('Navigation guard:', {
    to: to.path,
    from: from.path,
    isLoggedIn: userStore.isLoggedIn()
  })

  if (to.meta.requiresAuth && !userStore.isLoggedIn()) {
    console.log('Unauthorized access, redirecting to login') // 调试日志
    next('/login')
  } else if (to.path === '/login' && userStore.isLoggedIn()) {
    console.log('Already logged in, redirecting to home') // 调试日志
    next('/')
  } else {
    next()
  }
})

export default router 