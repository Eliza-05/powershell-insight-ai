import schemas from './contracts.schema.json'
import type { AnalysisResponse, Capabilities, Metadata, Mode, ModelStatus, PipelineResult, Span } from '../types/api'

// Snapshot of models_json_schema(PipelineResult, ComparisonResult, ErrorResponse) from
// backend/app/schemas/pipeline.py and backend/app/api/contracts.py. No sample/model calls.
// Validate the serialized FastAPI response without projecting, defaulting or stripping it.
type Schema = {
  $ref?: string; type?: string; const?: unknown; enum?: unknown[]; anyOf?: Schema[];
  properties?: Record<string, Schema>; required?: string[]; additionalProperties?: boolean | Schema;
  items?: Schema; minItems?: number; maxItems?: number; minLength?: number; maxLength?: number;
  minimum?: number; maximum?: number;
}
const definitions: Record<string, Schema> = schemas.$defs
export function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
function requireContract(condition: unknown): asserts condition {
  if (!condition) throw new Error('Invalid API contract')
}
function matches(value: unknown, schema: Schema): boolean {
  if (schema.$ref) return matches(value, definitions[schema.$ref.split('/').at(-1)!])
  if (schema.anyOf && !schema.anyOf.some(option => matches(value, option))) return false
  if ('const' in schema && value !== schema.const) return false
  if (schema.enum && !schema.enum.includes(value)) return false
  switch (schema.type) {
    case 'null': return value === null
    case 'boolean': return typeof value === 'boolean'
    case 'string': return typeof value === 'string'
      && (schema.minLength === undefined || Array.from(value).length >= schema.minLength)
      && (schema.maxLength === undefined || Array.from(value).length <= schema.maxLength)
    case 'integer':
    case 'number': return typeof value === 'number' && Number.isFinite(value)
      && (schema.type !== 'integer' || Number.isInteger(value))
      && (schema.minimum === undefined || value >= schema.minimum)
      && (schema.maximum === undefined || value <= schema.maximum)
    case 'array': return Array.isArray(value)
      && (schema.minItems === undefined || value.length >= schema.minItems)
      && (schema.maxItems === undefined || value.length <= schema.maxItems)
      && value.every(item => !schema.items || matches(item, schema.items))
    case 'object': {
      if (!object(value)) return false
      const properties = schema.properties ?? {}
      // FastAPI serializes default/null fields too. Missing fields in closed result
      // models must be rejected before components access their arrays or nested data.
      const required = schema.additionalProperties === false ? Object.keys(properties) : schema.required ?? []
      return required.every(key => Object.hasOwn(value, key)) && Object.entries(value).every(([key, item]) => {
        if (Object.hasOwn(properties, key)) return matches(item, properties[key])
        return schema.additionalProperties !== false
          && (typeof schema.additionalProperties !== 'object' || matches(item, schema.additionalProperties))
      })
    }
    default: return true // unconstrained JSON values in the backend's open dictionaries
  }
}
function serialized(value: unknown, name: string) { requireContract(matches(value, definitions[name])) }
function same(a: unknown, b: unknown): boolean {
  if (a === b) return true
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => same(v, b[i]))
  return object(a) && object(b) && Object.keys(a).length === Object.keys(b).length
    && Object.keys(a).every(key => Object.hasOwn(b, key) && same(a[key], b[key]))
}
function position(text: string, start: number) {
  const before = Array.from(text).slice(0, start)
  return { line: before.filter(c => c === '\n').length + 1, column: start - before.lastIndexOf('\n') }
}
function checkSpan(span: Span, text: string) {
  const start = position(text, span.start), end = position(text, span.end)
  requireContract(span.end >= span.start && span.end <= Array.from(text).length
    && span.line === start.line && span.column === start.column
    && span.end_line === end.line && span.end_column === end.column)
}
const slice = (text: string, start: number, end: number) => Array.from(text).slice(start, end).join('')
async function digest(text: string) {
  const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join('')
}

async function checkResult(result: PipelineResult, script: string) {
  const success = result.status === 'completed' || result.status === 'partial'
  const failed = !success
  requireContract(result.original === null || result.original === script)
  if (result.original !== null) requireContract(result.input_sha256 === await digest(result.original))
  requireContract(!success || result.original !== null)
  requireContract(!failed || (result.errors.length > 0 && result.llm === null))
  requireContract(result.llm !== null || (result.evidence.length === 0 && result.risk_label === 'unknown'))
  if (result.configuration === 'A') {
    requireContract(result.llm === null && result.evidence.length === 0 && result.risk_label === 'unknown')
    requireContract(!success || result.deterministic !== null)
  } else {
    requireContract(result.deterministic === null && (!success || result.llm !== null))
    if (result.configuration === 'B') requireContract(result.deobfuscation === null)
  }
  const recovery = result.deobfuscation
  if (recovery) {
    requireContract(recovery.input_sha256 === result.input_sha256)
    const layers = new Map(recovery.layers.map(layer => [layer.layer_id, layer]))
    requireContract(layers.size === recovery.layers.length)
    if (recovery.status !== 'rejected') requireContract(recovery.layers[0]?.layer_id === 'L0' && layers.get('L0')?.text === result.original)
    const steps = new Map<string, typeof recovery.transformations[number]>()
    for (const step of recovery.transformations) {
      const source = layers.get(step.source.layer_id)
      requireContract(source && step.root_source.layer_id === 'L0' && layers.has('L0'))
      checkSpan(step.source, source.text); checkSpan(step.root_source, layers.get('L0')!.text)
      requireContract(step.original_fragment === slice(source.text, step.source.start, step.source.end))
      requireContract(same(step.root_source, source.root_source ?? step.source))
      requireContract(!steps.has(step.transformation_id) && step.dependencies.every(id => steps.has(id)))
      requireContract(step.recovered_text === null || step.recovered_bytes_base64 === null)
      if (step.status === 'success') requireContract(step.deterministic_verified && step.recovered_text !== null)
      if (step.status === 'failed' || step.status === 'unsupported') requireContract(!step.deterministic_verified && step.recovered_text === null && step.recovered_bytes_base64 === null)
      if (step.status === 'partial') requireContract(step.deterministic_verified && step.recovery_kind === 'bytes' && step.recovered_bytes_base64 !== null)
      if (step.output_layer_id !== null) {
        const child = layers.get(step.output_layer_id)
        requireContract(child && child.parent_transformation_id === step.transformation_id && child.text === step.recovered_text && child.depth === source.depth + 1)
      }
      steps.set(step.transformation_id, step)
    }
    for (const layer of recovery.layers.slice(1)) {
      const parent = steps.get(layer.parent_transformation_id ?? '')
      requireContract(parent && parent.output_layer_id === layer.layer_id && same(parent.root_source, layer.root_source) && layer.provenance === 'deobfuscator_recovered')
    }
    for (const item of recovery.unresolved) {
      const layer = layers.get(item.source.layer_id); requireContract(layer); checkSpan(item.source, layer.text)
    }
  }
  if (result.deterministic) {
    requireContract(same(result.deterministic.deobfuscation, recovery))
    const d = result.deterministic
    requireContract(same(d.behaviors, [...new Set(d.findings.map(f => f.behavior_id))].sort()))
    const evidence = new Map(d.evidence.map(e => [e.evidence_id, e]))
    requireContract(evidence.size === d.evidence.length && new Set(d.findings.map(f => f.finding_id)).size === d.findings.length)
    for (const finding of d.findings) requireContract(finding.evidence_ids.every(id => evidence.has(id)))
    for (const item of d.evidence) {
      const layer = recovery?.layers.find(layer => layer.layer_id === item.source.layer_id)
      requireContract(layer && recovery); checkSpan(item.source, layer.text)
      const original = recovery.layers.find(layer => layer.layer_id === 'L0'); requireContract(original)
      checkSpan(item.root_source, original.text); requireContract(item.root_source.layer_id === 'L0')
      requireContract(item.fragment === slice(layer.text, item.source.start, item.source.end))
      requireContract(item.transformation_ids.every(id => recovery.transformations.some(t => t.transformation_id === id && t.deterministic_verified)))
      requireContract(item.provenance === (item.recovered_value !== null || layer.depth > 0 ? 'deobfuscator_recovered' : layer.provenance))
    }
  }
  if (result.llm) {
    const llm = result.llm
    requireContract(llm.risk_label === result.risk_label && llm.risk_rationale === result.risk_rationale)
    requireContract(new Set(llm.behaviors.map(f => f.behavior_id)).size === llm.behaviors.length)
    requireContract(new Set(llm.obfuscation_techniques).size === llm.obfuscation_techniques.length)
    requireContract(llm.risk_label !== 'high_risk' || llm.behaviors.length >= 2)
    requireContract(llm.risk_label !== 'benign' || (llm.uncertainty.level === 'low' && !llm.uncertainty.uninterpretable_fragments.length))
    requireContract(llm.prompt_injection.detected === !!llm.prompt_injection.snippets.length)
    requireContract(same(llm.behaviors.flatMap(f => f.evidence.map(e => [f.behavior_id, e.source_id, e.snippet])), result.evidence.map(e => [e.behavior_id, e.source_id, e.snippet])))
    for (const e of result.evidence) {
      const step = recovery?.transformations.find(t => t.transformation_id === e.source_id)
      let text: string | null
      if (e.source_id === 'original') {
        text = result.original
        requireContract(e.provenance === 'original' && e.transformation_id === null && e.root_source?.layer_id === 'L0' && e.root_source.start === e.start && e.root_source.end === e.end)
      } else {
        requireContract(step?.deterministic_verified && step.status === 'success')
        text = step.recovered_text
        requireContract(e.provenance === 'deobfuscator_recovered' && e.transformation_id === step.transformation_id && same(e.root_source, step.root_source))
      }
      requireContract(text !== null && e.end === e.start + Array.from(e.snippet).length && slice(text, e.start, e.end) === e.snippet)
      const at = position(text, e.start); requireContract(e.line === at.line && e.column === at.column)
    }
  }
  // Open operational dictionaries are retained, but fields used as UI text must be safe.
  for (const key of ['model', 'installed_digest', 'expected_digest', 'prompt_version', 'prompt_sha256', 'context_sha256']) {
    requireContract(result.operational[key] === undefined || typeof result.operational[key] === 'string')
  }
}

export async function analysisResponse(value: unknown, mode: Mode, script: string): Promise<AnalysisResponse> {
  serialized(value, mode === 'ABC' ? 'ComparisonResult' : 'PipelineResult')
  // The schema has checked every nested field before this type refinement.
  const checked = value as AnalysisResponse
  const results = 'results' in checked ? checked.results : [checked]
  requireContract(results.every((r, i) => r.configuration === (mode === 'ABC' ? ['A', 'B', 'C'][i] : mode)))
  requireContract(new Set(results.map(r => r.run_id)).size === results.length && new Set(results.map(r => r.input_sha256)).size === 1)
  await Promise.all(results.map(result => checkResult(result, script)))
  return checked // same object, including allowed additional operational data
}

function fields(value: unknown, required: Record<string, (v: unknown) => boolean>) {
  requireContract(object(value) && Object.entries(required).every(([key, test]) => test(value[key])))
}
const string = (v: unknown) => typeof v === 'string' && v.trim().length > 0
const number = (v: unknown) => typeof v === 'number' && Number.isFinite(v) && v >= 0
const strings = (v: unknown) => Array.isArray(v) && v.every(x => typeof x === 'string')
export function healthResponse(value: unknown): { status: string; version: string } {
  fields(value, { status: v => v === 'ok', version: string })
  return value as { status: string; version: string }
}
export function capabilitiesResponse(value: unknown): Capabilities {
  fields(value, { model: string, expected_digest: string, max_input_bytes: v => number(v) && Number.isInteger(v) && Number(v) > 0,
    options: v => object(v) && Object.values(v).every(n => typeof n === 'number' && Number.isFinite(n)), timeout_seconds: number, minimum_margin_bytes: number,
    mode_descriptions: v => object(v) && ['A', 'B', 'C', 'ABC'].every(key => string(v[key])) })
  return value as Capabilities
}
export function metadataResponse(value: unknown): Metadata {
  fields(value, { name: string, version: string, pilot_v2: string, pending_phase4: strings })
  requireContract(object(value))
  requireContract(value.experimental_model === undefined || string(value.experimental_model))
  requireContract(value.human_adjudications_pending === undefined || (number(value.human_adjudications_pending) && Number.isInteger(value.human_adjudications_pending)))
  return value as unknown as Metadata
}
export function modelStatusResponse(value: unknown): ModelStatus {
  fields(value, { model: string, expected_digest: string, available: v => typeof v === 'boolean' })
  requireContract(object(value))
  for (const key of ['ready_for_inference', 'resource_ready', 'analysis_active', 'circuit_blocked']) requireContract(value[key] === undefined || typeof value[key] === 'boolean')
  if (value.version !== undefined) fields(value.version, { version: string })
  if (value.memory !== undefined) fields(value.memory, { available_bytes: number, commit_available_bytes: number })
  if (value.error !== undefined) fields(value.error, { code: string, message: string })
  if (value.state !== undefined) fields(value.state, { model: v => object(v) && string(v.digest), residents: v => Array.isArray(v) && v.every(item => object(item) && string(item.name) && number(item.context_length)) })
  return value as unknown as ModelStatus
}
export function httpError(value: unknown): { code: string; message: string } | null {
  return matches(value, definitions.ErrorResponse) ? (value as { error: { code: string; message: string } }).error : null
}
