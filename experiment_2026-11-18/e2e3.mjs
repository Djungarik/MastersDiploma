// End-to-end run with a configurable analysis interval and output-audio capture.
// usage: node e2e3.mjs <run> <durationSeconds> <timeline.wav> <intervalSeconds>
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const RUN = process.argv[2]
const DURATION_S = Number(process.argv[3])
const WAV = path.resolve(process.argv[4])
const INTERVAL_S = Number(process.argv[5])
const out = path.resolve('runs', RUN)
fs.mkdirSync(out, { recursive: true })

const browser = await chromium.launch({
  channel: process.env.CH || 'chrome',
  headless: true,
  args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream',
    `--use-file-for-fake-audio-capture=${WAV}%noloop`, '--autoplay-policy=no-user-gesture-required'],
})
const context = await browser.newContext({ viewport: { width: 1600, height: 900 } })
await context.grantPermissions(['microphone'], { origin: 'http://localhost:3000' })
await context.addInitScript({ path: path.resolve('audio_tap.js') })
const page = await context.newPage()
const log = []
const t0 = Date.now()
page.on('console', (msg) => log.push({ t: Date.now(), type: msg.type(), text: msg.text() }))
page.on('pageerror', (err) => log.push({ t: Date.now(), type: 'pageerror', text: String(err) }))
page.on('response', (r) => { if (r.url().includes('/api/')) log.push({ t: Date.now(), type: 'http', text: `${r.request().method()} ${new URL(r.url()).pathname} ${r.status()}` }) })
let ua = ''
const save = async (final = false) => {
  const extra = final ? await page.evaluate(() => ({ rec: window.__rec, gain: window.__gain })) : {}
  fs.writeFileSync(path.join(out, 'log.json'), JSON.stringify({ t0, ua, interval_s: INTERVAL_S, wav: path.basename(WAV), log, ...extra }))
}

await page.goto('http://localhost:3000')
ua = await page.evaluate(() => navigator.userAgent)
await page.getByText('Create an account').click()
const email = `e2e_${Date.now()}@example.com`
await page.locator('input[type=email]').fill(email)
await page.locator('input[type=text]').fill('E2E_Tester')
const pw = page.locator('input[type=password]')
await pw.nth(0).fill('SecurePassword123')
await pw.nth(1).fill('SecurePassword123')
await page.getByRole('button', { name: 'Begin Your Journey' }).click()
await page.getByText('Initialize Whisper AI').waitFor({ timeout: 20000 })

await page.screenshot({ path: path.join(out, '01_main.png') })

await page.getByRole('button', { name: /Initialize Whisper AI/ }).click()
await page.getByRole('button', { name: 'Start Listening' }).waitFor({ timeout: 600000 })
log.push({ t: Date.now(), type: 'mark', text: 'model ready' })
// analysis interval slider (min 10000, max 60000, step 5000)
await page.evaluate((ms) => {
  const el = [...document.querySelectorAll('input[type=range]')].find((e) => e.max === '60000')
  const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
  setter.call(el, String(ms))
  el.dispatchEvent(new Event('input', { bubbles: true }))
}, INTERVAL_S * 1000)
await page.waitForTimeout(300)
const shown = await page.evaluate(() => [...document.querySelectorAll('input[type=range]')].find((e) => e.max === '60000').value)
log.push({ t: Date.now(), type: 'mark', text: 'interval set ' + shown })

// sample the master gain of the app's audio engine every 5 ms
await page.evaluate(async () => {
  const url = performance.getEntriesByType('resource').map((x) => x.name).find((n) => n.includes('/src/services/audioEngine.js'))
  const m = await import(url)
  window.__gain = []
  setInterval(() => {
    const e = m.audioEngine
    if (e.audioContext && e.masterGain) window.__gain.push([e.audioContext.currentTime, e.masterGain.gain.value, Date.now()])
  }, 5)
})

await page.getByRole('button', { name: 'Start Listening' }).click()
log.push({ t: Date.now(), type: 'mark', text: 'start listening click' })
const started = Date.now()
let shot = 2
while ((Date.now() - started) / 1000 < DURATION_S) {
  await page.waitForTimeout(30000)
  if (shot <= 6) await page.screenshot({ path: path.join(out, `0${shot++}_t${Math.round((Date.now() - started) / 1000)}.png`) })
  await save()
}
log.push({ t: Date.now(), type: 'mark', text: 'stop listening click' })
await page.getByRole('button', { name: 'Stop Listening' }).click()
await page.waitForTimeout(5000)
await save(true)
fs.writeFileSync(path.join(out, 'email.txt'), email)
await browser.close()
console.log('done', RUN, log.length, 'events')
