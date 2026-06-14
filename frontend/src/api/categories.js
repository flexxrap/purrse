import client from './client'

const categoriesApi = {
  list: async () => {
    const { data } = await client.get('/categories')
    return data
  },

  create: async (body) => {
    const { data } = await client.post('/categories', body)
    return data
  },

  update: async (id, body) => {
    const { data } = await client.patch(`/categories/${id}`, body)
    return data
  },

  remove: async (id) => {
    const { data } = await client.delete(`/categories/${id}`)
    return data
  },
}

export default categoriesApi
