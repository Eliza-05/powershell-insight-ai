import { Activity, CircleCheck, Cpu, Database, RefreshCw, Server, ShieldAlert } from 'lucide-react'
import type { Capabilities, ModelStatus } from '../types/api'

export function SystemStatus({ status, capabilities, loading, onRefresh, apiOnline, expanded = false }: {
  status: ModelStatus | null; capabilities: Capabilities | null; loading: boolean; onRefresh: () => void; apiOnline: boolean; expanded?: boolean;
}) {
  const ready = status?.available && status.ready_for_inference && !status.analysis_active
  const state = loading ? 'Consultando estado' : status?.analysis_active ? 'Análisis en curso' : ready ? 'Modelo disponible' : status?.available && !status.resource_ready ? 'Memoria insuficiente' : status?.available ? 'Modelo en espera' : 'Ollama no disponible'
  const gib = (bytes?: number) => bytes === undefined ? '—' : `${(bytes / 1024 ** 3).toFixed(1)} GiB`
  return <details className="system-card" open={expanded || undefined}>
    <summary><span className={`dot ${ready ? 'mint' : 'amber'}`} /><div><strong>Sistema local</strong><span>{apiOnline ? state : 'API sin conexión'}</span></div><Activity size={15} /></summary>
    <div className="system-details"><div className="system-model"><Cpu size={16} /><strong>{capabilities?.model ?? status?.model ?? 'Modelo pendiente de consulta'}</strong></div>
      <span className="badge amber-badge">LLM experimental · revisión humana pendiente</span>
      <dl><div><dt><Server size={12} />API</dt><dd>{apiOnline ? 'Conectada' : 'Sin conexión'}</dd></div><div><dt>Ollama</dt><dd>{status?.version?.version ?? '—'}</dd></div><div><dt>RAM libre</dt><dd>{gib(status?.memory?.available_bytes)}</dd></div><div><dt>Compromiso libre</dt><dd>{gib(status?.memory?.commit_available_bytes)}</dd></div></dl>
      {status?.available && !status.resource_ready && <p className="system-warning"><ShieldAlert size={13} />Sin reserva suficiente para inferir. A sigue disponible.</p>}
      {status?.circuit_blocked && <p className="system-warning">Circuito bloqueado por una interrupción anterior. Revisa el servicio local.</p>}
      {status?.error && <p className="system-warning">{status.error.message}</p>}
      <details className="digest-details"><summary><Database size={12} />Digest esperado</summary><code>{capabilities?.expected_digest ?? status?.expected_digest ?? 'Consulta pendiente'}</code><p>{status?.state?.model.digest === status?.expected_digest ? 'Coincide con el modelo instalado.' : 'Se comprobará antes de inferir.'}</p></details>
      <button className="button secondary" onClick={onRefresh} disabled={loading}><RefreshCw size={13} className={loading ? 'spin' : ''} />Actualizar estado</button>
    </div>
    <div className="system-footer"><CircleCheck size={12} />Procesamiento en tu equipo</div>
  </details>
}
