import { ArrowUpRight } from 'lucide-react'
import type { PipelineResult, Span, Transformation } from '../types/api'

const stepStatus: Record<string, string> = { success: 'recuperada', partial: 'bytes parciales', failed: 'fallida', unsupported: 'no soportada' }
const layerRank = (layer: string) => Number.parseInt(layer.replace(/\D/g, ''), 10) || 0

type Entry =
  | { key: string; span: Span; kind: 'step'; step: Transformation }
  | { key: string; span: Span; kind: 'unresolved'; reason: string }

/** Timeline of the deterministic 1A recovery that arrived with the result. Read-only: no new data, no inference.
 *  Rendered only when the result carries transformations or unresolved fragments. */
export function RecoveryTrace({ result, onLocate, embedded = false }: { result: PipelineResult; onLocate: (span: Span) => void; embedded?: boolean }) {
  const recovery = result.deobfuscation
  const entries: Entry[] = recovery ? [
    ...recovery.transformations.map(step => ({ key: step.transformation_id, span: step.source, kind: 'step' as const, step })),
    ...recovery.unresolved.map((u, i) => ({ key: `unresolved-${i}`, span: u.source, kind: 'unresolved' as const, reason: u.reason })),
  ].sort((a, b) => layerRank(a.span.layer_id) - layerRank(b.span.layer_id) || a.span.start - b.span.start || (a.kind === 'step' ? -1 : 1)) : []
  const layers = new Set(['L0', ...entries.map(e => e.span.layer_id)]).size
  const unresolved = entries.filter(e => e.kind === 'unresolved').length
  const summary = `${layers} ${layers === 1 ? 'capa' : 'capas'} · ${entries.length - unresolved} transf. · ${unresolved} sin resolver`

  const list = <ol className="trace-list">{entries.map(e => <li key={e.key} className={`trace-entry trace-${e.kind}`}>
    <span className="trace-mark">{e.span.layer_id} {e.span.line}:{e.span.column}</span>
    {e.kind === 'step' ? <div className="trace-body">
      <p><code>{e.step.technique}</code> <span className="trace-id">{e.step.transformation_id}</span></p>
      <p className="trace-meta">{e.step.deterministic_verified ? 'verificada' : stepStatus[e.step.status] ?? e.step.status} · {e.step.recovery_kind}{e.span.layer_id !== 'L0' && ` · raíz en el original L${e.step.root_source.line}:C${e.step.root_source.column}`}</p>
      <button className="text-button" aria-label={`Ubicar ${e.step.transformation_id} en el original`} onClick={() => onLocate(e.step.root_source)}>Ubicar<ArrowUpRight size={13} /></button>
    </div> : <div className="trace-body">
      <p>Fragmento sin resolver</p>
      <p className="trace-meta">{e.reason}</p>
    </div>}
  </li>)}</ol>

  if (embedded) return <div className="detail-content trace-embedded"><p className="trace-count">{summary}</p>{list}</div>
  return <aside className="trace-panel panel" aria-labelledby="trace-title">
    <div className="panel-heading"><h2 id="trace-title">Traza de recuperación 1A</h2><span className="trace-count">{summary}</span></div>
    {list}
  </aside>
}
