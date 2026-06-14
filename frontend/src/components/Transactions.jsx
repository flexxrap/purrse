import { useEffect, useRef, useState } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import transactionsApi from '../api/transactions'
import budgetsApi from '../api/budgets'
import categoriesApi from '../api/categories'
import recurringApi from '../api/recurring'
import useAuthStore from '../store/authStore'
import { formatMoney, formatDate, today, firstOfMonth, apiError } from '../utils'

const overlayStyle = { position: 'fixed', inset: 0, background: 'rgba(13,10,16,0.5)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 50, padding: '16px' }
const cardStyle = { background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '460px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)', maxHeight: 'calc(100dvh - 48px)', overflowY: 'auto' }
const inputStyle2 = { width: '100%', borderRadius: '10px', padding: '10px 14px', fontSize: '14px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }

const ImportCsvModal = ({ onClose, onSuccess }) => {
  const { t } = useTranslation()
  const [step, setStep] = useState(1)
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [mapping, setMapping] = useState({ date_col: 0, amount_col: 1, category_col: null, note_col: null })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const fileRef = useRef()

  const handleFileChange = (e) => {
    setFile(e.target.files[0] || null)
    setError('')
  }

  const handlePreview = async () => {
    if (!file) { setError(t('transactions.importSelectFile')); return }
    setLoading(true)
    setError('')
    try {
      const data = await transactionsApi.importPreview(file)
      setPreview(data)
      setStep(2)
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }

  const handleConfirm = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await transactionsApi.importConfirm(file, mapping)
      setResult(data)
      setStep(3)
      onSuccess()
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }

  const colOptions = (preview?.headers || []).map((h, i) => ({ label: `${i}: ${h}`, value: i }))

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={overlayStyle} onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.2 }}
        style={cardStyle} onClick={(e) => e.stopPropagation()}>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            {step === 1 ? t('transactions.importTitle1') : step === 2 ? t('transactions.importTitle2') : t('transactions.importTitle3')}
          </h3>
          <div style={{ display: 'flex', gap: '4px' }}>
            {[1, 2, 3].map(s => (
              <div key={s} style={{ width: '24px', height: '4px', borderRadius: '2px', background: s <= step ? 'var(--amaranth)' : 'var(--border-card)' }} />
            ))}
          </div>
        </div>

        {step === 1 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              {t('transactions.importHint')}
            </p>
            <div
              style={{ border: '2px dashed var(--border-card)', borderRadius: '12px', padding: '32px 16px', textAlign: 'center', cursor: 'pointer' }}
              onClick={() => fileRef.current?.click()}
            >
              <input ref={fileRef} type="file" accept=".csv,text/csv" style={{ display: 'none' }} onChange={handleFileChange} />
              {file
                ? <span style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 500 }}>{file.name}</span>
                : <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{t('transactions.importChoose')}</span>
              }
            </div>
            {error && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>}
            <div style={{ display: 'flex', gap: '10px' }}>
              <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
                style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}>
                {t('transactions.cancel')}
              </motion.div>
              <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handlePreview}
                style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}>
                {loading ? t('transactions.loading') : t('transactions.next')}
              </motion.div>
            </div>
          </div>
        )}

        {step === 2 && preview && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              {t('transactions.importFound', { count: preview.total_rows })}
            </p>
            {[
              { label: t('transactions.importDateCol'), key: 'date_col', required: true },
              { label: t('transactions.importAmountCol'), key: 'amount_col', required: true },
              { label: t('transactions.importCategoryCol'), key: 'category_col', required: false },
              { label: t('transactions.importNoteCol'), key: 'note_col', required: false },
            ].map(({ label, key, required }) => (
              <div key={key}>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{label}</label>
                <select
                  value={mapping[key] === null ? '' : mapping[key]}
                  onChange={(e) => setMapping(m => ({ ...m, [key]: e.target.value === '' ? null : parseInt(e.target.value, 10) }))}
                  style={inputStyle2}
                >
                  {!required && <option value="">{t('transactions.importSkip')}</option>}
                  {colOptions.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              </div>
            ))}
            {preview.rows.length > 0 && (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', fontSize: '11px', borderCollapse: 'collapse', color: 'var(--text-secondary)' }}>
                  <thead>
                    <tr>{preview.headers.map((h, i) => <th key={i} style={{ padding: '4px 8px', borderBottom: '1px solid var(--border-card)', textAlign: 'left', whiteSpace: 'nowrap' }}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {preview.rows.slice(0, 3).map((row, ri) => (
                      <tr key={ri}>{row.map((cell, ci) => <td key={ci} style={{ padding: '4px 8px', borderBottom: '1px solid var(--tx-border)', whiteSpace: 'nowrap', maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis' }}>{cell}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {error && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>}
            <div style={{ display: 'flex', gap: '10px' }}>
              <motion.div whileTap={{ scale: 0.97 }} onClick={() => { setStep(1); setError('') }}
                style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}>
                {t('transactions.back')}
              </motion.div>
              <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleConfirm}
                style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}>
                {loading ? t('transactions.importing') : t('transactions.import')}
              </motion.div>
            </div>
          </div>
        )}

        {step === 3 && result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '36px' }}>✓</div>
            <p style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>{t('transactions.importDone')}</p>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              {t('transactions.importStats', { created: result.created, skipped: result.skipped })}
            </p>
            <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
              style={{ borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: 'pointer', background: 'var(--amaranth-btn)', color: 'white', userSelect: 'none' }}>
              {t('transactions.close')}
            </motion.div>
          </div>
        )}
      </motion.div>
    </motion.div>
  )
}

const RecurringModal = ({ onClose, onSuccess }) => {
  const { t } = useTranslation()
  const [amount, setAmount] = useState('')
  const [frequency, setFrequency] = useState('monthly')
  const [startDate, setStartDate] = useState(today())
  const [note, setNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSave = async () => {
    const amountCents = Math.round(parseFloat(amount) * 100)
    if (!amountCents || amountCents <= 0 || !startDate) {
      setError(t('transactions.recurringError'))
      return
    }
    setLoading(true)
    setError('')
    try {
      await recurringApi.create({ amount_cents: amountCents, frequency, start_date: startDate, note: note.trim() || null })
      onSuccess()
      onClose()
    } catch (e) {
      setError(apiError(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
      style={overlayStyle} onClick={onClose}>
      <motion.div initial={{ opacity: 0, scale: 0.95, y: 8 }} animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }} transition={{ duration: 0.2 }}
        style={{ ...cardStyle, maxWidth: '380px' }} onClick={(e) => e.stopPropagation()}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>{t('transactions.recurringNew')}</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.amount')}</label>
            <input type="number" step="0.01" min="0.01" value={amount} onChange={e => setAmount(e.target.value)} style={inputStyle2} placeholder="0.00" autoFocus />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.frequency')}</label>
            <select value={frequency} onChange={e => setFrequency(e.target.value)} style={inputStyle2}>
              <option value="weekly">{t('transactions.weekly')}</option>
              <option value="monthly">{t('transactions.monthly')}</option>
              <option value="yearly">{t('transactions.yearly')}</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.startDate')}</label>
            <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} style={inputStyle2} />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.note')} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({t('transactions.optional')})</span></label>
            <input type="text" value={note} onChange={e => setNote(e.target.value)} style={inputStyle2} maxLength={500} />
          </div>
          {error && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{error}</div>}
        </div>
        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}>
            {t('transactions.cancel')}
          </motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}>
            {loading ? t('transactions.saving') : t('transactions.save')}
          </motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const TransactionModal = ({ transaction, categories, onSave, onClose, loading, error, initialType }) => {
  const { t } = useTranslation()
  const defaultCat = transaction?.category_id
    || (initialType ? (categories.find((c) => c.type === initialType)?.id || '') : '')
  const [amount, setAmount] = useState(transaction ? (transaction.amount_cents / 100).toFixed(2) : '')
  const [categoryId, setCategoryId] = useState(defaultCat)
  const [txDate, setTxDate] = useState(transaction?.tx_date || today())
  const [note, setNote] = useState(transaction?.note || '')
  const [localError, setLocalError] = useState('')

  const handleSave = () => {
    const amountCents = Math.round(parseFloat(amount) * 100)
    if (!amountCents || amountCents <= 0 || !categoryId || !txDate) {
      setLocalError(t('transactions.fillRequired'))
      return
    }
    setLocalError('')
    onSave({ amount_cents: amountCents, category_id: categoryId, tx_date: txDate, note: note.trim() || null })
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
        style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '16px', padding: '24px', width: '100%', maxWidth: '420px', boxShadow: '0 8px 40px rgba(0,0,0,0.2)', maxHeight: 'calc(100dvh - 48px)', overflowY: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: 0, marginBottom: '20px' }}>
          {transaction ? t('transactions.editTitle') : t('transactions.newTitle')}
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.amount')}</label>
            <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} style={inputStyle} placeholder="0.00" autoFocus />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.category')}</label>
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} style={{ ...inputStyle }}>
              <option value="">{t('transactions.allCategories')}</option>
              <optgroup label={t('transactions.expense')}>
                {categories.filter((c) => c.type === 'expense').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
              <optgroup label={t('transactions.income')}>
                {categories.filter((c) => c.type === 'income').map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </optgroup>
            </select>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>{t('transactions.date')}</label>
            <input type="date" value={txDate} onChange={(e) => setTxDate(e.target.value)} style={inputStyle} />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', marginBottom: '6px' }}>
              {t('transactions.note')} <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>({t('transactions.optional')})</span>
            </label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} style={{ ...inputStyle, resize: 'none' }} rows={2} placeholder={t('transactions.notePlaceholder')} maxLength={500} />
          </div>

          {(localError || error) && <div style={{ background: 'rgba(229,43,80,0.08)', border: '1px solid rgba(229,43,80,0.2)', color: '#E52B50', fontSize: '13px', borderRadius: '10px', padding: '10px 14px' }}>{localError || error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <motion.div whileTap={{ scale: 0.97 }} onClick={onClose}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 500, textAlign: 'center', cursor: 'pointer', border: '1px solid var(--border-card)', color: 'var(--text-primary)', background: 'var(--surface)', userSelect: 'none' }}
          >{t('transactions.cancel')}</motion.div>
          <motion.div whileTap={{ scale: 0.97 }} onClick={loading ? undefined : handleSave}
            style={{ flex: 1, borderRadius: '10px', padding: '11px', fontSize: '13px', fontWeight: 600, textAlign: 'center', cursor: loading ? 'not-allowed' : 'pointer', background: 'var(--amaranth-btn)', color: 'white', opacity: loading ? 0.7 : 1, userSelect: 'none' }}
          >{loading ? t('transactions.saving') : t('transactions.save')}</motion.div>
        </div>
      </motion.div>
    </motion.div>
  )
}

const Transactions = ({ quickAdd, onQuickAddConsumed }) => {
  const { user } = useAuthStore()
  const { t } = useTranslation()
  const currency = user?.currency || 'USD'

  const [filters, setFilters] = useState({ date_from: firstOfMonth(), date_to: today(), category_id: '', type: '', search: '' })
  const [modal, setModal] = useState(null)
  const [mutError, setMutError] = useState('')
  const [showImport, setShowImport] = useState(false)
  const [showRecurringModal, setShowRecurringModal] = useState(false)

  // Open the add-transaction modal automatically when triggered from Overview quick-add
  useEffect(() => {
    if (quickAdd) {
      setMutError('')
      setModal({ tx: null, type: quickAdd })
      onQuickAddConsumed?.()
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quickAdd])

  const { data: categories = [] } = useQuery({ queryKey: ['categories'], queryFn: categoriesApi.list })
  const categoryMap = Object.fromEntries(categories.map((c) => [c.id, c]))

  const { data: recurringList = [] } = useQuery({ queryKey: ['recurring'], queryFn: recurringApi.list })
  const queryClient = useQueryClient()
  const deleteRecurringMutation = useMutation({ mutationFn: recurringApi.remove, onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recurring'] }) })

  const { data, isLoading, isFetchingNextPage, fetchNextPage, hasNextPage } = useInfiniteQuery({
    queryKey: ['transactions', filters],
    queryFn: ({ pageParam }) => transactionsApi.list({
      ...filters,
      search: filters.search.length >= 3 ? filters.search : undefined,
      cursor: pageParam,
      limit: 50,
    }),
    initialPageParam: undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor || undefined,
  })

  const allItems = data?.pages.flatMap((p) => p.items) || []
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['transactions'] })

  const createMutation = useMutation({ mutationFn: transactionsApi.create, onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const updateMutation = useMutation({ mutationFn: ({ id, data: body }) => transactionsApi.update(id, body), onSuccess: () => { invalidate(); setModal(null); setMutError('') }, onError: (err) => setMutError(apiError(err)) })
  const deleteMutation = useMutation({ mutationFn: transactionsApi.remove, onSuccess: invalidate })

  const handleSave = (formData) => {
    if (modal?.tx) updateMutation.mutate({ id: modal.tx.id, data: formData })
    else createMutation.mutate(formData)
  }

  const isMutating = createMutation.isPending || updateMutation.isPending

  const inputStyle = { width: '100%', borderRadius: '8px', padding: '8px 12px', fontSize: '13px', border: '1px solid var(--border-card)', background: 'var(--surface)', color: 'var(--text-primary)', outline: 'none', boxSizing: 'border-box' }
  const iconBtn = { width: '28px', height: '28px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: 'var(--text-muted)', background: 'transparent', border: 'none', padding: 0 }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
        <h2 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{t('transactions.title')}</h2>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <motion.div whileTap={{ scale: 0.96 }}
            onClick={() => budgetsApi.exportCsv(filters.date_from, filters.date_to)}
            style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'var(--surface)', border: '0.5px solid var(--border-card)', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500, padding: '8px 12px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
          >
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
            CSV
          </motion.div>
          <motion.div whileTap={{ scale: 0.96 }}
            onClick={() => setShowImport(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'var(--surface)', border: '0.5px solid var(--border-card)', color: 'var(--text-secondary)', fontSize: '13px', fontWeight: 500, padding: '8px 12px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
          >
            <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4 4l4-4m0 0l4 4m-4-4V4" /></svg>
            Import
          </motion.div>
          <motion.div whileTap={{ scale: 0.96 }} onClick={() => { setMutError(''); setModal({ tx: null }) }}
            style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '13px', fontWeight: 500, padding: '8px 14px', borderRadius: '10px', cursor: 'pointer', userSelect: 'none' }}
          >
            <span style={{ fontSize: '16px', lineHeight: 1 }}>+</span> {t('transactions.add')}
          </motion.div>
        </div>
      </div>

      {/* Filters */}
      <div style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '14px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px' }} className="sm:grid-cols-4">
          {[
            { label: t('transactions.from'), key: 'date_from', type: 'date' },
            { label: t('transactions.to'), key: 'date_to', type: 'date' },
          ].map(({ label, key, type }) => (
            <div key={key}>
              <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>{label}</label>
              <input type={type} value={filters[key]} onChange={(e) => setFilters((f) => ({ ...f, [key]: e.target.value }))} style={inputStyle} />
            </div>
          ))}
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>{t('transactions.category')}</label>
            <select value={filters.category_id} onChange={(e) => setFilters((f) => ({ ...f, category_id: e.target.value }))} style={inputStyle}>
              <option value="">{t('transactions.allCategories')}</option>
              {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '4px' }}>{t('transactions.type')}</label>
            <select value={filters.type} onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value }))} style={inputStyle}>
              <option value="">{t('transactions.allTypes')}</option>
              <option value="expense">{t('transactions.expense')}</option>
              <option value="income">{t('transactions.income')}</option>
            </select>
          </div>
        </div>
        <div style={{ marginTop: '10px', position: 'relative' }}>
          <input
            type="text"
            value={filters.search}
            onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
            style={{ ...inputStyle, paddingLeft: '36px' }}
            placeholder={`${t('transactions.search')} — ${t('transactions.searchHint')}`}
          />
          <svg
            style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }}
            width="14" height="14" fill="none" viewBox="0 0 24 24" stroke="var(--text-muted)" strokeWidth="2"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
          </svg>
          {filters.search.length > 0 && filters.search.length < 3 && (
            <span style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', fontSize: '11px', color: 'var(--text-muted)' }}>
              {t('transactions.searchHint')}
            </span>
          )}
        </div>
      </div>

      {isLoading ? (
        <div style={{ display: 'flex', justifyContent: 'center', padding: '48px 0' }}>
          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '3px solid var(--border-card)', borderTopColor: 'var(--amaranth)', animation: 'spin 0.8s linear infinite' }} />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      ) : allItems.length === 0 ? (
        <div style={{ padding: '48px 24px', textAlign: 'center', background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px' }}>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: '0 0 4px' }}>{t('transactions.noFound')}</p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t('transactions.noFoundHint')}</p>
        </div>
      ) : (
        <div style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', overflow: 'hidden' }}>
          {allItems.map((tx, i) => {
            const cat = categoryMap[tx.category_id]
            const isExpense = cat?.type === 'expense'
            return (
              <div
                key={tx.id}
                style={{
                  display: 'flex', alignItems: 'center', gap: '12px',
                  padding: '12px 16px',
                  borderTop: i !== 0 ? '1px solid var(--tx-border)' : 'none',
                }}
              >
                <div style={{ width: '36px', height: '36px', borderRadius: '10px', flexShrink: 0, backgroundColor: (cat?.color || '#E52B50') + '22', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: cat?.color || '#E52B50' }} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{cat?.name || 'Uncategorized'}</span>
                    {tx.note && <span style={{ fontSize: '12px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} className="hidden sm:block">— {tx.note}</span>}
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{formatDate(tx.tx_date)}</span>
                </div>

                <div style={{ fontSize: '13px', fontWeight: 600, flexShrink: 0, color: isExpense ? 'var(--amaranth)' : '#10b981' }}>
                  {isExpense ? '−' : '+'}{formatMoney(tx.amount_cents, currency)}
                </div>

                <div style={{ display: 'flex', gap: '2px', flexShrink: 0 }}>
                  <button style={iconBtn} onClick={() => { setMutError(''); setModal({ tx }) }}
                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                  >
                    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  </button>
                  <button style={iconBtn} onClick={() => deleteMutation.mutate(tx.id)}
                    onMouseEnter={e => { e.currentTarget.style.color = 'var(--amaranth)'; e.currentTarget.style.background = 'rgba(229,43,80,0.08)' }}
                    onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent' }}
                  >
                    <svg width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            )
          })}

          {hasNextPage && (
            <div style={{ borderTop: '1px solid var(--tx-border)', padding: '12px 16px', textAlign: 'center' }}>
              <span
                onClick={() => fetchNextPage()}
                style={{ fontSize: '13px', fontWeight: 500, cursor: 'pointer', color: isFetchingNextPage ? 'var(--text-muted)' : 'var(--amaranth)', opacity: isFetchingNextPage ? 0.6 : 1 }}
              >
                {isFetchingNextPage ? t('transactions.loading') : t('transactions.loadMore')}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Recurring section */}
      <div style={{ background: 'var(--surface)', border: '0.5px solid var(--border-card)', borderRadius: '14px', padding: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>{t('transactions.recurringTitle')}</h3>
          <motion.div whileTap={{ scale: 0.96 }} onClick={() => setShowRecurringModal(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '5px', background: 'var(--amaranth-btn)', color: 'white', fontSize: '12px', fontWeight: 500, padding: '6px 10px', borderRadius: '8px', cursor: 'pointer', userSelect: 'none' }}>
            <span style={{ fontSize: '14px', lineHeight: 1 }}>+</span> {t('transactions.add')}
          </motion.div>
        </div>
        {recurringList.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>{t('transactions.recurringNone')}</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {recurringList.map((rt) => (
              <div key={rt.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg)', borderRadius: '10px', border: '1px solid var(--border-card)', opacity: rt.is_active ? 1 : 0.5 }}>
                <div>
                  <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-primary)' }}>{formatMoney(rt.amount_cents, currency)}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)', marginLeft: '8px' }}>{t(`transactions.${rt.frequency}`)}</span>
                  {rt.note && <span style={{ fontSize: '12px', color: 'var(--text-secondary)', marginLeft: '8px' }}>— {rt.note}</span>}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t('transactions.nextDate')}: {rt.next_date}</span>
                  <button
                    style={{ width: '24px', height: '24px', borderRadius: '6px', border: 'none', background: 'transparent', cursor: 'pointer', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 0 }}
                    onClick={() => deleteRecurringMutation.mutate(rt.id)}
                  >
                    <svg width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {modal !== null && (
          <TransactionModal
            transaction={modal.tx} categories={categories}
            onSave={handleSave} onClose={() => setModal(null)}
            loading={isMutating} error={mutError} initialType={modal.type}
          />
        )}
        {showImport && (
          <ImportCsvModal
            onClose={() => setShowImport(false)}
            onSuccess={invalidate}
          />
        )}
        {showRecurringModal && (
          <RecurringModal
            onClose={() => setShowRecurringModal(false)}
            onSuccess={() => queryClient.invalidateQueries({ queryKey: ['recurring'] })}
          />
        )}
      </AnimatePresence>
    </div>
  )
}

export default Transactions
