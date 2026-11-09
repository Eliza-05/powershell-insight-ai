import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import App from '../App'
import comparison from './fixtures/comparison.json'

afterEach(() => vi.unstubAllGlobals())
it.each(['invalid contract', 'HTML 502', 'invalid JSON'])('H02: real HTTP client handles %s in React without publishing findings', async failure => {
  const calls: string[] = []
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    calls.push(url)
    if (url === '/api/analyze/A') {
      if (failure === 'invalid contract') return { ok: true, status: 200, json: async () => ({ configuration: 'A', deterministic: { behaviors: ['B07'] } }) }
      return { ok: failure !== 'HTML 502', status: failure === 'HTML 502' ? 502 : 200, json: async () => { throw new SyntaxError('<html>private marker</html>') } }
    }
    const data = url === '/api/health' ? { status: 'ok', version: 'test' }
      : url === '/api/ollama/status' ? { model: 'synthetic', expected_digest: 'test', available: false }
      : url === '/api/capabilities' ? { model: 'synthetic', expected_digest: 'test', max_input_bytes: 65536, options: {}, timeout_seconds: 300, minimum_margin_bytes: 0, mode_descriptions: { A: 'A', B: 'B', C: 'C', ABC: 'ABC' } }
      : { name: 'test', version: 'test', pilot_v2: 'pending', pending_phase4: [] }
    return { ok: true, status: 200, json: async () => data }
  }))
  const user = userEvent.setup(); render(<App />); await screen.findByText('API conectada')
  await user.click(screen.getByRole('button', { name: 'Usar ejemplo' })); await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  const alert = await screen.findByRole('alert')
  expect(alert).toHaveTextContent(failure === 'HTML 502' ? 'HTTP 502' : failure === 'invalid JSON' ? 'JSON inválido' : 'no cumple el contrato')
  expect(alert).not.toHaveTextContent('private marker'); expect(screen.getByRole('heading', { name: 'Sin análisis todavía' })).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: 'Acceso a credenciales' })).toBeNull()
  expect(calls.filter(url => url.startsWith('/api/analyze/'))).toEqual(['/api/analyze/A'])
})

it('recovers after a contract error when the user explicitly retries a valid A response', async () => {
  let analyses = 0
  vi.stubGlobal('fetch', vi.fn(async (url: string) => {
    let data: unknown
    if (url === '/api/analyze/A') data = ++analyses === 1 ? { configuration: 'A' } : comparison.results[0]
    else if (url === '/api/health') data = { status: 'ok', version: 'test' }
    else if (url === '/api/ollama/status') data = { model: 'synthetic', expected_digest: 'test', available: false }
    else if (url === '/api/capabilities') data = { model: 'synthetic', expected_digest: 'test', max_input_bytes: 65536, options: {}, timeout_seconds: 300, minimum_margin_bytes: 0, mode_descriptions: { A: 'A', B: 'B', C: 'C', ABC: 'ABC' } }
    else data = { name: 'test', version: 'test', pilot_v2: 'pending', pending_phase4: [] }
    return { ok: true, status: 200, json: async () => data }
  }))
  const user = userEvent.setup(); render(<App />); await screen.findByText('API conectada')
  await user.click(screen.getByRole('button', { name: 'Usar ejemplo' }))
  await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  expect(await screen.findByRole('alert')).toHaveTextContent('no cumple el contrato')
  expect(analyses).toBe(1)
  await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  expect(await screen.findByRole('heading', { name: 'Reconocimiento' })).toBeVisible()
  expect(screen.queryByRole('alert')).toBeNull()
  expect(analyses).toBe(2)
})
