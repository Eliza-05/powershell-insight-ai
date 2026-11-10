// Dependency-free browser test transport for an isolated local Chrome profile.
// Never attaches to a user's existing browser or reads its tabs/profile.
import { spawn } from 'node:child_process'
import { mkdtemp, mkdir, writeFile, appendFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

export const delay = ms => new Promise(resolve => setTimeout(resolve, ms))
export async function launchChrome({ zoom = 1 } = {}) {
  const output = await mkdtemp(join(tmpdir(), 'psi-frontend-visual-'))
  const downloads = join(output, 'downloads')
  await mkdir(downloads)
  if (zoom !== 1) {
    await mkdir(join(output, 'profile', 'Default'), { recursive: true })
    // Chrome's default storage partition is "x". This sets actual page zoom in
    // the disposable profile; it does not apply CSS zoom or change the user's profile.
    await writeFile(join(output, 'profile', 'Default', 'Preferences'), JSON.stringify({ partition: { default_zoom_level: { x: Math.log(zoom) / Math.log(1.2) } } }))
  }
  const executable = process.env.PSI_TEST_CHROME ?? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
  const child = spawn(executable, [
    '--headless', '--remote-debugging-port=0', '--remote-debugging-address=127.0.0.1',
    '--disable-gpu',
    `--user-data-dir=${join(output, 'profile')}`, '--no-first-run', '--no-default-browser-check',
    '--disable-extensions', '--disable-background-networking', '--disable-component-update', '--disable-sync',
    'about:blank',
  ], { windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'] })
  console.log(`Chrome PID ${child.pid}; temporary profile: ${output}`)
  await writeFile(join(output, 'chrome.pid'), String(child.pid))
  let stderr = '', startError
  child.on('error', error => { startError = error })
  child.stderr.on('data', chunk => { stderr += chunk; void appendFile(join(output,'chrome.log'),chunk) })
  const deadline = Date.now() + 15000
  while (!/DevTools listening on (ws:\/\/[^\s]+)/.test(stderr)) {
    if (startError) throw startError
    if (child.exitCode !== null || Date.now() > deadline) throw new Error(`Chrome did not start: ${stderr.slice(-1500)}`)
    await delay(100)
  }
  const socket = new WebSocket(stderr.match(/DevTools listening on (ws:\/\/[^\s]+)/)[1])
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject })
  let nextId = 0
  const pending = new Map(), listeners = new Map()
  socket.onclose = () => { for (const item of pending.values()) { clearTimeout(item.timer); item.reject(new Error(`Chrome connection closed: ${item.method}`)) }; pending.clear() }
  socket.onmessage = event => {
    const message = JSON.parse(event.data)
    if (message.id) {
      const request = pending.get(message.id)
      if (!request) return
      pending.delete(message.id); clearTimeout(request.timer)
      if (message.error) request.reject(new Error(`${request.method}: ${message.error.message}`))
      else request.resolve(message.result)
    } else {
      for (const handler of listeners.get(message.method) ?? []) handler(message.params, message.sessionId)
    }
  }
  const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
    const id = ++nextId
    const timer = setTimeout(() => { pending.delete(id); reject(new Error(`Timed out: ${method}`)) }, 15000)
    pending.set(id, { resolve, reject, timer, method })
    socket.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }))
  })
  const on = (method, handler) => { if (!listeners.has(method)) listeners.set(method, []); listeners.get(method).push(handler) }
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: downloads, eventsEnabled: true })
  const { targetId } = await send('Target.createTarget', { url: 'about:blank' })
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true })
  const page = (method, params) => send(method, params, sessionId)
  try { await Promise.all([page('Page.enable'), page('Runtime.enable'), page('Network.enable'), page('Log.enable')]) }
  catch (error) {
    await writeFile(join(output,'startup-error.txt'), `${error}\n${stderr}`)
    try { await send('Browser.close') } catch { child.kill() }
    socket.close(); throw error
  }
  async function evaluate(expression) {
    const result = await page('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true })
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description ?? result.exceptionDetails.text)
    return result.result.value
  }
  async function waitFor(expression, timeout = 12000) {
    const until = Date.now() + timeout
    while (Date.now() < until) { if (await evaluate(expression)) return; await delay(70) }
    throw new Error(`Condition not reached: ${expression}`)
  }
  async function settled() {
    await evaluate('document.fonts.ready')
    await evaluate('new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    await delay(220) // existing 180 ms entry animations must finish before measuring overlap
  }
  async function click(selector) {
    await evaluate(`document.querySelector(${JSON.stringify(selector)})?.scrollIntoView({block:'center',inline:'nearest'})`)
    await settled()
    const rect = await evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)}); if(!e) throw new Error('Missing control');const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2}})()`)
    await page('Input.dispatchMouseEvent', { type: 'mousePressed', button: 'left', clickCount: 1, ...rect })
    await page('Input.dispatchMouseEvent', { type: 'mouseReleased', button: 'left', clickCount: 1, ...rect })
    await settled()
  }
  async function key(key, modifiers = 0) {
    const codes = { Tab: 9, Escape: 27, Enter: 13, ArrowRight: 39, ArrowLeft: 37, Home: 36, End: 35, a: 65, '+': 187, '-': 189, '0': 48 }
    await page('Input.dispatchKeyEvent', { type: 'keyDown', key, modifiers, windowsVirtualKeyCode: codes[key] })
    await page('Input.dispatchKeyEvent', { type: 'keyUp', key, modifiers, windowsVirtualKeyCode: codes[key] })
    await settled()
  }
  async function input(text) {
    await click('textarea[aria-label="Script PowerShell"]')
    await key('a', 2)
    await page('Input.insertText', { text })
    await settled()
  }
  async function screenshot(name) {
    const { data } = await page('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
    const path = join(output, `${name}.png`)
    await writeFile(path, Buffer.from(data, 'base64'))
    return path
  }
  async function close() {
    try { await send('Browser.close') } catch { child.kill() }
    socket.close()
  }
  return { output, downloads, send, on, page, evaluate, waitFor, settled, click, key, input, screenshot, close }
}
