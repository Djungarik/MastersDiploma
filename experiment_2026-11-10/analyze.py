# -*- coding: utf-8 -*-
"""Parse e2e console logs: per-iteration timings, recognised text, analysis result, transitions."""
import json, sys, statistics, re

scenes = json.load(open('scenes.json', encoding='utf-8'))
exp = {s['id']: s['expected'] for s in scenes}
ref = {s['id']: s['text'] for s in scenes}


def words(t):
    return re.findall(r"[a-z']+", t.lower())


def wer(r, h):
    r, h = words(r), words(h)
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        prev, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (r[i - 1] != h[j - 1]))
            prev, d[j] = d[j], cur
    return d[len(h)] / max(1, len(r))


def parse(run):
    d = json.load(open('runs/%s/log.json' % run, encoding='utf-8'))
    its, cur = [], None
    start = None
    for e in d['log']:
        t, x = e['t'], e['text']
        if e['type'] == 'mark' and x == 'start listening click':
            start = t
        if x == '[loop] iteration start':
            cur = {'t_start': t}
            its.append(cur)
        elif cur is None:
            continue
        elif x == '[loop] transcription start':
            cur['tr0'] = t
        elif 'Transcribing' in x and 'samples' in x:
            cur['audio_s'] = float(re.search(r'\(([\d.]+)s\)', x).group(1))
        elif x == '[loop] transcription end':
            cur['tr1'] = t
        elif x.startswith('[loop] transcribed text:'):
            cur['text'] = x.split(':', 1)[1].strip()
        elif x == '[loop] analysis start':
            cur['an0'] = t
        elif x.startswith('[loop] analysis end:'):
            cur['an1'] = t
            cur['analysis'] = json.loads(x.split(':', 1)[1])
        elif x.startswith('[loop] crossfade start'):
            cur['cf0'] = t
        elif 'Same mood, no change needed' in x:
            cur['same'] = True
        elif 'Crossfaded to mood' in x:
            cur['cf_mid'] = t
        elif e['type'] == 'http' and 'analyze-mood' in x:
            cur.setdefault('http', []).append(x)
    return d, start, its


rows = []
for run in sys.argv[1:]:
    d, start, its = parse(run)
    k = 0
    prev_mood = 'calm'
    for it in its:
        off = (it['t_start'] - start) / 1000
        scene = round((off - 5) / 20)  # window index: 0 = initial 5 s of silence
        r = {'run': run, 'offset_s': round(off, 1), 'scene': scene}
        if 'tr1' in it and 'tr0' in it:
            r['transcribe_ms'] = it['tr1'] - it['tr0']
            r['audio_s'] = it.get('audio_s')
        if 'text' in it:
            r['text'] = it['text']
            if scene in ref:
                r['wer'] = round(wer(ref[scene], it['text']), 3)
        if 'an1' in it:
            r['analysis_ms'] = it['an1'] - it['an0']
            r.update({k2: it['analysis'][k2] for k2 in ('mood', 'intensity', 'environment')})
            r['expected'] = exp.get(scene)
            r['match'] = r['mood'] == r['expected']
            r['changed'] = r['mood'] != prev_mood
            prev_mood = r['mood']
        if 'cf0' in it:
            r['to_crossfade_ms'] = it['cf0'] - it['an1']
            r['total_ms'] = it['cf0'] - it['t_start']
            if 'cf_mid' in it:
                r['fade_out_ms'] = it['cf_mid'] - it['cf0']
        r['http'] = it.get('http')
        rows.append(r)
json.dump(rows, open('e2e_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def stat(name, vals):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        print(name, 'n=0'); return
    print('%-18s n=%d min=%d median=%d mean=%d max=%d' % (name, len(vals), vals[0], statistics.median(vals), statistics.mean(vals), vals[-1]))


sc = [r for r in rows if r['scene'] >= 1 and r['scene'] <= 20]
print('iterations total', len(rows), 'scene windows', len(sc))
for run in sys.argv[1:]:
    rr = [r for r in sc if r['run'] == run]
    an = [r for r in rr if 'mood' in r]
    print(run, 'windows', len(rr), 'analysed', len(an), 'match', sum(r['match'] for r in an), 'transitions', sum(1 for r in rr if 'fade_out_ms' in r),
          'false', sum(1 for r in an if r['changed'] and not r['match']), 'mean WER %.3f' % statistics.mean(r['wer'] for r in rr if 'wer' in r))
stat('transcribe_ms', [r.get('transcribe_ms') for r in sc if r.get('audio_s', 0) > 15])
stat('analysis_ms', [r.get('analysis_ms') for r in sc])
stat('to_crossfade_ms', [r.get('to_crossfade_ms') for r in sc])
stat('total_ms', [r.get('total_ms') for r in sc])
stat('fade_out_ms', [r.get('fade_out_ms') for r in sc])
print('total > 3000:', sum(1 for r in sc if r.get('total_ms', 0) > 3000), 'of', sum(1 for r in sc if 'total_ms' in r))
for r in sc:
    if 'mood' not in r or not r['match']:
        print('ISSUE', r['run'], r['scene'], r.get('mood'), r.get('expected'), r.get('http'), (r.get('text') or '')[:90])
