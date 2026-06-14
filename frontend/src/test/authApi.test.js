import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('../api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
  },
}))

import client from '../api/client'
import authApi from '../api/auth'

beforeEach(() => {
  vi.clearAllMocks()
})

describe('authApi.register', () => {
  it('posts to /auth/register and returns data', async () => {
    const payload = { access_token: 'tok', token_type: 'bearer', user: { id: '1' } }
    client.post.mockResolvedValue({ data: payload })

    const result = await authApi.register('a@b.com', 'pass1234')

    expect(client.post).toHaveBeenCalledWith('/auth/register', { email: 'a@b.com', password: 'pass1234' })
    expect(result).toEqual(payload)
  })
})

describe('authApi.login', () => {
  it('posts to /auth/login and returns data', async () => {
    const payload = { access_token: 'tok2', token_type: 'bearer', user: { id: '1' } }
    client.post.mockResolvedValue({ data: payload })

    const result = await authApi.login('a@b.com', 'pass1234')

    expect(client.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'pass1234' })
    expect(result).toEqual(payload)
  })
})

describe('authApi.logout', () => {
  it('posts to /auth/logout and returns data', async () => {
    client.post.mockResolvedValue({ data: { ok: true } })

    const result = await authApi.logout()

    expect(client.post).toHaveBeenCalledWith('/auth/logout')
    expect(result).toEqual({ ok: true })
  })
})

describe('authApi.getMe', () => {
  it('gets /user/me and returns data', async () => {
    const user = { id: '1', email: 'a@b.com', currency: 'USD' }
    client.get.mockResolvedValue({ data: user })

    const result = await authApi.getMe()

    expect(client.get).toHaveBeenCalledWith('/user/me')
    expect(result).toEqual(user)
  })
})

describe('authApi.updateMe', () => {
  it('patches /user/me with body and returns data', async () => {
    const updated = { id: '1', email: 'new@b.com', currency: 'EUR' }
    client.patch.mockResolvedValue({ data: updated })

    const result = await authApi.updateMe({ currency: 'EUR' })

    expect(client.patch).toHaveBeenCalledWith('/user/me', { currency: 'EUR' })
    expect(result).toEqual(updated)
  })
})

describe('authApi.changePassword', () => {
  it('posts to /user/me/password', async () => {
    client.post.mockResolvedValue({ data: undefined })

    await authApi.changePassword('old123', 'new1234')

    expect(client.post).toHaveBeenCalledWith('/user/me/password', {
      old_password: 'old123',
      new_password: 'new1234',
    })
  })
})
