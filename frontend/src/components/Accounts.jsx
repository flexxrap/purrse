import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import accountsApi from '../api/accounts'
import useAuthStore from '../store/authStore'
import { formatMoney, formatDate, today, apiError } from '../utils'

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { duration: 0.35, delay: i * 0.08 } }),
}

const ACCOUNT_TYPES = ['cash', 'card', 'savings', 'other']
const ACCOUNT_TYPE_ICONS = { cash: '💵', card: '💳', savings: '🏦', other: '📦' }

const overlayStyle = { position: 'fixed', inset: 0, background: 'rgba(13,10,16,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }
const cardStyle = { background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '420px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)', maxHeight: 'calc(100dvh - 48px)', overflowY: 'auto' }
const inputStyle = { width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }
const labelStyle = { display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }
const errorStyle = { background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }

const AccountModal = ({ account, onSave, onClose, loading, error }) => {
  const { t } = useTranslation()
  const [name, setName] = useState(account?.name || '')
  const [type, setType] = useState(account?.type || 'cash')
  const [initialBalance, setInitialBalance] = useState(account ? (account.initial_balance_cents / 100).toFixed(2) : '0.00')
  const [isArchived, setIsArchived] = useState(account?.is_archived || false)
  const [localError, setLocalError] = useState('')

  const handleSave = () => {
    if (!name.trim()) { setLocalError(t('accounts.nameRequired')); return }
    const initialBalanceCents = Math.round(parseFloat(initialBalance || '0') * 100)
    if (isNaN(initialBalanceCents)) { setLocalError(t('accounts.balanceInvalid')); return }
    setLocalError('')
    const body = { name: name.trim(), type, initial_balance_cents: initialBalanceCents }
    if (account) body.is_archived = isArchived
    onSave(body)
  }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={overlayStyle} onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        style={cardStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {account ? t('accounts.editTitle') : t('accounts.newTitle')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={labelStyle}>{t('accounts.name')}</label>
            <input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} placeholder={t('accounts.namePlaceholder')} maxLength={64} autoFocus />
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.type')}</label>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {ACCOUNT_TYPES.map((tp) => (
                <div key={tp} onClick={() => setType(tp)}
                  style={{
                    flex: '1 1 70px', padding: '10px', borderRadius: '10px', textAlign: 'center', fontSize: '13px', fontWeight: 500, cursor: 'pointer', userSelect: 'none', transition: 'all 0.15s',
                    border: type === tp ? '1px solid rgba(229,43,80,0.3)' : '1px solid var(--border-card)',
                    background: type === tp ? 'rgba(229,43,80,0.08)' : 'var(--surface)',
                    color: type === tp ? 'var(--amaranth)' : 'var(--text-secondary)',
                  }}
                >
                  {ACCOUNT_TYPE_ICONS[tp]} {t(`accounts.type_${tp}`)}
                </div>
              ))}
            </div>
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.initialBalance')}</label>
            <input type="number" step="0.01" value={initialBalance} onChange={(e) => setInitialBalance(e.target.value)} style={inputStyle} placeholder="0.00" />
          </div>

          {account && (
            <div onClick={() => setIsArchived((a) => !a)} style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', userSelect: 'none' }}>
              <div style={{
                width: '36px', height: '20px', borderRadius: '10px', flexShrink: 0, position: 'relative', transition: 'background 0.15s',
                background: isArchived ? 'var(--amaranth)' : 'var(--border-card)',
              }}>
                <div style={{
                  width: '16px', height: '16px', borderRadius: '50%', background: 'white', position: 'absolute', top: '2px',
                  left: isArchived ? '18px' : '2px', transition: 'left 0.15s',
                }} />
              </div>
              <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>{t('accounts.archived')}</span>
            </div>
          )}

          {(localError || error) && <div style={errorStyle}>{localError || error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('accounts.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}
          >{loading ? t('accounts.saving') : t('accounts.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const TransferModal = ({ accounts, onSave, onClose, loading, error }) => {
  const { t } = useTranslation()
  const [fromId, setFromId] = useState(accounts[0]?.id || '')
  const [toId, setToId] = useState(accounts.find((a) => a.id !== accounts[0]?.id)?.id || '')
  const [amount, setAmount] = useState('')
  const [txDate, setTxDate] = useState(today())
  const [note, setNote] = useState('')
  const [localError, setLocalError] = useState('')

  const handleSave = () => {
    const amountCents = Math.round(parseFloat(amount) * 100)
    if (!amountCents || amountCents <= 0 || !fromId || !toId || !txDate) {
      setLocalError(t('accounts.transferFillRequired'))
      return
    }
    if (fromId === toId) {
      setLocalError(t('accounts.transferSameAccount'))
      return
    }
    setLocalError('')
    onSave({ from_account_id: fromId, to_account_id: toId, amount_cents: amountCents, tx_date: txDate, note: note.trim() || null })
  }

  return (
    <motion.div
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={overlayStyle} onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95 }}
        transition={{ duration: 0.2 }}
        style={cardStyle}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {t('accounts.transferTitle')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={labelStyle}>{t('accounts.transferFrom')}</label>
            <select value={fromId} onChange={(e) => setFromId(e.target.value)} style={inputStyle}>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.transferTo')}</label>
            <select value={toId} onChange={(e) => setToId(e.target.value)} style={inputStyle}>
              {accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.amount')}</label>
            <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} style={inputStyle} placeholder="0.00" />
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.date')}</label>
            <input type="date" value={txDate} onChange={(e) => setTxDate(e.target.value)} style={inputStyle} />
          </div>

          <div>
            <label style={labelStyle}>{t('accounts.note')} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({t('accounts.optional')})</span></label>
            <input type="text" value={note} onChange={(e) => setNote(e.target.value)} style={inputStyle} maxLength={500} />
          </div>

          {(localError || error) && <div style={errorStyle}>{localError || error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('accounts.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}
          >{loading ? t('accounts.saving') : t('accounts.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const AccountRow = ({ account, currency, onEdit, onDelete }) => {
  const iconBtn = { width: '28px', height: '28px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none', padding: 0 }
  const { t } = useTranslation()
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '10px 14px', opacity: account.is_archived ? 0.5 : 1 }}>
      <div style={{ width: '34px', height: '34px', borderRadius: '10px', flexShrink: 0, background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '16px' }}>
        {ACCOUNT_TYPE_ICONS[account.type] || '📦'}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{account.name}</span>
          {account.is_archived && <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>({t('accounts.archived')})</span>}
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t(`accounts.type_${account.type}`)}</span>
      </div>
      <div style={{ fontSize: '13px', fontWeight: 600, flexShrink: 0, color: account.balance_cents < 0 ? 'var(--amaranth)' : 'var(--text-primary)' }}>
        {formatMoney(account.balance_cents, currency)}
      </div>
      <div style={{ display: 'flex', gap: '2px', flexShrink: 0 }}>
        <button style={iconBtn} onClick={() => onEdit(account)}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
        >
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
        </button>
        <button style={iconBtn} onClick={() => onDelete(account.id)}
          onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
          onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
        >
          <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
        </button>
      </div>
    </div>
  )
}

const Accounts = () => {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const currency = user?.currency || 'USD'

  const [modal, setModal] = useState(null)
  const [showTransfer, setShowTransfer] = useState(false)
  const [mutError, setMutError] = useState('')
  const [deleteError, setDeleteError] = useState('')

  const { data: accounts = [], isLoading } = useQuery({ queryKey: ['accounts'], queryFn: accountsApi.list })
  const { data: transfers = [] } = useQuery({ queryKey: ['transfers'], queryFn: accountsApi.listTransfers })
  const accountMap = Object.fromEntries(accounts.map((a) => [a.id, a]))

  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['accounts'] })
  const invalidateTransfers = () => queryClient.invalidateQueries({ queryKey: ['transfers'] })

  const createMutation = useMutation({ mutationFn: accountsApi.create, onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const updateMutation = useMutation({ mutationFn: ({ id, data }) => accountsApi.update(id, data), onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const deleteMutation = useMutation({
    mutationFn: accountsApi.remove,
    onSuccess: () => { invalidate(); setDeleteError('') },
    onError: (err) => setDeleteError(apiError(err)),
  })
  const transferMutation = useMutation({
    mutationFn: accountsApi.createTransfer,
    onSuccess: () => { invalidate(); invalidateTransfers(); setShowTransfer(false); setMutError('') },
    onError: (err) => setMutError(apiError(err)),
  })

  const handleSave = (formData) => {
    if (modal?.account) updateMutation.mutate({ id: modal.account.id, data: formData })
    else createMutation.mutate(formData)
  }

  const isMutating = createMutation.isPending || updateMutation.isPending

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{t('accounts.title')}</h2>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {accounts.length >= 2 && (
            <motion.div whileTap={{ scale: 0.96 }} onClick={() => { setMutError(''); setShowTransfer(true) }}
              style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'var(--surface)', border: '0.5px solid var(--border-card)', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500, padding: '8px 12px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
            >
              <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4M16 17H4m0 0l4 4m-4-4l4-4" /></svg>
              {t('accounts.transfer')}
            </motion.div>
          )}
          <motion.div whileTap={{ scale: 0.96 }} onClick={() => { setMutError(''); setModal({ account: null }) }}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '13px', fontWeight: 500, padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
          >
            <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> {t('accounts.add')}
          </motion.div>
        </div>
      </div>

      {deleteError && <div style={errorStyle}>{deleteError}</div>}

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : accounts.length === 0 ? (
        <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
          style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px' }}
        >
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 4px' }}>{t('accounts.noAccounts')}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('accounts.noAccountsHint')}</p>
        </motion.div>
      ) : (
        <motion.div custom={0} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', overflow: 'hidden' }}
        >
          {accounts.map((account, i) => (
            <div key={account.id} style={i !== 0 ? { borderTop: '1px solid var(--tx-border)' } : {}}>
              <AccountRow
                account={account} currency={currency}
                onEdit={(a) => { setMutError(''); setModal({ account: a }) }}
                onDelete={(id) => { setDeleteError(''); deleteMutation.mutate(id) }}
              />
            </div>
          ))}
        </motion.div>
      )}

      {transfers.length > 0 && (
        <motion.div custom={1} variants={cardVariants} initial="hidden" animate="visible"
          style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '16px' }}
        >
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 12px' }}>{t('accounts.transfersTitle')}</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {transfers.map((tr) => (
              <div key={tr.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg)', borderRadius: '10px', border: '1px solid var(--border-card)' }}>
                <div style={{ minWidth: 0, overflow: 'hidden' }}>
                  <div style={{ fontSize: '13px', color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {accountMap[tr.from_account_id]?.name || '—'} → {accountMap[tr.to_account_id]?.name || '—'}
                  </div>
                  {tr.note && <div style={{ fontSize: '11px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{tr.note}</div>}
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0, marginLeft: '12px' }}>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>{formatMoney(tr.amount_cents, currency)}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{formatDate(tr.tx_date)}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {modal !== null && (
          <AccountModal account={modal.account} onSave={handleSave} onClose={() => setModal(null)} loading={isMutating} error={mutError} />
        )}
        {showTransfer && (
          <TransferModal accounts={accounts} onSave={(body) => transferMutation.mutate(body)} onClose={() => setShowTransfer(false)} loading={transferMutation.isPending} error={mutError} />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Accounts
