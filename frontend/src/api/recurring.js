import client from './client'

const recurringApi = {
  list: () => client.get('/recurring').then(r => r.data),
  create: (data) => client.post('/recurring', data).then(r => r.data),
  update: (id, data) => client.patch(`/recurring/${id}`, data).then(r => r.data),
  remove: (id) => client.delete(`/recurring/${id}`).then(r => r.data),
}

export default recurringApi
