import client from './client'

const analyticsApi = {
  summary: async (month) => {
    const { data } = await client.get('/analytics/summary', { params: { month } })
    return data
  },

  categories: async (month) => {
    const { data } = await client.get('/analytics/categories', { params: { month } })
    return data
  },

  trend: async (months = 6) => {
    const { data } = await client.get('/analytics/trend', { params: { months } })
    return data
  },
}

export default analyticsApi
