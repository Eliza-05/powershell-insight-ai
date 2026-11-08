import { useEffect, useState } from 'react'
import { ArrowDownToLine, ArrowUpRight, ChevronRight, GitCompareArrows, ScanSearch } from 'lucide-react'
import type { AnalysisResponse, PipelineResult, Span } from '../types/api'
import { behaviorNames, labelsOf, levelNames, resultsOf } from '../types/api'
import { Code, Loading, Notice, RiskBadge, StatusBadge, TechnicalDetail } from './Primitives'
import { formatSeconds, recoveryKindLabel, stepStatusLabel, techniqueLabel } from '../utils/labels'
import { RecoveryTrace } from './RecoveryTrace'
import { useMediaQuery } from '../hooks/useMediaQuery'

type Detail = 'findings' | 'evidence' | 'recovery' | 'timeline' | 'trace'
const tabs: { id: Detail; name: string }[] = [
  { id: 'findings', name: 'Hallazgos' }, { id: 'evidence', name: 'Evidencias' },
  { id: 'recovery', name: 'Recuperación' }, { id: 'timeline', name: 'Traza 1A' }, { id: 'trace', name: 'Detalles' },
]

function EmptyResults() {
  return <div className="empty-results">
    <h3>Sin análisis todavía</h3>
    <p>Pega o carga un script en el editor, elige un enfoque y pulsa «Analizar script».</p>
    <ul className="mode-list">
      <li className="mode-A"><span className="mode-letter">A</span><span><strong>Determinista.</strong> Desofuscación y reglas; funciona sin Ollama.</span></li>
      <li className="mode-B"><span className="mode-letter">B</span><span><strong>LLM directo.</strong> El modelo interpreta solo el original; experimental.</span></li>
      <li className="mode-C"><span className="mode-letter">C</span><span><strong>LLM asistido.</strong> El modelo recibe además la recuperación verificada de 1A; experimental.</span></li>
    </ul>
  </div>
}

function Findings({ result, onLocate }: { result: PipelineResult; onLocate: (span: Span) => void }) {
  const rows = result.configuration === 'A'
    ? result.deterministic?.findings.map(f => ({ id: f.finding_id, label: f.behavior_id, explanation: f.description, support: f.conditions, rule: f.rule_id,
        origin: result.deterministic?.evidence.find(e => f.evidence_ids.includes(e.evidence_id))?.root_source ?? null })) ?? []
    : result.llm?.behaviors.map(f => ({ id: f.behavior_id, label: f.behavior_id, explanation: f.explanation, support: [] as string[], rule: `Confianza declarada: ${levelNames[f.confidence] ?? f.confidence}`,
        origin: result.evidence.find(e => e.behavior_id === f.behavior_id)?.root_source ?? null })) ?? []
  return <div className="detail-content">
    {result.configuration !== 'A' && <Notice tone="warning"><strong>Predicciones experimentales del modelo.</strong> Las citas se comprueban literalmente; sus conclusiones y el riesgo no tienen adjudicación semántica humana. No constituyen un veredicto de seguridad.</Notice>}
    {rows.length ? <table className="findings-table">
      <thead><tr><th scope="col">Código</th><th scope="col">Comportamiento</th><th scope="col">Autor</th><th scope="col">Origen</th></tr></thead>
      <tbody>{rows.map(f => <tr key={f.id}>
        <td><span className="behavior-code">{f.label}</span></td>
        <td>
          <h3>{behaviorNames[f.label] ?? f.label}</h3>
          <p>{f.explanation}</p><span className="finding-rule">{f.rule}</span>
          {f.support.length > 0 && <details><summary>Condiciones que sustentan el hallazgo</summary><ul>{f.support.map((s, i) => <li key={i}>{s}</li>)}</ul></details>}
        </td>
        <td><span className="source-label">{result.configuration === 'A' ? 'REGLA' : 'MODELO'}</span></td>
        <td>{f.origin
          ? <button className="text-button" aria-label={`Ver origen de ${f.label}`} onClick={() => onLocate(f.origin!)}>Ver origen<ArrowUpRight size={13} /></button>
          : <span className="subtle">—</span>}</td>
      </tr>)}</tbody>
    </table> : <div className="quiet-empty"><h3>{result.errors.length ? 'Sin hallazgos aceptados' : 'Sin etiquetas sustentadas'}</h3><p>{result.errors.length ? 'La respuesta no produjo un reporte aceptado. Revisa el motivo de rechazo.' : 'La ausencia de etiquetas no confirma que el script sea benigno.'}</p></div>}
    {result.configuration !== 'A' && <div className="risk-explanation"><div><span className="field-label">Riesgo declarado por el modelo</span><RiskBadge risk={result.risk_label} /></div>
      <p>{result.risk_rationale}</p></div>}
    {result.llm && <div className="uncertainty-box"><h4>Incertidumbre <span>{levelNames[result.llm.uncertainty.level] ?? result.llm.uncertainty.level}</span></h4><p>{result.llm.uncertainty.notes}</p>
      {result.llm.uncertainty.uninterpretable_fragments.map((s, i) => <Code key={i}>{s}</Code>)}</div>}
  </div>
}

function Evidence({ result, onLocate }: { result: PipelineResult; onLocate: (span: Span) => void }) {
  const evidence = result.configuration === 'A'
    ? result.deterministic?.evidence.map(e => ({ id: e.evidence_id, text: e.fragment, origin: e.provenance, root: e.root_source,
        line: e.source.line, column: e.source.column, source: e.source.layer_id, recovered: e.recovered_value,
        transformations: e.transformation_ids.join(', ') })) ?? []
    : result.evidence.map((e, i) => ({ id: `${e.behavior_id}-${i}`, text: e.snippet, origin: e.provenance,
        root: e.root_source, line: e.line, column: e.column, source: e.source_id, recovered: null,
        transformations: e.transformation_id ?? '' }))
  return <div className="detail-content">
    <p className="section-intro">{result.configuration === 'A' ? 'Evidencias del análisis determinista.' : 'Citas literales verificadas; soporte semántico pendiente de revisión personal.'} Cada cita conserva la capa de origen. El botón de ubicación señala su ancla en el script original.</p>
    {evidence.length ? evidence.map(e => <article className="evidence-card" key={e.id}>
      <div className="evidence-meta"><span className={`badge ${e.origin === 'deobfuscator_recovered' ? 'mint-badge' : 'neutral-badge'}`}>{e.origin === 'deobfuscator_recovered' ? 'Recuperado por 1A' : 'Script original'}</span><code>{e.source} · L{e.line}:C{e.column}</code></div>
      <Code>{e.text}</Code>{e.recovered !== null && <div className="recovered-value"><span>Valor recuperado</span><Code>{e.recovered}</Code></div>}
      <div className="evidence-chain"><span>{e.origin === 'deobfuscator_recovered' ? 'Recuperación 1A' : 'Cita literal'}<ChevronRight size={13} />{e.root ? `Original · L${e.root.line}:C${e.root.column}` : `Fuente ${e.source}`}</span></div>
      <div className="evidence-footer"><small>{e.transformations || 'Sin transformaciones'}</small>{e.root && <button className="text-button" onClick={() => onLocate(e.root!)}>Ver origen<ArrowUpRight size={13} /></button>}</div>
    </article>) : <div className="quiet-empty"><h3>No hay citas aceptadas</h3><p>Las evidencias aparecerán aquí cuando existan hallazgos verificables.</p></div>}
    {result.configuration !== 'A' && <Notice>Una cita existente no demuestra por sí misma que sustente la interpretación del modelo.</Notice>}
  </div>
}

function RecoveryView({ result, onLocate }: { result: PipelineResult; onLocate: (span: Span) => void }) {
  const steps = result.deobfuscation?.transformations ?? []
  return <div className="detail-content">
    {result.configuration === 'B' && <Notice>B analiza exclusivamente el original. No se ejecutó el desofuscador en este pipeline.</Notice>}
    {steps.map(t => <article className="recovery-card" key={t.transformation_id}>
      <div className="evidence-meta"><span className="technique-tag">{techniqueLabel(t.technique)}</span><code>{t.transformation_id}</code><span className="subtle">{t.deterministic_verified ? 'Verificado por 1A' : 'Sin resolver'}</span></div>
      <div className="recovery-pair"><div><span className="field-label">Fragmento de origen</span><Code>{t.original_fragment}</Code></div><div><span className="field-label">{t.recovered_text !== null ? 'Texto recuperado' : 'Contenido no textual o desconocido'}</span>
        {t.recovered_text !== null ? <Code>{t.recovered_text}</Code> : <p className="subtle">{t.recovered_bytes_base64 ? 'Se recuperaron bytes. No se interpretan como código ni se ejecutan.' : 'No hay una sustitución textual verificada.'}</p>}</div></div>
      <div className="evidence-footer"><small>{recoveryKindLabel(t.recovery_kind)} · {stepStatusLabel(t.status)}</small><button className="text-button" onClick={() => onLocate(t.root_source)}>Ver origen<ArrowUpRight size={13} /></button></div>
      {t.warnings.length > 0 && <details><summary>Advertencias de transformación</summary>{t.warnings.map((w, i) => <TechnicalDetail key={i}>{w}</TechnicalDetail>)}</details>}
    </article>)}
    {!steps.length && <div className="quiet-empty"><h3>Sin recuperaciones deterministas</h3><p>{result.configuration === 'B' ? 'Esta configuración no incorpora evidencia de 1A.' : 'El motor no recuperó transformaciones dentro de su subconjunto soportado.'}</p></div>}
    {!!result.deobfuscation?.unresolved.length && <div><h4>Fragmentos aún desconocidos</h4>{result.deobfuscation.unresolved.map((u, i) => <div className="unresolved" key={i}><TechnicalDetail>{u.reason}</TechnicalDetail><button className="text-button" onClick={() => onLocate(u.source.layer_id === 'L0' ? u.source : result.deobfuscation!.transformations.find(t => t.source.layer_id === u.source.layer_id)?.root_source ?? u.source)}>Línea {u.source.line}<ArrowUpRight size={13} /></button></div>)}</div>}
    {!!result.llm?.recovered_content.length && <div className="model-recovery"><h4>Reconstrucciones declaradas por el modelo</h4><Notice tone="warning">No verificadas. No se admiten como evidencia de un hallazgo.</Notice>{result.llm.recovered_content.map((s, i) => <Code key={i}>{s}</Code>)}</div>}
  </div>
}

function Trace({ result }: { result: PipelineResult }) {
  const op = result.operational
  const warnings = [...new Set([...result.limitations, ...(result.deobfuscation?.warnings ?? []), ...(result.deterministic?.warnings ?? [])])]
  const limits = [...new Set([...(result.deobfuscation?.limits_hit ?? []), ...(result.deterministic?.limits_hit ?? [])])]
  const rows = [['ID', result.run_id], ['SHA-256 de entrada', result.input_sha256 ?? 'No disponible'], ['Inicio (UTC)', result.started_at],
    ['Duración', formatSeconds(result.duration_seconds, 3)], ...Object.entries(result.engine_versions).map(([k, v]) => [`Motor · ${k}`, v]),
    ...(result.configuration === 'A' ? [] : [['Modelo', op.model ?? 'No despachado'], ['Digest', op.installed_digest ?? op.expected_digest ?? 'Sin verificación'],
      ['Prompt', op.prompt_version ?? 'No construido'], ['Hash de prompt', op.prompt_sha256 ?? 'No disponible'], ['Hash de contexto', op.context_sha256 ?? 'No disponible'],
      ['Inferencia despachada', op.inference_dispatched ? 'Sí' : 'No'], ['Respuesta truncada', op.truncated ? 'Sí' : 'No']])]
  return <div className="detail-content"><dl className="metadata-grid">{rows.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{value}</dd></div>)}</dl>
    {!!op.request?.options && <details><summary>Parámetros de inferencia solicitados</summary><Code>{JSON.stringify({ options: op.request.options, think: op.request.think }, null, 2)}</Code></details>}
    {!!result.llm?.prompt_injection.detected && <Notice tone="warning"><strong>Instrucciones adversarias declaradas por el modelo.</strong>{result.llm.prompt_injection.snippets.map((s, i) => <Code key={i}>{s}</Code>)}</Notice>}
    <details open={result.status !== 'completed'}><summary>Advertencias y limitaciones ({warnings.length + limits.length + (result.deterministic?.indicators.length ?? 0)})</summary><p className="technical-caption">Mensajes técnicos del motor, en su idioma original.</p><ul className="technical-list">{warnings.map((l, i) => <li key={i}>{l}</li>)}{limits.map(l => <li key={l}>Límite alcanzado: {l}</li>)}{result.deterministic?.indicators.map(i => <li key={i.indicator_id}>{i.reason}</li>)}</ul></details>
    {!!op.response?.message?.content && result.errors.length > 0 && <details className="raw-response"><summary>Respuesta cruda rechazada · solo diagnóstico</summary><Notice>Contenido no aceptado por el validador. No se presenta como hallazgo.</Notice><Code>{op.response.message.content}</Code></details>}
  </div>
}

export function Results({ response, busy, mode, stale, onLocate }: { response: AnalysisResponse | null; busy: boolean; mode: string; stale: boolean; onLocate: (span: Span) => void }) {
  const [selected, setSelected] = useState(0)
  const [detailChoice, setDetail] = useState<Detail>('findings')
  const wide = useMediaQuery('(min-width: 1440px)')
  useEffect(() => { setSelected(0); setDetail('findings') }, [response])
  const results = response ? resultsOf(response) : []
  const result = results[Math.min(selected, results.length - 1)]
  // The 1A trace only appears when this result carries recovery work: a right column on wide screens, a tab otherwise.
  const hasTrace = !busy && !!result?.deobfuscation && (result.deobfuscation.transformations.length > 0 || result.deobfuscation.unresolved.length > 0)
  const visibleTabs = tabs.filter(t => t.id !== 'timeline' || (hasTrace && !wide))
  const detail: Detail = visibleTabs.some(t => t.id === detailChoice) ? detailChoice : 'findings'
  function exportResult() {
    if (!response) return
    const blob = new Blob([JSON.stringify(response, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `powershell-insight-${result.run_id}.json`; a.click()
    setTimeout(() => URL.revokeObjectURL(url), 0)
  }
  const techniques = result ? [
    ...(result.deobfuscation?.techniques_detected ?? []).map(technique => ({ technique, origin: '1A' })),
    ...(result.llm?.obfuscation_techniques ?? []).map(technique => ({ technique, origin: 'LLM' })),
  ] : []
  // Highlighted figures only for results that produced a report; a failed run shows its error instead.
  const produced = !!result && (result.status === 'completed' || result.status === 'partial')
  const recoveredCount = result?.deobfuscation?.transformations.filter(t => t.deterministic_verified && t.recovered_text !== null).length
  return <>
  <section className="results-panel panel" aria-label="Resultados del análisis" aria-busy={busy}>
    <div className="panel-heading"><h2><span className="heading-icon" aria-hidden="true"><ScanSearch size={16} /></span>{results.length === 3 ? 'Perspectivas A/B/C' : 'Resultados del análisis'}</h2>
      {response && !busy ? <button className="button secondary export-button" title="Exportar resultado JSON" aria-label="Exportar resultado JSON" onClick={exportResult}><ArrowDownToLine size={16} /><span>JSON</span></button> : <span className="result-readiness">{busy ? 'En proceso' : 'Sin análisis'}</span>}
    </div>
    {busy ? <Loading mode={mode} /> : !result ? <EmptyResults /> : <div className="results-scroll">
      {stale && <div className="stale-notice" role="status">El texto cambió. Estos resultados corresponden al análisis anterior.</div>}
      {results.length === 3 && <div className="comparison-strip" role="group" aria-label="Comparación de pipelines" onKeyDown={event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
        event.preventDefault()
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (selected + (event.key === 'ArrowRight' ? 1 : -1) + 3) % 3
        setSelected(next); setDetail('findings'); document.getElementById(`comparison-${results[next].configuration}`)?.focus()
      }}>
        {results.map((r, i) => <button id={`comparison-${r.configuration}`} tabIndex={selected === i ? 0 : -1} className={`comparison-card mode-${r.configuration} ${selected === i ? 'selected' : ''}`} key={r.run_id} onClick={() => { setSelected(i); setDetail('findings') }} aria-label={`Ver resultado ${r.configuration} · ${r.configuration === 'A' ? 'Determinista' : r.configuration === 'B' ? 'LLM directo' : 'LLM asistido'}`} aria-pressed={selected === i}>
          <div className="comparison-card-title"><span className="mode-letter">{r.configuration}</span><span>{r.configuration === 'A' ? 'Determinista' : r.configuration === 'B' ? 'LLM directo' : 'LLM asistido'}</span></div>
          <StatusBadge status={r.status} /><div className="comparison-labels">{labelsOf(r).length ? labelsOf(r).map(b => <span key={b} className={results.every(other => labelsOf(other).includes(b)) ? 'shared-label' : 'different-label'}>{b}</span>) : <span className="no-labels">Sin etiquetas aceptadas</span>}</div>
          <div className="comparison-meta"><span>{r.configuration === 'A' ? 'Reglas 1B' : 'LLM experimental'}</span><span>{formatSeconds(r.duration_seconds)}</span></div>
          <div className="comparison-evidence"><span>{r.configuration === 'A' ? r.deterministic?.evidence.length ?? 0 : r.evidence.length} citas</span><span>{r.configuration === 'B' ? 'Solo original' : `${r.deobfuscation?.transformations.filter(t => t.deterministic_verified && t.recovered_text !== null).length ?? 0} recuperaciones 1A`}</span></div>
        </button>)}
        {new Set(results.map(r => [...labelsOf(r)].sort().join(','))).size > 1 && <div className="difference-note"><span className="dot amber" />Las etiquetas marcadas difieren entre pipelines.</div>}
        <div className="comparison-note"><GitCompareArrows size={13} />Las diferencias entre salidas no son métricas de calidad científica.</div>
      </div>}
      <div className={`result-overview mode-${result.configuration}`}>
        <div className="result-topline"><div className="result-title"><span className="mode-letter">{result.configuration}</span><div><h3>{result.configuration === 'A' ? 'Lectura determinista' : `Predicciones experimentales ${result.configuration}`}</h3><span>{result.configuration === 'A' ? 'Desofuscador 1A + detector 1B' : `${result.configuration === 'B' ? 'Original' : 'Original + recuperación 1A'} → ${result.operational.model ?? 'Modelo no despachado'} · experimental`}</span></div></div><StatusBadge status={result.status} /></div>
        {produced && <dl className="result-facts">
          <div><dt>Comportamientos</dt><dd>{labelsOf(result).length}</dd></div>
          {result.deobfuscation && <div><dt>Fragmentos recuperados</dt><dd>{recoveredCount}</dd></div>}
          <div><dt>Duración</dt><dd>{formatSeconds(result.duration_seconds)}</dd></div>
        </dl>}
        {produced && <p className="risk-line">{result.configuration === 'A'
          ? 'Riesgo: no aplica (A no clasifica riesgo)'
          : <>Riesgo declarado por el modelo <RiskBadge risk={result.risk_label} /></>}</p>}
        {techniques.length > 0 && <div className="techniques"><span>Técnicas</span>{techniques.map(t => <code key={`${t.technique}-${t.origin}`} title={t.origin === '1A' ? 'Detectada por el motor determinista 1A' : 'Declarada por el modelo provisional'}>{techniqueLabel(t.technique)} · {t.origin}</code>)}</div>}
      </div>
      {(result.status === 'partial' || !!result.llm?.uncertainty.uninterpretable_fragments.length || !!result.deobfuscation?.unresolved.length) && <div className="result-notices"><Notice tone="warning"><strong>Caso indeterminado o de alcance parcial.</strong> Hay fragmentos sin resolver; la ausencia de etiquetas no demuestra benignidad.</Notice></div>}
      {!!result.errors.length && <div className="result-errors" role="alert">{result.errors.map((e, i) => <Notice tone="error" key={i}><strong>{e.code === 'context_limit' ? 'El contexto completo supera el límite del modelo' : e.code === 'insufficient_memory' ? 'Sin margen suficiente de memoria' : e.code === 'invalid_response' ? 'La respuesta no superó la validación' : 'No se pudo completar este pipeline'}</strong><TechnicalDetail>{e.message}</TechnicalDetail><code>{e.code} · {e.stage}</code></Notice>)}</div>}
      <div className="detail-tabs" role="tablist" aria-label="Detalles del resultado" onKeyDown={event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
        event.preventDefault(); const i = visibleTabs.findIndex(t => t.id === detail)
        const index = event.key === 'Home' ? 0 : event.key === 'End' ? visibleTabs.length - 1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + visibleTabs.length) % visibleTabs.length
        setDetail(visibleTabs[index].id); document.getElementById(`tab-${visibleTabs[index].id}`)?.focus()
      }}>{visibleTabs.map(({ id, name }) => <button key={id} id={`tab-${id}`} role="tab" aria-selected={detail === id} tabIndex={detail === id ? 0 : -1} aria-controls="result-detail" onClick={() => setDetail(id)}>{name}</button>)}</div>
      <div role="tabpanel" id="result-detail" aria-labelledby={`tab-${detail}`}>
        {detail === 'findings' && <Findings result={result} onLocate={onLocate} />}{detail === 'evidence' && <Evidence result={result} onLocate={onLocate} />}
        {detail === 'recovery' && <RecoveryView result={result} onLocate={onLocate} />}
        {detail === 'timeline' && <RecoveryTrace embedded result={result} onLocate={onLocate} />}{detail === 'trace' && <Trace result={result} />}
      </div>
      <div className="result-footer"><span title={result.input_sha256 ?? ''}>SHA-256 {result.input_sha256?.slice(0, 16) ?? 'no disponible'}…</span></div>
    </div>}
  </section>
  {hasTrace && wide && <RecoveryTrace result={result} onLocate={onLocate} />}
  </>
}
