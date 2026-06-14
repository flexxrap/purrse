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
}

export default transactionsApi
