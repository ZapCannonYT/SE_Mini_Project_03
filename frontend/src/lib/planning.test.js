import { reorderQty, classifyRisk } from './planning.js'

describe('reorderQty', () => {
  it('computes demand + safety - stock', () => {
    expect(reorderQty(100, 20, 50)).toBe(70)
  })
  it('rounds up fractional demand', () => {
    expect(reorderQty(10.2, 0, 0)).toBe(11)
  })
  it('never goes negative', () => {
    expect(reorderQty(10, 5, 500)).toBe(0)
  })
})

describe('classifyRisk', () => {
  it('is stockout when stock is below demand', () => {
    expect(classifyRisk(99, 100, 3)).toBe('stockout')
  })
  it('stock equal to demand is not a risk', () => {
    expect(classifyRisk(100, 100, 3)).toBe('none')
  })
  it('stock equal to factor * demand is not a risk', () => {
    expect(classifyRisk(300, 100, 3)).toBe('none')
  })
  it('just above factor * demand is overstock', () => {
    expect(classifyRisk(301, 100, 3)).toBe('overstock')
  })
})
