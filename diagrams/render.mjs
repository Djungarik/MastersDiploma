// Renders every *.svg in this folder to PNG with the installed Chrome.
// Usage: node render.mjs   (requires playwright-core; path can be given via PLAYWRIGHT_CORE)
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'

const corePath = process.env.PLAYWRIGHT_CORE || 'playwright-core'
const { chromium } = await import(corePath.includes(path.sep) || corePath.includes('/') ? pathToFileURL(corePath).href : corePath)

const dir = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'))
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ deviceScaleFactor: 2 })
for (const file of fs.readdirSync(dir).filter((f) => f.endsWith('.svg'))) {
  const svg = fs.readFileSync(path.join(dir, file), 'utf8')
  await page.setContent(`<html><body style="margin:0;background:white">${svg}</body></html>`)
  const el = await page.$('svg')
  await el.screenshot({ path: path.join(dir, file.replace('.svg', '.png')) })
  console.log('rendered', file)
}
await browser.close()
