import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Results } from '../components/Results'
import { analysisResponse } from '../services/contracts'
import type { AnalysisResponse, Mode, PipelineResult } from '../types/api'
import captured from './fixtures/integrated-qwen3.json'
import historical from './fixtures/comparison.json'

const packets = captured as unknown as Record<string, { mode: Mode; script: string; response: AnalysisResponse }>

describe('perfil integrado · contrato real de la API simulada', () => {
  it.each(Object.keys(packets))('preserves %s and its full operational JSON', async name => {
    const p = packets[name]
    const result = await analysisResponse(p.response, p.mode, p.script)
    expect(result).toBe(p.response)
    expect(JSON.parse(JSON.stringify(result))).toEqual(p.response)
  })
  it.each(['decisions', 'citations', 'operations', 'preprocessing', 'original_report', 'wrong_span'])('rejects malformed %s before rendering', async kind => {
    const p = structuredClone(packets.kept)
    const op = (p.response as PipelineResult).operational
    if (kind === 'decisions') Object.assign(op.evidence_check!, { decisions: {} })
    if (kind === 'citations') Object.assign(op.evidence_check!.decisions![0], { citations: null })
    if (kind === 'operations') Object.assign(op.evidence_check!.decisions![0].citations[0], { operations: 'unsafe' })
    if (kind === 'preprocessing') Object.assign(op.preprocessing!, { sources: [null] })
    if (kind === 'original_report') Object.assign(op.model_report_before_evidence_check!, { behaviors: null })
    if (kind === 'wrong_span') op.evidence_check!.decisions![0].citations[0].operations[0].start = 0
    await expect(analysisResponse(p.response, p.mode, p.script)).rejects.toThrow()
  })
})

describe('presentación discreta del postprocesamiento', () => {
  it.each(['kept', 'dropped', 'incoherent', 'opaque', 'recovered'])('distinguishes original/accepted/limitations in %s without another analysis', async name => {
    const p = packets[name], locate = vi.fn(), user = userEvent.setup()
    render(<Results response={p.response} busy={false} mode={p.mode} stale={false} onLocate={locate} />)
    expect(screen.queryByRole('region', { name: 'Verificación determinista de evidencia' })).toBeNull()
    await user.click(screen.getByRole('button', { name: 'Predicción y postprocesamiento' }))
    const detail = screen.getByRole('region', { name: 'Verificación determinista de evidencia' })
    expect(within(detail).getByText('Predicción original del LLM')).toBeInTheDocument()
    expect(within(detail).getByText('Resultado aceptado')).toBeInTheDocument()
    expect(within(detail).getByText(/no que el comportamiento no exista/)).toBeInTheDocument()
    if (name === 'kept') {
      await user.click(within(detail).getByText('B05 · Soporte estructural limitado'))
      await user.click(within(detail).getByRole('button', { name: 'Ver origen de la cita de B05' }))
      expect(locate).toHaveBeenCalledOnce()
    }
    if (name === 'dropped' || name === 'recovered') expect(within(detail).getByText('B05 · No verificado por el postprocesamiento')).toBeInTheDocument()
    if (name === 'incoherent') {
      expect(screen.getByRole('alert')).toHaveTextContent('Publicación rechazada')
      expect(within(detail).getByText('No se publica un informe LLM')).toBeInTheDocument()
      expect(within(detail).getByText('Riesgo alto')).toBeInTheDocument()
      expect(screen.queryByText('Deterministic behavior does not establish intent or safety.')).toBeNull()
    }
    if (name === 'opaque') expect(screen.getByText('Sanitización parcial o región opaca.')).toBeInTheDocument()
    await user.click(screen.getByRole('tab', { name: 'Evidencias' }))
    await user.click(screen.getByRole('tab', { name: 'Detalles' }))
    expect(screen.getByRole('region', { name: 'Verificación determinista de evidencia' })).toBeInTheDocument()
  })
  it('retains historical Qwen14/A without requiring new fields', () => {
    render(<Results response={historical as unknown as AnalysisResponse} busy={false} mode="ABC" stale={false} onLocate={vi.fn()} />)
    expect(screen.queryByText('Predicción y postprocesamiento')).toBeNull()
  })
  it('does not interpret an invalid raw response as an empty model prediction', async () => {
    render(<Results response={packets.invalid_json.response} busy={false} mode="B" stale={false} onLocate={vi.fn()} />)
    await userEvent.click(screen.getByRole('tab', { name: 'Detalles' }))
    expect(screen.getByText('No disponible en el contrato aceptado')).toBeInTheDocument()
    expect(screen.getByText('No se publica un informe LLM')).toBeInTheDocument()
    expect(screen.queryByText('Sin etiquetas declaradas')).toBeNull()
  })
  it('renders adversarial report text as text, never HTML', async () => {
    const p = structuredClone(packets.kept)
    ;(p.response as PipelineResult).operational.model_report_before_evidence_check!.risk_rationale = '<img src=x onerror="alert(1)">'
    const { container } = render(<Results response={p.response} busy={false} mode="B" stale={false} onLocate={vi.fn()} />)
    await userEvent.click(screen.getByRole('tab', { name: 'Detalles' }))
    expect(container.querySelector('img')).toBeNull()
    expect(screen.getByText(/<img src=x/, { exact: false })).toBeInTheDocument()
  })
})
