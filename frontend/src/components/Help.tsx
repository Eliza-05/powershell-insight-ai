import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'
import type { Metadata } from '../types/api'
import { behaviorNames } from '../types/api'
import { Notice } from './Primitives'

export function Help({ open, onClose, metadata, modelName }: { open: boolean; onClose: () => void; metadata: Metadata | null; modelName?: string }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const dialog = ref.current
    if (open && !dialog?.open) dialog?.showModal()
    else if (!open && dialog?.open) dialog.close()
  }, [open])
  return <dialog ref={ref} className="help-dialog" aria-labelledby="help-title" onCancel={onClose} onClose={onClose}>
    <div className="dialog-heading"><h2 id="help-title">Guía y límites</h2><button className="icon-button" aria-label="Cerrar ayuda" onClick={onClose}><X size={20} /></button></div>
    <p>Hay tres enfoques independientes. Un análisis completado indica que terminó el procesamiento; no certifica que todas sus conclusiones sean correctas.</p>
    <dl className="help-modes">
      <div><dt><b>A</b> Determinista</dt><dd>Desofusca y aplica reglas dentro de un subconjunto documentado. Funciona sin Ollama; no determina intención.</dd></div>
      <div><dt><b>B</b> LLM directo</dt><dd>El modelo recibe solo el original. Sus etiquetas, explicaciones y riesgo son predicciones sin adjudicación semántica.</dd></div>
      <div><dt><b>C</b> LLM asistido</dt><dd>Recibe original y recuperación verificable de 1A. No recibe las etiquetas o decisiones del detector 1B.</dd></div>
    </dl>
    <Notice tone="warning"><strong>{modelName ? `${modelName} es experimental.` : 'El modelo configurado es experimental.'}</strong> Sin selección científica aprobada. Puede inventar operaciones o interpretar mal una cita existente. Una respuesta inválida se rechaza; una cita literal no garantiza una explicación correcta. No usar para decisiones reales de seguridad sin revisión humana.</Notice>
    <div className="help-static"><p>Los scripts nunca se ejecutan. No se visitan sus URLs. Tu contenido permanece en memoria de la aplicación; exportar JSON es una acción explícita. Solo se guarda la preferencia de tema.</p></div>
    <details><summary>Qué significan las etiquetas B01–B07</summary><ul>{Object.entries(behaviorNames).map(([id, name]) => <li key={id}><code>{id}</code> · {name}</li>)}</ul><p>Son categorías de comportamiento, no un veredicto de maliciosidad. Una misma muestra puede tener cero, una o múltiples etiquetas.</p></details>
    <details><summary>Estado de la investigación y pendientes de Fase 4</summary><p>El modelo configurado se utiliza solo para exploración local. Piloto histórico Qwen3.5 v2: {metadata?.pilot_v2 ?? 'PENDIENTE / INCONCLUSO'}. H1/H2 no demostradas.{metadata?.human_adjudications_pending !== undefined && ` Respuestas pendientes de revisión personal: ${metadata.human_adjudications_pending}.`}</p><ol>{(metadata?.pending_phase4 ?? ['Evaluación independiente con casos no vistos, referencias revisadas, configuración congelada y presupuesto autorizado.']).map((s, i) => <li key={i}>{s}</li>)}</ol></details>
    <div className="help-footer"><span>Proyecto académico · prototipo local</span><button className="button primary" onClick={onClose}>Volver al estudio</button></div>
  </dialog>
}
