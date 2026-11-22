// UI checks for test cases 5.1, 5.2, 5.5 and negative scenarios 1, 2, 3, 9
import { chromium } from 'playwright-core'
import fs from 'node:fs'
import path from 'node:path'

const out = path.resolve('runs', 'cases')
fs.mkdirSync(out, { recursive: true })
const results = {}
const email = `cases_${Date.now()}@example.com`
const PASSWORD = 'SecurePassword123'

async function register(page, mail, pass = PASSWORD, confirm = pass) {
  await page.goto('http://localhost:3000')
  await page.getByText('Create an account').click()
  await page.locator('input[type=email]').fill(mail)
  await page.locator('input[type=text]').fill('DM_Master')
  await page.locator('input[type=password]').nth(0).fill(pass)
  await page.locator('input[type=password]').nth(1).fill(confirm)
  await page.getByRole('button', { name: 'Begin Your Journey' }).click()
}
const formError = async (page) => (await page.locator('.text-blood-300').first().textContent({ timeout: 5000 })).trim()

// ---------- registration, validation, duplicate, login ----------
{
  const browser = await chromium.launch({ channel: 'chrome', headless: true })
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } })
  const page = await ctx.newPage()
  const http = []
  page.on('response', (r) => { if (r.url().includes('/api/auth')) http.push(`${r.request().method()} ${new URL(r.url()).pathname} ${r.status()}`) })

  await register(page, email, PASSWORD, 'Different123')
  results.password_mismatch = await formError(page)
  await register(page, email, '123', '123')
  results.short_password = await formError(page)

  await register(page, email)
  await page.getByRole('button', { name: /Initialize Whisper AI/ }).waitFor({ timeout: 15000 })
  results.tc51_registered = true
  results.tc51_token = await page.evaluate(() => !!localStorage.getItem('adaptive_ost_token'))
  await page.getByRole('button', { name: 'Logout' }).click()
  await page.getByText('Welcome Back').waitFor()
  results.logout_token_removed = await page.evaluate(() => !localStorage.getItem('adaptive_ost_token'))

  await register(page, email)
  results.duplicate_email = await formError(page)

  await page.goto('http://localhost:3000')
  await page.locator('input[type=email]').fill(email)
  await page.locator('input[type=password]').fill('WrongPassword1')
  await page.getByRole('button', { name: 'Enter the Realm' }).click()
  results.wrong_password = await formError(page)
  await page.screenshot({ path: path.join(out, 'wrong_password.png') })

  await page.locator('input[type=password]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Enter the Realm' }).click()
  await page.getByRole('button', { name: /Initialize Whisper AI/ }).waitFor({ timeout: 15000 })
  results.tc52_login = true
  results.tc52_user_shown = await page.getByText('DM_Master').isVisible()
  results.auth_http = http
  await browser.close()
}

// ---------- microphone denied ----------
{
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-fake-device-for-media-stream', '--deny-permission-prompts'] })
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 }, permissions: [] })
  const page = await ctx.newPage()
  const log = []
  page.on('console', (m) => log.push(m.text()))
  await page.goto('http://localhost:3000')
  await page.locator('input[type=email]').fill(email)
  await page.locator('input[type=password]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Enter the Realm' }).click()
  await page.getByRole('button', { name: /Initialize Whisper AI/ }).click()
  await page.getByRole('button', { name: 'Start Listening' }).waitFor({ timeout: 600000 })
  await page.getByRole('button', { name: 'Start Listening' }).click()
  await page.waitForTimeout(1500)
  results.mic_denied_toast = (await page.locator('.fixed.top-4 p').first().textContent().catch(() => null))
  results.mic_denied_status = await page.getByText('Idle').isVisible()
  results.mic_denied_button = await page.getByRole('button', { name: 'Start Listening' }).isVisible()
  await page.screenshot({ path: path.join(out, 'mic_denied.png') })
  await page.waitForTimeout(5500)
  results.mic_denied_toast_gone = (await page.locator('.fixed.top-4 p').count()) === 0
  await browser.close()
}

// ---------- manual mood selection (TC 5.5) and behaviour while listening (scenario 9) ----------
{
  const wav = path.resolve('timeline.wav')
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-fake-device-for-media-stream', '--use-fake-ui-for-media-stream', `--use-file-for-fake-audio-capture=${wav}%noloop`, '--autoplay-policy=no-user-gesture-required'] })
  const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } })
  await ctx.grantPermissions(['microphone'], { origin: 'http://localhost:3000' })
  const page = await ctx.newPage()
  const log = []
  page.on('console', (m) => log.push({ t: Date.now(), text: m.text() }))
  await page.goto('http://localhost:3000')
  await page.locator('input[type=email]').fill(email)
  await page.locator('input[type=password]').fill(PASSWORD)
  await page.getByRole('button', { name: 'Enter the Realm' }).click()
  await page.getByRole('button', { name: /Initialize Whisper AI/ }).click()
  await page.getByRole('button', { name: 'Start Listening' }).waitFor({ timeout: 600000 })
  const label = () => page.locator('h2.font-display').first().textContent()

  // manual selection without listening
  await page.getByText('Developer Tools').click()
  await page.locator('select').selectOption('epic')
  await page.getByRole('button', { name: 'Play', exact: true }).click()
  await page.waitForTimeout(2500)
  results.tc55_label_after_manual = await label()
  results.tc55_playing = await page.getByText('Playing').isVisible()
  results.tc55_console = log.filter((l) => /Playing ambient soundscape/.test(l.text)).map((l) => l.text).slice(-1)[0]
  await page.screenshot({ path: path.join(out, 'manual_epic.png') })

  // manual selection while the loop is running: the next analysis overrides it
  await page.getByRole('button', { name: 'Start Listening' }).click()
  const started = Date.now()
  await page.waitForTimeout(12000)
  await page.locator('select').selectOption('spooky')
  await page.getByRole('button', { name: 'Play', exact: true }).click()
  await page.waitForTimeout(1500)
  results.s9_label_after_manual = await label()
  results.s9_manual_at_s = Math.round((Date.now() - started) / 100) / 10
  await page.waitForTimeout(20000)
  results.s9_label_after_next_analysis = await label()
  results.s9_analysis = log.filter((l) => l.text.startsWith('[loop] analysis end')).map((l) => ({ at_s: Math.round((l.t - started) / 100) / 10, text: l.text.slice(21, 120) }))
  await page.getByRole('button', { name: 'Stop Listening' }).click()
  await page.waitForTimeout(1000)
  results.stop_status_idle = await page.getByText('Idle').isVisible()
  results.stop_still_playing = await page.getByText('Playing').isVisible()
  await page.getByText('Stop All Audio').click()
  await page.waitForTimeout(500)
  results.stop_all_no_track = await page.getByText('No track').isVisible()
  await browser.close()
}

fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(results, null, 1))
fs.writeFileSync(path.join(out, 'email.txt'), email)
console.log(JSON.stringify(results, null, 1))
