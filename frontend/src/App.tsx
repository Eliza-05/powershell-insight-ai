import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowRight, BookOpen, ChevronRight, CircleHelp, GitCompareArrows, LockKeyhole, Moon, PanelLeft, ShieldCheck, Sun, Terminal, X } from 'lucide-react'
import type { AnalysisResponse, Capabilities, Metadata, Mode, ModelStatus, Span } from './types/api'
import { api, ApiFailure } from './services/api'
import { Editor, textareaOffset, utf8Bytes } from './components/Editor'
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
  const [apiOnline, setApiOnline] = useState(false)
  const editorRef = useRef<HTMLTextAreaElement>(null)
  const running = useRef(false)
  const mounted = useRef(true)
  const maxBytes = capabilities?.max_input_bytes ?? 65536
  const oversized = utf8Bytes(script) > maxBytes

  const refreshStatus = useCallback(async () => {
    setStatusLoading(true)
    try { const state = await api.modelStatus(); if (mounted.current) { setModelStatus(state); setApiOnline(true) } }
    catch (e) { if (mounted.current && !(e instanceof ApiFailure && e.code === 'status_busy')) { setModelStatus(null); setApiOnline(false) } }
    finally { if (mounted.current) setStatusLoading(false) }
  }, [])

  useEffect(() => {
    mounted.current = true
    let current = true
    void api.health().then(() => { if (current) setApiOnline(true) }).catch(() => { if (current) setApiOnline(false) })
    void api.capabilities().then(v => { if (current) setCapabilities(v) }).catch(() => {})
    void api.metadata().then(v => { if (current) setMetadata(v) }).catch(() => {})
    void refreshStatus()
    return () => { current = false; mounted.current = false }
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
    running.current = true; setBusy(true); setError(''); setActiveMode(mode)
    const submitted = script
    try {
      const value = await api.analyze(submitted, mode)
      if (mounted.current) { setResponse(value); setAnalyzedScript(submitted); setApiOnline(true) }
    } catch (e) { if (mounted.current) { setError(e instanceof ApiFailure ? e.message : 'No se pudo completar el análisis.'); if (e instanceof ApiFailure && e.code === 'connection_error') setApiOnline(false) } }
    finally { running.current = false; if (mounted.current) { setBusy(false); void refreshStatus() } }
  }

  function locate(span: Span) {
    if (script !== analyzedScript) { setError('El texto cambió. Vuelve a analizarlo antes de ubicar una evidencia.'); return }
    if (span.layer_id !== 'L0') { setError('Este fragmento pertenece a una capa recuperada. Revisa su trazabilidad en Recuperación.'); return }
    const editor = editorRef.current
    if (editor) { editor.focus(); editor.setSelectionRange(textareaOffset(analyzedScript, span.start), textareaOffset(analyzedScript, span.end)); editor.scrollTop = Math.max(0, (span.line - 3) * 24); editor.scrollIntoView?.({ behavior: 'smooth', block: 'center' }) }
  }
  function replaceScript(text: string, name: string) { setScript(text); setFilename(name); setError('') }

  return <div className="app-shell">
    <a className="skip-link" href="#workspace">Ir al espacio de análisis</a>
    <aside className="sidebar" aria-label="Navegación del estudio">
      <a className="brand" href="#workspace" aria-label="PowerShell Insight AI · inicio">
        <span className="brand-mark"><Terminal size={25} /></span>
        <span>PowerShell<strong>Insight <em>AI</em></strong></span>
      </a>
      <div className="sidebar-workspace"><span className="dot mint" />Security workspace</div>
      <div className="nav-caption">ANALIZAR</div>
      <nav>
        <button className={mode !== 'ABC' ? 'active' : ''} aria-label="Analysis studio" disabled={busy} onClick={() => { setMode('A'); editorRef.current?.focus() }}>
          <PanelLeft size={20} /><span>Analysis studio</span>
        </button>
        <button className={mode === 'ABC' ? 'active' : ''} aria-label="Comparar pipelines" disabled={busy} onClick={() => setMode('ABC')}>
          <GitCompareArrows size={20} /><span>Comparar pipelines</span>
        </button>
      </nav>
      <div className="nav-divider" />
      <div className="nav-caption">CONTEXTO</div>
      <nav><button aria-label="Guía del estudio" onClick={() => setHelpOpen(true)}><BookOpen size={20} /><span>Guía y límites</span><ArrowRight size={15} /></button></nav>
      <div className="sidebar-bottom">
        <div className="local-context"><LockKeyhole size={17} /><span>Tu equipo. Tu evidencia.<small>Procesamiento local</small></span></div>
        <SystemStatus status={modelStatus} capabilities={capabilities} loading={statusLoading} onRefresh={() => void refreshStatus()} apiOnline={apiOnline} />
        <div className="sidebar-footer"><span>v{metadata?.version ?? '0.3.0'}</span><span>LOCAL ONLY</span></div>
      </div>
    </aside>
    <div className="main-shell">
      <header className="topbar">
        <div className="breadcrumbs"><LockKeyhole size={16} /><span>Workspace local</span><ChevronRight size={15} /><strong>Analysis studio</strong></div>
        <div className="topbar-actions">
          <button id="system-toggle" className={`api-chip ${apiOnline ? 'online' : ''}`} aria-label="Ver estado del sistema" aria-expanded={systemOpen} onClick={() => setSystemOpen(v => !v)}>
            <span className={`dot ${apiOnline ? 'mint' : 'amber'}`} />{apiOnline ? 'API conectada' : 'API sin conexión'}<ChevronRight size={14} />
          </button>
          <button className="icon-button" title="Guía y límites" aria-label="Abrir ayuda contextual" onClick={() => setHelpOpen(true)}><CircleHelp size={20} /></button>
          <button className="icon-button theme-button" title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'} aria-label={theme === 'dark' ? 'Activar modo claro' : 'Activar modo oscuro'} onClick={toggle}>{theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}</button>
        </div>
        {systemOpen && <div className="system-popover" role="region" aria-label="Estado del sistema">
          <div><span>Estado del sistema</span><button className="icon-button" aria-label="Cerrar estado del sistema" onClick={() => setSystemOpen(false)}><X size={19} /></button></div>
          <SystemStatus expanded status={modelStatus} capabilities={capabilities} loading={statusLoading} onRefresh={() => void refreshStatus()} apiOnline={apiOnline} />
        </div>}
      </header>
      <main id="workspace" className="workspace">
        <div className="page-heading">
          <div><div className="eyebrow">SCRIPT INTELLIGENCE</div><h1>Analysis studio</h1><p>Del código a la evidencia, sin ejecutarlo.</p></div>
          <div className="page-context"><span><ShieldCheck size={18} />Análisis estático</span><button className="provisional-label" onClick={() => setHelpOpen(true)}><span className="dot amber" />LLM experimental<CircleHelp size={15} /></button></div>
        </div>
        <PipelineSelector mode={mode} onChange={setMode} busy={busy} canRun={!!script.trim() && !oversized} onRun={() => void analyze()} />
        {oversized && <p className="input-warning" role="alert">El texto supera el límite de {maxBytes.toLocaleString('es-CO')} bytes UTF-8.</p>}
        {error && <div className="workspace-error" role="alert"><Notice tone="error">{error}</Notice><button className="icon-button" aria-label="Cerrar error" onClick={() => setError('')}><X size={18} /></button></div>}
        <div className="workbench-grid">
          <Editor script={script} onChange={setScript} busy={busy} maxBytes={maxBytes} filename={filename} onFile={replaceScript} onError={setError} onRun={() => void analyze()} editorRef={editorRef} />
          <Results response={response} busy={busy} mode={activeMode} stale={!!response && script !== analyzedScript} onLocate={locate} />
        </div>
        <footer className="workspace-footer"><span><LockKeyhole size={14} />No ejecutamos scripts ni visitamos sus destinos.</span><button onClick={() => setHelpOpen(true)}>Cómo interpretar los resultados<ArrowRight size={15} /></button></footer>
      </main>
    </div>
    <Help open={helpOpen} onClose={() => setHelpOpen(false)} metadata={metadata} />
  </div>
}
