import client from './client'

const accountsApi = {
  list: async () => {
    const { data } = await client.get('/accounts')
    return data
  },

  create: async (body) => {
    const { data } = await client.post('/accounts', body)
    return data
  },

  update: async (id, body) => {
    const { data } = await client.patch(`/accounts/${id}`, body)
    return data
  },

  remove: async (id) => {
    const { data } = await client.delete(`/accounts/${id}`)
    return data
  },

  listTransfers: async () => {
    const { data } = await client.get('/accounts/transfers')
    return data
  },

  createTransfer: async (body) => {
    const { data } = await client.post('/accounts/transfers', body)
    return data
  },
}

export default accountsApi
