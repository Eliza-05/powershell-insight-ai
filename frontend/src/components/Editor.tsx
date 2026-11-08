import { useEffect, useLayoutEffect, useRef, useState, type RefObject } from 'react'

/** Lines located with "Ver origen" (1-based, inclusive). `key` restarts the flash for each new location. */
export type MarkedLines = { line: number; endLine: number; key: number }
// Must match the CSS line-height of the gutter and textarea, and the 24 px step used by App.locate().
const LINE_HEIGHT = 24
const PADDING_TOP = 14
import { FileCode2, FileUp, Trash2 } from 'lucide-react'

export const DEMO_SCRIPT = "Write-Output ('studio-'+'local')\nGet-Process -Id 734201"
export function utf8Bytes(value: string) { return new TextEncoder().encode(value).length }
/** Python spans count code points. Textarea selection counts UTF-16 after newline normalization. */
export function textareaOffset(original: string, pythonOffset: number) {
  return Array.from(original).slice(0, pythonOffset).join('').replace(/\r\n?/g, '\n').length
}

export function Editor({ script, onChange, busy, maxBytes, filename, onFile, onError, onRun, editorRef, marked = null }: {
  script: string; onChange: (text: string) => void; busy: boolean; maxBytes: number; filename: string;
  onFile: (text: string, name: string) => void; onError: (error: string) => void; onRun: () => void;
  editorRef: RefObject<HTMLTextAreaElement | null>; marked?: MarkedLines | null;
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const gutterRef = useRef<HTMLDivElement>(null)
  const markRef = useRef<HTMLDivElement>(null)
  // Keep the marked band aligned with the textarea's scroll position (same approach as the gutter).
  function placeMark(scrollTop: number) {
    if (markRef.current && marked) markRef.current.style.transform = `translateY(${PADDING_TOP + (marked.line - 1) * LINE_HEIGHT - scrollTop}px)`
  }
  const bodyRef = useRef<HTMLDivElement>(null)
  // Long lines scroll horizontally inside the terminal; a soft right-edge fade signals hidden content.
  function updateOverflowHint() {
    const area = editorRef.current, body = bodyRef.current
    if (!area || !body) return
    const hidden = area.scrollWidth - area.clientWidth - area.scrollLeft > 1
    body.toggleAttribute('data-more-right', hidden)
    body.style.setProperty('--scrollbar-right', `${area.offsetWidth - area.clientWidth}px`)
    body.style.setProperty('--scrollbar-bottom', `${area.offsetHeight - area.clientHeight}px`)
  }
  useLayoutEffect(() => { placeMark(editorRef.current?.scrollTop ?? 0); updateOverflowHint() })
  useEffect(() => {
    window.addEventListener('resize', updateOverflowHint)
    return () => window.removeEventListener('resize', updateOverflowHint)
  }, []) // the handler only reads refs, so subscribing once is enough
  const dragDepth = useRef(0)
  const [dragging, setDragging] = useState(false)
  const size = utf8Bytes(script)
  const lineCount = script ? script.split('\n').length : 0
  async function loadFile(file?: File) {
    if (!file) return
    if (!/\.(ps1|txt)$/i.test(file.name)) { onError('Selecciona un archivo .ps1 o .txt.'); return }
    if (file.size > maxBytes) { onError(`El archivo supera el límite de ${(maxBytes / 1024).toFixed(0)} KiB.`); return }
    try {
      const text = new TextDecoder('utf-8', { fatal: true }).decode(await file.arrayBuffer()).replace(/^\uFEFF/, '')
      onFile(text, file.name)
    } catch { onError('No se pudo leer el archivo como texto UTF-8.'); }
  }
  return <section className={`editor-panel panel ${dragging ? 'is-dragging' : ''}`} aria-label="Entrada del análisis"
    onDragEnter={e => { e.preventDefault(); if (!busy && e.dataTransfer.types.includes('Files')) { dragDepth.current++; setDragging(true) } }}
    onDragOver={e => { e.preventDefault(); if (!busy) e.dataTransfer.dropEffect = 'copy' }}
    onDragLeave={e => { e.preventDefault(); dragDepth.current = Math.max(0, dragDepth.current - 1); if (!dragDepth.current) setDragging(false) }}
    onDrop={e => {
      e.preventDefault(); dragDepth.current = 0; setDragging(false)
      if (busy || !e.dataTransfer.files.length) return
      if (e.dataTransfer.files.length !== 1) { onError('Carga un solo archivo .ps1 o .txt a la vez.'); return }
      void loadFile(e.dataTransfer.files[0])
    }}>
    <div className="panel-heading"><h2><span className="heading-icon" aria-hidden="true"><FileCode2 size={16} /></span>Script de entrada</h2></div>
    <div className="editor-toolbar">
      <button className="button secondary" disabled={busy} onClick={() => fileRef.current?.click()}><FileUp size={16} />Cargar archivo</button>
      <button className="button ghost" disabled={busy} onClick={() => onFile(DEMO_SCRIPT, 'ejemplo_estatico.ps1')}>Usar ejemplo</button>
      <button className="icon-button" aria-label="Limpiar script" title="Limpiar script" disabled={busy || !script} onClick={() => onFile('', 'sin_titulo.ps1')}><Trash2 size={17} /></button>
      <span className="editor-drop-hint" id="source-help">o arrastra un archivo <code>.ps1</code> / <code>.txt</code></span>
    </div>
    <div className="terminal-window">
    {/* Decorative window chrome only: plain text title, inert circles, no prompt and no execution affordance. */}
    <div className="terminal-titlebar">
      <span className="terminal-title" title={filename}><span aria-hidden="true">insight@local: ~/</span><span className="filename">{filename}</span></span>
      <span className="terminal-controls" aria-hidden="true"><i /><i /><i /></span>
    </div>
    <div className="editor-body" ref={bodyRef}>
      <div className="line-numbers" aria-hidden="true" ref={gutterRef}>{script ? script.split('\n').map((_, i) => <div key={i} className={marked && i + 1 >= marked.line && i + 1 <= marked.endLine ? 'is-marked' : undefined}>{i + 1}</div>) : null}</div>
      {marked && <div key={marked.key} ref={markRef} className="line-mark" aria-hidden="true" style={{ height: (marked.endLine - marked.line + 1) * LINE_HEIGHT }} />}
      <textarea ref={editorRef} aria-label="Script PowerShell" value={script} disabled={busy}
        aria-describedby="source-help source-meta"
        placeholder="Pega aquí un script PowerShell o carga un archivo .ps1 o .txt (UTF-8)."
        spellCheck={false} autoCapitalize="off" autoCorrect="off" wrap="off"
        onScroll={e => { if (gutterRef.current) gutterRef.current.scrollTop = e.currentTarget.scrollTop; placeMark(e.currentTarget.scrollTop); updateOverflowHint() }}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); onRun() } }} />
    </div>
    <div className="editor-status" id="source-meta"><span>{lineCount} {lineCount === 1 ? 'línea' : 'líneas'} <span className="meta-separator">·</span> <span className={size > maxBytes ? 'text-error' : ''}>{size.toLocaleString('es-CO')} / {maxBytes.toLocaleString('es-CO')} B</span> <span className="meta-separator">·</span> UTF-8</span><span>Análisis estático: el script no se ejecuta</span></div>
    </div>
    {dragging && <div className="drop-overlay" role="status"><FileUp size={32} /><strong>Suelta el archivo para cargarlo</strong><span>UTF-8 · un archivo a la vez · sin ejecución</span></div>}
      <input ref={fileRef} type="file" accept=".ps1,.txt,text/plain" aria-label="Seleccionar archivo PowerShell" className="sr-only" disabled={busy}
        onChange={e => { void loadFile(e.target.files?.[0]); e.target.value = '' }} />
  </section>
}
