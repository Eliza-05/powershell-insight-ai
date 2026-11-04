import { useEffect, useRef } from 'react'
import { BookOpen, ShieldCheck, X } from 'lucide-react'
import type { Metadata } from '../types/api'
import { behaviorNames } from '../types/api'
import { Notice } from './Primitives'

export function Help({ open, onClose, metadata }: { open: boolean; onClose: () => void; metadata: Metadata | null }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    if (open && !dialog?.open) dialog?.showModal()
    else if (!open && dialog?.open) dialog.close()
  }, [open])
  return <dialog ref={ref} className="help-dialog" aria-labelledby="help-title" onCancel={onClose} onClose={onClose}>
    <div className="dialog-heading"><div className="help-icon"><BookOpen size={20} /></div><button className="icon-button" aria-label="Cerrar ayuda" onClick={onClose}><X size={20} /></button></div>
    <span className="eyebrow">POWERSHELL INSIGHT AI</span><h2 id="help-title">Leer el código. Conservar el contexto.</h2>
    <p>El estudio ofrece tres perspectivas independientes. Un análisis completado indica que terminó el procesamiento; no certifica que todas sus conclusiones sean correctas.</p>
    <div className="help-modes"><div><b>A</b><h3>Determinista</h3><p>Desofusca y aplica reglas dentro de un subconjunto documentado. Funciona sin Ollama; no determina intención.</p></div><div><b>B</b><h3>LLM directo</h3><p>El modelo recibe solo el original. Sus etiquetas, explicaciones y riesgo son predicciones sin adjudicación semántica.</p></div><div><b>C</b><h3>LLM asistido</h3><p>Recibe original y recuperación verificable de 1A. No recibe las etiquetas o decisiones del detector 1B.</p></div></div>
    <Notice tone="warning"><strong>Qwen2.5-Coder 14B es experimental.</strong> Adoptado por viabilidad operativa, sin selección científica aprobada. Puede inventar operaciones o interpretar mal una cita existente. Una respuesta inválida se rechaza; una cita literal no garantiza una explicación correcta. No usar para decisiones reales de seguridad sin revisión humana.</Notice>
    <div className="help-static"><ShieldCheck size={18} /><p>Los scripts nunca se ejecutan. No se visitan sus URLs. Tu contenido permanece en memoria de la aplicación; exportar JSON es una acción explícita. Solo se guarda la preferencia de tema.</p></div>
    <details><summary>Qué significan las etiquetas B01–B07</summary><ul>{Object.entries(behaviorNames).map(([id, name]) => <li key={id}><code>{id}</code> · {name}</li>)}</ul><p>Son categorías de comportamiento, no un veredicto de maliciosidad. Una misma muestra puede tener cero, una o múltiples etiquetas.</p></details>
    <details><summary>Estado de la investigación y pendientes de Fase 4</summary><p>Modelo adoptado solo para exploración local. Piloto histórico Qwen3.5 v2: {metadata?.pilot_v2 ?? 'PENDIENTE / INCONCLUSO'}. H1/H2 no demostradas; ocho respuestas Qwen14 pendientes de revisión personal.</p><ol>{(metadata?.pending_phase4 ?? ['Evaluación independiente con casos no vistos, referencias revisadas, configuración congelada y presupuesto autorizado.']).map((s, i) => <li key={i}>{s}</li>)}</ol></details>
    <div className="help-footer"><span>Proyecto académico · MVP técnico</span><button className="button primary" onClick={onClose}>Volver al estudio</button></div>
  </dialog>
}
