// Run from the repository root: node frontend/browser/verify.mjs [--baseline]
// Uses installed Chrome, no extra dependencies, an isolated TEMP profile and TEMP artifacts.
import assert from 'node:assert/strict'
import { readFile, writeFile, stat, readdir } from 'node:fs/promises'
import { join } from 'node:path'
import { launchChrome, delay } from './chrome.mjs'

const base = process.env.PSI_TEST_URL ?? 'http://127.0.0.1:5173'
assert(['127.0.0.1', 'localhost'].includes(new URL(base).hostname), 'Browser tests only target loopback')
const baseline = process.argv.includes('--baseline')
const interactionOnly = process.argv.includes('--interaction')
const layoutOnly = process.argv.includes('--layout-only')
const viewportArgument = process.argv.find(arg => /^--viewport=\d+x\d+$/.test(arg))
const zoom = process.argv.includes('--zoom200') ? 2 : 1
const fixtures = JSON.parse(await readFile(new URL('../src/test/fixtures/comparison.json', import.meta.url), 'utf8'))
const chrome = await launchChrome({ zoom })
console.log(`Artifacts: ${chrome.output}`)
const report = { baseline, browser: await chrome.send('Browser.getVersion'), cases: [], downloads: [], keyboard: [], requests: [], errors: [], failures: [], externalRequests: [] }
let stage = 'startup', comparisonMode = 'completed'
let lastA = null
const aRequests = new Set()
const downloads = []
chrome.on('Browser.downloadWillBegin', event => downloads.push({ ...event, completed: false }))
chrome.on('Browser.downloadProgress', event => { const item = downloads.find(d => d.guid === event.guid); if (item && event.state === 'completed') item.completed = true })
chrome.on('Runtime.exceptionThrown', event => report.errors.push({ stage, kind: 'exception', details: event.exceptionDetails }))
chrome.on('Runtime.consoleAPICalled', event => { if (['error', 'warning'].includes(event.type)) report.errors.push({ stage, kind: event.type, values: event.args.map(a => a.value ?? a.description) }) })
chrome.on('Log.entryAdded', event => { if (event.entry.level === 'error') report.errors.push({ stage, kind: 'log', entry: event.entry }) })
chrome.on('Network.requestWillBeSent', event => report.requests.push({ stage, method: event.request.method, url: event.request.url, initiator: event.initiator.type }))
chrome.on('Network.responseReceived', event => { if (new URL(event.response.url).pathname === '/api/analyze/A') aRequests.add(event.requestId) })
chrome.on('Network.loadingFinished', event => {
  if (aRequests.delete(event.requestId)) void chrome.page('Network.getResponseBody', { requestId: event.requestId }).then(body => { lastA = JSON.parse(body.body) }).catch(error => report.failures.push({ stage, message: `Could not capture A response: ${error}` }))
})
chrome.on('Fetch.requestPaused', event => {
  const handle = async () => {
    const url = new URL(event.request.url)
    const isLocal = url.origin === new URL(base).origin
    if (!isLocal && !['data:', 'blob:'].includes(url.protocol)) {
      report.externalRequests.push({ stage, url: event.request.url })
      return chrome.page('Fetch.failRequest', { requestId: event.requestId, errorReason: 'BlockedByClient' })
    }
    if (isLocal && /^\/api\/(compare|analyze\/[BC])$/.test(url.pathname)) {
      const body = JSON.parse(event.request.postData ?? '{}')
      assert.equal(body.script, fixtures.results[0].original, 'Synthetic LLM fixture must match submitted original')
      const value = structuredClone(fixtures)
      if (comparisonMode === 'unavailable') for (const result of value.results.slice(1)) Object.assign(result, {
        status: 'unavailable', llm: null, evidence: [], risk_label: 'unknown',
        errors: [{ code: 'ollama_unavailable', message: 'SIMULATED offline browser fixture', stage: 'provider' }],
      })
      if (comparisonMode === 'partial') {
        for (const result of value.results) result.run_id += '-partial-simulated'
        Object.assign(value.results[1], { status:'unavailable',llm:null,evidence:[],risk_label:'unknown',errors:[{code:'model_missing',message:'SIMULATED missing model',stage:'provider'}] })
        const c=value.results[2];c.status='partial';c.risk_label='unknown';c.llm.risk_label='unknown'
        Object.assign(c.llm.uncertainty,{level:'high',notes:'SIMULATED partial interpretation',uninterpretable_fragments:['SIMULATED unresolved fragment']})
        c.llm.recovered_content=['SIMULATED model reconstruction, not deterministic evidence']
      }
      const data = url.pathname === '/api/compare' ? value : value.results.find(r => url.pathname.endsWith(`/${r.configuration}`))
      return chrome.page('Fetch.fulfillRequest', { requestId: event.requestId, responseCode: 200,
        responseHeaders: [{ name: 'Content-Type', value: 'application/json; charset=utf-8' }], body: Buffer.from(JSON.stringify(data)).toString('base64') })
    }
    return chrome.page('Fetch.continueRequest', { requestId: event.requestId })
  }
  handle().catch(error => { report.failures.push({ stage, message: String(error) }); void chrome.page('Fetch.failRequest', { requestId: event.requestId, errorReason: 'BlockedByClient' }) })
})

const metrics = `(() => {
  const rect = selector => { const el=document.querySelector(selector);if(!el)return null;const r=el.getBoundingClientRect();const s=getComputedStyle(el);return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom,scrollHeight:el.scrollHeight,clientHeight:el.clientHeight,flexShrink:s.flexShrink,overflow:s.overflow}};
  const panel=rect('.editor-panel'),terminal=rect('.terminal-window'),footer=rect('.editor-status'),header=rect('.results-panel>.panel-heading'),notice=rect('.stale-notice'),button=rect('.export-button');
  const overlaps = button&&notice&&button.x<notice.right&&button.right>notice.x&&button.y<notice.bottom&&button.bottom>notice.y;
  return { viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio,clientWidth:document.documentElement.clientWidth}, document:{width:document.documentElement.scrollWidth,height:document.documentElement.scrollHeight}, panel,terminal,footer,header,notice,button,
    footerVisible:!!footer&&footer.bottom<=terminal.bottom+.5&&footer.bottom<=panel.bottom+.5,
    staleOverlap:!!overlaps,
    comparisonOverflow:Array.from(document.querySelectorAll('.comparison-card')).flatMap(card=>{const bounds=card.getBoundingClientRect();return Array.from(card.querySelectorAll('div,span,svg')).map(e=>({text:e.textContent?.slice(0,60),rect:e.getBoundingClientRect()})).filter(e=>e.rect.width>0&&(e.rect.left<bounds.left-.5||e.rect.right>bounds.right+.5)).map(e=>({text:e.text,left:e.rect.left,right:e.rect.right,cardLeft:bounds.left,cardRight:bounds.right}))}),
    offenders:Array.from(document.querySelectorAll('body *')).map(e=>({tag:e.tagName,class:e.className?.baseVal??e.className,text:e.textContent?.slice(0,50),right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).filter(e=>e.right>document.documentElement.clientWidth+.5&&e.width>0).slice(0,16) };
})()`

async function open(width, height, theme) {
  await chrome.page('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false })
  const { identifier } = await chrome.page('Page.addScriptToEvaluateOnNewDocument', { source: `localStorage.setItem('psi-theme',${JSON.stringify(theme)})` })
  await chrome.page('Page.navigate', { url: base })
  await chrome.waitFor('!!document.querySelector("textarea") && document.documentElement.dataset.theme === ' + JSON.stringify(theme))
  await chrome.page('Page.removeScriptToEvaluateOnNewDocument', { identifier })
  await chrome.settled()
}
async function record(name, reset = true) {
  if(reset)await chrome.evaluate('(() => {window.scrollTo(0,0);const p=document.querySelector(".results-panel");if(p)p.scrollTop=0})()')
  await chrome.settled()
  const data = await chrome.evaluate(metrics)
  data.name = name; data.screenshot = await chrome.screenshot(name)
  report.cases.push(data)
  if (!baseline) {
    if (data.document.width > data.viewport.clientWidth + .5) report.failures.push({ name, issue: 'V02 horizontal overflow', width: data.document.width, offenders: data.offenders })
    if (!data.footerVisible) report.failures.push({ name, issue: 'V01 editor footer clipped', footer: data.footer, terminal: data.terminal })
    if (data.staleOverlap || (data.button && data.button.bottom > data.header.bottom + .5)) report.failures.push({ name, issue: 'V03 header/notice overlap', button: data.button, header: data.header, notice: data.notice })
    if (data.comparisonOverflow.length) report.failures.push({ name, issue: 'Comparison card content clipped', offenders: data.comparisonOverflow })
  }
}
async function runA(script) {
  if (script !== undefined) await chrome.input(script)
  else await chrome.click('button.button.ghost') // Usar ejemplo
  lastA = null
  await chrome.click('.analyze-button')
  await chrome.waitFor('!!document.querySelector(".result-overview") && !document.querySelector(".loading-state")')
  await chrome.settled()
  const deadline = Date.now() + 5000
  while (!lastA && Date.now() < deadline) await delay(50)
  assert(lastA, 'Actual A HTTP response must be captured')
}
async function exportJson(expected, filenamePattern) {
  const previous = downloads.length
  await chrome.click('.export-button')
  const deadline = Date.now() + 10000
  while ((!downloads[previous] || !downloads[previous].completed) && Date.now() < deadline) await delay(60)
  const download = downloads[previous]
  assert(download?.completed, 'Native browser download must complete')
  assert.match(download.suggestedFilename, filenamePattern)
  const path = join(chrome.downloads, download.suggestedFilename)
  const info = await stat(path)
  const content = JSON.parse(await readFile(path, 'utf8'))
  if (expected) assert.deepEqual(content, expected, 'Export must retain every returned field')
  report.downloads.push({ path, name: download.suggestedFilename, bytes: info.size, original: 'results' in content ? content.results[0].original : content.original,
    configurations: 'results' in content ? content.results.map(r => r.configuration) : [content.configuration], evidenceCount: 'results' in content ? content.results.map(r => r.evidence.length) : content.deterministic?.evidence.length })
  return content
}
try {
  await chrome.page('Fetch.enable', { patterns: [{ urlPattern: '*' }] })
  const sizes = interactionOnly ? [] : viewportArgument ? [viewportArgument.split('=')[1].split('x').map(Number)] : baseline ? [[1024,768],[320,844]] : zoom === 2 ? [[1024,768],[1440,900]] : [[1920,1080],[1440,900],[1366,768],[1024,768],[768,1024],[390,844],[320,844]]
  for (const [width,height] of sizes) for (const theme of ['light','dark']) {
    stage = `${width}x${height}-${theme}`
    await open(width,height,theme)
    await record(`${stage}-empty`)
    await runA()
    await record(`${stage}-result`)
    if(await chrome.evaluate('innerWidth<=600')) {
      await chrome.click('#tab-evidence');await record(`${stage}-evidence-scrolled`,false)
      await chrome.click('#tab-recovery');await record(`${stage}-recovery-scrolled`,false)
      await chrome.click('#tab-findings')
    }
    await chrome.click('[aria-label="Limpiar script"]')
    await chrome.waitFor('!!document.querySelector(".stale-notice")')
    await record(`${stage}-stale`)
    console.log(`Measured ${stage}`)
  }
  if (!baseline && !layoutOnly) {
    stage='selection-without-analysis'
    const postsBefore=report.requests.filter(r=>r.method==='POST').length
    await open(1024,768,'light')
    for(const mode of ['B','C','ABC','A'])await chrome.click(`input[value="${mode}"]`)
    assert.equal(report.requests.filter(r=>r.method==='POST').length,postsBefore,'Mounting and selecting modes must not submit analysis')
    stage = 'downloads-A'
    await open(1024,768,'dark')
    const original = '# á🧪 <texto> "comillas"\\ruta\nWrite-Output (\'studio-\'+\'local\')\nGet-Process -Id 734201'
    await runA(original)
    const a = await exportJson(lastA, /^powershell-insight-analisis-A-.*\.json$/)
    assert.equal(a.original, original); assert.equal(a.configuration,'A'); assert.equal(a.llm,null)
    assert(a.deterministic.evidence.length > 0 && a.deobfuscation.transformations.length > 0)
    for (const evidence of a.deterministic.evidence) assert(evidence.provenance && evidence.root_source.layer_id === 'L0')
    await chrome.click('[aria-label="Limpiar script"]')
    await exportJson(a, /-entrada-anterior\.json$/)

    stage = 'comparison-mocked'
    await chrome.input(fixtures.results[0].original)
    await chrome.click('input[value="ABC"]')
    await chrome.click('.analyze-button')
    await chrome.waitFor('document.querySelectorAll(".comparison-card").length===3')
    for (const configuration of ['A', 'B', 'C']) {
      await chrome.click(`#comparison-${configuration}`)
      await record(`1024x768-dark-comparison-${configuration}`)
    }
    await exportJson(fixtures, /^powershell-insight-comparacion-ABC-.*\.json$/)
    await chrome.click('[aria-label="Limpiar script"]')
    await record('1024x768-dark-comparison-stale')
    await exportJson(fixtures, /^powershell-insight-comparacion-ABC-.*-entrada-anterior\.json$/)
    await chrome.click('[aria-label="Activar modo claro"]')
    await chrome.waitFor('document.documentElement.dataset.theme === "light"')
    await record('1024x768-light-comparison-stale')
    await chrome.click('[aria-label="Activar modo oscuro"]')
    await chrome.waitFor('document.documentElement.dataset.theme === "dark"')
    comparisonMode = 'unavailable'
    await chrome.input(fixtures.results[0].original)
    await chrome.click('.analyze-button')
    await chrome.waitFor('document.querySelectorAll(".status-unavailable").length===2')
    await chrome.click('#comparison-B')
    assert(await chrome.evaluate('document.querySelector(".result-errors").textContent.includes("SIMULATED offline")'))
    await record('1024x768-dark-comparison-unavailable')
    comparisonMode='partial'
    await chrome.click('.analyze-button')
    await chrome.waitFor('document.querySelector(".status-partial")!==null')
    await chrome.click('#comparison-C')
    assert(await chrome.evaluate('document.querySelector(".result-notices").textContent.includes("Caso indeterminado")'))
    await chrome.click('#tab-recovery')
    assert(await chrome.evaluate('document.querySelector(".model-recovery").textContent.includes("No verificadas") && document.querySelector(".recovery-card").textContent.includes("Verificado por 1A")'))
    await record('1024x768-dark-comparison-partial-recovery')

    if (process.argv.includes('--comparison-layout')) {
      comparisonMode = 'completed'
      for (const [width, height] of [[1920,1080],[1440,900],[1366,768],[1024,768],[768,1024],[390,844],[320,844]]) for (const theme of ['light', 'dark']) {
        stage = 'comparison-mocked'
        await open(width, height, theme)
        await chrome.input(fixtures.results[0].original)
        await chrome.click('input[value="ABC"]')
        await chrome.click('.analyze-button')
        await chrome.waitFor('document.querySelectorAll(".comparison-card").length===3')
        await chrome.click('#comparison-C')
        await record(`${width}x${height}-${theme}-comparison-C`)
        await chrome.click('[aria-label="Limpiar script"]')
        await record(`${width}x${height}-${theme}-comparison-stale`)
        console.log(`Measured comparison ${width}x${height}-${theme}`)
      }
    }

    stage = 'keyboard'
    await open(1024,768,'light')
    await chrome.click('[aria-label="Ver estado del sistema"]')
    await chrome.key('Escape')
    assert.equal(await chrome.evaluate('document.activeElement.id'),'system-toggle')
    report.keyboard.push('System Escape returns focus')
    await chrome.click('[aria-label="Ver estado del sistema"]')
    await chrome.click('[aria-label="Cerrar estado del sistema"]')
    assert.equal(await chrome.evaluate('document.activeElement.id'),'system-toggle', 'System close button must return focus')
    report.keyboard.push('System close button returns focus')
    await chrome.click('[aria-label="Abrir ayuda contextual"]')
    assert(await chrome.evaluate('document.querySelector("dialog").open'))
    await chrome.key('Escape')
    assert(await chrome.evaluate('!document.querySelector("dialog").open && document.activeElement.getAttribute("aria-label")==="Abrir ayuda contextual"'))
    report.keyboard.push('Help Escape returns focus')
    await runA()
    await chrome.click('#tab-findings'); await chrome.key('ArrowRight')
    assert.equal(await chrome.evaluate('document.activeElement.id'),'tab-evidence')
    await chrome.key('End'); assert.equal(await chrome.evaluate('document.activeElement.id'),'tab-trace')
    await chrome.evaluate('document.querySelector(".skip-link").focus()')
    await chrome.key('Tab')
    assert.equal(await chrome.evaluate('document.activeElement.id'),'system-toggle')
    await chrome.key('Tab',8) // CDP modifier bits: Shift=8, Control=2
    assert(await chrome.evaluate('document.activeElement.matches(".skip-link") && document.activeElement.getBoundingClientRect().top>=0'))
    report.keyboard.push('Tab and Shift+Tab move focus in both directions; skip link visible')
    for (let index=0;index<18;index++) {
      await chrome.key('Tab')
      const focus = await chrome.evaluate(`(() => {const e=document.activeElement,r=e.getBoundingClientRect();const indicator=e.matches('textarea')?e.closest('.terminal-window'):e.matches('input[name="pipeline"]')?e.closest('label'):e;const s=getComputedStyle(indicator);return {tag:e.tagName,type:e.type,label:e.getAttribute('aria-label'),width:r.width,height:r.height,visible:r.bottom>0&&r.top<innerHeight&&r.right>0&&r.left<innerWidth,outline:s.outlineStyle,focusIndicator:(s.outlineStyle!=='none'&&parseFloat(s.outlineWidth)>0)||(e.matches('textarea')&&s.boxShadow!=='none')}})()`)
      report.keyboard.push(focus)
      assert(focus.visible && !(focus.type==='file'&&focus.width<=1), 'Keyboard must not stop on invisible controls')
      assert(focus.tag==='BODY'||focus.focusIndicator,'Focused page controls must have a visible focus indicator')
    }
    await chrome.screenshot('keyboard-focus')

    stage = 'long-content'
    await open(1024,768,'dark')
    await runA('# long static source\n' + Array.from({length:80},(_,i)=>`# ${i} ${'x'.repeat(220)}`).join('\n') + '\nGet-Process -Id 734201')
    const scrolling = await chrome.evaluate(`(() => {const e=document.querySelector('textarea');e.scrollTop=e.scrollHeight;e.scrollLeft=e.scrollWidth;e.dispatchEvent(new Event('scroll'));return {vertical:e.scrollTop,horizontal:e.scrollLeft,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight}})()`)
    assert(scrolling.vertical>0 && scrolling.horizontal>0, 'Long script remains accessible through independent editor scroll')
    report.scrolling=scrolling
    await record('1024x768-dark-long-content')

    stage='upload-unicode'
    await open(1024,768,'light')
    const source='# á🧪\r\nWrite-Output (\'studio-\'+\'local\')\r\nGet-Process -Id 734201\r\n'
    const filename='muestra_unicode_'+ 'archivo_largo_'.repeat(8)+'.ps1'
    const inputPath=join(chrome.output,filename)
    await writeFile(inputPath,'\uFEFF'+source,'utf8')
    const {root}=await chrome.page('DOM.getDocument')
    const {nodeId}=await chrome.page('DOM.querySelector',{nodeId:root.nodeId,selector:'input[type="file"]'})
    await chrome.page('DOM.setFileInputFiles',{nodeId,files:[inputPath]})
    await chrome.waitFor('document.querySelector("textarea").value.includes("Get-Process")')
    lastA=null;await chrome.click('.analyze-button')
    await chrome.waitFor('document.querySelector(".result-overview")!==null')
    for(let i=0;!lastA&&i<50;i++)await delay(50)
    assert.equal(lastA?.original,source,'UTF-8 upload strips BOM and preserves Unicode/CRLF in submitted original')
    report.upload={filename,inputPath,originalPreserved:true}
    await record('1024x768-light-long-filename-upload')

    report.zoom = { requested:zoom, method:'Chrome page zoom in isolated profile', actualBrowserZoomVerified:zoom===2,
      observed:await chrome.evaluate('({innerWidth,innerHeight,devicePixelRatio,visualScale:visualViewport.scale})') }
    if(zoom===2) {
      assert.equal(report.zoom.observed.devicePixelRatio,2,'Actual browser zoom must double DPR')
      assert.equal(report.zoom.observed.innerWidth,512,'200% page zoom must halve the 1024px CSS layout viewport')
      assert.equal(report.zoom.observed.visualScale,1,'Browser zoom is different from pinch or screenshot scaling')
    }
    const forbidden = report.requests.filter(r => /\/api\/(compare|analyze\/[BC])/.test(r.url) && !['comparison-mocked'].includes(r.stage))
    assert.equal(forbidden.length,0,'Mount/navigation must not start LLM requests')
  }
} catch (error) {
  report.failures.push({ stage, message: error.stack })
  try { await chrome.screenshot('failure') } catch {}
} finally {
  if(report.errors.length)report.failures.push({stage:'console',message:'Unexpected browser errors',count:report.errors.length})
  report.downloadFiles = await readdir(chrome.downloads)
  await writeFile(join(chrome.output,'report.json'),JSON.stringify(report,null,2))
  await chrome.close()
  console.log(JSON.stringify({ report:join(chrome.output,'report.json'), cases:report.cases.length, downloads:report.downloads.length, errors:report.errors.length, failures:report.failures },null,2))
  if (report.failures.length) process.exitCode=1
}
