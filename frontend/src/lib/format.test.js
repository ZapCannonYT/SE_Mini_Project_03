import { formatDateTime, formatQty, parseApiDate } from './format.js'

describe('format helpers', () => {
  it('rounds floating point noise to two decimals', () => {
    expect(formatQty(478.91999999999996)).toBe('478.92')
    expect(formatQty(966.3000000000001)).toBe('966.3')
    expect(formatQty(12)).toBe('12')
    expect(formatQty(0)).toBe('0')
  })

  it('reads timestamps without a timezone as UTC', () => {
    expect(parseApiDate('2026-11-17T06:18:37.242246').toISOString()).toBe('2026-11-17T06:18:37.242Z')
    expect(parseApiDate('2026-11-17T06:18:37+05:30').toISOString()).toBe('2026-11-17T00:48:37.000Z')
    expect(parseApiDate('2026-11-17T06:18:37Z').toISOString()).toBe('2026-11-17T06:18:37.000Z')
  })

  it('falls back to the raw text for bad input', () => {
    expect(formatDateTime('not a date')).toBe('not a date')
    expect(formatDateTime(null)).toBe('')
  })
})
