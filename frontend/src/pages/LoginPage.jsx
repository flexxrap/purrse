import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { useThemeStore } from '../store/themeStore'
import { Logo } from '../components/Logo'
import useAuth from '../hooks/useAuth'
import useAuthStore from '../store/authStore'
import authApi from '../api/auth'
import { apiError } from '../utils'

const LoginPage = () => {
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [tgLoading, setTgLoading] = useState(false)
  const [tgError, setTgError] = useState(false)

  const { login, register } = useAuth()
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()
  const { theme } = useThemeStore()
  const { t } = useTranslation()
  const isDark = theme === 'dark'

  const tg = window.Telegram?.WebApp
  const isTelegramWebApp = !!(tg?.initData)

  const tryTelegramLogin = () => {
    if (!tg?.initData) return
    setTgLoading(true)
    setTgError(false)
    authApi.telegramLogin(tg.initData)
      .then(({ access_token, user }) => {
        setAuth(access_token, user)
        navigate('/dashboard')
      })
      .catch(() => {
        setTgLoading(false)
        setTgError(true)
      })
  }

  useEffect(() => {
    if (isTelegramWebApp) tryTelegramLogin()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleSubmit = async () => {
    if (!email.trim() || !password.trim()) {
      setError(t('auth.emptyFields'))
      return
    }
    setError('')
    setLoading(true)
    try {
      if (tab === 'login') {
        await login(email, password)
      } else {
        await register(email, password)
      }
      navigate('/dashboard')
    } catch (err) {
      setError(apiError(err))
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit()
  }

  const pageBg = isDark
    ? '#0D0A10'
    : 'linear-gradient(135deg, #FDF0F5 0%, #F5EEFF 50%, #EEF5FF 100%)'

  const tabSwitcherBg = isDark ? 'rgba(255,255,255,0.06)' : '#F5E8EC'
  const activeTabBg = isDark ? 'rgba(255,255,255,0.10)' : '#FFFFFF'
  const activeTabShadow = isDark ? 'none' : '0 1px 4px rgba(229,43,80,0.1)'

  return (
    <div
      style={{
        minHeight: '100vh',
        background: pageBg,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Blobs */}
      <div style={{ position: 'absolute', top: '-140px', left: '-140px', width: '420px', height: '420px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(229,43,80,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', bottom: '-140px', right: '-140px', width: '420px', height: '420px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(100,160,255,0.12) 0%, transparent 70%)', pointerEvents: 'none' }} />

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        style={{
          width: '100%',
          maxWidth: '420px',
          padding: '32px',
          position: 'relative',
          zIndex: 10,
          background: 'var(--surface)',
          border: '0.5px solid var(--border-card)',
          borderRadius: '16px',
          boxShadow: isDark ? '0 4px 40px rgba(0,0,0,0.4)' : '0 4px 40px rgba(229,43,80,0.06)',
        }}
      >
        {/* Telegram loading/error state */}
        {isTelegramWebApp && (
          <div style={{ textAlign: 'center', marginBottom: '28px' }}>
            <Logo size={48} dark={isDark} />
            {tgLoading && (
              <>
                <p style={{ color: 'var(--text-primary)', fontWeight: 600, margin: '12px 0 4px' }}>purrse</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: 0 }}>Входим через Telegram…</p>
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '16px' }}>
                  <div style={{ width: '24px', height: '24px', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
                </div>
              </>
            )}
            {tgError && (
              <>
                <p style={{ color: 'var(--text-primary)', fontWeight: 600, margin: '12px 0 4px' }}>Не удалось войти</p>
                <p style={{ color: 'var(--text-secondary)', fontSize: '13px', margin: '0 0 16px' }}>Попробуй ещё раз или войди по почте</p>
                <motion.div whileTap={{ scale: 0.97 }} onClick={tryTelegramLogin}
                  style={{ background: 'var(--amaranth-btn)', color: 'white', borderRadius: '10px', padding: '11px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', userSelect: 'none', marginBottom: '10px' }}
                >
                  Повторить
                </motion.div>
              </>
            )}
          </div>
        )}

        {/* Hide email form while Telegram loading or Telegram success */}
        {(!isTelegramWebApp || tgError) && <>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', marginBottom: '6px' }}>
            <Logo size={26} dark={isDark} />
            <span style={{
              fontSize: '20px', fontWeight: 500, letterSpacing: '-0.3px',
              background: 'linear-gradient(135deg, #E52B50, #64A0FF)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>purrse</span>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>{t('auth.tagline')}</p>
        </div>

        {/* Tab switcher */}
        <div style={{ display: 'flex', background: tabSwitcherBg, borderRadius: '12px', padding: '4px', marginBottom: '24px' }}>
          {['login', 'register'].map((t_) => (
            <button
              key={t_}
              onClick={() => { setTab(t_); setError('') }}
              style={{
                flex: 1,
                padding: '9px',
                borderRadius: '9px',
                border: 'none',
                background: tab === t_ ? activeTabBg : 'transparent',
                boxShadow: tab === t_ ? activeTabShadow : 'none',
                color: tab === t_ ? 'var(--text-primary)' : 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: tab === t_ ? 500 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s',
                outline: 'none',
              }}
            >
              {t_ === 'login' ? t('auth.signIn') : t('auth.createAccount')}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('auth.email')}</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{ width: '100%', borderRadius: '10px', padding: '11px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('auth.password')}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={handleKeyDown}
              style={{ width: '100%', borderRadius: '10px', padding: '11px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
              placeholder={tab === 'register' ? t('auth.passwordPlaceholderNew') : t('auth.passwordPlaceholder')}
              autoComplete={tab === 'login' ? 'current-password' : 'new-password'}
            />
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.div
            whileTap={{ scale: 0.97 }}
            onClick={loading ? undefined : handleSubmit}
            style={{
              background: 'var(--amaranth-btn)',
              color: 'white',
              borderRadius: '10px',
              padding: '12px',
              fontSize: '14px',
              fontWeight: 600,
              textAlign: 'center',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.75 : 1,
              userSelect: 'none',
            }}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <span style={{ width: '14px', height: '14px', border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.7s linear infinite' }} />
                {tab === 'login' ? t('auth.signingIn') : t('auth.creatingAccount')}
              </span>
            ) : (
              tab === 'login' ? t('auth.signIn') : t('auth.createAccount')
            )}
          </motion.div>
        </div>
        </>}
      </motion.div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}

export default LoginPage
