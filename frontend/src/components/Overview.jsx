import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import {
  ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend,
  LineChart, Line, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import analyticsApi from '../api/analytics'
import useAuthStore from '../store/authStore'
import { formatMoney, currentMonth } from '../utils'

const FALLBACK_COLORS = ['#E52B50', '#64A0FF', '#AA40FF', '#E8A020', '#10b981', '#2060D0']

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: i * 0.08 } }),
}

const Overview = ({ onQuickAdd }) => {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const currency = user?.currency || 'USD'
  const month = currentMonth()

  const { data: summary, isLoading: sumLoading } = useQuery({
    queryKey: ['analytics', 'summary', month],
    queryFn: () => analyticsApi.summary(month),
  })

  const { data: catData, isLoading: catLoading } = useQuery({
    queryKey: ['analytics', 'categories', month],
    queryFn: () => analyticsApi.categories(month),
  })

  const { data: trendData, isLoading: trendLoading } = useQuery({
    queryKey: ['analytics', 'trend'],
    queryFn: () => analyticsApi.trend(6),
  })

  const trendItems = (trendData?.items || []).map((item) => ({
    month: item.month,
    Income: item.income_cents,
    Expense: item.expense_cents,
  }))

  const pieItems = catData?.items || []

  if (sumLoading && catLoading && trendLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '80px 0' }}>
        <div style={{ width: '32px', height: '32px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    )
  }

  const balanceCents = summary?.balance_cents ?? 0

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Hero balance card */}
      <motion.div
        custom={0} variants={cardVariants} initial="hidden" animate="visible"
        style={{
          background: 'linear-gradient(135deg, #E52B50 0%, #A0153A 45%, #1A1060 100%)',
          borderRadius: '14px', padding: '24px', position: 'relative', overflow: 'hidden',
        }}
      >
        <div style={{ position: 'absolute', top: '-60px', right: '-60px', width: '220px', height: '220px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(100,160,255,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', bottom: '-50px', left: '35%', width: '180px', height: '180px', borderRadius: '50%', background: 'radial-gradient(circle, rgba(100,160,255,0.15) 0%, transparent 70%)', pointerEvents: 'none' }} />
        <p style={{ color: 'rgba(255,255,255,0.55)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.09em', marginBottom: '6px', marginTop: 0 }}>
          {t('overview.balance')} · {new Date().toLocaleString('en-US', { month: 'long', year: 'numeric' })}
        </p>
        <p style={{ color: 'white', fontSize: '36px', fontWeight: 700, letterSpacing: '-0.5px', margin: 0 }}>
          {formatMoney(balanceCents, currency)}
        </p>
      </motion.div>

      {/* Quick add buttons */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <motion.button whileTap={{ scale: 0.97 }} onClick={() => onQuickAdd?.('income')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '14px', borderRadius: '12px', border: '1px solid rgba(16,185,129,0.25)', background: 'rgba(16,185,129,0.08)', color: '#059669', fontSize: '14px', fontWeight: 600, cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '18px', lineHeight: 1 }}>↑</span> {t('overview.addIncome')}
        </motion.button>
        <motion.button whileTap={{ scale: 0.97 }} onClick={() => onQuickAdd?.('expense')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', padding: '14px', borderRadius: '12px', border: '1px solid rgba(229,43,80,0.25)', background: 'rgba(229,43,80,0.08)', color: 'var(--icon-a-color)', fontSize: '14px', fontWeight: 600, cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '18px', lineHeight: 1 }}>↓</span> {t('overview.addExpense')}
        </motion.button>
      </div>

      {/* Income + Expense stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <motion.div custom={1} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '16px' }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--icon-b)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="var(--icon-b-color)" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 19V5m-7 7l7-7 7 7" />
            </svg>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px', marginTop: 0 }}>{t('overview.income')}</p>
          <p style={{ color: 'var(--text-primary)', fontSize: '20px', fontWeight: 700, margin: 0 }}>{formatMoney(summary?.income_cents ?? 0, currency)}</p>
        </motion.div>

        <motion.div custom={2} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '16px' }}
        >
          <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: 'var(--icon-a)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '12px' }}>
            <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="var(--icon-a-color)" strokeWidth="2.5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v14m7-7l-7 7-7-7" />
            </svg>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '4px', marginTop: 0 }}>{t('overview.expenses')}</p>
          <p style={{ color: 'var(--text-primary)', fontSize: '20px', fontWeight: 700, margin: 0 }}>{formatMoney(summary?.expense_cents ?? 0, currency)}</p>
        </motion.div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        <motion.div custom={3} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '20px' }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '16px', marginTop: 0 }}>{t('overview.spendingByCategory')}</h3>
          {pieItems.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '180px', fontSize: '13px', color: 'var(--text-muted)' }}>
              {t('overview.noExpenseData')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieItems} dataKey="total_cents" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2}>
                  {pieItems.map((entry, i) => (
                    <Cell key={entry.category_id || i} fill={entry.color || FALLBACK_COLORS[i % FALLBACK_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(v) => [formatMoney(v, currency), '']} contentStyle={{ borderRadius: '10px', border: '1px solid var(--border-card)', fontSize: '12px', background: 'var(--surface)', color: 'var(--text-primary)' }} />
                <Legend formatter={(v) => <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{v}</span>} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </motion.div>

        <motion.div custom={4} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '20px' }}
        >
          <h3 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '16px', marginTop: 0 }}>{t('overview.monthlyTrend')}</h3>
          {trendItems.length === 0 ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '180px', fontSize: '13px', color: 'var(--text-muted)' }}>
              {t('overview.noTrendData')}
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={trendItems} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-card)" />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <YAxis tickFormatter={(v) => formatMoney(v, currency).replace(/\.00$/, '')} tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={70} />
                <Tooltip formatter={(v, name) => [formatMoney(v, currency), name]} contentStyle={{ borderRadius: '10px', border: '1px solid var(--border-card)', fontSize: '12px', background: 'var(--surface)', color: 'var(--text-primary)' }} />
                <Legend formatter={(v) => <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{v}</span>} />
                <Line type="monotone" dataKey="Income" stroke="#64A0FF" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                <Line type="monotone" dataKey="Expense" stroke="#E52B50" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </motion.div>
      </div>
    </div>
  )
}

export default Overview
