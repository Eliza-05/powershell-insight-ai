/** Live loopback API. B/C only on an explicitly attested synthetic transport. */
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterAll, beforeAll, expect, it, vi } from 'vitest'
import App from '../src/App'
import { api } from '../src/services/api'
import schemas from '../src/services/contracts.schema.json'
import packets from '../src/test/fixtures/integrated-qwen3.json'
import { Results } from '../src/components/Results'
import type { Mode } from '../src/types/api'

const originalFetch = globalThis.fetch
const base = process.env.PSI_TEST_URL ?? 'http://127.0.0.1:8000'
if (!['127.0.0.1', 'localhost'].includes(new URL(base).hostname)) throw new Error('Loopback tests only')
const synthetic = process.env.PSI_TEST_SYNTHETIC === '1'
beforeAll(async () => {
  if (synthetic) expect((await (await originalFetch(`${base}/__test/state`)).json()).synthetic).toBe(true)
  vi.stubGlobal('fetch', (input: RequestInfo | URL, init?: RequestInit) => originalFetch(new URL(String(input), base), init))
})
afterAll(() => vi.unstubAllGlobals())

it.skipIf(!synthetic).each(['kept', 'dropped', 'incoherent', 'opaque', 'recovered', 'comparison'] as const)('exercises the real Qwen3 service and UI with transport-only simulation: %s', async name => {
  const packet = packets[name]
  const result = await api.analyze(packet.script, packet.mode as Mode)
  render(<Results response={result} busy={false} mode={packet.mode} stale={false} onLocate={vi.fn()} />)
  if ('results' in result) {
    expect(result.results.map(r => r.configuration)).toEqual(['A', 'B', 'C'])
    await userEvent.click(screen.getByRole('button', { name: /Ver resultado B/ }))
  }
  await userEvent.click(screen.getByRole('button', { name: 'Predicción y postprocesamiento' }))
  expect(screen.getByRole('region', { name: 'Verificación determinista de evidencia' })).toBeVisible()
  const r = 'results' in result ? result.results[1] : result
  expect(r.operational.model).toBe('qwen3-coder:30b')
  expect(r.operational.evidence_check?.version).toBe('evidence-check-v2-bounded')
  if (name === 'incoherent') expect(r.errors[0].code).toBe('evidence_check_incoherent')
  if (name === 'dropped' || name === 'recovered') expect(r.llm?.behaviors).toEqual([])
})

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
  const capabilities = await (await originalFetch(`${base}/api/capabilities`)).json()
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
  const openapi = await (await originalFetch(`${base}/openapi.json`)).json()
  function normalized(value: unknown): unknown {
    if (typeof value === 'string') return value.replace('#/$defs/', '#/components/schemas/')
    if (Array.isArray(value)) return value.map(normalized)
    if (typeof value === 'object' && value !== null) return Object.fromEntries(Object.entries(value).filter(([key, item]) => key !== 'default' || item !== null).map(([key, item]) => [key, normalized(item)]))
    return value
  }
  for (const [name, schema] of Object.entries(schemas.$defs)) expect(normalized(openapi.components.schemas[name]), name).toEqual(normalized(schema))
})
