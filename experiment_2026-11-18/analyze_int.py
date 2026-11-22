# -*- coding: utf-8 -*-
"""Analyse interval runs: per-window results, accuracy per scene, delays, transitions (gain trace)."""
import json, sys, statistics, re, math, io

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
    its, cur, start = [], None, None
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
            m = re.search(r'\(([\d.]+)s\)', x)
            if m:
                cur['audio_s'] = float(m.group(1))
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
        elif e['type'] == 'http' and 'analyze-mood' in x:
            cur.setdefault('http', []).append(x)
    return d, start, its


def run_rows(run):
    d, start, its = parse(run)
    I = d['interval_s']
    slot = max(I, 20)
    rows, prev = [], 'calm'
    for it in its:
        off = (it['t_start'] - start) / 1000
        # window covered by this iteration: [off - I, off] (first one: [0, 5])
        w0, w1 = max(0.0, off - I), off
        # scene whose slot overlaps the window most
        best, bo = None, 0
        for k in range(1, 21):
            s0, s1 = 5 + slot * (k - 1), 5 + slot * k
            ov = min(w1, s1) - max(w0, s0)
            if ov > bo:
                best, bo = k, ov
        r = {'run': run, 'interval': I, 'offset_s': round(off, 1), 'scene': best if bo > 1 else None}
        if 'tr1' in it and 'tr0' in it:
            r['transcribe_ms'] = it['tr1'] - it['tr0']
            r['audio_s'] = it.get('audio_s')
        if 'text' in it:
            r['text'] = it['text']
        if 'an1' in it:
            r['analysis_ms'] = it['an1'] - it['an0']
            r['analysis_end_off'] = it['an1'] - it['t_start']
            r.update({k2: it['analysis'][k2] for k2 in ('mood', 'intensity', 'environment')})
            r['expected'] = exp.get(r['scene'])
            r['match'] = r['mood'] == r['expected']
            r['changed'] = r['mood'] != prev
            prev = r['mood']
        if 'cf0' in it:
            r['to_crossfade_ms'] = it['cf0'] - it['an1']
            r['total_ms'] = it['cf0'] - it['t_start']
        r['http'] = it.get('http')
        rows.append(r)
    return d, rows


def transitions(d):
    """Gain-trace check of every transition in the real loop."""
    G = d.get('gain') or []
    res = []
    i = 1
    while i < len(G):
        # a transition starts where the gain starts to fall from a plateau
        if G[i][1] < G[i - 1][1] - 1e-4 and G[i - 1][1] > 0.3:
            t0 = G[i - 1][0]
            g0 = G[i - 1][1]
            j = i
            steps = []
            while j < len(G) and G[j][0] < t0 + 4.0:
                steps.append(abs(G[j][1] - G[j - 1][1]))
                j += 1
            seg = [g for g in G[i - 1:j]]
            zero = next((g for g in seg if g[1] <= 0.001), None)
            back = None
            if zero:
                back = next((g for g in seg if g[0] > zero[0] and g[1] >= 0.99 * g0), None)
            res.append({'t': round(t0, 2), 'gain0': round(g0, 3), 'max_step': round(max(steps), 4),
                        'fade_out_s': round(zero[0] - t0, 3) if zero else None,
                        'fade_in_s': round(back[0] - zero[0], 3) if (zero and back) else None})
            # skip past this transition
            while i < len(G) and G[i][0] < t0 + 4.0:
                i += 1
        i += 1
    return res


out = io.open('int_summary.txt', 'w', encoding='utf-8')
allrows = {}
summary = {}
for run in sys.argv[1:]:
    d, rows = run_rows(run)
    I = d['interval_s']
    allrows[run] = rows
    sc = [r for r in rows if r['scene']]
    an = [r for r in sc if 'mood' in r]
    # state after each scene: mood of the last analysed window of that scene
    after = {}
    for r in an:
        after[r['scene']] = r['mood']
    scene_ok = sum(1 for k in range(1, 21) if after.get(k) == exp[k])
    trans = transitions(d)
    tr_ms = [r['transcribe_ms'] for r in sc if 'transcribe_ms' in r and (r.get('audio_s') or 0) > I - 1]
    tot = [r['total_ms'] for r in sc if 'total_ms' in r]
    wers = []
    if I >= 20:
        wers = [wer(ref[r['scene']], r['text']) for r in sc if 'text' in r]
    proc = [r['analysis_end_off'] for r in sc if 'analysis_end_off' in r]
    starts = [r['offset_s'] for r in rows]
    dev = max(abs((b - a) - I) for a, b in zip(starts[1:], starts[2:])) if len(starts) > 2 else None
    s = {
        'proc_median_s': round(statistics.median(proc) / 1000, 2) if proc else None,
        'proc_max_s': round(max(proc) / 1000, 2) if proc else None,
        'proc_le3': sum(1 for x in proc if x <= 3000), 'proc_n': len(proc),
        'cadence_dev_s': round(dev, 2) if dev is not None else None,
        'interval': I, 'windows': len(sc), 'analysed': len(an), 'window_match': sum(r['match'] for r in an),
        'scene_state_ok': scene_ok, 'changes': sum(1 for r in an if r['changed']),
        'false_changes': sum(1 for r in an if r['changed'] and not r['match']),
        'transitions_gain': len(trans), 'max_gain_step': max((t['max_step'] for t in trans), default=None),
        'fade_out_range': [min((t['fade_out_s'] for t in trans if t['fade_out_s']), default=None), max((t['fade_out_s'] for t in trans if t['fade_out_s']), default=None)],
        'fade_in_range': [min((t['fade_in_s'] for t in trans if t['fade_in_s']), default=None), max((t['fade_in_s'] for t in trans if t['fade_in_s']), default=None)],
        'transcribe_median_s': round(statistics.median(tr_ms) / 1000, 2) if tr_ms else None,
        'transcribe_max_s': round(max(tr_ms) / 1000, 2) if tr_ms else None,
        'total_median_s': round(statistics.median(tot) / 1000, 2) if tot else None,
        'total_max_s': round(max(tot) / 1000, 2) if tot else None,
        'total_le3': sum(1 for x in tot if x <= 3000), 'total_n': len(tot),
        'wer_mean': round(statistics.mean(wers) * 100, 1) if wers else None,
        'skipped': sum(1 for r in sc if 'mood' not in r),
        'http_errors': sum(1 for r in sc for h in (r.get('http') or []) if not h.endswith(' 200')),
    }
    summary[run] = s
    out.write('%s %s\n' % (run, json.dumps(s, ensure_ascii=False)))
    for r in sc:
        out.write('   w@%6.1f scene %2s exp %-7s got %-7s %s tr %s tot %s | %s\n' % (r['offset_s'], r['scene'], r.get('expected'), r.get('mood'), 'ok ' if r.get('match') else 'BAD' if 'mood' in r else '---',
                                                                     r.get('transcribe_ms'), r.get('total_ms'), (r.get('text') or '')[:70]))
    out.write('   transitions: %s\n' % trans)
out.close()
json.dump({'summary': summary, 'rows': allrows}, open('int_rows.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(open('int_summary.txt', encoding='utf-8').read()[:6000])
