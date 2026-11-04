import type { ReactNode } from 'react'
import { AlertCircle, Check, CircleDashed, LoaderCircle, ShieldQuestion } from 'lucide-react'
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
export function Notice({ children, tone = 'muted' }: { children: ReactNode; tone?: 'muted' | 'warning' | 'error' }) {
  return <div className={`notice notice-${tone}`}><AlertCircle size={16} aria-hidden="true" /><div>{children}</div></div>
}
export function Loading({ mode }: { mode: string }) {
  return <div className="loading-state" role="status" aria-live="polite">
    <div className="scan-visual"><div className="scan-line" /><LoaderCircle className="spin" size={28} /></div>
    <span className="eyebrow">ANÁLISIS {mode}</span><h3>Conectando las evidencias</h3>
    <p>{mode === 'A' ? 'El motor revisa el texto y sus transformaciones estáticas.' : 'Las solicitudes se procesan una a una. El modelo local puede tardar varios minutos.'}</p>
    <span className="subtle">Tu script se trata exclusivamente como texto.</span>
  </div>
}
