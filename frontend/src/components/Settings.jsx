import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import authApi from '../api/auth'
import useAuthStore from '../store/authStore'
import useAuth from '../hooks/useAuth'
import { apiError } from '../utils'

const SuccessBanner = ({ msg }) => (
  <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', color: '#059669', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{msg}</div>
)
const ErrorBanner = ({ msg }) => (
  <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{msg}</div>
)

const CURRENCIES = [
  { code: 'USD', name: 'US Dollar' },
  { code: 'EUR', name: 'Euro' },
  { code: 'GBP', name: 'British Pound' },
  { code: 'BYN', name: 'Belarusian Ruble' },
  { code: 'RUB', name: 'Russian Ruble' },
  { code: 'PLN', name: 'Polish Zloty' },
  { code: 'UAH', name: 'Ukrainian Hryvnia' },
  { code: 'KZT', name: 'Kazakhstani Tenge' },
  { code: 'CHF', name: 'Swiss Franc' },
  { code: 'JPY', name: 'Japanese Yen' },
  { code: 'CNY', name: 'Chinese Yuan' },
  { code: 'CAD', name: 'Canadian Dollar' },
  { code: 'AUD', name: 'Australian Dollar' },
]

const card = { background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }
const sectionTitle = { fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-secondary)', margin: 0 }
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }
const inputStyle = { width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }

const Settings = () => {
  const { user, accessToken, setAuth } = useAuthStore()
  const { logout } = useAuth()
  const { t, i18n } = useTranslation()

  const [currency, setCurrency] = useState(user?.currency || 'USD')
  const [newEmail, setNewEmail] = useState('')
  const [profileSuccess, setProfileSuccess] = useState('')
  const [profileError, setProfileError] = useState('')

  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [pwSuccess, setPwSuccess] = useState(false)
  const [pwError, setPwError] = useState('')

  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  const updateMutation = useMutation({
    mutationFn: (body) => authApi.updateMe(body),
    onSuccess: (updatedUser) => {
      setAuth(accessToken, updatedUser)
      setNewEmail('')
      setProfileSuccess(updatedUser.email !== user?.email ? t('settings.emailUpdated') : t('settings.saved'))
      setProfileError('')
      setTimeout(() => setProfileSuccess(''), 3000)
    },
    onError: (err) => { setProfileError(apiError(err)); setProfileSuccess('') },
  })

  const passwordMutation = useMutation({
    mutationFn: () => authApi.changePassword(oldPassword, newPassword),
    onSuccess: () => {
      setOldPassword(''); setNewPassword('')
      setPwSuccess(true); setPwError('')
      setTimeout(() => setPwSuccess(false), 3000)
    },
    onError: (err) => { setPwError(apiError(err)); setPwSuccess(false) },
  })

  const handleSaveProfile = () => {
    const body = {}
    if (newEmail.trim()) body.email = newEmail.trim()
    if (currency !== user?.currency) body.currency = currency
    if (Object.keys(body).length === 0) return
    updateMutation.mutate(body)
  }

  return (
    <div style={{ maxWidth: '480px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{t('settings.title')}</h2>

      {/* Profile card */}
      <div style={card}>
        <p style={sectionTitle}>{t('settings.profile')}</p>

        <div>
          <label style={labelStyle}>{t('settings.email')}</label>
          <div style={{ ...inputStyle, background: 'var(--bg)', color: 'var(--text-secondary)', userSelect: 'all' }}>
            {user?.email || t('settings.noEmail')}
          </div>
        </div>

        {user?.email && (
          <div>
            <label style={labelStyle}>{t('settings.newEmail')}</label>
            <input
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              style={inputStyle}
              placeholder="new@example.com"
              autoComplete="email"
            />
          </div>
        )}

        <div>
          <label style={labelStyle}>{t('settings.currency')}</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)} style={inputStyle}>
            {CURRENCIES.map((c) => (
              <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
            ))}
          </select>
        </div>

        {profileError && <ErrorBanner msg={profileError} />}
        {profileSuccess && <SuccessBanner msg={profileSuccess} />}

        <motion.div
          whileTap={{ scale: 0.97 }}
          onClick={updateMutation.isPending ? undefined : handleSaveProfile}
          style={{
            background: 'var(--amaranth-btn)', color: 'white', borderRadius: '10px', padding: '11px',
            fontSize: '13px', fontWeight: 600, textAlign: 'center',
            cursor: updateMutation.isPending ? 'not-allowed' : 'pointer',
            opacity: updateMutation.isPending ? 0.7 : 1, userSelect: 'none',
          }}
        >
          {updateMutation.isPending ? t('settings.saving') : t('settings.saveChanges')}
        </motion.div>
      </div>

      {/* Change password card — only for email users */}
      {user?.email && (
        <div style={card}>
          <p style={sectionTitle}>{t('settings.changePassword')}</p>

          <div>
            <label style={labelStyle}>{t('settings.oldPassword')}</label>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              style={inputStyle}
              autoComplete="current-password"
            />
          </div>

          <div>
            <label style={labelStyle}>{t('settings.newPassword')}</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              style={inputStyle}
              placeholder={t('settings.newPasswordMin')}
              autoComplete="new-password"
            />
          </div>

          {pwError && <ErrorBanner msg={pwError} />}
          {pwSuccess && <SuccessBanner msg={t('settings.passwordChanged')} />}

          <motion.div
            whileTap={{ scale: 0.97 }}
            onClick={passwordMutation.isPending ? undefined : () => passwordMutation.mutate()}
            style={{
              background: 'var(--amaranth-btn)', color: 'white', borderRadius: '10px', padding: '11px',
              fontSize: '13px', fontWeight: 600, textAlign: 'center',
              cursor: passwordMutation.isPending ? 'not-allowed' : 'pointer',
              opacity: (passwordMutation.isPending || !oldPassword || newPassword.length < 8) ? 0.5 : 1,
              userSelect: 'none',
            }}
          >
            {passwordMutation.isPending ? t('settings.saving') : t('settings.changePassword')}
          </motion.div>
        </div>
      )}

      {/* Language card */}
      <div style={card}>
        <p style={sectionTitle}>{t('settings.language')}</p>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['en', 'ru'].map((lng) => (
            <motion.div
              key={lng}
              whileTap={{ scale: 0.97 }}
              onClick={() => i18n.changeLanguage(lng)}
              style={{
                flex: 1, padding: '10px', borderRadius: '10px', textAlign: 'center',
                fontSize: '13px', fontWeight: 500, cursor: 'pointer', userSelect: 'none',
                border: i18n.language === lng ? '1px solid rgba(229,43,80,0.3)' : '1px solid var(--border-card)',
                background: i18n.language === lng ? 'rgba(229,43,80,0.08)' : 'var(--surface)',
                color: i18n.language === lng ? 'var(--amaranth)' : 'var(--text-secondary)',
              }}
            >
              {lng === 'en' ? '🇬🇧 English' : '🇷🇺 Русский'}
            </motion.div>
          ))}
        </div>
      </div>

      {/* Account card */}
      <div style={card}>
        <p style={sectionTitle}>{t('settings.account')}</p>

        <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
          {t('settings.memberSince')}{' '}
          <span style={{ color: 'var(--text-primary)' }}>
            {user?.created_at
              ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
              : '—'}
          </span>
        </div>

        {!showLogoutConfirm ? (
          <motion.div
            whileTap={{ scale: 0.97 }}
            onClick={() => setShowLogoutConfirm(true)}
            style={{
              borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500,
              textAlign: 'center', cursor: 'pointer', userSelect: 'none',
              background: 'rgba(229,43,80,0.06)', border: '1px solid rgba(229,43,80,0.15)', color: 'var(--icon-a-color)',
            }}
          >
            {t('settings.signOut')}
          </motion.div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', textAlign: 'center', margin: 0 }}>{t('settings.confirmSignOut')}</p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <motion.div whileTap={{ scale: 0.97 }} onClick={() => setShowLogoutConfirm(false)}
                style={{ flex: 1, borderRadius: '10px', padding: '10px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
              >{t('settings.cancel')}</motion.div>
              <motion.div whileTap={{ scale: 0.97 }} onClick={logout}
                style={{ flex: 1, borderRadius: '10px', padding: '10px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: 'pointer', background: 'var(--amaranth-btn)', color: 'white', userSelect: 'none' }}
              >{t('settings.signOut')}</motion.div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Settings
