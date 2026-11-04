import { useRef, useState, type RefObject } from 'react'
import { FileCode2, FileUp, LockKeyhole, Trash2 } from 'lucide-react'

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
    <div className="panel-heading"><div><FileCode2 size={21} /><h2>Script de entrada</h2></div>
      <button className="button secondary" disabled={busy} onClick={() => fileRef.current?.click()}><FileUp size={18} />Cargar archivo</button>
    </div>
    <div className="editor-toolbar"><span><span className="file-dot" /><span className="filename" title={filename}>{filename}</span></span>
      <div><button className="button ghost" disabled={busy} onClick={() => onFile(DEMO_SCRIPT, 'ejemplo_estatico.ps1')}>Usar ejemplo</button>
      <button className="icon-button" aria-label="Limpiar script" title="Limpiar script" disabled={busy || !script} onClick={() => onFile('', 'sin_titulo.ps1')}><Trash2 size={18} /></button></div>
    </div>
    <div className="editor-body">
      <div className="line-numbers" aria-hidden="true" ref={gutterRef}>{Array.from({ length: Math.max(script.split('\n').length, 12) }, (_, i) => <div key={i}>{i + 1}</div>)}</div>
      <textarea ref={editorRef} aria-label="Script PowerShell" value={script} disabled={busy}
        aria-describedby="source-help source-meta"
        placeholder={'# Pega aquí tu script PowerShell.\n# También puedes cargar un archivo.\n\n# Solo lectura estática. Nunca se ejecuta.'}
        spellCheck={false} autoCapitalize="off" autoCorrect="off" wrap="off"
        onScroll={e => { if (gutterRef.current) gutterRef.current.scrollTop = e.currentTarget.scrollTop }}
        onChange={e => onChange(e.target.value)}
        onKeyDown={e => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); onRun() } }} />
    </div>
    <div className="editor-status" id="source-meta"><span>PowerShell <span className="meta-separator">/</span> UTF-8 <span className="meta-separator">/</span> {script ? script.split('\n').length : 0} líneas</span><span className={size > maxBytes ? 'text-error' : ''}>{size.toLocaleString('es-CO')} / {maxBytes.toLocaleString('es-CO')} B</span></div>
    <div className="editor-drop-hint" id="source-help"><FileUp size={17} /><span>Arrastra un archivo <code>.ps1</code> o <code>.txt</code> a este panel.</span></div>
    <div className="editor-security"><LockKeyhole size={14} /><span>Tu código se analiza como texto no confiable.</span></div>
    {dragging && <div className="drop-overlay" role="status"><FileUp size={32} /><strong>Suelta el archivo para cargarlo</strong><span>UTF-8 · un archivo a la vez · sin ejecución</span></div>}
      <input ref={fileRef} type="file" accept=".ps1,.txt,text/plain" aria-label="Seleccionar archivo PowerShell" className="sr-only" disabled={busy}
        onChange={e => { void loadFile(e.target.files?.[0]); e.target.value = '' }} />
  </section>
}
