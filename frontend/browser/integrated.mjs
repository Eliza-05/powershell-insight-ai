// Full real HTTP path against the explicit transport-only synthetic backend.
// Refuses to submit B/C unless the loopback server attests /__test/state.synthetic.
import assert from 'node:assert/strict'
import { readFile, writeFile } from 'node:fs/promises'
import { join } from 'node:path'
import { launchChrome, delay } from './chrome.mjs'

const base = process.env.PSI_TEST_URL ?? 'http://127.0.0.1:8765'
assert(['localhost', '127.0.0.1'].includes(new URL(base).hostname))
const state = async () => { const r = await fetch(base + '/__test/state'); assert(r.ok); const s = await r.json(); assert.equal(s.synthetic, true); return s }
await state()
const packets = JSON.parse(await readFile(new URL('../src/test/fixtures/integrated-qwen3.json', import.meta.url), 'utf8'))
const browser = await launchChrome({ zoom: process.argv.includes('--zoom200') ? 2 : 1 })
const report = { output: browser.output, browser: await browser.send('Browser.getVersion'), cases: [], downloads: [], failures: [], errors: [], externalRequests: [], keyboard: [] }
let lastResponse = null
let expectedChats = (await state()).chats
const tracked = new Set(), downloads = []
browser.on('Network.responseReceived', e => { if (/\/api\/(compare|analyze\/[ABC])$/.test(e.response.url)) tracked.add(e.requestId) })
browser.on('Network.loadingFinished', e => { if (tracked.delete(e.requestId)) void browser.page('Network.getResponseBody', { requestId: e.requestId }).then(r => { lastResponse = JSON.parse(r.body) }).catch(error => report.failures.push(String(error))) })
browser.on('Runtime.exceptionThrown', e => report.errors.push(e.exceptionDetails))
browser.on('Runtime.consoleAPICalled', e => { if (e.type === 'error') report.errors.push(e.args.map(a => a.value ?? a.description)) })
browser.on('Log.entryAdded', e => { if (e.entry.level === 'error') report.errors.push(e.entry) })
browser.on('Network.loadingFailed', e => report.errors.push({ networkFailure: e.errorText, canceled: e.canceled }))
browser.on('Browser.downloadWillBegin', e => downloads.push({ ...e, completed: false }))
browser.on('Browser.downloadProgress', e => { const d = downloads.find(d => d.guid === e.guid); if (d && e.state === 'completed') d.completed = true })
browser.on('Fetch.requestPaused', e => {
  const url = new URL(e.request.url)
  if (url.origin !== new URL(base).origin && !['data:', 'blob:'].includes(url.protocol)) {
    report.externalRequests.push(url.href)
    void browser.page('Fetch.failRequest', { requestId: e.requestId, errorReason: 'BlockedByClient' })
  } else void browser.page('Fetch.continueRequest', { requestId: e.requestId })
})

async function open(width, height, theme) {
  await browser.page('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor: 1, mobile: false })
  const { identifier } = await browser.page('Page.addScriptToEvaluateOnNewDocument', { source: `localStorage.setItem('psi-theme',${JSON.stringify(theme)})` })
  await browser.page('Page.navigate', { url: base })
  await browser.waitFor('!!document.querySelector("textarea") && !!document.querySelector(".api-chip.online")')
  await browser.page('Page.removeScriptToEvaluateOnNewDocument', { identifier })
  await browser.waitFor('!document.querySelector("input[value=B]").disabled')
  await browser.settled()
  assert.equal((await state()).chats, expectedChats, 'Mount/navigation must not dispatch a model request')
}
async function analyze(script, mode) {
  await browser.input(script); await browser.click(`input[value="${mode}"]`)
  lastResponse = null
  await browser.click('.analyze-button')
  const deadline = Date.now() + 12000
  while (!lastResponse && Date.now() < deadline) await delay(40)
  assert(lastResponse, 'Capture the actual HTTP response')
  await browser.waitFor('!!document.querySelector(".result-overview") && !document.querySelector(".loading-state")')
  await browser.settled()
  expectedChats += mode === 'ABC' ? 2 : mode === 'A' ? 0 : 1
  assert.equal((await state()).chats, expectedChats, 'One explicit attempt per B/C; none for A')
  return lastResponse
}
async function exportJson(expected, stale = false) {
  const i = downloads.length
  await browser.click('.export-button')
  const deadline = Date.now() + 10000
  while (!downloads[i]?.completed && Date.now() < deadline) await delay(50)
  assert(downloads[i]?.completed, 'Native download completed')
  const name = downloads[i].suggestedFilename, path = join(browser.downloads, name)
  assert.match(name, stale ? /-entrada-anterior\.json$/ : /^powershell-insight-(analisis-[ABC]|comparacion-ABC)-.*\.json$/)
  assert.deepEqual(JSON.parse(await readFile(path, 'utf8')), expected)
  report.downloads.push({ name, path, exactResponsePreserved: true })
}
async function details() {
  await browser.click('#tab-trace')
  await browser.waitFor('!!document.querySelector(".verification-detail")')
  const count = await state()
  await browser.click('#tab-evidence'); await browser.click('#tab-trace')
  assert.equal((await state()).chats, count.chats, 'Tabs must not dispatch another model request')
}
async function record(name) {
  const metrics = await browser.evaluate(`({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,clientWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,verifier:!!document.querySelector('.verification-detail'),theme:document.documentElement.dataset.theme})`)
  assert(metrics.scrollWidth <= metrics.clientWidth + .5, 'No horizontal page overflow')
  report.cases.push({ name, ...metrics, screenshot: await browser.screenshot(name) })
}

try {
  await browser.page('Fetch.enable', { patterns: [{ urlPattern: '*' }] })
  const before = await state()
  await open(1366, 768, 'light')
  for (const mode of ['B', 'C', 'ABC', 'A']) await browser.click(`input[value="${mode}"]`)
  assert.equal((await state()).chats, before.chats, 'No generation on mount or selection')
  const a = await analyze("# á🧪\r\nWrite-Output ('safe-'+'text')\r\nGet-Process", 'A')
  assert.equal(a.llm, null); assert.equal(a.input_sha256.length, 64)
  await exportJson(a)
  await browser.input('Write-Output "changed"'); await exportJson(a, true)
  for (const name of ['kept', 'recovered', 'comparison', 'dropped', 'incoherent', 'opaque', 'invalid_json', 'bad_citation']) {
    const p = packets[name], start = await state()
    const response = await analyze(p.script, p.mode)
    const results = response.results ?? [response]
    assert.equal((await state()).chats - start.chats, p.mode === 'ABC' ? 2 : 1, 'Exactly one attempt per B/C request')
    if (p.mode === 'ABC') {
      assert.deepEqual(results.map(r => r.configuration), ['A', 'B', 'C'])
      for (const mode of ['A', 'B', 'C']) await browser.click('#comparison-' + mode)
      await browser.click('#comparison-B')
    }
    await details()
    if (name === 'incoherent') assert(await browser.evaluate('document.querySelector(".verification-detail").textContent.includes("Publicación del resultado rechazada")'))
    if (name === 'opaque') assert(await browser.evaluate('document.body.textContent.includes("Sanitización parcial o región opaca")'))
    if (['kept', 'recovered', 'comparison', 'incoherent'].includes(name)) await exportJson(response)
    await record('functional-' + name)
  }
  const sizes = process.argv.includes('--zoom200') ? [[1024, 768]] : [[1920,1080],[1366,768],[1024,768],[768,1024],[390,844],[320,844]]
  for (const [width, height] of sizes) for (const theme of ['light', 'dark']) {
    await open(width, height, theme)
    await analyze(packets.dropped.script, 'B'); await details()
    await browser.click('.verifier-decision summary')
    await browser.evaluate('document.querySelector(".verification-detail").scrollIntoView({block:"start"})')
    await browser.settled(); await record(`${width}x${height}-${theme}-verifier`)
    console.log(`Verified ${width}x${height} ${theme}`)
  }
  if (process.argv.includes('--zoom200')) {
    const z = await browser.evaluate('({dpr:devicePixelRatio,width:innerWidth,scale:visualViewport.scale})')
    assert.equal(z.dpr, 2); assert.equal(z.width, 512); assert.equal(z.scale, 1)
    report.zoom = z
  }
  await open(1024, 768, 'light')
  await browser.click('[aria-label="Ver estado del sistema"]'); await browser.key('Escape')
  assert.equal(await browser.evaluate('document.activeElement.id'), 'system-toggle')
  await browser.click('[aria-label="Abrir ayuda contextual"]'); await browser.key('Escape')
  assert(await browser.evaluate('!document.querySelector("dialog").open'))
  await browser.key('Tab'); await browser.key('Tab', 8)
  report.keyboard.push('Tab/Shift+Tab; Escape restores system/help focus')
  assert.equal(report.errors.length, 0)
  assert.equal(report.externalRequests.length, 0)
} catch (error) {
  report.failures.push(error.stack)
  try { report.lastPage = await browser.evaluate('({url:location.href,ready:document.readyState,html:document.documentElement.outerHTML.slice(0,3000)})') } catch {}
  try { await browser.screenshot('failure') } catch {}
} finally {
  await writeFile(join(browser.output, 'integrated-report.json'), JSON.stringify(report, null, 2))
  await browser.close()
  console.log(JSON.stringify({ report: join(browser.output, 'integrated-report.json'), cases: report.cases.length, downloads: report.downloads.length, failures: report.failures }, null, 2))
  if (report.failures.length) process.exitCode = 1
}
