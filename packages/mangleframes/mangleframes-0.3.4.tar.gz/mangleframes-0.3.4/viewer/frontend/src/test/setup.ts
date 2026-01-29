import '@testing-library/jest-dom'

class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}

global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

class MockDOMMatrixReadOnly {
  a = 1
  b = 0
  c = 0
  d = 1
  e = 0
  f = 0
  static fromMatrix() {
    return new MockDOMMatrixReadOnly()
  }
  transformPoint() {
    return { x: 0, y: 0 }
  }
}

global.DOMMatrixReadOnly = MockDOMMatrixReadOnly as unknown as typeof DOMMatrixReadOnly
