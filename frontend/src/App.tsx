import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, CircleHelp, Moon, Sun, Terminal, X } from 'lucide-react'
import type { AnalysisResponse, Capabilities, Metadata, Mode, ModelStatus, Span } from './types/api'
import { api, ApiFailure } from './services/api'
import { Editor, textareaOffset, utf8Bytes, type MarkedLines } from './components/Editor'
import { Help } from './components/Help'
import { Notice } from './components/Primitives'
import { Results } from './components/Results'
import { PipelineSelector } from './components/PipelineSelector'
import { SystemStatus } from './components/SystemStatus'
import { useTheme } from './hooks/useTheme'

export default function App() {
  const { theme, toggle } = useTheme()
  const [script, setScript] = useState('')
  const [filename, setFilename] = useState('sin_titulo.ps1')
  const [mode, setMode] = useState<Mode>('A')
  const [response, setResponse] = useState<AnalysisResponse | null>(null)
  const [analyzedScript, setAnalyzedScript] = useState('')
  const [busy, setBusy] = useState(false)
  const [activeMode, setActiveMode] = useState<Mode>('A')
  const [error, setError] = useState('')
  const [helpOpen, setHelpOpen] = useState(false)
  const [systemOpen, setSystemOpen] = useState(false)
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null)
  const [metadata, setMetadata] = useState<Metadata | null>(null)
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [providerError, setProviderError] = useState('')
  const [apiOnline, setApiOnline] = useState(false)
  const [marked, setMarked] = useState<MarkedLines | null>(null) // lines last located with "Ver origen" (display only)
  const editorRef = useRef<HTMLTextAreaElement>(null)
  const running = useRef(false)
  const mounted = useRef(true)
  const inputRevision = useRef(0)
  const statusRevision = useRef(0)
  const maxBytes = capabilities?.max_input_bytes ?? 65536
  const oversized = utf8Bytes(script) > maxBytes
  // Display-only summary of the provider status already fetched; it never gates or triggers analysis.
  const ollamaReady = !!(modelStatus?.available && modelStatus.ready_for_inference)
  const modelName = capabilities?.model ?? metadata?.experimental_model
  const ollamaLabel = providerError ? 'estado del proveedor no disponible'
    : !modelStatus ? (statusLoading ? 'consultando Ollama' : 'Ollama sin datos')
    : ollamaReady ? 'Ollama disponible'
    : modelStatus.available && modelStatus.resource_ready === false ? 'Ollama sin memoria suficiente'
    : modelStatus.available ? 'Ollama no listo' : 'Ollama no disponible'

  const refreshStatus = useCallback(async () => {
    const revision = ++statusRevision.current
    const current = () => mounted.current && revision === statusRevision.current
    setStatusLoading(true)
    await Promise.allSettled([
      api.health().then(() => { if (current()) setApiOnline(true) }, () => { if (current()) setApiOnline(false) }),
      api.modelStatus().then(state => {
        if (current()) { setModelStatus(state); setProviderError('') }
      }, e => {
        if (current()) {
          setModelStatus(null)
          setProviderError(e instanceof ApiFailure && e.code === 'status_busy'
            ? 'Ya hay una consulta del proveedor en curso. Actualiza el estado cuando termine.'
            : 'No se pudo consultar el estado del proveedor. A funciona sin Ollama.')
        }
      }),
    ])
    if (current()) setStatusLoading(false)
  }, [])

  useEffect(() => {
    mounted.current = true
    let current = true
    void api.capabilities().then(v => { if (current) setCapabilities(v) }).catch(() => {})
    void api.metadata().then(v => { if (current) setMetadata(v) }).catch(() => {})
    void refreshStatus()
    return () => { current = false; mounted.current = false; ++statusRevision.current; ++inputRevision.current }
  }, [refreshStatus])

  useEffect(() => {
    if (!systemOpen) return
    function dismiss(event: KeyboardEvent) {
      if (event.key === 'Escape') { setSystemOpen(false); document.getElementById('system-toggle')?.focus() }
    }
    document.addEventListener('keydown', dismiss)
    return () => document.removeEventListener('keydown', dismiss)
  }, [systemOpen])

  async function analyze() {
    if (running.current || !script.trim() || oversized) return
    ++inputRevision.current
    running.current = true; setBusy(true); setError(''); setActiveMode(mode)
    const submitted = script
    try {
      const value = await api.analyze(submitted, mode)
      if (mounted.current) { setResponse(value); setAnalyzedScript(submitted) }
    } catch (e) { if (mounted.current) setError(e instanceof ApiFailure ? e.message : 'No se pudo completar el análisis.') }
    finally { running.current = false; if (mounted.current) { setBusy(false); void refreshStatus() } }
  }

  function locate(span: Span) {
    if (script !== analyzedScript) { setError('El texto cambió. Vuelve a analizarlo antes de ubicar una evidencia.'); return }
    if (span.layer_id !== 'L0') { setError('Este fragmento pertenece a una capa recuperada. Revisa su trazabilidad en Recuperación.'); return }
    const editor = editorRef.current
    if (editor) { editor.focus(); editor.setSelectionRange(textareaOffset(analyzedScript, span.start), textareaOffset(analyzedScript, span.end)); editor.scrollTop = Math.max(0, (span.line - 3) * 24); editor.scrollIntoView?.({ behavior: 'smooth', block: 'center' }); setMarked({ line: span.line, endLine: span.end_line, key: Date.now() }) }
  }
  function editScript(text: string) { ++inputRevision.current; setScript(text) }
  function replaceScript(text: string, name: string) { ++inputRevision.current; setScript(text); setFilename(name); setError('') }

  return <div className="app-shell">
    <a className="skip-link" href="#workspace">Ir al espacio de análisis</a>
    <header className="topbar">
      <div className="brand">
        <span className="brand-mark" aria-hidden="true"><Terminal size={16} /></span>
        <span className="brand-name">PowerShell Insight AI</span>
        <span className="brand-version">v{metadata?.version ?? '0.3.0'}</span>
      </div>
      <div className="topbar-actions">
        <button id="system-toggle" className={`api-chip ${apiOnline ? 'online' : ''}`} aria-label="Ver estado del sistema" aria-expanded={systemOpen} onClick={() => setSystemOpen(v => !v)}>
          <span className={`dot ${apiOnline && ollamaReady ? 'mint' : 'amber'}`} />{apiOnline ? 'API conectada' : 'API sin conexión'}{apiOnline && <span className="chip-detail"> · {ollamaLabel}</span>}<ChevronDown size={14} />
        </button>
        <button className="icon-button" title="Guía y límites" aria-label="Abrir ayuda contextual" onClick={() => setHelpOpen(true)}><CircleHelp size={19} /></button>
        <button className="icon-button" title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'} aria-label={theme === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'} onClick={toggle}>{theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}</button>
      </div>
      {systemOpen && <div className="system-popover" role="region" aria-label="Estado del sistema">
        <div><span>Estado del sistema</span><button className="icon-button" aria-label="Cerrar estado del sistema" onClick={() => { setSystemOpen(false); document.getElementById('system-toggle')?.focus() }}><X size={19} /></button></div>
        <SystemStatus expanded status={modelStatus} capabilities={capabilities} loading={statusLoading} onRefresh={() => void refreshStatus()} apiOnline={apiOnline} providerError={providerError} />
      </div>}
    </header>
    <main id="workspace" className="workspace">
      <h1 className="page-title">Análisis de script</h1>
      <PipelineSelector mode={mode} onChange={setMode} busy={busy} canRun={!!script.trim() && !oversized} onRun={() => void analyze()} modelName={modelName}
        warning={mode !== 'A' && apiOnline && !ollamaReady ? providerError || `${mode === 'ABC' ? 'Comparar necesita' : `${mode} necesita`} Ollama y ahora no está listo. A funciona sin Ollama.` : undefined} />
      {oversized && <p className="input-warning" role="alert">El texto supera el límite de {maxBytes.toLocaleString('es-CO')} bytes UTF-8.</p>}
      {error && <div className="workspace-error" role="alert"><Notice tone="error">{error}</Notice><button className="icon-button" aria-label="Cerrar error" onClick={() => setError('')}><X size={18} /></button></div>}
      <div className="workbench-grid">
        <Editor script={script} onChange={editScript} busy={busy} maxBytes={maxBytes} filename={filename} onFile={replaceScript} onError={setError} onRun={() => void analyze()} editorRef={editorRef} inputRevision={inputRevision} marked={response && script === analyzedScript ? marked : null} />
        <Results response={response} busy={busy} mode={activeMode} stale={!!response && script !== analyzedScript} onLocate={locate} />
      </div>
    </main>
    <Help open={helpOpen} onClose={() => setHelpOpen(false)} metadata={metadata} modelName={modelName} />
  </div>
}
