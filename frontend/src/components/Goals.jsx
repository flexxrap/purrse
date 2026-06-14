import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import goalsApi from '../api/goals'
import useAuthStore from '../store/authStore'
import { formatMoney, formatDate, today, apiError } from '../utils'

const GOAL_GRADIENTS = [
  { bar: 'linear-gradient(90deg, #E52B50, #64A0FF)', accent: '#E52B50' },
  { bar: 'linear-gradient(90deg, #64A0FF, #2060D0)', accent: '#64A0FF' },
  { bar: 'linear-gradient(90deg, #E52B50, #AA40FF)', accent: '#AA40FF' },
  { bar: 'linear-gradient(90deg, #E8A020, #C07010)', accent: '#E8A020' },
]

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { duration: 0.35, delay: i * 0.08 } }),
}

const GoalModal = ({ goal, onSave, onClose, loading, error }) => {
  const { t } = useTranslation()
  const [name, setName] = useState(goal?.name || '')
  const [target, setTarget] = useState(goal ? (goal.target_cents / 100).toFixed(2) : '')
  const [current, setCurrent] = useState(goal ? (goal.current_cents / 100).toFixed(2) : '0')
  const [deadline, setDeadline] = useState(goal?.deadline || '')
  const [localError, setLocalError] = useState('')

  const handleSave = () => {
    const targetCents = Math.round(parseFloat(target) * 100)
    const currentCents = Math.round(parseFloat(current || 0) * 100)
    if (!name.trim() || !targetCents || targetCents <= 0) {
      setLocalError(t('goals.fillRequired'))
      return
    }
    setLocalError('')
    onSave({ name: name.trim(), target_cents: targetCents, current_cents: Math.max(0, currentCents), deadline: deadline || null })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={{ position: 'fixed', inset: 0, background: 'rgba(13,10,16,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }}
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '420px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)', maxHeight: 'calc(100dvh - 48px)', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {goal ? t('goals.editTitle') : t('goals.newTitle')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('goals.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} autoFocus
              style={{ width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
              placeholder={t('goals.namePlaceholder')}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('goals.targetAmount')}</label>
              <input type="number" step="0.01" min="0.01" value={target} onChange={(e) => setTarget(e.target.value)}
                style={{ width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
                placeholder="0.00"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('goals.savedSoFar')}</label>
              <input type="number" step="0.01" min="0" value={current} onChange={(e) => setCurrent(e.target.value)}
                style={{ width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
                placeholder="0.00"
              />
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
              {t('goals.deadline')} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({t('goals.optional')})</span>
            </label>
            <input type="date" value={deadline} min={today()} onChange={(e) => setDeadline(e.target.value)}
              style={{ width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }}
            />
          </div>

          {(localError || error) && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{localError || error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('goals.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}
          >{loading ? t('goals.saving') : t('goals.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const Goals = () => {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const currency = user?.currency || 'USD'
  const [modal, setModal] = useState(null)
  const [mutError, setMutError] = useState('')

  const { data: goals = [], isLoading } = useQuery({ queryKey: ['goals'], queryFn: goalsApi.list })

  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['goals'] })

  const createMutation = useMutation({ mutationFn: goalsApi.create, onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const updateMutation = useMutation({ mutationFn: ({ id, data }) => goalsApi.update(id, data), onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const deleteMutation = useMutation({ mutationFn: goalsApi.remove, onSuccess: invalidate })

  const handleSave = (formData) => {
    if (modal?.goal) updateMutation.mutate({ id: modal.goal.id, data: formData })
    else createMutation.mutate(formData)
  }

  const pct = (goal) => goal.target_cents > 0 ? Math.min(100, Math.round((goal.current_cents / goal.target_cents) * 100)) : 0
  const isMutating = createMutation.isPending || updateMutation.isPending

  const iconBtn = { width: '28px', height: '28px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none', padding: 0 }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{t('goals.title')}</h2>
        <motion.div whileTap={{ scale: 0.96 }} onClick={() => { setMutError(''); setModal({ goal: null }) }}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '13px', fontWeight: 500, padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> {t('goals.add')}
        </motion.div>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : goals.length === 0 ? (
        <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
          style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px' }}
        >
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 4px' }}>{t('goals.noGoals')}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('goals.noGoalsHint')}</p>
        </motion.div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {goals.map((goal, idx) => {
            const progress = pct(goal)
            const isComplete = progress >= 100
            const gradient = GOAL_GRADIENTS[idx % GOAL_GRADIENTS.length]
            return (
              <motion.div key={goal.id} custom={idx} variants={cardVariants} initial="hidden" animate="visible"
                style={{
                  background: 'var(--surface)',
                  border: '0.5px solid var(--border-card)',
                  borderTop: `3px solid ${gradient.accent}`,
                  borderRadius: '14px',
                  padding: '18px 18px 16px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{goal.name}</h3>
                      {isComplete && (
                        <span style={{ fontSize: '11px', fontWeight: 600, padding: '2px 8px', borderRadius: '20px', background: 'rgba(16,185,129,0.12)', color: '#059669' }}>
                          {t('goals.done')}
                        </span>
                      )}
                    </div>
                    {goal.deadline && (
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '3px 0 0' }}>
                        {t('goals.deadline')}: {formatDate(goal.deadline)}
                      </p>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '2px' }}>
                    <button style={iconBtn} onClick={() => { setMutError(''); setModal({ goal }) }}
                      onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                      onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                    >
                      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                    </button>
                    <button style={iconBtn} onClick={() => deleteMutation.mutate(goal.id)}
                      onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                      onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                    >
                      <svg width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{formatMoney(goal.current_cents, currency)} {t('goals.saved')}</span>
                  <span style={{ fontWeight: 600, background: gradient.bar, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    {progress}% {t('goals.of')} {formatMoney(goal.target_cents, currency)}
                  </span>
                </div>

                <div style={{ height: '6px', borderRadius: '99px', overflow: 'hidden', background: 'var(--progress-track)' }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut', delay: idx * 0.08 }}
                    style={{ height: '100%', borderRadius: '99px', background: isComplete ? '#10b981' : gradient.bar }}
                  />
                </div>

                <div style={{ marginTop: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  {formatMoney(goal.target_cents - goal.current_cents, currency)} {t('goals.remaining')}
                </div>
              </motion.div>
            )
          })}
        </div>
      )}

      <AnimatePresence>
        {modal !== null && (
          <GoalModal
            goal={modal.goal}
            onSave={handleSave}
            onClose={() => setModal(null)}
            loading={isMutating}
            error={mutError}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Goals
