import client from './client'

const authApi = {
  register: async (email, password) => {
    const { data } = await client.post('/auth/register', { email, password })
    return data
  },

  login: async (email, password) => {
    const { data } = await client.post('/auth/login', { email, password })
    return data
  },

  logout: async () => {
    const { data } = await client.post('/auth/logout')
    return data
  },

  getMe: async () => {
    const { data } = await client.get('/user/me')
    return data
  },

  updateMe: async (body) => {
    const { data } = await client.patch('/user/me', body)
    return data
  },

  refresh: async () => {
    const { data } = await client.post('/auth/refresh')
    return data
  },
}

export default authApi
