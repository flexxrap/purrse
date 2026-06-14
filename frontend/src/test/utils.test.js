import { describe, it, expect } from 'vitest'
import { formatMoney, formatDate, currentMonth, today, firstOfMonth, apiError } from '../utils'

describe('formatMoney', () => {
  it('formats cents as currency string', () => {
    expect(formatMoney(1050, 'USD')).toBe('$10.50')
  })

  it('formats zero correctly', () => {
    expect(formatMoney(0, 'USD')).toBe('$0.00')
  })

  it('returns em-dash for null', () => {
    expect(formatMoney(null)).toBe('—')
  })

  it('returns em-dash for undefined', () => {
    expect(formatMoney(undefined)).toBe('—')
  })

  it('includes currency code and amount for any 3-letter code', () => {
    const result = formatMoney(1000, 'ZZZ')
    expect(result).toContain('ZZZ')
    expect(result).toContain('10.00')
  })

  it('defaults currency to USD', () => {
    expect(formatMoney(100)).toBe('$1.00')
  })
})

describe('formatDate', () => {
  it('formats a date string', () => {
    expect(formatDate('2024-01-15')).toBe('Jan 15, 2024')
  })

  it('returns em-dash for null', () => {
    expect(formatDate(null)).toBe('—')
  })

  it('returns em-dash for empty string', () => {
    expect(formatDate('')).toBe('—')
  })
})

describe('currentMonth', () => {
  it('returns YYYY-MM format', () => {
    expect(currentMonth()).toMatch(/^\d{4}-\d{2}$/)
  })
})

describe('today', () => {
  it('returns YYYY-MM-DD format', () => {
    expect(today()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('firstOfMonth', () => {
  it('always returns the 1st day', () => {
    expect(firstOfMonth()).toMatch(/^\d{4}-\d{2}-01$/)
  })
})

describe('apiError', () => {
  it('extracts detail from axios response', () => {
    const err = { response: { data: { detail: 'Not found' } } }
    expect(apiError(err)).toBe('Not found')
  })

  it('falls back to error message', () => {
    const err = { message: 'Network Error' }
    expect(apiError(err)).toBe('Network Error')
  })

  it('falls back to generic string for null', () => {
    expect(apiError(null)).toBe('Something went wrong')
  })

  it('falls back to generic string for empty object', () => {
    expect(apiError({})).toBe('Something went wrong')
  })
})
