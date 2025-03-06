import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { io } from 'socket.io-client'
import { ElNotification } from 'element-plus'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || '{}'))
  const unreadCount = ref(parseInt(localStorage.getItem('unreadCount') || '0'))
  const socket = ref(null)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(userData) {
    user.value = userData
    localStorage.setItem('user', JSON.stringify(userData))
  }

  function setUnreadCount(count) {
    unreadCount.value = count
    localStorage.setItem('unreadCount', count.toString())
  }

  function login(tokenValue, userData) {
    setToken(tokenValue)
    setUser(userData)
    initializeWebSocket()
  }

  function logout() {
    disconnectWebSocket()
    token.value = ''
    user.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  function isLoggedIn() {
    return !!token.value
  }

  function getAuthHeader() {
    return token.value ? `Bearer ${token.value}` : ''
  }

  function updateUser(userData) {
    user.value = { ...user.value, ...userData }
    localStorage.setItem('user', JSON.stringify(user.value))
  }

  function decrementUnreadCount() {
    if (unreadCount.value > 0) {
      const newCount = unreadCount.value - 1
      setUnreadCount(newCount)
    }
  }

  function resetUnreadCount() {
    setUnreadCount(0)
  }

  function initializeWebSocket() {
    if (!isLoggedIn()) return
    
    if (socket.value) {
      socket.value.disconnect()
    }

    socket.value = io('https://api.searchsomething.top', {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
      auth: {
        token: token.value
      },
      extraHeaders: {
        Authorization: `Bearer ${token.value}`
      }
    })

    socket.value.on('connect', () => {
      console.log('WebSocket connected')
    })

    socket.value.on('new_notification', (data) => {
      console.log('收到新通知:', data)
      setUnreadCount(data.unread_count)
      
      ElNotification({
        title: '新消息通知',
        message: data.content,
        type: 'info',
        duration: 3000
      })
    })

    socket.value.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    socket.value.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error)
    })
  }

  function disconnectWebSocket() {
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
  }

  return {
    token,
    user,
    unreadCount,
    login,
    logout,
    isLoggedIn,
    getAuthHeader,
    updateUser,
    decrementUnreadCount,
    resetUnreadCount,
    setUnreadCount,
    initializeWebSocket,
    disconnectWebSocket
  }
}) 
