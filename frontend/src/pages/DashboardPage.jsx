import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import useAuthStore from '../store/authStore'
import { useThemeStore } from '../store/themeStore'
import { Logo } from '../components/Logo'
import Overview from '../components/Overview'
import Transactions from '../components/Transactions'
import Goals from '../components/Goals'
import Budget from '../components/Budget'
import Categories from '../components/Categories'
import Accounts from '../components/Accounts'
import Settings from '../components/Settings'

const ONBOARDING_KEY = 'purrse-onboarded'

const OnboardingModal = ({ onDone, onGoCategories }) => {
  const { t } = useTranslation()
  const steps = [
    { icon: '📊', text: t('onboarding.step1') },
    { icon: '🏷️', text: t('onboarding.step2') },
    { icon: '🎯', text: t('onboarding.step3') },
  ]
  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(13,10,16,0.6)', backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '16px' }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.93, y: 16 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '20px', padding: '32px 28px', width: '100%', maxWidth: '400px', boxShadow: '0 12px 60px rgba(0,0,0,0.25)', textAlign: 'center' }}
      >
        <div style={{ fontSize: '36px', marginBottom: '12px' }}>🐱</div>
        <h2 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 6px' }}>{t('onboarding.title')}</h2>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 24px' }}>{t('onboarding.subtitle')}</p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '28px', textAlign: 'left' }}>
          {steps.map(({ icon, text }, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'var(--bg)', borderRadius: '10px', padding: '10px 14px' }}>
              <span style={{ fontSize: '18px' }}>{icon}</span>
              <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{text}</span>
            </div>
          ))}
        </div>

        <motion.div whileTap={{ scale: 0.97 }} onClick={onGoCategories}
          style={{ background: 'var(--amaranth-btn)', color: 'white', borderRadius: '10px', padding: '12px', fontSize: '14px', fontWeight: 600, cursor: 'pointer', userSelect: 'none', marginBottom: '10px' }}
        >
          {t('onboarding.cta')}
        </motion.div>
        <div onClick={onDone} style={{ fontSize: '13px', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}>
          {t('onboarding.skip')}
        </div>
      </motion.div>
    </motion.div>
  )
}

const TABS = [
  { id: 'overview',      key: 'nav.overview',     icon: '📊' },
  { id: 'transactions',  key: 'nav.transactions', icon: '💸' },
  { id: 'accounts',      key: 'nav.accounts',     icon: '💳' },
  { id: 'goals',         key: 'nav.goals',        icon: '🎯' },
  { id: 'budget',        key: 'nav.budget',       icon: '📅' },
  { id: 'categories',    key: 'nav.categories',   icon: '🏷️' },
  { id: 'settings',      key: 'nav.settings',     icon: '⚙️' },
]

const ghostBtn = {
  background: 'transparent',
  border: '0.5px solid var(--border-card)',
  borderRadius: '8px',
  padding: '6px 10px',
  cursor: 'pointer',
  color: 'var(--text-secondary)',
  fontSize: '13px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  lineHeight: 1,
}

const DashboardPage = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [pendingQuickAdd, setPendingQuickAdd] = useState(null)
  const [showOnboarding, setShowOnboarding] = useState(() => !localStorage.getItem(ONBOARDING_KEY))
  const { user } = useAuthStore()

  const quickAddTransaction = (type) => {
    setActiveTab('transactions')
    setPendingQuickAdd(type)
  }

  const closeOnboarding = () => {
    localStorage.setItem(ONBOARDING_KEY, '1')
    setShowOnboarding(false)
  }
  const goCategories = () => {
    closeOnboarding()
    setActiveTab('categories')
  }

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    if (tg?.colorScheme) {
      // Sync theme with Telegram (best effort — user can still override)
    }
  }, [])
  const { theme, toggleTheme } = useThemeStore()
  const { t, i18n } = useTranslation()

  const initials = user?.email?.[0]?.toUpperCase() || 'U'
  const tgPhotoUrl = window.Telegram?.WebApp?.initDataUnsafe?.user?.photo_url || null
  const isDark = theme === 'dark'

  const sidebarBg = isDark
    ? 'linear-gradient(160deg,#1A0D15 0%,#120A1A 35%,#0A0E1F 70%,#080D1A 100%)'
    : 'linear-gradient(160deg,#F8E8F0 0%,#EEE0F8 35%,#E0EEFF 70%,#F0F8FF 100%)'

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':     return <Overview onQuickAdd={quickAddTransaction} />
      case 'transactions': return <Transactions quickAdd={pendingQuickAdd} onQuickAddConsumed={() => setPendingQuickAdd(null)} />
      case 'accounts':     return <Accounts />
      case 'goals':        return <Goals />
      case 'budget':       return <Budget />
      case 'categories':   return <Categories />
      case 'settings':     return <Settings />
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <AnimatePresence>
        {showOnboarding && (
          <OnboardingModal onDone={closeOnboarding} onGoCategories={goCategories} />
        )}
      </AnimatePresence>

      {/* ── Mobile top bar ── */}
      <div
        className="md:hidden sticky top-0 z-40"
        style={{ background: sidebarBg, borderBottom: '0.5px solid var(--border)' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px' }}>
          <button onClick={() => setActiveTab('overview')} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}>
            <Logo size={22} dark={isDark} />
            <span style={{
              fontSize: '15px', fontWeight: 500, letterSpacing: '-0.3px',
              background: 'linear-gradient(135deg, #E52B50, #64A0FF)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>purrse</span>
          </button>
          <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
            <button onClick={toggleTheme} style={{ ...ghostBtn, padding: '4px 8px', fontSize: '14px' }}>
              {isDark ? '☀️' : '🌙'}
            </button>
            <button
              onClick={() => i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en')}
              style={{ ...ghostBtn, padding: '4px 8px', fontSize: '12px', fontWeight: 500 }}
            >
              {i18n.language === 'en' ? 'RU' : 'EN'}
            </button>
            <button onClick={() => setActiveTab('settings')} style={{ width: '28px', height: '28px', borderRadius: '50%', overflow: 'hidden', border: 'none', padding: 0, cursor: 'pointer', flexShrink: 0, background: 'linear-gradient(135deg, #E52B50, #64A0FF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              {tgPhotoUrl
                ? <img src={tgPhotoUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                : <span style={{ color: 'white', fontSize: '11px', fontWeight: 700 }}>{initials}</span>
              }
            </button>
          </div>
        </div>
      </div>

      {/* ── Desktop layout ── */}
      <div className="flex">
        {/* Sidebar */}
        <aside
          className="hidden md:flex md:flex-col md:fixed md:inset-y-0 md:left-0 md:w-52 z-30"
          style={{ background: sidebarBg, borderRight: '0.5px solid var(--border)', overflow: 'hidden' }}
        >
          {/* Blobs */}
          <div style={{ position: 'absolute', top: '-60px', left: '-60px', width: '200px', height: '200px', borderRadius: '50%', background: 'radial-gradient(circle,rgba(229,43,80,0.15) 0%,transparent 70%)', pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: '-60px', right: '-40px', width: '180px', height: '180px', borderRadius: '50%', background: 'radial-gradient(circle,rgba(100,160,255,0.18) 0%,transparent 70%)', pointerEvents: 'none' }} />

          {/* Logo */}
          <button onClick={() => setActiveTab('overview')} style={{ padding: '24px 20px 16px', display: 'flex', alignItems: 'center', gap: '10px', position: 'relative', background: 'transparent', border: 'none', cursor: 'pointer', textAlign: 'left' }}>
            <Logo size={28} dark={isDark} />
            <span style={{
              fontSize: '17px', fontWeight: 500, letterSpacing: '-0.3px',
              background: 'linear-gradient(135deg, #E52B50, #64A0FF)',
              WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            }}>purrse</span>
          </button>

          {/* Nav */}
          <nav style={{ flex: 1, padding: '4px 12px', display: 'flex', flexDirection: 'column', gap: '2px', position: 'relative' }}>
            {TABS.map(({ id, key }) => {
              const isActive = activeTab === id
              return (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    padding: '9px 12px',
                    borderRadius: '10px',
                    border: isActive ? '0.5px solid rgba(229,43,80,0.18)' : '0.5px solid transparent',
                    background: isActive
                      ? 'linear-gradient(135deg,rgba(229,43,80,0.1),rgba(100,160,255,0.1))'
                      : 'transparent',
                    color: isActive ? 'var(--nav-active-color)' : 'var(--nav-color)',
                    fontSize: '14px',
                    fontWeight: isActive ? 500 : 400,
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    outline: 'none',
                  }}
                >
                  {t(key)}
                </button>
              )
            })}
          </nav>

          {/* Bottom */}
          <div style={{ padding: '12px 16px 20px', borderTop: '0.5px solid var(--border)', position: 'relative', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={toggleTheme} style={ghostBtn}>
                {isDark ? '☀️' : '🌙'}
              </button>
              <button
                onClick={() => i18n.changeLanguage(i18n.language === 'en' ? 'ru' : 'en')}
                style={{ ...ghostBtn, fontWeight: 500 }}
              >
                {i18n.language === 'en' ? 'RU' : 'EN'}
              </button>
            </div>
            <button onClick={() => setActiveTab('settings')} style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0, width: '100%', textAlign: 'left' }}>
              <div style={{ width: '30px', height: '30px', borderRadius: '50%', overflow: 'hidden', flexShrink: 0, background: 'linear-gradient(135deg, #E52B50, #64A0FF)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {tgPhotoUrl
                  ? <img src={tgPhotoUrl} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <span style={{ color: 'white', fontSize: '11px', fontWeight: 700 }}>{initials}</span>
                }
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-secondary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {user?.email}
              </span>
            </button>
          </div>
        </aside>

        {/* Main content */}
        <div className="md:ml-52 flex-1" style={{ minWidth: 0 }}>
          <main style={{ maxWidth: '860px', margin: '0 auto', padding: '24px 16px 80px' }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.18 }}
              >
                {renderContent()}
              </motion.div>
            </AnimatePresence>
          </main>
        </div>
      </div>

      {/* ── Mobile bottom navigation ── */}
      <nav
        className="md:hidden"
        style={{
          position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 40,
          display: 'flex', background: 'var(--surface)',
          borderTop: '0.5px solid var(--border)',
          paddingBottom: 'env(safe-area-inset-bottom, 0px)',
        }}
      >
        {TABS.map(({ id, key, icon }) => {
          const isActive = activeTab === id
          return (
            <button
              key={id}
              onClick={() => setActiveTab(id)}
              style={{
                flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
                gap: '3px', padding: '8px 2px 7px', background: 'transparent', border: 'none',
                cursor: 'pointer', outline: 'none',
                color: isActive ? 'var(--nav-active-color)' : 'var(--nav-color)',
              }}
            >
              <span style={{ fontSize: '19px', lineHeight: 1, opacity: isActive ? 1 : 0.55 }}>{icon}</span>
              <span style={{ fontSize: '10px', fontWeight: isActive ? 600 : 400, whiteSpace: 'nowrap' }}>{t(key)}</span>
            </button>
          )
        })}
      </nav>
    </div>
  )
}

export default DashboardPage
