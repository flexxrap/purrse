import axios from 'axios'
import useAuthStore from '../store/authStore'

// Empty string → relative paths → Vite proxy in dev, same-origin in prod
const BASE_URL = import.meta.env.VITE_API_URL ?? ''

const client = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

client.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

let isRefreshing = false
let refreshQueue = []

const flushQueue = (token) => {
  refreshQueue.forEach(({ resolve }) => resolve(token))
  refreshQueue = []
}

const rejectQueue = (error) => {
  refreshQueue.forEach(({ reject }) => reject(error))
  refreshQueue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    originalRequest._retry = true

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      }).then((token) => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return client(originalRequest)
      })
    }

    isRefreshing = true

    try {
      const response = await axios.post(
        `${BASE_URL}/auth/refresh`,
        {},
        { withCredentials: true }
      )
      const { access_token } = response.data
      useAuthStore.getState().setAuth(access_token, useAuthStore.getState().user)
      flushQueue(access_token)
      originalRequest.headers.Authorization = `Bearer ${access_token}`
      return client(originalRequest)
    } catch (refreshError) {
      rejectQueue(refreshError)
      useAuthStore.getState().clearAuth()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default client
