import { describe, it, expect, beforeEach } from 'vitest'
import useAuthStore from '../store/authStore'

describe('authStore', () => {
  beforeEach(() => {
    useAuthStore.setState({ accessToken: null, user: null, initialized: false })
  })

  it('initial state is empty', () => {
    const { accessToken, user, initialized } = useAuthStore.getState()
    expect(accessToken).toBeNull()
    expect(user).toBeNull()
    expect(initialized).toBe(false)
  })

  it('setAuth stores token and user', () => {
    const testUser = { id: '1', email: 'a@b.com' }
    useAuthStore.getState().setAuth('tok_abc', testUser)
    const { accessToken, user } = useAuthStore.getState()
    expect(accessToken).toBe('tok_abc')
    expect(user).toEqual(testUser)
  })

  it('clearAuth resets token and user to null', () => {
    useAuthStore.getState().setAuth('tok_abc', { id: '1' })
    useAuthStore.getState().clearAuth()
    const { accessToken, user } = useAuthStore.getState()
    expect(accessToken).toBeNull()
    expect(user).toBeNull()
  })

  it('clearAuth does not reset initialized flag', () => {
    useAuthStore.getState().setInitialized()
    useAuthStore.getState().clearAuth()
    expect(useAuthStore.getState().initialized).toBe(true)
  })

  it('setInitialized flips flag to true', () => {
    expect(useAuthStore.getState().initialized).toBe(false)
    useAuthStore.getState().setInitialized()
    expect(useAuthStore.getState().initialized).toBe(true)
  })

  it('replacing token does not clear user', () => {
    const user = { id: '1', email: 'a@b.com' }
    useAuthStore.getState().setAuth('tok_old', user)
    useAuthStore.getState().setAuth('tok_new', user)
    expect(useAuthStore.getState().accessToken).toBe('tok_new')
    expect(useAuthStore.getState().user).toEqual(user)
  })
})
