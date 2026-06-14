import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import budgetsApi from '../api/budgets'
import categoriesApi from '../api/categories'
import useAuthStore from '../store/authStore'
import { formatMoney, currentMonth } from '../utils'

const cardVariants = {
  hidden: { opacity: 0, y: 16 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { duration: 0.3, delay: i * 0.06 } }),
}

const BudgetModal = ({ categories, month, existing, onClose }) => {
  const { t } = useTranslation()
  const { user } = useAuthStore()
  const currency = user?.currency || 'USD'
  const queryClient = useQueryClient()

  const [categoryId, setCategoryId] = useState(existing?.category_id || '')
  const [amount, setAmount] = useState(existing ? (existing.limit_cents / 100).toFixed(0) : '')
  const [error, setError] = useState('')

  const upsertMutation = useMutation({
    mutationFn: () => budgetsApi.upsert(categoryId, month, Math.round(parseFloat(amount) * 100)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['budget-bars'] })
      onClose()
    },
    onError: (err) => setError(err?.response?.data?.detail || t('budget.saveError')),
  })

  const expenseCategories = categories.filter((c) => c.type === 'expense')
  const inputStyle = { width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(13,10,16,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '400px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)', maxHeight: 'calc(100dvh - 48px)', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {t('budget.setLimit')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('categories.title')}</label>
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} style={inputStyle} disabled={!!existing}>
              <option value="">{t('transactions.allCategories')}</option>
              {expenseCategories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
              {t('budget.limitLabel')} ({currency})
            </label>
            <input
              type="number" step="1" min="1" value={amount}
              onChange={(e) => setAmount(e.target.value)}
              style={inputStyle} placeholder="0" autoFocus
            />
          </div>

          {error && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('goals.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }}
            onClick={() => {
              if (!categoryId) { setError(t('budget.errorCategory')); return }
              if (!amount || parseFloat(amount) <= 0) { setError(t('budget.errorAmount')); return }
              upsertMutation.mutate()
            }}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: upsertMutation.isPending ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: upsertMutation.isPending ? 0.7 : 1, userSelect: 'none' }}
          >{upsertMutation.isPending ? t('goals.saving') : t('goals.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const Budget = () => {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const currency = user?.currency || 'USD'
  const month = currentMonth()

  const [modal, setModal] = useState(null)
  const queryClient = useQueryClient()

  const { data: bars = [], isLoading: barsLoading } = useQuery({
    queryKey: ['budget-bars', month],
    queryFn: () => budgetsApi.bars(month),
  })

  const { data: budgets = [] } = useQuery({
    queryKey: ['budgets', month],
    queryFn: () => budgetsApi.list(month),
  })

  const { data: categories = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (id) => budgetsApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['budget-bars'] })
    },
  })

  const budgetByCatId = Object.fromEntries(budgets.map((b) => [b.category_id, b]))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 2px' }}>{t('budget.title')}</h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{month}</p>
        </div>
        <motion.div whileTap={{ scale: 0.96 }} onClick={() => setModal({ existing: null })}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '13px', fontWeight: 500, padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> {t('budget.add')}
        </motion.div>
      </div>

      {barsLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : bars.length === 0 ? (
        <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
          style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px' }}
        >
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 4px' }}>{t('budget.empty')}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('budget.emptyHint')}</p>
        </motion.div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {bars.map((item, idx) => {
            const isOver = item.pct >= 100
            const isWarning = item.pct >= 80 && !isOver
            const barColor = isOver ? '#E52B50' : isWarning ? '#E8A020' : '#64A0FF'
            const budget = budgetByCatId[item.category_id]

            return (
              <motion.div key={String(item.category_id)} custom={idx} variants={cardVariants} initial="hidden" animate="visible"
                style={{
                  background: 'var(--surface)',
                  border: `0.5px solid var(--border-card)`,
                  borderLeft: `3px solid ${isOver ? '#E52B50' : item.color}`,
                  borderRadius: '14px',
                  padding: '16px 18px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: item.color, flexShrink: 0 }} />
                    <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>{item.name}</span>
                    {isOver && <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 7px', borderRadius: '20px', background: 'rgba(229,43,80,0.1)', color: '#E52B50' }}>{t('budget.over')}</span>}
                    {isWarning && <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 7px', borderRadius: '20px', background: 'rgba(232,160,32,0.12)', color: '#C07010' }}>80%</span>}
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {budget && (
                      <>
                        <button
                          onClick={() => setModal({ existing: { ...budget, category_id: item.category_id } })}
                          style={{ width: '26px', height: '26px', borderRadius: '7px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none' }}
                          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                        >
                          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                        </button>
                        <button
                          onClick={() => deleteMutation.mutate(budget.id)}
                          style={{ width: '26px', height: '26px', borderRadius: '7px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none' }}
                          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                        >
                          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                        </button>
                      </>
                    )}
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px' }}>
                  <span>{formatMoney(item.actual_cents, currency)} {t('budget.spent')}</span>
                  <span style={{ fontWeight: 600, color: isOver ? '#E52B50' : 'var(--text-primary)' }}>
                    {item.pct}% {t('budget.of')} {formatMoney(item.limit_cents, currency)}
                  </span>
                </div>

                <div style={{ height: '6px', borderRadius: '99px', overflow: 'hidden', background: 'var(--progress-track)' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(item.pct, 100)}%` }}
                    transition={{ duration: 0.7, ease: 'easeOut', delay: idx * 0.06 }}
                    style={{ height: '100%', borderRadius: '99px', background: barColor }}
                  />
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <AnimatePresence>
        {modal !== null && (
          <BudgetModal
            categories={categories}
            month={month}
            existing={modal.existing}
            onClose={() => setModal(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Budget
