export type Pipeline = 'A' | 'B' | 'C'
export type Mode = Pipeline | 'ABC'
export type ExecutionStatus = 'completed' | 'partial' | 'rejected' | 'unavailable' | 'error'
export type Risk = 'unknown' | 'benign' | 'suspicious' | 'high_risk'
export interface Span { layer_id: string; start: number; end: number; line: number; column: number; end_line: number; end_column: number }
export interface Transformation {
  transformation_id: string; technique: string; source: Span; root_source: Span;
  original_fragment: string; recovered_text: string | null; recovered_bytes_base64: string | null;
  recovery_kind: string; status: string; deterministic_verified: boolean; dependencies: string[]; warnings: string[];
  output_layer_id: string | null;
}
export interface Recovery {
  input_sha256: string | null;
  layers: { layer_id: string; source_name: string; provenance: string; text: string; depth: number; parent_transformation_id: string | null; root_source: Span | null }[];
  status: string; engine_version: string; techniques_detected: string[];
  transformations: Transformation[]; unresolved: { source: Span; reason: string }[];
  limits_hit: string[]; warnings: string[];
}
export interface RuleEvidence {
  evidence_id: string; fragment: string; source: Span; root_source: Span;
  provenance: string; transformation_ids: string[]; recovered_value: string | null;
}
export interface Deterministic {
  deobfuscation: Recovery;
  status: string; ruleset_version: string; behaviors: string[];
  findings: { finding_id: string; behavior_id: string; description: string; rule_id: string; evidence_ids: string[]; conditions: string[]; limitations: string[] }[];
  evidence: RuleEvidence[]; warnings: string[]; limits_hit: string[];
  indicators: { indicator_id: string; reason: string }[];
}
export interface ModelReport {
  behaviors: { behavior_id: string; explanation: string; confidence: string; evidence: { source_id: string; snippet: string }[] }[];
  obfuscation_techniques: string[]; recovered_content: string[]; risk_label: Risk; risk_rationale: string;
  uncertainty: { level: string; notes: string; uninterpretable_fragments: string[] };
  prompt_injection: { detected: boolean; snippets: string[]; notes: string }; limitations: string[];
}
export interface LocatedEvidence {
  behavior_id: string; source_id: string; snippet: string; start: number; end: number;
  line: number; column: number; root_source: Span | null; transformation_id: string | null;
  provenance: 'original' | 'deobfuscator_recovered'; validation: string;
}
export interface VerifierOperation {
  behavior_id: string; rule_id: string; start: number; end: number; snippet: string;
  conditions: string[]; limitations: string[];
  operands: { role: string; start: number; end: number; snippet: string }[];
}
export interface VerifierDecision {
  from: string; to: string | null; action: 'kept' | 'dropped' | 'relabelled';
  support: string; reason: string; human_validated: boolean; source_diagnostics: string[];
  citations: { source_id: string; start: number; end: number; snippet: string; line: number; column: number;
    provenance: string; root_source: Span | null; support: string; reason: string; operations: VerifierOperation[] }[];
}
export interface EvidenceCheck {
  version: string; status?: string; decisions?: VerifierDecision[];
  changes: { from: string; to: string | null; action: string }[];
  final_behavior_ids?: string[]; candidate_behavior_ids?: string[];
  risk_preserved_from_model?: Risk; limitations?: string[]; error?: string;
}
export interface Preprocessing {
  version: string;
  sources: { source_text_sha256: string; source_ids: string[]; coverage: string;
    comment_spans: [number, number][];
    diagnostics: { start: number; end: number; reason: string; fatal: boolean }[] }[];
}
export interface PipelineResult {
  schema_version: string; run_id: string; configuration: Pipeline; status: ExecutionStatus;
  input_sha256: string | null; original: string | null; started_at: string; duration_seconds: number;
  engine_versions: Record<string, string>; deobfuscation: Recovery | null; deterministic: Deterministic | null;
  llm: ModelReport | null; llm_review_status: string; evidence: LocatedEvidence[];
  risk_label: Risk; risk_rationale: string; limitations: string[];
  errors: { code: string; message: string; stage: string }[];
  operational: {
    model_report_before_evidence_check?: ModelReport;
    model_behaviors_before_evidence_check?: { behavior_id: string; evidence: { source_id: string; snippet: string }[] }[];
    evidence_check?: EvidenceCheck;
    preprocessing?: Preprocessing;
    model?: string; installed_digest?: string; expected_digest?: string; prompt_version?: string;
    prompt_sha256?: string; context_sha256?: string; request_sha256?: string;
    inference_dispatched?: boolean; truncated?: boolean; input_token_upper_bound?: number;
    request?: { options: Record<string, number>; think?: boolean; [key: string]: unknown };
    response?: { message?: { content?: string }; [key: string]: unknown };
    resources?: { minimum_available_bytes: number; minimum_commit_available_bytes: number; margin_violated: boolean };
    [key: string]: unknown;
  };
}
export interface Comparison { schema_version: string; results: PipelineResult[]; quality_metrics_computed: false }
export type AnalysisResponse = PipelineResult | Comparison
export interface Capabilities {
  provider?: string; llm_disclaimer?: string;
  max_input_bytes: number; model: string; expected_digest: string; options: Record<string, number>;
  timeout_seconds: number; minimum_margin_bytes: number; mode_descriptions: Record<Mode, string>;
}
export interface ModelStatus {
  model: string; expected_digest: string; available: boolean; ready_for_inference?: boolean;
  resource_ready?: boolean; circuit_blocked?: boolean; analysis_active?: boolean;
  version?: { version: string }; state?: { model: { digest: string }; residents: { name: string; context_length: number }[] };
  memory?: { available_bytes: number; commit_available_bytes: number };
  error?: { code: string; message: string };
}
export interface Metadata { name: string; version: string; pilot_v2: string; pending_phase4: string[]; experimental_model?: string; human_adjudications_pending?: number }
export const behaviorNames: Record<string, string> = {
  B01: 'Obtención remota', B02: 'Ejecución dinámica', B03: 'Persistencia', B04: 'Cambio de defensas',
  B05: 'Reconocimiento', B06: 'Comunicación de red', B07: 'Acceso a credenciales',
}
export const statusNames: Record<ExecutionStatus, string> = {
  completed: 'Completado', partial: 'Parcial', rejected: 'Entrada rechazada', unavailable: 'No disponible', error: 'Respuesta rechazada',
}
export const riskNames: Record<Risk, string> = { unknown: 'Desconocido', benign: 'Benigno', suspicious: 'Sospechoso', high_risk: 'Riesgo alto' }
export const levelNames: Record<string, string> = { low: 'Baja', medium: 'Media', high: 'Alta' }
export function resultsOf(response: AnalysisResponse): PipelineResult[] { return 'results' in response ? response.results : [response] }
export function labelsOf(r: PipelineResult): string[] { return r.deterministic?.behaviors ?? r.llm?.behaviors.map(b => b.behavior_id) ?? [] }
