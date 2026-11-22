import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const RUN = process.argv[2] || 'run1'
const DURATION_S = Number(process.argv[3] || 415)
const WAV = path.resolve(process.argv[4] || 'timeline.wav')
const out = path.resolve('runs', RUN)
fs.mkdirSync(out, { recursive: true })

const browser = await chromium.launch({
  channel: 'chrome',
  headless: true,
  args: [
    '--use-fake-device-for-media-stream',
    '--use-fake-ui-for-media-stream',
    `--use-file-for-fake-audio-capture=${WAV}%noloop`,
    '--autoplay-policy=no-user-gesture-required',
  ],
})
const context = await browser.newContext({ viewport: { width: 1600, height: 900 } })
await context.grantPermissions(['microphone'], { origin: 'http://localhost:3000' })
const page = await context.newPage()
const log = []
const t0 = Date.now()
page.on('console', (msg) => log.push({ t: Date.now(), type: msg.type(), text: msg.text() }))
page.on('pageerror', (err) => log.push({ t: Date.now(), type: 'pageerror', text: String(err) }))
page.on('response', (r) => { if (r.url().includes('/api/')) log.push({ t: Date.now(), type: 'http', text: `${r.request().method()} ${new URL(r.url()).pathname} ${r.status()}` }) })
const save = () => fs.writeFileSync(path.join(out, 'log.json'), JSON.stringify({ t0, ua: uaString, log }, null, 1))
let uaString = ''

await page.goto('http://localhost:3000')
uaString = await page.evaluate(() => navigator.userAgent)
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
log.push({ t: Date.now(), type: 'mark', text: 'init click' })
await page.getByRole('button', { name: /Initialize Whisper AI/ }).click()
await page.getByRole('button', { name: 'Start Listening' }).waitFor({ timeout: 600000 })
log.push({ t: Date.now(), type: 'mark', text: 'model ready' })
await page.getByRole('button', { name: 'Start Listening' }).click()
log.push({ t: Date.now(), type: 'mark', text: 'start listening click' })
const started = Date.now()
let shot = 2
while ((Date.now() - started) / 1000 < DURATION_S) {
  await page.waitForTimeout(20000)
  if (shot <= 8) await page.screenshot({ path: path.join(out, `0${shot++}_t${Math.round((Date.now() - started) / 1000)}.png`) })
  save()
}
await page.screenshot({ path: path.join(out, '09_before_stop.png') })
log.push({ t: Date.now(), type: 'mark', text: 'stop listening click' })
await page.getByRole('button', { name: 'Stop Listening' }).click()
await page.waitForTimeout(8000)
await page.screenshot({ path: path.join(out, '10_after_stop.png') })
save()
fs.writeFileSync(path.join(out, 'email.txt'), email)
await browser.close()
console.log('done', RUN, log.length, 'events')
