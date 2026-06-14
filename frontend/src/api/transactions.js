import client from './client'

const transactionsApi = {
  list: async (params = {}) => {
    const cleaned = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== '' && v != null)
    )
    const { data } = await client.get('/transactions', { params: cleaned })
    return data
  },

  create: async (body) => {
    const { data } = await client.post('/transactions', body)
    return data
  },

  update: async (id, body) => {
    const { data } = await client.patch(`/transactions/${id}`, body)
    return data
  },

  remove: async (id) => {
    const { data } = await client.delete(`/transactions/${id}`)
    return data
  },

  importPreview: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return client.post('/transactions/import/preview', fd).then(r => r.data)
  },
  importConfirm: (file, mapping, accountId) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('mapping', JSON.stringify(mapping))
    fd.append('account_id', accountId)
    return client.post('/transactions/import/confirm', fd).then(r => r.data)
  },
}

export default transactionsApi
