import axios from 'axios'

const api = axios.create({
  baseURL: 'https://api.searchsomething.top/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器，添加 token
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
}, error => {
  return Promise.reject(error)
})

// 响应拦截器
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

// API 函数
export const register = (userData) => api.post('/register', userData)
export const login = (credentials) => api.post('/login', credentials)
export const sendCode = (email) => api.post('/send-verification-code', { email })
export const sendRegisterCode = (email) => api.post('/send-register-code', { email })
export const verifyCode = (email, code) => api.post('/verify-code', { email, code })
export const resetPassword = (resetData) => api.post('/reset-password', resetData)
export const checkUsername = (username) => api.post('/check-username', { username })

// 获取帖子列表
export const getPosts = (page = 1, pageSize = 10) => 
  api.get(`/posts?page=${page}&page_size=${pageSize}`)

// 创建帖子
export const createPost = (postData) => {
  console.log('Sending post data:', postData)  // 调试日志
  return api.post('/posts', postData)
}

// 获取社区统计信息
export const getCommunityStats = () => api.get('/community-stats') 
