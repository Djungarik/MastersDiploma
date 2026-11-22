import { test } from 'node:test'
import assert from 'node:assert/strict'
import { createLoopController } from './loopController.js'

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

test('iterations never overlap when processing is longer than the interval', async () => {
  let active = 0
  let maxActive = 0
  let count = 0
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 10,
    runIteration: async () => {
      active += 1
      maxActive = Math.max(maxActive, active)
      count += 1
      await sleep(40) // four times longer than the interval
      active -= 1
    },
  })

  loop.start()
  await sleep(150)
  loop.stop()
  await sleep(60)

  assert.equal(maxActive, 1)
  assert.ok(count >= 2, `expected several iterations, got ${count}`)
})

test('result of an iteration that finishes after stop() is reported as stale', async () => {
  const applied = []
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 1000,
    runIteration: async ({ isStale }) => {
      await sleep(50) // "request" still in flight when the session is stopped
      if (isStale()) return
      applied.push('music changed')
    },
  })

  loop.start()
  await sleep(20) // iteration is in progress
  assert.equal(loop.isBusy(), true)
  loop.stop()
  await sleep(80)

  assert.deepEqual(applied, [])
  assert.equal(loop.isBusy(), false)
})

test('no iterations are started after stop()', async () => {
  let count = 0
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 10,
    runIteration: async () => { count += 1 },
  })

  loop.start()
  await sleep(40)
  loop.stop()
  const countAtStop = count
  await sleep(60)

  assert.ok(countAtStop >= 1)
  assert.equal(count, countAtStop)
  assert.equal(loop.isRunning(), false)
})

test('start() while running does not create a second loop', async () => {
  let count = 0
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 1000,
    runIteration: async () => { count += 1 },
  })

  const first = loop.start()
  const second = loop.start()
  await sleep(40)
  loop.stop()

  assert.equal(first, second)
  assert.equal(count, 1)
})

test('a restarted session ignores the late result of the previous one', async () => {
  const applied = []
  let call = 0
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 1000,
    runIteration: async ({ isStale }) => {
      const id = ++call
      await sleep(id === 1 ? 60 : 5)
      if (!isStale()) applied.push(id)
    },
  })

  loop.start()
  await sleep(20)
  loop.stop()
  loop.start() // new session while iteration 1 is still pending
  await sleep(1150)
  loop.stop()

  assert.ok(!applied.includes(1), 'late result of session 1 must be ignored')
  assert.ok(applied.includes(2), 'new session must work after the old iteration ends')
})

test('an exception inside an iteration does not stop the loop', async () => {
  let count = 0
  const errors = []
  const loop = createLoopController({
    firstDelay: 5,
    getInterval: () => 10,
    onError: (error) => errors.push(error.message),
    runIteration: async () => {
      count += 1
      if (count === 1) throw new Error('boom')
    },
  })

  loop.start()
  await sleep(60)
  loop.stop()

  assert.deepEqual(errors, ['boom'])
  assert.ok(count >= 2)
})
