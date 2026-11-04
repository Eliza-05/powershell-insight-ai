/** Live loopback API + React DOM integration. Uses A only: zero LLM calls. */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterAll, beforeAll, expect, it, vi } from 'vitest'
import App from '../src/App'

const originalFetch = globalThis.fetch
beforeAll(() => {
  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => originalFetch(new URL(String(input), 'http://127.0.0.1:8000'), init))
})
afterAll(() => vi.unstubAllGlobals())

it('renders deterministic findings and verified recovery through the running FastAPI server', async () => {
  const user = userEvent.setup()
  render(<App />)
  expect(await screen.findByText('API conectada', {}, { timeout: 15000 })).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Usar ejemplo' }))
  await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  expect(await screen.findByRole('heading', { name: 'Reconocimiento' }, { timeout: 15000 })).toBeVisible()
  expect(screen.getByText('Desofuscador 1A + detector 1B')).toBeVisible()
  await user.click(screen.getByRole('tab', { name: 'Recuperación' }))
  expect(screen.getByText('studio-local')).toBeVisible()
  await user.click(screen.getByRole('button', { name: 'Abrir ayuda contextual' }))
  expect(screen.getByRole('dialog')).toBeVisible()
  expect(screen.getByText('Qwen2.5-Coder 14B es experimental.')).toBeVisible()
})
