import client from './client'

const goalsApi = {
  list: async () => {
    const { data } = await client.get('/goals')
    return data
  },

  create: async (body) => {
    const { data } = await client.post('/goals', body)
    return data
  },

  update: async (id, body) => {
    const { data } = await client.patch(`/goals/${id}`, body)
    return data
  },

  remove: async (id) => {
    const { data } = await client.delete(`/goals/${id}`)
    return data
  },
}

export default goalsApi
