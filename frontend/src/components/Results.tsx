import { useEffect, useState } from 'react'
import { ArrowDownToLine, ArrowUpRight, Binary, ChevronDown, ChevronRight, Clock3, Code2, FileSearch2, Fingerprint, GitCompareArrows, Layers3, ListChecks, ScanLine, ShieldCheck, Sparkles } from 'lucide-react'
import type { AnalysisResponse, PipelineResult, Span } from '../types/api'
import { behaviorNames, labelsOf, levelNames, resultsOf } from '../types/api'
import { Code, Loading, Notice, RiskBadge, StatusBadge } from './Primitives'

type Detail = 'findings' | 'evidence' | 'recovery' | 'trace'
const tabs: { id: Detail; name: string; icon: typeof Layers3 }[] = [
  { id: 'findings', name: 'Hallazgos', icon: ListChecks }, { id: 'evidence', name: 'Evidencias', icon: ScanLine },
  { id: 'recovery', name: 'Recuperación', icon: Binary }, { id: 'trace', name: 'Detalles', icon: Fingerprint },
]

function EmptyResults() {
  return <div className="empty-results">
    <div className="evidence-signal" aria-hidden="true"><span><Code2 size={24} /></span><i /><span><Layers3 size={24} /></span><i /><span><Fingerprint size={24} /></span></div>
    <span className="eyebrow">ESPERANDO UN ANÁLISIS</span><h3>Una lectura. Tres perspectivas.</h3>
    <p>Ejecuta un pipeline para explorar comportamientos, contenido recuperado y la evidencia que los sustenta.</p>
    <div className="empty-perspectives">
      <div><span className="perspective-key mode-A">A</span><div><strong>Operaciones observadas</strong><p>Desofuscación y reglas deterministas.</p></div><ShieldCheck size={18} /></div>
      <div><span className="perspective-key mode-B">B</span><div><strong>Interpretación del original</strong><p>LLM directo, sin recuperación previa.</p></div><Sparkles size={18} /></div>
      <div><span className="perspective-key mode-C">C</span><div><strong>Interpretación con contexto</strong><p>LLM con evidencia verificable de 1A.</p></div><Layers3 size={18} /></div>
    </div>
    <p className="empty-safety"><ShieldCheck size={16} />Sin ejecución. Cada resultado conserva su procedencia.</p>
  </div>
}

function Findings({ result }: { result: PipelineResult }) {
  const rows = result.configuration === 'A'
    ? result.deterministic?.findings.map(f => ({ id: f.finding_id, label: f.behavior_id, explanation: f.description, support: f.conditions, rule: f.rule_id })) ?? []
    : result.llm?.behaviors.map(f => ({ id: f.behavior_id, label: f.behavior_id, explanation: f.explanation, support: [] as string[], rule: `Confianza declarada: ${levelNames[f.confidence] ?? f.confidence}` })) ?? []
  return <div className="detail-content">
    {result.configuration !== 'A' && <Notice tone="warning"><strong>Predicciones experimentales del modelo.</strong> Las citas se comprueban literalmente; sus conclusiones y el riesgo no tienen adjudicación semántica humana. No constituyen un veredicto de seguridad.</Notice>}
    {rows.length ? rows.map(f => <article className="finding-card" key={f.id}>
      <div className="finding-heading"><span className="behavior-code">{f.label}</span><h3>{behaviorNames[f.label] ?? f.label}</h3><span className="source-label">{result.configuration === 'A' ? 'REGLA' : 'MODELO'}</span></div>
      <p>{f.explanation}</p><span className="finding-rule">{f.rule}</span>
      {f.support.length > 0 && <details><summary>Condiciones que sustentan el hallazgo</summary><ul>{f.support.map((s, i) => <li key={i}>{s}</li>)}</ul></details>}
    </article>) : <div className="quiet-empty"><FileSearch2 size={28} /><h3>{result.errors.length ? 'Sin hallazgos aceptados' : 'Sin etiquetas sustentadas'}</h3><p>{result.errors.length ? 'La respuesta no produjo un reporte aceptado. Revisa el motivo de rechazo.' : 'La ausencia de etiquetas no confirma que el script sea benigno.'}</p></div>}
    <div className="risk-explanation"><div><span className="eyebrow">RIESGO {result.configuration === 'A' ? 'SIN CLASIFICAR' : 'DECLARADO POR EL MODELO'}</span><RiskBadge risk={result.risk_label} /></div>
      <p>{result.configuration === 'A' ? 'El motor identifica operaciones. No determina intención, legitimidad ni seguridad del script.' : result.risk_rationale}</p></div>
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
      <div className="evidence-chain"><Fingerprint size={15} /><span>{e.origin === 'deobfuscator_recovered' ? 'Recuperación 1A' : 'Cita literal'}<ChevronRight size={13} />{e.root ? `Original · L${e.root.line}:C${e.root.column}` : `Fuente ${e.source}`}</span></div>
      <div className="evidence-footer"><small>{e.transformations || 'Sin transformaciones'}</small>{e.root && <button className="text-button" onClick={() => onLocate(e.root!)}>Ver origen<ArrowUpRight size={13} /></button>}</div>
    </article>) : <div className="quiet-empty"><ScanLine size={28} /><h3>No hay citas aceptadas</h3><p>Las evidencias aparecerán aquí cuando existan hallazgos verificables.</p></div>}
    {result.configuration !== 'A' && <Notice>Una cita existente no demuestra por sí misma que sustente la interpretación del modelo.</Notice>}
  </div>
}

function RecoveryView({ result, onLocate }: { result: PipelineResult; onLocate: (span: Span) => void }) {
  const steps = result.deobfuscation?.transformations ?? []
  return <div className="detail-content">
    {result.configuration === 'B' && <Notice>B analiza exclusivamente el original. No se ejecutó el desofuscador en este pipeline.</Notice>}
    {steps.map(t => <article className="recovery-card" key={t.transformation_id}>
      <div className="evidence-meta"><span className="badge mint-badge">{t.technique}</span><code>{t.transformation_id}</code><span className="subtle">{t.deterministic_verified ? 'Verificado por 1A' : 'Sin resolver'}</span></div>
      <div className="recovery-pair"><div><span className="eyebrow">FRAGMENTO DE ORIGEN</span><Code>{t.original_fragment}</Code></div><div><span className="eyebrow">{t.recovered_text !== null ? 'TEXTO RECUPERADO' : 'CONTENIDO NO TEXTUAL / DESCONOCIDO'}</span>
        {t.recovered_text !== null ? <Code>{t.recovered_text}</Code> : <p className="subtle">{t.recovered_bytes_base64 ? 'Se recuperaron bytes. No se interpretan como código ni se ejecutan.' : 'No hay una sustitución textual verificada.'}</p>}</div></div>
      <div className="evidence-footer"><small>{t.recovery_kind} · {t.status}</small><button className="text-button" onClick={() => onLocate(t.root_source)}>Ver origen<ArrowUpRight size={13} /></button></div>
      {t.warnings.length > 0 && <details><summary>Advertencias de transformación</summary><ul>{t.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul></details>}
    </article>)}
    {!steps.length && <div className="quiet-empty"><Binary size={28} /><h3>Sin recuperaciones deterministas</h3><p>{result.configuration === 'B' ? 'Esta configuración no incorpora evidencia de 1A.' : 'El motor no recuperó transformaciones dentro de su subconjunto soportado.'}</p></div>}
    {!!result.deobfuscation?.unresolved.length && <div><h4>Fragmentos aún desconocidos</h4>{result.deobfuscation.unresolved.map((u, i) => <div className="unresolved" key={i}><p>{u.reason}</p><button className="text-button" onClick={() => onLocate(u.source.layer_id === 'L0' ? u.source : result.deobfuscation!.transformations.find(t => t.source.layer_id === u.source.layer_id)?.root_source ?? u.source)}>Línea {u.source.line}<ArrowUpRight size={13} /></button></div>)}</div>}
    {!!result.llm?.recovered_content.length && <div className="model-recovery"><h4><Sparkles size={15} />Reconstrucciones declaradas por el modelo</h4><Notice tone="warning">No verificadas. No se admiten como evidencia de un hallazgo.</Notice>{result.llm.recovered_content.map((s, i) => <Code key={i}>{s}</Code>)}</div>}
  </div>
}

function Trace({ result }: { result: PipelineResult }) {
  const op = result.operational
  const warnings = [...new Set([...result.limitations, ...(result.deobfuscation?.warnings ?? []), ...(result.deterministic?.warnings ?? [])])]
  const limits = [...new Set([...(result.deobfuscation?.limits_hit ?? []), ...(result.deterministic?.limits_hit ?? [])])]
  const rows = [['ID', result.run_id], ['SHA-256 de entrada', result.input_sha256 ?? 'No disponible'], ['Inicio (UTC)', result.started_at],
    ['Duración', `${result.duration_seconds.toFixed(3)} s`], ...Object.entries(result.engine_versions).map(([k, v]) => [`Motor · ${k}`, v]),
    ...(result.configuration === 'A' ? [] : [['Modelo', op.model ?? 'No despachado'], ['Digest', op.installed_digest ?? op.expected_digest ?? 'Sin verificación'],
      ['Prompt', op.prompt_version ?? 'No construido'], ['Hash de prompt', op.prompt_sha256 ?? 'No disponible'], ['Hash de contexto', op.context_sha256 ?? 'No disponible'],
      ['Inferencia despachada', op.inference_dispatched ? 'Sí' : 'No'], ['Respuesta truncada', op.truncated ? 'Sí' : 'No']])]
  return <div className="detail-content"><dl className="metadata-grid">{rows.map(([name, value]) => <div key={name}><dt>{name}</dt><dd>{value}</dd></div>)}</dl>
    {!!op.request?.options && <details><summary>Parámetros de inferencia solicitados</summary><Code>{JSON.stringify({ options: op.request.options, think: op.request.think }, null, 2)}</Code></details>}
    {!!result.llm?.prompt_injection.detected && <Notice tone="warning"><strong>Instrucciones adversarias declaradas por el modelo.</strong>{result.llm.prompt_injection.snippets.map((s, i) => <Code key={i}>{s}</Code>)}</Notice>}
    <details open={result.status !== 'completed'}><summary>Advertencias y limitaciones ({warnings.length + limits.length + (result.deterministic?.indicators.length ?? 0)})</summary><ul>{warnings.map((l, i) => <li key={i}>{l}</li>)}{limits.map(l => <li key={l}>Límite alcanzado: {l}</li>)}{result.deterministic?.indicators.map(i => <li key={i.indicator_id}>{i.reason}</li>)}</ul></details>
    {!!op.response?.message?.content && result.errors.length > 0 && <details className="raw-response"><summary>Respuesta cruda rechazada · solo diagnóstico</summary><Notice>Contenido no aceptado por el validador. No se presenta como hallazgo.</Notice><Code>{op.response.message.content}</Code></details>}
  </div>
}

export function Results({ response, busy, mode, stale, onLocate }: { response: AnalysisResponse | null; busy: boolean; mode: string; stale: boolean; onLocate: (span: Span) => void }) {
  const [selected, setSelected] = useState(0)
  const [detail, setDetail] = useState<Detail>('findings')
  useEffect(() => { setSelected(0); setDetail('findings') }, [response])
  const results = response ? resultsOf(response) : []
  const result = results[Math.min(selected, results.length - 1)]
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
  return <section className="results-panel panel" aria-label="Resultados del análisis" aria-busy={busy}>
    <div className="panel-heading"><div><ScanLine size={21} /><h2>{results.length === 3 ? 'Perspectivas A/B/C' : 'Resultados del análisis'}</h2></div>
      {response && !busy ? <button className="button secondary export-button" title="Exportar resultado JSON" aria-label="Exportar resultado JSON" onClick={exportResult}><ArrowDownToLine size={18} /><span>JSON</span></button> : <span className="result-readiness">{busy ? 'En proceso' : 'Sin análisis'}</span>}
    </div>
    {busy ? <Loading mode={mode} /> : !result ? <EmptyResults /> : <>
      {stale && <div className="stale-notice" role="status">El texto cambió. Estos resultados corresponden al análisis anterior.</div>}
      {results.length === 3 && <div className="comparison-strip" role="group" aria-label="Comparación de pipelines" onKeyDown={event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
        event.preventDefault()
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? 2 : (selected + (event.key === 'ArrowRight' ? 1 : -1) + 3) % 3
        setSelected(next); setDetail('findings'); document.getElementById(`comparison-${results[next].configuration}`)?.focus()
      }}>
        {results.map((r, i) => <button id={`comparison-${r.configuration}`} tabIndex={selected === i ? 0 : -1} className={`comparison-card mode-${r.configuration} ${selected === i ? 'selected' : ''}`} key={r.run_id} onClick={() => { setSelected(i); setDetail('findings') }} aria-label={`Ver resultado ${r.configuration} · ${r.configuration === 'A' ? 'Determinista' : r.configuration === 'B' ? 'LLM directo' : 'LLM asistido'}`} aria-pressed={selected === i}>
          <div className="comparison-card-title"><span className="mode-letter">{r.configuration}</span><span>{r.configuration === 'A' ? 'Determinista' : r.configuration === 'B' ? 'LLM directo' : 'LLM asistido'}</span><ChevronRight size={13} /></div>
          <StatusBadge status={r.status} /><div className="comparison-labels">{labelsOf(r).length ? labelsOf(r).map(b => <span key={b} className={results.every(other => labelsOf(other).includes(b)) ? 'shared-label' : 'different-label'}>{b}</span>) : <span className="no-labels">Sin etiquetas aceptadas</span>}</div>
          <div className="comparison-meta"><span>{r.configuration === 'A' ? 'Reglas 1B' : 'LLM experimental'}</span><span>{r.duration_seconds.toFixed(2)} s</span></div>
          <div className="comparison-evidence"><span>{r.configuration === 'A' ? r.deterministic?.evidence.length ?? 0 : r.evidence.length} citas</span><span>{r.configuration === 'B' ? 'Solo original' : `${r.deobfuscation?.transformations.filter(t => t.deterministic_verified && t.recovered_text !== null).length ?? 0} recuperaciones 1A`}</span></div>
        </button>)}
        {new Set(results.map(r => [...labelsOf(r)].sort().join(','))).size > 1 && <div className="difference-note"><span className="dot amber" />Las etiquetas marcadas difieren entre pipelines.</div>}
        <div className="comparison-note"><GitCompareArrows size={13} />Las diferencias entre salidas no son métricas de calidad científica.</div>
      </div>}
      <div className={`result-overview mode-${result.configuration}`}><div className="result-topline"><div className="result-title"><span className="mode-letter">{result.configuration}</span><div><h3>{result.configuration === 'A' ? 'Lectura determinista' : `Predicciones experimentales ${result.configuration}`}</h3><span>{result.configuration === 'A' ? 'Desofuscador 1A + detector 1B' : `${result.configuration === 'B' ? 'Original' : 'Original + recuperación 1A'} → ${result.operational.model ?? 'Modelo no despachado'} · experimental`}</span></div></div><StatusBadge status={result.status} /></div>
        <div className="result-metrics"><div><span>COMPORTAMIENTOS</span><strong>{labelsOf(result).length}<small>categorías</small></strong></div><div><span>RIESGO{result.configuration !== 'A' ? ' DEL MODELO' : ''}</span><RiskBadge risk={result.risk_label} /></div><div><span>DURACIÓN</span><strong><Clock3 size={17} />{result.duration_seconds.toFixed(2)}<small>s</small></strong></div></div>
        {techniques.length > 0 && <div className="techniques"><span>Técnicas</span>{techniques.map(t => <code key={`${t.technique}-${t.origin}`} title={t.origin === '1A' ? 'Detectada por el motor determinista 1A' : 'Declarada por el modelo provisional'}>{t.technique} · {t.origin}</code>)}</div>}
      </div>
      {(result.status === 'partial' || !!result.llm?.uncertainty.uninterpretable_fragments.length || !!result.deobfuscation?.unresolved.length) && <Notice tone="warning"><strong>Caso indeterminado o de alcance parcial.</strong> Hay fragmentos sin resolver; la ausencia de etiquetas no demuestra benignidad.</Notice>}
      {!!result.errors.length && <div className="result-errors" role="alert">{result.errors.map((e, i) => <Notice tone="error" key={i}><strong>{e.code === 'context_limit' ? 'El contexto completo supera el límite del modelo' : e.code === 'insufficient_memory' ? 'Sin margen suficiente de memoria' : e.code === 'invalid_response' ? 'La respuesta no superó la validación' : 'No se pudo completar este pipeline'}</strong><p>{e.message}</p><code>{e.code} · {e.stage}</code></Notice>)}</div>}
      <div className="detail-tabs" role="tablist" aria-label="Detalles del resultado" onKeyDown={event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
        event.preventDefault(); const i = tabs.findIndex(t => t.id === detail)
        const index = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (i + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length
        setDetail(tabs[index].id); document.getElementById(`tab-${tabs[index].id}`)?.focus()
      }}>{tabs.map(({ id, name, icon: Icon }) => <button key={id} id={`tab-${id}`} role="tab" aria-selected={detail === id} tabIndex={detail === id ? 0 : -1} aria-controls="result-detail" onClick={() => setDetail(id)}><Icon size={15} />{name}</button>)}</div>
      <div role="tabpanel" id="result-detail" aria-labelledby={`tab-${detail}`}>
        {detail === 'findings' && <Findings result={result} />}{detail === 'evidence' && <Evidence result={result} onLocate={onLocate} />}
        {detail === 'recovery' && <RecoveryView result={result} onLocate={onLocate} />}{detail === 'trace' && <Trace result={result} />}
      </div>
      <div className="result-footer"><Fingerprint size={12} /><span title={result.input_sha256 ?? ''}>{result.input_sha256?.slice(0, 16) ?? 'Entrada sin hash'}…</span><span>Procedencia conservada<ChevronDown size={11} /></span></div>
    </>}
  </section>
}
