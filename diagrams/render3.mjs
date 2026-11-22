import { chromium } from 'playwright-core'
import fs from 'node:fs'
const files = process.argv.slice(2)
const b = await chromium.launch({ channel: 'chrome', headless: true })
const p = await b.newPage({ deviceScaleFactor: 2 })
for (const f of files) {
  await p.setContent(`<html><body style="margin:0;background:white">${fs.readFileSync(f, 'utf8')}</body></html>`)
  await (await p.$('svg')).screenshot({ path: f.replace('.svg', '.png') })
}
await b.close()
