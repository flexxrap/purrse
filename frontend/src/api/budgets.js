import client from './client'

const budgetsApi = {
  list: async (month) => {
    const { data } = await client.get('/budgets', { params: { month } })
    return data
  },

  upsert: async (category_id, month, limit_cents) => {
    const { data } = await client.post('/budgets', { category_id, month, limit_cents })
    return data
  },

  remove: async (id) => {
    await client.delete(`/budgets/${id}`)
  },

  bars: async (month) => {
    const { data } = await client.get('/analytics/budget', { params: { month } })
    return data
  },

  exportCsv: (date_from, date_to) => {
    const params = new URLSearchParams()
    if (date_from) params.set('date_from', date_from)
    if (date_to) params.set('date_to', date_to)
    const url = `${import.meta.env.VITE_API_URL}/transactions/export/csv?${params}`
    window.open(url, '_blank')
  },
}

export default budgetsApi
