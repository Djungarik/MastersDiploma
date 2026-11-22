/**
 * Loop Controller
 *
 * Schedules iterations of the agentic loop so that:
 * - only one iteration runs at a time (the next one is planned after the
 *   previous one has finished, never in parallel);
 * - every start() opens a new session, and stop() closes it, so an iteration
 *   that is still awaiting a response can detect that its result is stale
 *   and must be ignored.
 *
 * The controller has no dependency on React or the browser, which makes the
 * scheduling rules testable with `node --test`.
 */
export function createLoopController({
  runIteration,
  getInterval,
  firstDelay = 5000,
  onError = () => {},
  setTimer = setTimeout,
  clearTimer = clearTimeout,
  now = Date.now,
}) {
  let sessionId = 0
  let running = false
  let busy = false
  let timer = null

  function schedule(id, delay) {
    timer = setTimer(async () => {
      timer = null
      if (id !== sessionId || !running) return

      // Guard against overlapping iterations (e.g. a leftover one from a
      // previous session that has not returned yet)
      if (busy) {
        schedule(id, getInterval())
        return
      }

      const startedAt = now()
      busy = true
      try {
        await runIteration({ isStale: () => id !== sessionId })
      } catch (error) {
        onError(error)
      } finally {
        busy = false
      }

      if (id !== sessionId || !running) return
      // Keep the cadence close to the configured interval, but never start
      // the next iteration before the previous one has finished
      const elapsed = now() - startedAt
      schedule(id, Math.max(0, getInterval() - elapsed))
    }, delay)
  }

  return {
    /** Start a new session; does nothing if the loop is already running */
    start() {
      if (running) return sessionId
      running = true
      sessionId += 1
      schedule(sessionId, firstDelay)
      return sessionId
    },

    /** Stop the loop and invalidate results of the iteration in progress */
    stop() {
      if (!running) return
      running = false
      sessionId += 1
      if (timer !== null) {
        clearTimer(timer)
        timer = null
      }
    },

    isRunning: () => running,
    isBusy: () => busy,
    getSessionId: () => sessionId,
  }
}

export default createLoopController
