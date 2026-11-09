import { afterEach, describe, expect, it, vi } from 'vitest'
import { api } from '../services/api'
import { analysisResponse, capabilitiesResponse, healthResponse, metadataResponse, modelStatusResponse } from '../services/contracts'
import comparison from './fixtures/comparison.json'
import partial from './fixtures/partial.json'
import rejected from './fixtures/rejected.json'
import staticResults from './fixtures/static-regressions.json'
import type { Mode } from '../types/api'

afterEach(() => vi.unstubAllGlobals())
const reply = (data: unknown, status = 200) => ({ ok: status < 400, status, json: async () => data })

describe('H02 · contratos completos y procedencia', () => {
  it.each([...comparison.results, partial, rejected, ...Object.values(staticResults)])('accepts valid $configuration/$status without changing data', async result => {
    expect(await analysisResponse(result, result.configuration as Mode, result.original)).toBe(result)
  })
  it('keeps every field of a full comparison and open operational dictionaries', async () => {
    const data = structuredClone(comparison)
    Object.assign(data.results[1].operational, { future_diagnostic: { notes: ['á🧪', '<img src=x>'], count: 42 } })
    expect(await analysisResponse(data, 'ABC', data.results[0].original)).toBe(data)
  })
  it.each([
    null, [], {}, { configuration: 'C' },
    { ...comparison.results[0], deterministic: null },
    { ...comparison.results[1], evidence: null },
    { ...comparison.results[0], status: 'benign' },
    { ...comparison.results[0], duration_seconds: -1 },
    { ...comparison.results[0], unexpected_top_level: 'forbidden by FastAPI' },
    { ...comparison.results[0], input_sha256: 'wrong' },
    { ...comparison.results[0], schema_version: 'pipeline-v999' },
    { ...comparison.results[1], status: 'error', errors: [{ code: 'invalid_response', message: 'bad', stage: 'response' }] },
  ])('rejects incomplete, unknown or incoherent serialized results (%#)', async value => {
    await expect(analysisResponse(value, 'A', comparison.results[0].original)).rejects.toThrow()
  })
  it('rejects missing nested fields instead of defaulting or deleting response data', async () => {
    const value = structuredClone(comparison.results[0])
    const step = value.deobfuscation!.transformations[0]
    delete (step as Partial<typeof step>).warnings
    await expect(analysisResponse(value, 'A', value.original)).rejects.toThrow()
  })
  it('rejects results for a different submitted input or mode', async () => {
    await expect(analysisResponse(comparison.results[0], 'B', comparison.results[0].original)).rejects.toThrow()
    await expect(analysisResponse(comparison.results[0], 'A', 'Write-Output other')).rejects.toThrow()
  })
  it('rejects a fabricated quote even when it is repeated in both evidence lists', async () => {
    const value = structuredClone(comparison.results[1])
    value.llm!.behaviors[0].evidence[0].snippet = 'invented quote'
    value.evidence[0].snippet = 'invented quote'
    await expect(analysisResponse(value, 'B', value.original)).rejects.toThrow()
  })
  it.each(['order', 'ids', 'hash', 'missing', 'metrics'] as const)('rejects incoherent comparison: %s', async kind => {
    const value = structuredClone(comparison)
    if (kind === 'order') value.results.reverse()
    if (kind === 'ids') value.results[2].run_id = value.results[0].run_id
    if (kind === 'hash') value.results[2].input_sha256 = '0'.repeat(64)
    if (kind === 'missing') value.results.pop()
    if (kind === 'metrics') Object.assign(value, { quality_metrics_computed: true })
    await expect(analysisResponse(value, 'ABC', comparison.results[0].original)).rejects.toThrow()
  })
  it('keeps valid rejected output diagnostic and never accepts its claims', async () => {
    expect(await analysisResponse(rejected, 'B', rejected.original)).toBe(rejected)
    const value = structuredClone(rejected)
    Object.assign(value, { llm: comparison.results[1].llm, evidence: comparison.results[1].evidence })
    await expect(analysisResponse(value, 'B', value.original)).rejects.toThrow()
  })
  it.each(['B', 'C'] as const)('accepts provider failures for %s without risk/findings', async configuration => {
    const value = structuredClone(comparison.results[configuration === 'B' ? 1 : 2])
    Object.assign(value, { status: 'unavailable', llm: null, evidence: [], risk_label: 'unknown', errors: [{ code: 'model_missing', message: 'SIMULATED missing model', stage: 'provider' }] })
    expect(await analysisResponse(value, configuration, value.original)).toBe(value)
  })
  it('accepts a comparison with A completed and B/C unavailable independently', async () => {
    const value = structuredClone(comparison)
    for (const result of value.results.slice(1)) Object.assign(result, { status: 'unavailable', llm: null, evidence: [], risk_label: 'unknown', errors: [{ code: 'ollama_unavailable', message: 'SIMULATED offline', stage: 'provider' }] })
    expect(await analysisResponse(value, 'ABC', value.results[0].original)).toBe(value)
  })
})

describe('H02 · errores recuperables sin reintentos', () => {
  it.each([400, 409, 422, 500, 503])('preserves HTTP %s and structured error', async status => {
    const fetch = vi.fn().mockResolvedValue(reply({ error: { code: 'synthetic_failure', message: 'SIMULATED', details: [] } }, status))
    vi.stubGlobal('fetch', fetch)
    await expect(api.analyze('Write-Output 1', 'A')).rejects.toMatchObject({ code: 'synthetic_failure', status, message: 'SIMULATED' })
    expect(fetch).toHaveBeenCalledTimes(1)
  })
  it('preserves HTTP 502 for an HTML body without displaying its content', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 502, json: async () => { throw new SyntaxError('private HTML marker') } }))
    await expect(api.health()).rejects.toMatchObject({ code: 'http_error', status: 502, message: expect.stringContaining('HTTP 502') })
    await expect(api.health()).rejects.not.toHaveProperty('message', expect.stringContaining('private HTML marker'))
  })
  it('distinguishes invalid JSON from a malformed successful contract', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad json') } }))
    await expect(api.health()).rejects.toMatchObject({ code: 'invalid_json', status: 200 })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ configuration: 'C' })))
    await expect(api.analyze('Write-Output 1', 'C')).rejects.toMatchObject({ code: 'invalid_contract', status: 200 })
  })
  it('does not classify a JSON-shaped invalid HTTP error as a transport error', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(reply({ error: { code: {}, message: ['private'] } }, 503)))
    await expect(api.health()).rejects.toMatchObject({ code: 'http_error', status: 503 })
  })
  it('reports transport failure and body cancellation separately', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('private connection detail')))
    await expect(api.health()).rejects.toMatchObject({ code: 'connection_error', status: 0 })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => { throw new DOMException('abort', 'AbortError') } }))
    await expect(api.health()).rejects.toMatchObject({ code: 'connection_timeout', status: 0 })
  })
  it.each(['A', 'B', 'C', 'ABC'] as const)('checks and preserves payload and endpoint for %s', async mode => {
    const data = mode === 'ABC' ? comparison : comparison.results.find(r => r.configuration === mode)!
    const fetch = vi.fn().mockResolvedValue(reply(data)); vi.stubGlobal('fetch', fetch)
    await api.analyze(comparison.results[0].original, mode)
    expect(fetch).toHaveBeenCalledExactlyOnceWith(mode === 'ABC' ? '/api/compare' : `/api/analyze/${mode}`, expect.objectContaining({ method: 'POST', body: JSON.stringify({ script: comparison.results[0].original }) }))
  })
})

it('validates status/capability/metadata fields used by React, preserving public extras', () => {
  expect(() => healthResponse({ status: 'down', version: '1' })).toThrow()
  expect(() => capabilitiesResponse({ model: {} })).toThrow()
  expect(() => metadataResponse({ name: 'test', version: '1', pilot_v2: 'pending', pending_phase4: null })).toThrow()
  expect(() => modelStatusResponse({ model: 'test', expected_digest: 'test', available: true, state: {} })).toThrow()
  const status = { model: 'test', expected_digest: 'test', available: false, future_diagnostic: { value: 'kept' } }
  expect(modelStatusResponse(status)).toBe(status)
})
