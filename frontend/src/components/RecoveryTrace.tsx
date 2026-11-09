import { ArrowUpRight, ListTree } from 'lucide-react'
import type { PipelineResult, Span, Transformation } from '../types/api'
import { recoveryKindLabel, stepStatusLabel, techniqueLabel } from '../utils/labels'
import { TechnicalDetail } from './Primitives'

const layerRank = (layer: string) => Number.parseInt(layer.replace(/\D/g, ''), 10) || 0
const samePlace = (a: Span, b: Span) => a.layer_id === b.layer_id && a.start === b.start && a.end === b.end

type Entry =
  | { key: string; span: Span; kind: 'step'; step: Transformation; reasons: string[] }
  | { key: string; span: Span; kind: 'unresolved'; reason: string }

/** Timeline of the deterministic 1A recovery that arrived with the result. Read-only: no new data, no inference.
 *  Rendered only when the result carries transformations or unresolved fragments. */
export function RecoveryTrace({ result, onLocate, embedded = false }: { result: PipelineResult; onLocate: (span: Span) => void; embedded?: boolean }) {
  const recovery = result.deobfuscation
  const steps: Entry[] = (recovery?.transformations ?? []).map(step => ({ key: step.transformation_id, span: step.source, kind: 'step', step, reasons: [] }))
  const loose: Entry[] = []
  // A failed transformation and its unresolved fragment at the same position are one event: show them together.
  ;(recovery?.unresolved ?? []).forEach((u, i) => {
    const owner = steps.find(e => e.kind === 'step' && samePlace(e.span, u.source))
    if (owner?.kind === 'step') owner.reasons.push(u.reason)
    else loose.push({ key: `unresolved-${i}`, span: u.source, kind: 'unresolved', reason: u.reason })
  })
  const entries = [...steps, ...loose].sort((a, b) => layerRank(a.span.layer_id) - layerRank(b.span.layer_id) || a.span.start - b.span.start || (a.kind === 'step' ? -1 : 1))
  const layers = new Set(recovery?.layers.map(layer => layer.layer_id) ?? []).size
  const unresolvedCount = recovery?.unresolved.length ?? 0
  const stepCount = recovery?.transformations.length ?? 0
  const summary = `${layers} ${layers === 1 ? 'capa' : 'capas'} · ${stepCount} ${stepCount === 1 ? 'transformación' : 'transformaciones'} · ${unresolvedCount} sin resolver`

  const list = <ol className="trace-list">{entries.map(e => <li key={e.key} className={`trace-entry trace-${e.kind}${e.kind === 'step' && e.reasons.length ? ' has-reason' : ''}`}>
    <span className="trace-mark">{e.span.layer_id} {e.span.line}:{e.span.column}</span>
    {e.kind === 'step' ? <div className="trace-body">
      <p className="trace-technique">{techniqueLabel(e.step.technique)}</p>
      <p className="trace-meta"><span className="trace-id">{e.step.transformation_id}</span> · {e.step.deterministic_verified ? 'verificada' : stepStatusLabel(e.step.status)} · {recoveryKindLabel(e.step.recovery_kind)}{e.span.layer_id !== 'L0' && ` · raíz en el original L${e.step.root_source.line}:C${e.step.root_source.column}`}</p>
      {e.reasons.map((reason, i) => <div className="trace-reason" key={i}><span className="trace-flag">sin resolver</span><TechnicalDetail>{reason}</TechnicalDetail></div>)}
      <button className="text-button" aria-label={`Ver origen de ${e.step.transformation_id}`} onClick={() => onLocate(e.step.root_source)}>Ver origen<ArrowUpRight size={13} /></button>
    </div> : <div className="trace-body">
      <span className="trace-flag">sin resolver</span>
      <TechnicalDetail>{e.reason}</TechnicalDetail>
    </div>}
  </li>)}</ol>

  if (embedded) return <div className="detail-content trace-embedded"><p className="trace-count">{summary}</p>{list}</div>
  return <aside className="trace-panel panel" aria-labelledby="trace-title">
    <div className="panel-heading"><h2 id="trace-title"><span className="heading-icon" aria-hidden="true"><ListTree size={16} /></span>Traza de recuperación 1A</h2></div>
    <div className="trace-scroll"><p className="trace-count">{summary}</p>{list}</div>
  </aside>
}
