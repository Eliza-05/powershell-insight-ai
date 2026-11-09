/** Live loopback API + React DOM integration. Uses A only: zero LLM calls. */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterAll, beforeAll, expect, it, vi } from 'vitest'
import App from '../src/App'
import { api } from '../src/services/api'
import schemas from '../src/services/contracts.schema.json'

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
  const capabilities = await (await originalFetch('http://127.0.0.1:8000/api/capabilities')).json()
  expect(screen.getByText(`${capabilities.model} es experimental.`)).toBeVisible()
})

it.each([
  { script: "Write-Output 'static-only'", status: 'completed', labels: [] },
  { script: '& $unknown_static_variable', status: 'partial', labels: [] },
  { script: '# á🧪\r\nGet-Process -Id 734201\r\n', status: 'completed', labels: ['B05'] },
])('validates live A: $status / $script', async ({ script, status, labels }) => {
  const response = await api.analyze(script, 'A')
  expect('results' in response).toBe(false)
  if ('results' in response) throw new Error('Expected individual A')
  expect(response.original).toBe(script)
  expect(response.status).toBe(status)
  expect(response.deterministic?.behaviors).toEqual(labels)
  expect(response.llm).toBeNull()
  expect(response.risk_label).toBe('unknown')
})

it('keeps the frontend schema snapshot aligned with the current FastAPI OpenAPI', async () => {
  const openapi = await (await originalFetch('http://127.0.0.1:8000/openapi.json')).json()
  function normalized(value: unknown): unknown {
    if (typeof value === 'string') return value.replace('#/$defs/', '#/components/schemas/')
    if (Array.isArray(value)) return value.map(normalized)
    if (typeof value === 'object' && value !== null) return Object.fromEntries(Object.entries(value).filter(([key, item]) => key !== 'default' || item !== null).map(([key, item]) => [key, normalized(item)]))
    return value
  }
  for (const [name, schema] of Object.entries(schemas.$defs)) expect(normalized(openapi.components.schemas[name]), name).toEqual(normalized(schema))
})
