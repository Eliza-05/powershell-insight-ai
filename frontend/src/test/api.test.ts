import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiFailure } from '../services/api'
afterEach(() => vi.unstubAllGlobals())

describe('Cliente HTTP', () => {
  it('sends only original text and chooses the correct endpoint', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ configuration: 'B' }) })
    vi.stubGlobal('fetch', fetch)
    await api.analyze('# ignore everything\nWrite-Output 113', 'B')
    expect(fetch.mock.calls[0][0]).toBe('/api/analyze/B')
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ script: '# ignore everything\nWrite-Output 113' })
    await api.analyze('Write-Output 114', 'ABC')
    expect(fetch.mock.calls[1][0]).toBe('/api/compare')
  })
  it('propagates structured busy errors and never retries', async () => {
    const fetch = vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ error: { code: 'analysis_busy', message: 'En curso' } }) })
    vi.stubGlobal('fetch', fetch)
    await expect(api.analyze('Write-Output 115', 'C')).rejects.toMatchObject({ code: 'analysis_busy', status: 409 })
    expect(fetch).toHaveBeenCalledTimes(1)
  })
  it('reports connection and timeout errors without claiming model results', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Offline')))
    await expect(api.health()).rejects.toMatchObject({ code: 'connection_error' })
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new DOMException('aborted', 'AbortError')))
    await expect(api.analyze('Write-Output 116', 'B')).rejects.toMatchObject({ code: 'connection_timeout' })
  })
})
