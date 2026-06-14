import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import authApi from '../api/auth'
import useAuthStore from '../store/authStore'
import useAuth from '../hooks/useAuth'
import { apiError } from '../utils'

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
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [error, setError] = useState('')
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false)

  const updateMutation = useMutation({
    mutationFn: (body) => authApi.updateMe(body),
    onSuccess: (updatedUser) => {
      setAuth(accessToken, updatedUser)
      setSaveSuccess(true)
      setError('')
      setTimeout(() => setSaveSuccess(false), 3000)
    },
    onError: (err) => setError(apiError(err)),
  })

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

        <div>
          <label style={labelStyle}>{t('settings.currency')}</label>
          <select value={currency} onChange={(e) => setCurrency(e.target.value)} style={inputStyle}>
            {CURRENCIES.map((c) => (
              <option key={c.code} value={c.code}>{c.code} — {c.name}</option>
            ))}
          </select>
        </div>

        {error && (
          <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>
        )}

        {saveSuccess && (
          <div style={{ background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)', color: '#059669', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{t('settings.saved')}</div>
        )}

        <motion.div
          whileTap={{ scale: 0.97 }}
          onClick={updateMutation.isPending ? undefined : () => updateMutation.mutate({ currency })}
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
