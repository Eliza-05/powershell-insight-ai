import { GitCompareArrows, LoaderCircle, Play, TriangleAlert } from 'lucide-react'
import type { Mode } from '../types/api'

const choices = [
  { id: 'A', title: 'Determinista' },
  { id: 'B', title: 'LLM directo' },
  { id: 'C', title: 'LLM asistido' },
  { id: 'ABC', title: 'Comparar' },
] as const

function descriptions(modelName?: string): Record<Mode, string> { return {
  A: 'Original → desofuscación → reglas. Funciona sin Ollama.',
  B: `Solo el original → ${modelName ?? 'modelo configurado'} experimental. Sin información del motor determinista.`,
  C: `Original + recuperación verificada de 1A → ${modelName ?? 'modelo configurado'} experimental. Sin etiquetas de 1B.`,
  ABC: 'El mismo script, tres ejecuciones independientes. Las diferencias no miden calidad científica.',
} }

export function PipelineSelector({ mode, onChange, busy, canRun, onRun, warning, modelName }: {
  mode: Mode; onChange: (mode: Mode) => void; busy: boolean; canRun: boolean; onRun: () => void; warning?: string; modelName?: string;
}) {
  return <section className="analysis-command" aria-label="Selección del pipeline">
    <div className="command-row">
      <fieldset disabled={busy} className="pipeline-fieldset">
        <legend>Enfoque</legend>
        <div className="pipeline-options">
          {choices.map(({ id, title }) => <label className={`pipeline-option mode-${id} ${mode === id ? 'selected' : ''}`} key={id}>
            <input type="radio" name="pipeline" value={id} checked={mode === id} onChange={() => onChange(id)}
              aria-label={id === 'ABC' ? 'Comparación A/B/C' : `${id} · ${title}`} aria-describedby="pipeline-description" />
            <span className="pipeline-key">{id === 'ABC' ? <GitCompareArrows size={15} /> : id}</span>
            <span>{title}</span>
          </label>)}
        </div>
      </fieldset>
      <button className="button primary analyze-button" disabled={busy || !canRun} onClick={onRun} aria-describedby={warning ? 'run-warning' : undefined}>
        {busy ? <LoaderCircle className="spin" size={17} /> : <Play size={15} fill="currentColor" />}
        {busy ? 'Analizando…' : mode === 'ABC' ? 'Comparar A/B/C' : 'Analizar script'}
        {!busy && <kbd aria-hidden="true">Ctrl+Enter</kbd>}
      </button>
    </div>
    <p className="pipeline-description" id="pipeline-description"><span className={`description-mark mode-${mode}`}>{mode === 'ABC' ? 'A/B/C' : mode}</span>{descriptions(modelName)[mode]}</p>
    {warning && <p className="run-warning" id="run-warning"><TriangleAlert size={15} aria-hidden="true" />{warning}</p>}
  </section>
}
