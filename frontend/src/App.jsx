import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import useAuthStore from './store/authStore'
import { useThemeStore } from './store/themeStore'
import authApi from './api/auth'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'

const ProtectedRoute = ({ children }) => {
  const { accessToken } = useAuthStore()
  if (!accessToken) return <Navigate to="/login" replace />
  return children
}

const App = () => {
  const { setAuth, setInitialized, initialized } = useAuthStore()
  const { theme } = useThemeStore()

  useEffect(() => {
    document.documentElement.className = theme
  }, [theme])

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    const initData = tg?.initData

    if (initData) {
      tg.ready()
      tg.expand()
    }

    authApi
      .refresh()
      .then(({ access_token }) => authApi.getMe().then((user) => setAuth(access_token, user)))
      .catch(() => {
        if (initData) {
          return authApi
            .telegramLogin(initData)
            .then(({ access_token, user }) => setAuth(access_token, user))
            .catch(() => {})
        }
      })
      .finally(() => setInitialized())
  // setAuth and setInitialized are stable Zustand setters — safe to omit
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!initialized) {
    return (
      <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div
          style={{
            width: '32px', height: '32px', borderRadius: '50%',
            border: '3px solid var(--border-card)',
            borderTopColor: 'var(--amaranth)',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
