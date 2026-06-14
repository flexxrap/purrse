import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import categoriesApi from '../api/categories'
import { apiError } from '../utils'

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { duration: 0.35, delay: i * 0.08 } }),
}

const CategoryModal = ({ category, onSave, onClose, loading, error }) => {
  const { t } = useTranslation()
  const [name, setName] = useState(category?.name || '')
  const [color, setColor] = useState(category?.color || '#E52B50')
  const [type, setType] = useState(category?.type || 'expense')

  const handleSave = () => {
    if (!name.trim()) return
    onSave({ name: name.trim(), color, type })
  }

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
        style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '420px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {category ? t('categories.editTitle') : t('categories.newTitle')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('categories.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} placeholder={t('categories.namePlaceholder')} maxLength={64} autoFocus />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('categories.color')}</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input type="color" value={color} onChange={(e) => setColor(e.target.value)} style={{ width: '44px', height: '44px', borderRadius: '10px', cursor: 'pointer', border: 'none', padding: '2px', background: 'transparent' }} />
              <div style={{ flex: 1, height: '44px', borderRadius: '10px', border: '1px solid var(--border-card)', background: color + '22', display: 'flex', alignItems: 'center', padding: '0 14px', gap: '8px' }}>
                <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: color, flexShrink: 0 }} />
                <span style={{ fontSize: '13px', fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{color}</span>
              </div>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('categories.type')}</label>
            <div style={{ display: 'flex', gap: '8px' }}>
              {['expense', 'income'].map((tp) => (
                <div key={tp} onClick={() => setType(tp)}
                  style={{
                    flex: 1, padding: '10px', borderRadius: '10px', textAlign: 'center', fontSize: '13px', fontWeight: 500, cursor: 'pointer', userSelect: 'none', transition: 'all 0.15s',
                    border: type === tp
                      ? tp === 'expense' ? '1px solid rgba(229,43,80,0.3)' : '1px solid rgba(16,185,129,0.3)'
                      : '1px solid var(--border-card)',
                    background: type === tp
                      ? tp === 'expense' ? 'rgba(229,43,80,0.08)' : 'rgba(16,185,129,0.08)'
                      : 'var(--surface)',
                    color: type === tp
                      ? tp === 'expense' ? 'var(--icon-a-color)' : '#059669'
                      : 'var(--text-secondary)',
                  }}
                >
                  {tp === 'expense' ? `↓ ${t('categories.expense')}` : `↑ ${t('categories.income')}`}
                </div>
              ))}
            </div>
          </div>

          {error && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('categories.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}
          >{loading ? t('categories.saving') : t('categories.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const CategoryRow = ({ category, onEdit, onDelete }) => {
  const iconBtn = { width: '28px', height: '28px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none', padding: 0 }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px' }}>
      <div style={{ width: '34px', height: '34px', borderRadius: '10px', flexShrink: 0, backgroundColor: category.color + '22', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: category.color }} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>{category.name}</span>
      </div>
      <div style={{ display: 'flex', gap: '2px' }}>
        <button style={iconBtn} onClick={() => onEdit(category)}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
        >
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
        </button>
        <button style={iconBtn} onClick={() => onDelete(category.id)}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
        >
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
        </button>
      </div>
    </div>
  )
}

const Categories = () => {
  const { t } = useTranslation()
  const [modal, setModal] = useState(null)
  const [mutError, setMutError] = useState('')

  const { data: categories = [], isLoading } = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })

  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['categories'] })

  const createMutation = useMutation({ mutationFn: categoriesApi.create, onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const updateMutation = useMutation({ mutationFn: ({ id, data }) => categoriesApi.update(id, data), onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const deleteMutation = useMutation({ mutationFn: categoriesApi.remove, onSuccess: invalidate })

  const handleSave = (formData) => {
    if (modal?.category) updateMutation.mutate({ id: modal.category.id, data: formData })
    else createMutation.mutate(formData)
  }

  const expenses = categories.filter((c) => c.type === 'expense')
  const incomes = categories.filter((c) => c.type === 'income')
  const isMutating = createMutation.isPending || updateMutation.isPending

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 2px' }}>{t('categories.title')}</h2>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('categories.count', { count: categories.length })}</p>
        </div>
        <motion.div whileTap={{ scale: 0.96 }} onClick={() => { setMutError(''); setModal({ category: null }) }}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '13px', fontWeight: 500, padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> {t('categories.add')}
        </motion.div>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : categories.length === 0 ? (
        <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
          style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px' }}
        >
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 4px' }}>{t('categories.noCategories')}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('categories.noCategoriesHint')}</p>
        </motion.div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {expenses.length > 0 && (
            <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
              style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', overflow: 'hidden' }}
            >
              <div style={{ padding: '10px 14px', background: 'var(--badge-r)', borderBottom: '1px solid var(--border-card)' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--badge-r-color)' }}>
                  ↓ {t('categories.expense')} ({expenses.length})
                </span>
              </div>
              {expenses.map((cat, i) => (
                <div key={cat.id} style={i !== 0 ? { borderTop: '1px solid var(--tx-border)' } : {}}>
                  <CategoryRow category={cat} onEdit={(c) => { setMutError(''); setModal({ category: c }) }} onDelete={(id) => deleteMutation.mutate(id)} />
                </div>
              ))}
            </motion.div>
          )}

          {incomes.length > 0 && (
            <motion.div custom={1} variants={cardVariants} initial="hidden" animate="visible"
              style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', overflow: 'hidden' }}
            >
              <div style={{ padding: '10px 14px', background: 'var(--badge-b)', borderBottom: '1px solid var(--border-card)' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--badge-b-color)' }}>
                  ↑ {t('categories.income')} ({incomes.length})
                </span>
              </div>
              {incomes.map((cat, i) => (
                <div key={cat.id} style={i !== 0 ? { borderTop: '1px solid var(--tx-border)' } : {}}>
                  <CategoryRow category={cat} onEdit={(c) => { setMutError(''); setModal({ category: c }) }} onDelete={(id) => deleteMutation.mutate(id)} />
                </div>
              ))}
            </motion.div>
          )}
        </div>
      )}

      <AnimatePresence>
        {modal !== null && (
          <CategoryModal category={modal.category} onSave={handleSave} onClose={() => setModal(null)} loading={isMutating} error={mutError} />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Categories
