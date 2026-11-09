import type { ReactNode } from 'react'
import { AlertCircle, Check, CircleDashed, ShieldQuestion } from 'lucide-react'
import type { ExecutionStatus, Risk } from '../types/api'
import { riskNames, statusNames } from '../types/api'

export function StatusBadge({ status }: { status: ExecutionStatus }) {
  const Icon = status === 'completed' ? Check : status === 'partial' ? CircleDashed : AlertCircle
  return <span className={`badge status-${status}`}><Icon size={12} />{statusNames[status]}</span>
}
export function RiskBadge({ risk }: { risk: Risk }) {
  return <span className={`badge risk-${risk}`}><ShieldQuestion size={13} />{riskNames[risk]}</span>
}
export function Code({ children, className = '' }: { children: string; className?: string }) {
  return <pre className={`code-block ${className}`}><code>{children}</code></pre>
}
/** Untranslated backend message shown as secondary technical detail, never as UI copy. */
export function TechnicalDetail({ children }: { children: string }) {
  return <p className="technical-detail"><span>Motivo técnico:</span> {children}</p>
}
export function Notice({ children, tone = 'muted' }: { children: ReactNode; tone?: 'muted' | 'warning' | 'error' }) {
  return <div className={`notice notice-${tone}`}><AlertCircle size={16} aria-hidden="true" /><div>{children}</div></div>
}
export function Loading({ mode }: { mode: string }) {
  return <div className="loading-state" role="status" aria-live="polite">
    <h3>Análisis {mode === 'ABC' ? 'A/B/C' : mode} en curso</h3>
    <p>{mode === 'A' ? 'El motor revisa el texto y sus transformaciones estáticas.' : 'Las solicitudes se procesan una a una. El modelo local puede tardar varios minutos.'}</p>
    {/* Neutral placeholders for the layout to come: no percentages, no fake stages. */}
    <div className="skeleton" aria-hidden="true">
      <div className="skeleton-row"><i className="sk-circle" /><i className="sk-line w40" /><i className="sk-pill" /></div>
      <div className="skeleton-row"><i className="sk-block" /><i className="sk-block" /><i className="sk-block" /></div>
      <i className="sk-line w100" /><i className="sk-line w85" /><i className="sk-line w60" />
    </div>
  </div>
}
