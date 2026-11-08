import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import App from '../App'
import { api, ApiFailure } from '../services/api'
import type { AnalysisResponse, Comparison, PipelineResult } from '../types/api'
import comparisonData from './fixtures/comparison.json'
import partialData from './fixtures/partial.json'
import rejectedData from './fixtures/rejected.json'

vi.mock('../services/api', async importOriginal => {
  const real = await importOriginal<typeof import('../services/api')>()
  return { ...real, api: { health: vi.fn(), metadata: vi.fn(), capabilities: vi.fn(), modelStatus: vi.fn(), analyze: vi.fn() } }
})
const comparison = comparisonData as unknown as Comparison
const partial = partialData as PipelineResult
const rejected = rejectedData as PipelineResult

beforeEach(() => {
  localStorage.clear()
  vi.mocked(api.health).mockResolvedValue({ status: 'ok', version: '0.3.0' })
  vi.mocked(api.capabilities).mockResolvedValue({ max_input_bytes: 65536, model: 'qwen3.5:4b-q4_K_M', expected_digest: 'synthetic-digest', options: {}, timeout_seconds: 300, minimum_margin_bytes: 2147483648, mode_descriptions: {} as never })
  vi.mocked(api.metadata).mockResolvedValue({ name: 'PowerShell Insight AI', version: '0.3.0', pilot_v2: 'PENDIENTE / INCONCLUSO', pending_phase4: ['Cierre metodológico', 'Selección definitiva', 'Memoria', 'Evaluación independiente', 'Adjudicación humana', 'H1/H2', 'Congelación'] })
  vi.mocked(api.modelStatus).mockResolvedValue({ model: 'qwen3.5:4b-q4_K_M', expected_digest: 'synthetic-digest', available: false, error: { code: 'ollama_unavailable', message: 'Ollama apagado para pruebas.' } })
  vi.mocked(api.analyze).mockResolvedValue(comparison.results[0])
})

async function renderApp() {
  const user = userEvent.setup()
  render(<App />)
  await screen.findByText('API conectada')
  return user
}
async function loadExample(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('button', { name: 'Usar ejemplo' }))
}

describe('Workspace', () => {
  it('starts empty with A selected and never infers on mount', async () => {
    await renderApp()
    expect(screen.getByRole('heading', { name: 'Sin análisis todavía' })).toBeVisible()
    expect(screen.getByRole('radio', { name: 'A · Determinista' })).toBeChecked()
    expect(screen.getByRole('button', { name: /Analizar script/ })).toBeDisabled()
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('uploads only when explicitly requested, preserves exact input and displays A', async () => {
    const user = await renderApp()
    await loadExample(user)
    const text = (screen.getByRole('textbox', { name: 'Script PowerShell' }) as HTMLTextAreaElement).value
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(api.analyze).toHaveBeenCalledExactlyOnceWith(text, 'A')
    expect(await screen.findByRole('heading', { name: 'Reconocimiento' })).toBeVisible()
    expect(screen.getByText('REGLA')).toBeVisible()
    expect(screen.getByText('Desofuscador 1A + detector 1B')).toBeVisible()
    expect(screen.getByText(/El motor identifica operaciones/)).toBeVisible()
  })
  it('shows a real loading state, blocks duplicates and isolates selection', async () => {
    let finish!: (value: AnalysisResponse) => void
    vi.mocked(api.analyze).mockImplementation(() => new Promise(resolve => { finish = resolve }))
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(await screen.findByText('Análisis A en curso')).toBeVisible()
    expect(screen.getByRole('textbox', { name: 'Script PowerShell' })).toBeDisabled()
    expect(screen.getByRole('radio', { name: 'B · LLM directo' })).toBeDisabled()
    expect(api.analyze).toHaveBeenCalledTimes(1)
    await act(async () => { finish(comparison.results[0]) })
    await screen.findByRole('heading', { name: 'Reconocimiento' })
  })
  it('shows connection errors without manufacturing results or retries', async () => {
    vi.mocked(api.analyze).mockRejectedValue(new ApiFailure('connection_error', 'API local no disponible'))
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('API local no disponible')
    expect(screen.getByRole('heading', { name: 'Sin análisis todavía' })).toBeVisible()
    expect(api.analyze).toHaveBeenCalledTimes(1)
  })
  it('shows stale results after edits and does not relabel them', async () => {
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    await screen.findByRole('heading', { name: 'Reconocimiento' })
    await user.type(screen.getByRole('textbox', { name: 'Script PowerShell' }), '\n# cambio')
    expect(screen.getByRole('status')).toHaveTextContent('corresponden al análisis anterior')
    expect(api.analyze).toHaveBeenCalledTimes(1)
  })
  it('enforces UTF-8 byte limits before submitting', async () => {
    await renderApp()
    fireEvent.change(screen.getByRole('textbox', { name: 'Script PowerShell' }), { target: { value: 'ñ'.repeat(40000) } })
    expect(screen.getByRole('alert')).toHaveTextContent('supera el límite')
    expect(screen.getByRole('button', { name: /Analizar script/ })).toBeDisabled()
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('changes and persists light/dark preference without storing source', async () => {
    const user = await renderApp()
    // Light is the default theme; the first toggle switches to dark.
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    await user.click(screen.getByRole('button', { name: 'Activar modo oscuro' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem('psi-theme')).toBe('dark')
    await loadExample(user)
    expect(localStorage.length).toBe(1)
    await user.click(screen.getByRole('button', { name: 'Activar modo claro' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    expect(localStorage.getItem('psi-theme')).toBe('light')
  })
  it('exposes model state and digest from the header even without the desktop sidebar', async () => {
    const user = await renderApp()
    await user.click(screen.getByRole('button', { name: 'Ver estado del sistema' }))
    const panel = screen.getByRole('region', { name: 'Estado del sistema' })
    expect(within(panel).getByText('qwen3.5:4b-q4_K_M')).toBeVisible()
    expect(within(panel).getByText('Ollama apagado para pruebas.')).toBeVisible()
    await user.click(within(panel).getByText('Digest esperado'))
    expect(within(panel).getByText('synthetic-digest')).toBeVisible()
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('renders help, provisional state and pending research without starting inference', async () => {
    const user = await renderApp()
    await user.click(screen.getByRole('button', { name: 'Abrir ayuda contextual' }))
    expect(screen.getByRole('dialog')).toBeVisible()
    expect(screen.getByText('Qwen2.5-Coder 14B es experimental.')).toBeVisible()
    await user.click(screen.getByText('Estado de la investigación y pendientes de Fase 4'))
    expect(screen.getByText(/Piloto histórico Qwen3.5 v2: PENDIENTE/)).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Volver al estudio' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('file import validates UTF-8 and file size without executing content', async () => {
    const user = await renderApp()
    const file = new File(["# file-only\nWrite-Output 'hello'"], 'own_sample.ps1', { type: 'text/plain' })
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode("# file-only\nWrite-Output 'hello'").buffer })
    await user.upload(screen.getByLabelText('Seleccionar archivo PowerShell'), file)
    expect(await screen.findByText('own_sample.ps1')).toBeVisible()
    expect(screen.getByRole('textbox', { name: 'Script PowerShell' })).toHaveValue("# file-only\nWrite-Output 'hello'")
    expect(api.analyze).not.toHaveBeenCalled()
    const oversized = new File(['x'.repeat(65537)], 'large.txt', { type: 'text/plain' })
    await user.upload(screen.getByLabelText('Seleccionar archivo PowerShell'), oversized)
    expect(await screen.findByRole('alert')).toHaveTextContent('supera el límite')
  })
  it('rejects non-UTF8 imported data and can clear input', async () => {
    const user = await renderApp(); await loadExample(user)
    const file = new File([new Uint8Array([255])], 'invalid.txt')
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new Uint8Array([255]).buffer })
    await user.upload(screen.getByLabelText('Seleccionar archivo PowerShell'), file)
    expect(await screen.findByRole('alert')).toHaveTextContent('UTF-8')
    await user.click(screen.getByRole('button', { name: 'Limpiar script' }))
    expect(screen.getByRole('textbox', { name: 'Script PowerShell' })).toHaveValue('')
  })
  it('loads a dropped UTF-8 file through the existing validation without running analysis', async () => {
    await renderApp()
    const file = new File(['# drop source'], 'dropped.ps1', { type: 'text/plain' })
    Object.defineProperty(file, 'arrayBuffer', { value: async () => new TextEncoder().encode('# drop source').buffer })
    const panel = screen.getByRole('region', { name: 'Entrada del análisis' })
    fireEvent.dragEnter(panel, { dataTransfer: { types: ['Files'] } })
    expect(screen.getByRole('status')).toHaveTextContent('Suelta el archivo')
    fireEvent.drop(panel, { dataTransfer: { files: [file] } })
    await screen.findByText('dropped.ps1')
    expect(screen.getByRole('textbox', { name: 'Script PowerShell' })).toHaveValue('# drop source')
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('rejects multiple dropped files instead of silently discarding one', async () => {
    await renderApp()
    const files = [new File(['a'], 'a.txt'), new File(['b'], 'b.txt')]
    fireEvent.drop(screen.getByRole('region', { name: 'Entrada del análisis' }), { dataTransfer: { files } })
    expect(await screen.findByRole('alert')).toHaveTextContent('un solo archivo')
    expect(screen.getByRole('textbox', { name: 'Script PowerShell' })).toHaveValue('')
    expect(api.analyze).not.toHaveBeenCalled()
  })
  it('dismisses the system inspector with Escape and returns focus to its trigger', async () => {
    const user = await renderApp()
    await user.click(screen.getByRole('button', { name: 'Ver estado del sistema' }))
    await user.keyboard('{Escape}')
    expect(screen.queryByRole('region', { name: 'Estado del sistema' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Ver estado del sistema' })).toHaveFocus()
  })
})

describe('Resultados y procedencia', () => {
  it('retains distinct authorship for 1A techniques and LLM claims', async () => {
    const value = structuredClone(comparison.results[2])
    value.llm!.obfuscation_techniques = ['OT-CONCAT']
    vi.mocked(api.analyze).mockResolvedValue(value)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'C · LLM asistido' }))
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(await screen.findByText('OT-CONCAT · 1A')).toBeVisible()
    expect(screen.getByText('OT-CONCAT · LLM')).toBeVisible()
  })
  it('marks differences without reporting a comparative quality score', async () => {
    const value = structuredClone(comparison)
    value.results[1].llm!.behaviors = []
    value.results[1].evidence = []
    vi.mocked(api.analyze).mockResolvedValue(value)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'Comparación A/B/C' }))
    await user.click(screen.getByRole('button', { name: /Comparar A\/B\/C/ }))
    expect(await screen.findByText('Las etiquetas marcadas difieren entre pipelines.')).toBeVisible()
    expect(screen.getByText(/no son métricas de calidad científica/)).toBeVisible()
    expect(screen.queryByText(/F1|precisión|ganador/)).not.toBeInTheDocument()
  })
  it('renders ABC independently and selects each result', async () => {
    vi.mocked(api.analyze).mockResolvedValue(comparison)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'Comparación A/B/C' }))
    await user.click(screen.getByRole('button', { name: /Comparar A\/B\/C/ }))
    const cards = await screen.findByLabelText('Comparación de pipelines')
    expect(within(cards).getAllByRole('button')).toHaveLength(3)
    expect(screen.getByText(/no son métricas de calidad científica/)).toBeVisible()
    await user.click(within(cards).getByRole('button', { name: /resultado B/ }))
    expect(screen.getByText('Predicciones experimentales del modelo.')).toBeVisible()
    expect(screen.getByText('MODELO')).toBeVisible()
    await user.click(within(cards).getByRole('button', { name: /resultado C/ }))
    expect(screen.getByText(`Original + recuperación 1A → ${comparison.results[2].operational.model} · experimental`)).toBeVisible()
    expect(api.analyze).toHaveBeenCalledTimes(1)
  })
  it('keeps partial uncertainty visible and separates model recovery', async () => {
    vi.mocked(api.analyze).mockResolvedValue(partial)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'C · LLM asistido' }))
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(await screen.findByText('Parcial')).toBeVisible()
    expect(screen.getByText('Caso indeterminado o de alcance parcial.')).toBeVisible()
    expect(screen.getByText('Alta')).toBeVisible()
    await user.click(screen.getByRole('tab', { name: 'Recuperación' }))
    expect(screen.getByText('Fragmentos aún desconocidos')).toBeVisible()
  })
  it('rejected model output is never shown as accepted findings or HTML', async () => {
    vi.mocked(api.analyze).mockResolvedValue(rejected)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'B · LLM directo' }))
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    expect(await screen.findByText('La respuesta no superó la validación')).toBeVisible()
    expect(screen.getByText('Sin hallazgos aceptados')).toBeVisible()
    expect(screen.queryByText('MODELO')).not.toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Detalles' }))
    await user.click(screen.getByText('Respuesta cruda rechazada · solo diagnóstico'))
    expect(screen.getByText('INVALID <img src=x onerror=alert(1)>')).toBeVisible()
    expect(document.querySelector('img[src="x"]')).toBeNull()
  })
  it('shows evidence origin and locates the exact original span', async () => {
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    await screen.findByRole('heading', { name: 'Reconocimiento' })
    await user.click(screen.getByRole('tab', { name: 'Evidencias' }))
    expect(screen.getAllByText('Script original').length).toBeGreaterThan(0)
    const locate = screen.getAllByRole('button', { name: 'Ver origen' })[0]
    await user.click(locate)
    const editor = screen.getByRole('textbox', { name: 'Script PowerShell' }) as HTMLTextAreaElement
    expect(editor).toHaveFocus()
    expect(editor.selectionEnd).toBeGreaterThan(editor.selectionStart)
    await user.click(screen.getByRole('tab', { name: 'Recuperación' }))
    expect(screen.getByText('studio-local')).toBeVisible()
    expect(screen.getByText('Verificado por 1A')).toBeVisible()
  })
  it('supports keyboard navigation between result tabs', async () => {
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('button', { name: /Analizar script/ }))
    await screen.findByRole('heading', { name: 'Reconocimiento' })
    screen.getByRole('tab', { name: 'Hallazgos' }).focus()
    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('tab', { name: 'Evidencias' })).toHaveFocus()
    expect(screen.getByRole('tab', { name: 'Evidencias' })).toHaveAttribute('aria-selected', 'true')
    await user.keyboard('{End}')
    expect(screen.getByRole('tab', { name: 'Detalles' })).toHaveFocus()
  })
  it('switches comparison perspectives by keyboard without another analysis request', async () => {
    vi.mocked(api.analyze).mockResolvedValue(comparison)
    const user = await renderApp(); await loadExample(user)
    await user.click(screen.getByRole('radio', { name: 'Comparación A/B/C' }))
    await user.click(screen.getByRole('button', { name: /Comparar A\/B\/C/ }))
    const cards = await screen.findByRole('group', { name: 'Comparación de pipelines' })
    within(cards).getByRole('button', { name: /resultado A/ }).focus()
    await user.keyboard('{ArrowRight}')
    expect(within(cards).getByRole('button', { name: /resultado B/ })).toHaveFocus()
    expect(within(cards).getByRole('button', { name: /resultado B/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Predicciones experimentales del modelo.')).toBeVisible()
    expect(api.analyze).toHaveBeenCalledTimes(1)
  })
})

it('shows the adopted Qwen14 profile and keeps empty predictions experimental', async () => {
  vi.mocked(api.capabilities).mockResolvedValue({ max_input_bytes: 65536, model: 'qwen2.5-coder:14b', expected_digest: 'q14-test-digest', options: {}, timeout_seconds: 300, minimum_margin_bytes: 2147483648, mode_descriptions: {} as never })
  const value = structuredClone(comparison.results[1])
  value.operational.model = 'qwen2.5-coder:14b'
  value.llm!.behaviors = []
  value.evidence = []
  vi.mocked(api.analyze).mockResolvedValue(value)
  const user = await renderApp()
  expect(api.analyze).not.toHaveBeenCalled()
  await loadExample(user)
  await user.click(screen.getByRole('radio', { name: 'B · LLM directo' }))
  await user.click(screen.getByRole('button', { name: /Analizar script/ }))
  expect(await screen.findByRole('heading', { name: 'Predicciones experimentales B' })).toBeVisible()
  expect(screen.getByText('Original → qwen2.5-coder:14b · experimental')).toBeVisible()
  expect(screen.getByText(/No constituyen un veredicto de seguridad/)).toBeVisible()
  expect(screen.getByText(/La ausencia de etiquetas no confirma/)).toBeVisible()
  expect(api.analyze).toHaveBeenCalledExactlyOnceWith(expect.any(String), 'B')
})
