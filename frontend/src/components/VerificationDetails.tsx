import type { PipelineResult, Span } from '../types/api'
import { riskNames } from '../types/api'
import { Code, Notice, TechnicalDetail } from './Primitives'

export function SanitizationNotice({ result }: { result: PipelineResult }) {
  const sources = result.operational.preprocessing?.sources.filter(s => s.diagnostics.length) ?? []
  return sources.length > 0 ? <Notice tone="warning"><strong>Sanitización parcial o región opaca.</strong> Se conservó el texto incierto; pueden quedar comentarios o instrucciones visibles para el modelo. Esta capa no elimina toda inyección de instrucciones.</Notice> : null
}

export function VerificationDetails({ result, onLocate }: { result: PipelineResult; onLocate: (span: Span) => void }) {
  if (result.configuration === 'A') return null
  const op = result.operational, check = op.evidence_check, before = op.model_report_before_evidence_check
  const originalIds = before?.behaviors.map(b => b.behavior_id) ?? op.model_behaviors_before_evidence_check?.map(b => b.behavior_id)
  if (!check && !originalIds && !op.preprocessing) return null
  const rejected = check?.status === 'rejected_incoherent'
  const unpublished = !result.llm && ['error', 'unavailable', 'rejected'].includes(result.status)
  const decisions = check?.decisions ?? []
  const risk = before?.risk_label ?? check?.risk_preserved_from_model
  return <section className="verification-detail" aria-label="Verificación determinista de evidencia">
    <h4>Predicción y postprocesamiento</h4>
    {rejected && <Notice tone="error"><strong>Publicación del resultado rechazada.</strong> El filtrado de etiquetas entra en conflicto con el riesgo del modelo. Esto no es una conclusión de benignidad.</Notice>}
    <dl className="metadata-grid">
      <div><dt>Predicción original del LLM</dt><dd>{originalIds === undefined ? 'No disponible en el contrato aceptado' : originalIds.join(', ') || 'Sin etiquetas declaradas'}</dd></div>
      <div><dt>Resultado aceptado</dt><dd>{unpublished ? 'No se publica un informe LLM' : result.llm?.behaviors.map(b => b.behavior_id).join(', ') || 'Sin etiquetas conservadas'}</dd></div>
      {risk && <div><dt>Riesgo atribuido originalmente al modelo</dt><dd>{riskNames[risk]}</dd></div>}
      {check && <div><dt>Verificador</dt><dd>{check.version}</dd></div>}
    </dl>
    <Notice>Conservar una etiqueta indica soporte estructural limitado. Descartarla significa «no verificado por el postprocesamiento», no que el comportamiento no exista. No hay validación semántica humana.</Notice>
    {decisions.map((d, index) => <details className="verifier-decision" key={`${d.from}-${index}`}>
      <summary>{d.from} · {d.action === 'kept' ? 'Soporte estructural limitado' : d.action === 'dropped' ? 'No verificado por el postprocesamiento' : `Reclasificado a ${d.to ?? 'otra etiqueta'} · requiere revisión`}</summary>
      <TechnicalDetail>{d.reason}</TechnicalDetail>
      {d.citations.map((c, i) => <article className="evidence-card" key={i}>
        <div className="evidence-meta"><code>{c.source_id} · L{c.line}:C{c.column} · [{c.start}, {c.end})</code></div>
        <Code>{c.snippet}</Code><TechnicalDetail>{c.reason}</TechnicalDetail>
        {c.operations.map((operation, j) => <div key={j}><p className="finding-rule">{operation.rule_id} · [{operation.start}, {operation.end})</p><Code>{operation.snippet}</Code>
          <ul>{operation.conditions.map((condition, n) => <li key={n}>{condition}</li>)}</ul>
          {operation.limitations.map((limit, n) => <TechnicalDetail key={n}>{limit}</TechnicalDetail>)}</div>)}
        {c.root_source && <button className="text-button" onClick={() => onLocate(c.root_source!)}>Ver origen de la cita de {d.from}</button>}
      </article>)}
      {d.source_diagnostics.map((diagnostic, i) => <TechnicalDetail key={i}>{diagnostic}</TechnicalDetail>)}
    </details>)}
    {!check?.decisions && !!check?.changes.length && <p>La versión histórica solo registró cambios resumidos: {check.changes.map(c => `${c.from} → ${c.to ?? 'no conservada'}`).join('; ')}. No incluye decisiones estructuradas.</p>}
    {!!op.preprocessing?.sources.some(s => s.diagnostics.length) && <details><summary>Diagnósticos de sanitización</summary>
      {op.preprocessing.sources.flatMap((s, i) => s.diagnostics.map((diagnostic, j) => <div key={`${i}-${j}`}><code>{s.source_ids.join(', ') || 'Fragmento de traza'} · [{diagnostic.start}, {diagnostic.end})</code><TechnicalDetail>{diagnostic.reason}</TechnicalDetail></div>))}
    </details>}
    {check?.limitations?.map((limit, i) => <TechnicalDetail key={i}>{limit}</TechnicalDetail>)}
    {before && <details><summary>Respuesta original del modelo · auditoría</summary><Code>{JSON.stringify(before, null, 2)}</Code></details>}
  </section>
}
