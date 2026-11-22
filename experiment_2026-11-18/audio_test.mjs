// Volume and transition-quality test through the real UI and the real audio engine module.
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const RUN = process.argv[2] || 'audio_before'
const out = path.resolve('runs', RUN)
fs.mkdirSync(out, { recursive: true })
const browser = await chromium.launch({
  channel: process.env.CH || 'chrome',
  headless: true,
  args: ['--autoplay-policy=no-user-gesture-required', '--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
})
const context = await browser.newContext({ viewport: { width: 1600, height: 900 } })
await context.addInitScript({ path: path.resolve('audio_tap.js') })
const page = await context.newPage()
const log = []
page.on('console', (m) => log.push({ t: Date.now(), text: m.text() }))
page.on('pageerror', (e) => log.push({ t: Date.now(), text: 'pageerror ' + e }))

await page.goto('http://localhost:3000')
await page.getByText('Create an account').click()
const email = `audio_${Date.now()}@example.com`
await page.locator('input[type=email]').fill(email)
await page.locator('input[type=text]').fill('Audio_Tester')
const pw = page.locator('input[type=password]')
await pw.nth(0).fill('SecurePassword123')
await pw.nth(1).fill('SecurePassword123')
await page.getByRole('button', { name: 'Begin Your Journey' }).click()
await page.getByText('Developer Tools').waitFor({ timeout: 20000 })
await page.getByText('Developer Tools').click()

const mark = (label) => page.evaluate((l) => window.__mark(l), label)
const wait = (ms) => page.waitForTimeout(ms)
async function setVolume(v) {
  await page.evaluate((val) => {
    const el = [...document.querySelectorAll('input[type=range]')].find((e) => e.max === '1')
    const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set
    setter.call(el, String(val))
    el.dispatchEvent(new Event('input', { bubbles: true }))
  }, v)
}
const engine = (fn, ...args) => page.evaluate(async ([f, a]) => {
  const m = await import(performance.getEntriesByType('resource').map((x) => x.name).find((n) => n.includes('/src/services/audioEngine.js')))
  return m.audioEngine[f](...a)
}, [fn, args])

// sample the master gain value every 5 ms (AudioParam.value reflects the automation in Chrome)
await page.evaluate(async () => {
  const m = await import(performance.getEntriesByType('resource').map((x) => x.name).find((n) => n.includes('/src/services/audioEngine.js')))
  window.__gain = []
  setInterval(() => {
    const e = m.audioEngine
    if (e.audioContext && e.masterGain) window.__gain.push([e.audioContext.currentTime, e.masterGain.gain.value])
  }, 5)
})

// 1) manual playback of calm via the Developer Tools panel (UI path)
await page.locator('select').selectOption('calm')
await page.getByRole('button', { name: 'Play' }).click()
await wait(300)
await mark('play calm (manual)')
await wait(5000)

// 2) volume steps through the Volume slider (UI path)
for (const v of [1.0, 0.7, 0.4, 0.1, 0.0, 0.7]) {
  await mark('volume ' + v)
  await setVolume(v)
  await wait(3000)
}
await wait(3000)

// 3) transitions through the same call the agentic loop makes: audioEngine.crossfadeTo(url, 3, mood)
for (const mood of ['tense', 'epic', 'spooky', 'mystery', 'calm']) {
  await mark('crossfade -> ' + mood)
  await engine('crossfadeTo', null, 3, mood)
  await wait(8000)
}
// 4) transition shortly after a volume change
await mark('volume 0.5')
await setVolume(0.5)
await wait(4000)
await mark('volume 0.8')
await setVolume(0.8)
await wait(400)
await mark('crossfade -> epic (after volume)')
await engine('crossfadeTo', null, 3, 'epic')
await wait(8000)
// 5b) two commands in quick succession: the second must wait for the first transition
await mark('two commands -> tense, epic')
await page.evaluate(async () => {
  const url = performance.getEntriesByType('resource').map((x) => x.name).find((n) => n.includes('/src/services/audioEngine.js'))
  const m = await import(url)
  m.audioEngine.crossfadeTo(null, 3, 'tense')
  m.audioEngine.crossfadeTo(null, 3, 'epic')
})
await wait(9000)
// 5) manual switch while playing (Play button again, UI path)
await page.locator('select').selectOption('mystery')
await mark('manual play mystery while playing')
await page.getByRole('button', { name: 'Play' }).click()
await wait(6000)

const rec = await page.evaluate(() => { window.__rec.gain = window.__gain; return window.__rec })
fs.writeFileSync(path.join(out, 'envelope.json'), JSON.stringify({ email, ua: await page.evaluate(() => navigator.userAgent), rec, log }))
await browser.close()
console.log('done', RUN, rec.t.length, 'blocks', rec.marks.length, 'marks')
