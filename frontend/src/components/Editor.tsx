import { useRef, useState, type RefObject } from 'react'
import { FileUp, Trash2 } from 'lucide-react'

export const DEMO_SCRIPT = "Write-Output ('studio-'+'local')\nGet-Process -Id 734201"
export function utf8Bytes(value: string) { return new TextEncoder().encode(value).length }
/** Python spans count code points. Textarea selection counts UTF-16 after newline normalization. */
export function textareaOffset(original: string, pythonOffset: number) {
  return Array.from(original).slice(0, pythonOffset).join('').replace(/\r\n?/g, '\n').length
}

export function Editor({ script, onChange, busy, maxBytes, filename, onFile, onError, onRun, editorRef }: {
  script: string; onChange: (text: string) => void; busy: boolean; maxBytes: number; filename: string;
  onFile: (text: string, name: string) => void; onError: (error: string) => void; onRun: () => void;
  editorRef: RefObject<HTMLTextAreaElement | null>;
}) {
  const fileRef = useRef<HTMLInputElement>(null)
  const gutterRef = useRef<HTMLDivElement>(null)
  const dragDepth = useRef(0)
  const [dragging, setDragging] = useState(false)
  const size = utf8Bytes(script)
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
    <div className="panel-heading"><h2>Script de entrada</h2><span className="filename" title={filename}>{filename}</span></div>
    <div className="editor-toolbar">
      <button className="button secondary" disabled={busy} onClick={() => fileRef.current?.click()}><FileUp size={16} />Cargar archivo</button>
      <button className="button ghost" disabled={busy} onClick={() => onFile(DEMO_SCRIPT, 'ejemplo_estatico.ps1')}>Usar ejemplo</button>
      <button className="icon-button" aria-label="Limpiar script" title="Limpiar script" disabled={busy || !script} onClick={() => onFile('', 'sin_titulo.ps1')}><Trash2 size={17} /></button>
      <span className="editor-drop-hint" id="source-help">o arrastra un archivo <code>.ps1</code> / <code>.txt</code></span>
    </div>
    <div className="editor-body">
      <div className="line-numbers" aria-hidden="true" ref={gutterRef}>{script ? script.split('\n').map((_, i) => <div key={i}>{i + 1}</div>) : null}</div>
      <textarea ref={editorRef} aria-label="Script PowerShell" value={script} disabled={busy}
        aria-describedby="source-help source-meta"
        placeholder="Pega aquí un script PowerShell o carga un archivo .ps1 o .txt (UTF-8)."
        spellCheck={false} autoCapitalize="off" autoCorrect="off" wrap="off"
        onScroll={e => { if (gutterRef.current) gutterRef.current.scrollTop = e.currentTarget.scrollTop }}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); onRun() } }} />
    </div>
    <div className="editor-status" id="source-meta"><span>{script ? script.split('\n').length : 0} líneas <span className="meta-separator">·</span> <span className={size > maxBytes ? 'text-error' : ''}>{size.toLocaleString('es-CO')} / {maxBytes.toLocaleString('es-CO')} B</span> <span className="meta-separator">·</span> UTF-8</span><span>Análisis estático: el script no se ejecuta</span></div>
    {dragging && <div className="drop-overlay" role="status"><FileUp size={32} /><strong>Suelta el archivo para cargarlo</strong><span>UTF-8 · un archivo a la vez · sin ejecución</span></div>}
      <input ref={fileRef} type="file" accept=".ps1,.txt,text/plain" aria-label="Seleccionar archivo PowerShell" className="sr-only" disabled={busy}
        onChange={e => { void loadFile(e.target.files?.[0]); e.target.value = '' }} />
  </section>
}
