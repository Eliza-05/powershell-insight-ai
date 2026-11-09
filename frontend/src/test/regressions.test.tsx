import { StrictMode } from 'react'
import { act, fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { Results } from '../components/Results'
import { RecoveryTrace } from '../components/RecoveryTrace'
import { api, ApiFailure } from '../services/api'
import comparison from './fixtures/comparison.json'
import rejected from './fixtures/rejected.json'
import staticResults from './fixtures/static-regressions.json'
import type { AnalysisResponse, Capabilities, PipelineResult } from '../types/api'

vi.mock('../services/api', async original => ({ ...(await original()), api: { health: vi.fn(), capabilities: vi.fn(), metadata: vi.fn(), modelStatus: vi.fn(), analyze: vi.fn() } }))
const offline = { model: 'synthetic-model:test', expected_digest: 'synthetic', available: false, error: { code: 'ollama_unavailable', message: 'SIMULATED offline' } }
const caps: Capabilities = { model: 'synthetic-model:test', expected_digest: 'synthetic', max_input_bytes: 65536, options: {}, timeout_seconds: 300, minimum_margin_bytes: 0,
  mode_descriptions: { A: 'Static', B: 'Original', C: 'Recovered', ABC: 'Compare' } }
function pending<T>() { let resolve!: (v: T) => void; let reject!: (e: unknown) => void; const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no }); return { promise, resolve, reject } }
beforeEach(() => {
  localStorage.clear()
  vi.mocked(api.health).mockResolvedValue({ status: 'ok', version: '0.3.0' })
  vi.mocked(api.capabilities).mockResolvedValue(caps)
  vi.mocked(api.metadata).mockResolvedValue({ name: 'PowerShell Insight AI', version: '0.3.0', pilot_v2: 'PENDIENTE', pending_phase4: [] })
  vi.mocked(api.modelStatus).mockResolvedValue(offline)
  vi.mocked(api.analyze).mockResolvedValue(comparison.results[0] as unknown as PipelineResult)
})
afterEach(() => vi.unstubAllGlobals())
async function start(example = true) {
  const user = userEvent.setup(); render(<App />); await screen.findByText('API conectada')
  if (example) await user.click(screen.getByRole('button', { name: 'Usar ejemplo' }))
  return user
}
function slowFile(name = 'old.ps1') {
  const read = pending<ArrayBuffer>(), file = new File(['# slow'], name)
  Object.defineProperty(file, 'arrayBuffer', { value: () => read.promise })
  return { ...read, file, finish: (text = '# old') => read.resolve(new TextEncoder().encode(text).buffer) }
}
function drop(files: File[]) { fireEvent.drop(screen.getByRole('region', { name: 'Entrada del análisis' }), { dataTransfer: { files } }) }
async function analyze(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  await screen.findByRole('heading', { name: 'Reconocimiento' })
}

describe('H01 · prevalece la última intención del usuario', () => {
  it('moves from the editor to the visible export control without an invisible file-input stop', async () => {
    const user = await start(); await analyze(user)
    screen.getByRole('textbox', { name: 'Script PowerShell' }).focus()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Exportar análisis A en JSON' })).toHaveFocus()
  })
  it.each([true, false])('keeps latest file for either completion order (older first: %s)', async olderFirst => {
    await start(); const old = slowFile(), next = slowFile('latest.txt'); drop([old.file]); drop([next.file])
    await act(async () => { if (olderFirst) { old.finish(); next.finish('# latest') } else { next.finish('# latest'); old.finish() } })
    expect(screen.getByRole('textbox')).toHaveValue('# latest'); expect(screen.getByText('latest.txt')).toBeInTheDocument()
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it.each(['edit', 'clear', 'example', 'invalid file', 'multiple files'] as const)('invalidates pending read on %s', async action => {
    const user = await start(); const old = slowFile(); drop([old.file])
    if (action === 'edit') fireEvent.change(screen.getByRole('textbox'), { target: { value: '# manual' } })
    if (action === 'clear') await user.click(screen.getByRole('button', { name: 'Limpiar script' }))
    if (action === 'example') await user.click(screen.getByRole('button', { name: 'Usar ejemplo' }))
    if (action === 'invalid file') drop([new File(['inert'], 'wrong.exe')])
    if (action === 'multiple files') drop([new File(['a'], 'a.txt'), new File(['b'], 'b.txt')])
    const expected = (screen.getByRole('textbox') as HTMLTextAreaElement).value
    await act(async () => old.finish())
    expect(screen.getByRole('textbox')).toHaveValue(expected); expect(screen.queryByText('old.ps1')).toBeNull()
  })
  it('can cancel a pending read by clearing an already empty editor', async () => {
    const user = await start(false); const file = slowFile(); drop([file.file]); await user.click(screen.getByRole('button', { name: 'Limpiar script' }))
    await act(async () => file.finish()); expect(screen.getByRole('textbox')).toHaveValue('')
  })
  it('ignores obsolete read failures instead of replacing the current error', async () => {
    await start(); const file = slowFile(); drop([file.file]); drop([new File(['x'], 'wrong.exe')])
    await act(async () => file.reject(new Error('old failure')))
    expect(screen.getByRole('alert')).toHaveTextContent('Selecciona un archivo .ps1 o .txt.')
    expect(screen.getByRole('alert')).not.toHaveTextContent('UTF-8')
  })
  it('invalidates pending files synchronously when analysis begins', async () => {
    const user = await start(); const file = slowFile(), result = pending<AnalysisResponse>(); drop([file.file]); vi.mocked(api.analyze).mockReturnValue(result.promise)
    const text = (screen.getByRole('textbox') as HTMLTextAreaElement).value
    await user.click(screen.getByRole('button', { name: /Analizar script/ })); await act(async () => file.finish())
    expect(screen.getByRole('textbox')).toHaveValue(text); expect(screen.getByRole('textbox')).toBeDisabled()
    await act(async () => result.resolve(comparison.results[0] as unknown as PipelineResult)); expect(screen.queryByText(/corresponden al análisis anterior/)).toBeNull()
  })
  it('still uploads a valid BOM/Unicode/CRLF TXT without automatic analysis', async () => {
    const user = await start(false), text = '# á🧪\r\nGet-Process\r\n', file = new File(['\uFEFF' + text], 'unicode.txt')
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode('\uFEFF' + text).buffer })
    await user.upload(screen.getByLabelText('Seleccionar archivo PowerShell'), file); await screen.findByText('unicode.txt')
    expect(api.analyze).not.toHaveBeenCalled(); await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(api.analyze).toHaveBeenCalledExactlyOnceWith(text, 'A')
  })
})

describe('H03 · backend y proveedor independientes', () => {
  it('returns focus to the system trigger when its close button is used', async () => {
    const user = await start()
    await user.click(screen.getByRole('button', { name: 'Ver estado del sistema' }))
    await user.click(screen.getByRole('button', { name: 'Cerrar estado del sistema' }))
    expect(screen.queryByRole('region', { name: 'Estado del sistema' })).toBeNull()
    expect(screen.getByRole('button', { name: 'Ver estado del sistema' })).toHaveFocus()
  })
  it.each(['offline', 'memory', 'missing', 'ready', 'status error'] as const)('keeps A available with provider %s', async state => {
    if (state === 'memory') vi.mocked(api.modelStatus).mockResolvedValue({ ...offline, available: true, resource_ready: false, ready_for_inference: false, error: { code: 'insufficient_memory', message: 'SIMULATED memory' } })
    if (state === 'missing') vi.mocked(api.modelStatus).mockResolvedValue({ ...offline, error: { code: 'model_missing', message: 'SIMULATED missing model' } })
    if (state === 'ready') vi.mocked(api.modelStatus).mockResolvedValue({ ...offline, available: true, resource_ready: true, ready_for_inference: true, error: undefined })
    if (state === 'status error') vi.mocked(api.modelStatus).mockRejectedValue(new ApiFailure('http_error', 'SIMULATED status failure', 500))
    const user = await start(); expect(screen.getByText('API conectada')).toBeInTheDocument(); await analyze(user)
    expect(api.analyze).toHaveBeenCalledExactlyOnceWith(expect.any(String), 'A')
    if (state === 'status error') {
      await user.click(screen.getByRole('button', { name: 'Ver estado del sistema' }))
      expect(screen.getByText('Estado del proveedor no disponible')).toBeInTheDocument()
      expect(screen.getByRole('region', { name: 'Estado del sistema' })).toHaveTextContent('APIConectada')
    }
  })
  it.each([true, false])('keeps successful health when provider fails, independent of response order (%s)', async healthFirst => {
    const health = pending<{ status: string; version: string }>(), status = pending<typeof offline>()
    vi.mocked(api.health).mockReturnValue(health.promise); vi.mocked(api.modelStatus).mockReturnValue(status.promise); render(<App />)
    await act(async () => { if (healthFirst) { health.resolve({ status: 'ok', version: '1' }); status.reject(new Error('provider')) } else { status.reject(new Error('provider')); health.resolve({ status: 'ok', version: '1' }) } })
    expect(screen.getByText('API conectada')).toBeInTheDocument(); expect(screen.getByText(/estado del proveedor no disponible/)).toBeInTheDocument()
  })
  it('does not let provider success override failed health', async () => {
    vi.mocked(api.health).mockRejectedValue(new ApiFailure('connection_error', 'offline')); const user = userEvent.setup(); render(<App />)
    await user.click(screen.getByRole('button', { name: 'Ver estado del sistema' }))
    expect(screen.getByRole('button', { name: 'Ver estado del sistema' })).toHaveTextContent('API sin conexión')
  })
  it('ignores late health and provider results from a previous StrictMode effect', async () => {
    const health = pending<{ status: string; version: string }>(), status = pending<typeof offline>()
    vi.mocked(api.health).mockReturnValueOnce(health.promise); vi.mocked(api.modelStatus).mockReturnValueOnce(status.promise)
    render(<StrictMode><App /></StrictMode>); await screen.findByText('API conectada')
    await act(async () => { health.reject(new Error('obsolete')); status.resolve({ ...offline, available: true } as typeof offline) })
    expect(screen.getByText('API conectada')).toBeInTheDocument(); expect(screen.getByText(/Ollama no disponible/)).toBeInTheDocument(); expect(api.analyze).not.toHaveBeenCalled()
  })
})

describe('H05 · modelo público y fallback genérico', () => {
  it.each(['model-a:test', 'otro-modelo:local'])('uses %s in selector and help without inference', async model => {
    vi.mocked(api.capabilities).mockResolvedValue({ ...caps, model }); const user = await start()
    await user.click(screen.getByRole('radio', { name: 'B · LLM directo' })); expect(screen.getByText(new RegExp(`Solo el original → ${model}`))).toBeInTheDocument()
    await user.click(screen.getByRole('radio', { name: 'C · LLM asistido' })); expect(screen.getByText(new RegExp(`Original \\+ recuperación verificada de 1A → ${model}`))).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Abrir ayuda contextual' })); expect(screen.getByText(`${model} es experimental.`)).toBeInTheDocument(); expect(api.analyze).not.toHaveBeenCalled()
  })
  it('falls back to public metadata when capabilities fail', async () => {
    vi.mocked(api.capabilities).mockRejectedValue(new Error('caps')); vi.mocked(api.metadata).mockResolvedValue({ name: 'test', version: '1', pilot_v2: 'pending', pending_phase4: [], experimental_model: 'metadata-model:test', human_adjudications_pending: 3 })
    const user = await start(); await user.click(screen.getByRole('button', { name: 'Abrir ayuda contextual' }))
    expect(screen.getByText('metadata-model:test es experimental.')).toBeInTheDocument()
  })
  it('does not invent a model when capabilities and metadata are unavailable', async () => {
    vi.mocked(api.capabilities).mockRejectedValue(new Error('caps')); vi.mocked(api.metadata).mockRejectedValue(new Error('metadata'))
    const user = await start(); await user.click(screen.getByRole('radio', { name: 'B · LLM directo' })); expect(screen.getByText(/Solo el original → modelo configurado experimental/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Abrir ayuda contextual' })); expect(screen.getByText('El modelo configurado es experimental.')).toBeInTheDocument(); expect(screen.queryByText(/Qwen14|Qwen2.5-Coder/)).toBeNull()
  })
})

describe('H06 · capas del contrato', () => {
  it('counts L0, L1 and L2 even when no transformation originates from L2', () => {
    render(<RecoveryTrace result={staticResults.multilayer as unknown as PipelineResult} onLocate={() => {}} embedded />)
    expect(screen.getByText('3 capas · 2 transformaciones · 0 sin resolver')).toBeInTheDocument()
  })
  it('counts L0 for a result with no recovery and hides the empty trace in Results', () => {
    const view = render(<RecoveryTrace result={staticResults.empty as unknown as PipelineResult} onLocate={() => {}} embedded />)
    expect(screen.getByText('1 capa · 0 transformaciones · 0 sin resolver')).toBeInTheDocument(); view.unmount()
    render(<Results response={staticResults.empty as unknown as PipelineResult} busy={false} mode="A" stale={false} onLocate={() => {}} />)
    expect(screen.queryByRole('tab', { name: 'Traza 1A' })).toBeNull(); expect(screen.queryByRole('complementary')).toBeNull()
  })
})

describe('H07 · JSON íntegro y alcance explícito', () => {
  async function exported() {
    let blob: Blob | undefined, name = ''
    vi.stubGlobal('URL', class extends URL { static createObjectURL = (value: Blob) => { blob = value; return 'blob:test' }; static revokeObjectURL = vi.fn() })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) { name = this.download })
    await userEvent.setup().click(screen.getByRole('button', { name: /Exportar .* en JSON/ }))
    const text = await new Promise<string>(resolve => { const reader = new FileReader(); reader.onload = () => resolve(String(reader.result)); reader.readAsText(blob!) })
    return { value: JSON.parse(text), name, type: blob!.type }
  }
  it('exports an individual Unicode analysis including every original field', async () => {
    const data = staticResults.unicode
    render(<Results response={data as unknown as PipelineResult} busy={false} mode="A" stale={false} onLocate={() => {}} />)
    expect(screen.getByRole('button', { name: 'Exportar análisis A en JSON' })).toBeInTheDocument()
    const output = await exported(); expect(output.value).toEqual(data); expect(output.value.original).toContain('á🧪\r\n')
    expect(output.name).toBe(`powershell-insight-analisis-A-${data.run_id}.json`); expect(output.type).toBe('application/json')
  })
  it('exports the full comparison with a stable filename after selecting C', async () => {
    render(<Results response={comparison as unknown as AnalysisResponse} busy={false} mode="ABC" stale={false} onLocate={() => {}} />)
    await userEvent.setup().click(screen.getByRole('button', { name: /resultado C/ }))
    expect(screen.getByRole('button', { name: 'Exportar comparación completa A/B/C en JSON' })).toBeInTheDocument()
    const output = await exported(); expect(output.value).toEqual(comparison); expect(output.name).toBe(`powershell-insight-comparacion-ABC-${comparison.results[0].run_id}.json`)
  })
  it('warns on stale export and keeps its original instead of the empty editor', async () => {
    const user = await start(); await analyze(user); await user.click(screen.getByRole('button', { name: 'Limpiar script' }))
    expect(screen.getByRole('status')).toHaveTextContent('La exportación JSON conserva esa entrada anterior')
    expect(screen.getByRole('button', { name: 'Exportar análisis A en JSON · entrada anterior' })).toBeInTheDocument()
    const output = await exported(); expect(output.value).toEqual(comparison.results[0]); expect(output.name).toContain('-entrada-anterior.json'); expect(screen.getByRole('textbox')).toHaveValue('')
  })
})

it('keeps A, accepted evidence, and rejected B separate in a simulated comparison', async () => {
  const data = structuredClone(comparison); Object.assign(data.results[1], rejected)
  vi.mocked(api.analyze).mockResolvedValue(data as unknown as AnalysisResponse)
  const user = await start(); await user.click(screen.getByRole('radio', { name: 'Comparación A/B/C' })); await user.click(screen.getByRole('button', { name: /Comparar A\/B\/C/ }))
  const cards = await screen.findByRole('group', { name: 'Comparación de pipelines' }); await user.click(within(cards).getByRole('button', { name: /resultado B/ }))
  expect(screen.getByText('Sin hallazgos aceptados')).toBeInTheDocument(); await user.click(within(cards).getByRole('button', { name: /resultado C/ }))
  expect(screen.getByRole('heading', { name: 'Predicciones experimentales C' })).toBeInTheDocument(); expect(api.analyze).toHaveBeenCalledTimes(1)
})
