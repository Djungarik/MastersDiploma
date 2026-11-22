# -*- coding: utf-8 -*-
"""Calls the running backend: classification agreement (H3) and server analysis latency."""
import json, time, sys, statistics, urllib.request
REPEATS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
scenes = json.load(open('scenes.json', encoding='utf-8'))
rows = []
for rep in range(1, REPEATS + 1):
    for sc in scenes:
        req = urllib.request.Request('http://127.0.0.1:8000/api/analyze-mood', data=json.dumps({'text': sc['text']}).encode(), headers={'Content-Type': 'application/json'})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.loads(r.read()); status = r.status
        except urllib.error.HTTPError as e:
            body = {'error': e.read().decode()[:200]}; status = e.code
        dt = time.perf_counter() - t0
        rows.append({'rep': rep, 'id': sc['id'], 'expected': sc['expected'], 'status': status, 'ms': round(dt * 1000), **{k: body.get(k) for k in ('mood', 'intensity', 'environment')}})
        time.sleep(2.2)  # stay below the provider rate limit
json.dump(rows, open('api_results.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
ok = [r for r in rows if r['status'] == 200]
ms = sorted(r['ms'] for r in ok)
print('requests', len(rows), 'ok', len(ok))
print('latency ms: min %d median %d mean %d p95 %d max %d' % (ms[0], statistics.median(ms), statistics.mean(ms), ms[int(len(ms) * 0.95) - 1], ms[-1]))
match = sum(r['mood'] == r['expected'] for r in ok)
print('agreement %d/%d = %.1f%%' % (match, len(ok), 100 * match / len(ok)))
for rep in range(1, REPEATS + 1):
    rr = [r for r in ok if r['rep'] == rep]
    print(' rep', rep, sum(r['mood'] == r['expected'] for r in rr), '/', len(rr))
