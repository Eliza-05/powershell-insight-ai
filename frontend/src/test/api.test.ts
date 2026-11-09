import { afterEach, describe, expect, it, vi } from 'vitest'
import { api, ApiFailure } from '../services/api'
import comparison from './fixtures/comparison.json'
afterEach(() => vi.unstubAllGlobals())

describe('Cliente HTTP', () => {
  it('shares an in-flight provider poll and fetches fresh state after completion', async () => {
    let finish!: (value: unknown) => void
    const state = { model:'synthetic',expected_digest:'test',available:false }
    const fetch = vi.fn().mockReturnValue(new Promise(resolve => { finish = resolve }))
    vi.stubGlobal('fetch',fetch)
    const first=api.modelStatus(),second=api.modelStatus()
    expect(first).toBe(second);expect(fetch).toHaveBeenCalledTimes(1)
    finish({ok:true,status:200,json:async()=>state})
    await expect(first).resolves.toEqual(state);await expect(second).resolves.toEqual(state)
    fetch.mockResolvedValue({ok:true,status:200,json:async()=>({...state,available:true})})
    await expect(api.modelStatus()).resolves.toMatchObject({available:true});expect(fetch).toHaveBeenCalledTimes(2)
  })
  it('clears a failed shared poll without automatic retries', async () => {
    const fetch=vi.fn().mockRejectedValue(new TypeError('SIMULATED offline'));vi.stubGlobal('fetch',fetch)
    const results=await Promise.allSettled([api.modelStatus(),api.modelStatus()])
    expect(results.every(r=>r.status==='rejected'&&r.reason.code==='connection_error')).toBe(true)
    expect(fetch).toHaveBeenCalledTimes(1)
    fetch.mockResolvedValue({ok:true,status:200,json:async()=>({model:'synthetic',expected_digest:'test',available:false})})
    await expect(api.modelStatus()).resolves.toHaveProperty('available',false);expect(fetch).toHaveBeenCalledTimes(2)
  })
  it('sends only original text and chooses the correct endpoint', async () => {
    const fetch = vi.fn().mockResolvedValueOnce({ ok: true, status: 200, json: async () => comparison.results[1] })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => comparison })
    vi.stubGlobal('fetch', fetch)
    await api.analyze(comparison.results[1].original, 'B')
    expect(fetch.mock.calls[0][0]).toBe('/api/analyze/B')
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({ script: comparison.results[1].original })
    await api.analyze(comparison.results[0].original, 'ABC')
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
