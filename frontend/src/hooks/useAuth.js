import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import authApi from '../api/auth'
import useAuthStore from '../store/authStore'

const useAuth = () => {
  const { setAuth, clearAuth } = useAuthStore()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const login = async (email, password) => {
    const data = await authApi.login(email, password)
    setAuth(data.access_token, data.user)
    return data
  }

  const register = async (email, password) => {
    const data = await authApi.register(email, password)
    setAuth(data.access_token, data.user)
    return data
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore errors — still clear local state
    }
    clearAuth()
    queryClient.clear()
    navigate('/login')
  }

  return { login, register, logout }
}

export default useAuth
