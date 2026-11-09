import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'
import { webcrypto } from 'node:crypto'

Object.defineProperty(globalThis, 'crypto', { value: webcrypto, configurable: true })

afterEach(() => { cleanup() })
Object.defineProperty(window, 'matchMedia', { writable: true, value: vi.fn().mockImplementation(query => ({
  matches: false, media: query, onchange: null, addListener: vi.fn(), removeListener: vi.fn(),
  addEventListener: vi.fn(), removeEventListener: vi.fn(), dispatchEvent: vi.fn(),
})) })
HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', '') }
HTMLDialogElement.prototype.close = function () { this.removeAttribute('open') }
Element.prototype.scrollIntoView = vi.fn()
