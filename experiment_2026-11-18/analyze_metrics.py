# -*- coding: utf-8 -*-
"""Uniform timing metrics for all runs (10.11.2026 and 18.11.2026).

For every analysed fragment:
  transcribe  - local transcription time;
  analysis    - /api/analyze-mood request time;
  processing  - from the iteration start (= end of the fragment) to the analysis response
                (transcription + analysis + overhead); defined for every analysed fragment;
For every actual change of the music (the engine logged "Crossfaded to mood"):
  to_change   - from the iteration start to the start of the sound change (fade-out start);
  reaction    - from the end of the utterance on the audio timeline to the start of the sound change.
The audio timeline starts at the "Recording started" console mark (the fake microphone file starts
playing when the recorder starts).

usage: python analyze_metrics.py   (run from experiment_2026-11-18)
"""
import json, os, re, statistics, wave, array

HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(HERE, '..', 'experiment_2026-11-10')
scenes = json.load(open(os.path.join(HERE, 'scenes.json'), encoding='utf-8'))
EXP = {s['id']: s['expected'] for s in scenes}


def segments_from_wav(path):
    w = wave.open(path)
    sr = w.getframerate()
    x = array.array('h', w.readframes(w.getnframes()))
    segs, inside, last = [], False, 0
    for i in range(0, len(x), 480):
        t = i / sr
        if max(abs(v) for v in x[i:i + 480]) > 200:
            if not inside:
                segs.append([t, t])
                inside = True
            segs[-1][1] = t + 0.01
            last = t
        elif inside and t - last > 1.5:
            inside = False
    return segs


def utterances(interval):
    if interval == 20:
        p = os.path.join(HERE, 'timeline_20_used.json')
        return {k + 1: tuple(s) for k, s in enumerate(json.load(open(p))['segments'])}
    lay = json.load(open(os.path.join(HERE, 'timeline_%d.json' % interval)))['layout']
    return {e['scene']: (e['start_s'], e['end_s']) for e in lay}


def parse(path):
    d = json.load(open(path, encoding='utf-8'))
    L = d['log']
    rec = next(e['t'] for e in L if 'Recording started' in e['text'])
    its, cur = [], None
    for e in L:
        x, t = e['text'], e['t']
        if x == '[loop] iteration start':
            cur = {'t0': t}
            its.append(cur)
        elif cur is None:
            continue
        elif x == '[loop] transcription start':
            cur['tr0'] = t
        elif x == '[loop] transcription end':
            cur['tr1'] = t
        elif x.startswith('[loop] transcribed text:'):
            cur['text'] = x.split(':', 1)[1].strip()
        elif x == '[loop] analysis start':
            cur['an0'] = t
        elif x.startswith('[loop] analysis end:'):
            cur['an1'] = t
            cur['mood'] = json.loads(x.split(':', 1)[1])['mood']
        elif x.startswith('[loop] crossfade start'):
            cur['cf0'] = t
        elif 'Crossfaded to mood' in x:
            cur['changed'] = True
    return rec, its, d.get('interval_s', 20)


def scene_of(off, interval):
    slot = max(interval, 20)
    w0, w1 = max(0.0, off - interval), off
    best, bo = None, 0
    for k in range(1, 21):
        s0, s1 = 5 + slot * (k - 1), 5 + slot * k
        ov = min(w1, s1) - max(w0, s0)
        if ov > bo:
            best, bo = k, ov
    return best if bo > 1 else None


def run_metrics(path, interval=None):
    rec, its, I = parse(path)
    I = interval or I
    utt = utterances(I)
    rows = []
    for it in its:
        off = (it['t0'] - rec) / 1000
        k = scene_of(off, I)
        if not k or 'an1' not in it:
            continue
        r = {'scene': k, 'mood': it['mood'], 'expected': EXP[k],
             'transcribe': (it['tr1'] - it['tr0']) / 1000, 'analysis': (it['an1'] - it['an0']) / 1000,
             'processing': (it['an1'] - it['t0']) / 1000, 'text': it.get('text', '')}
        if it.get('changed'):
            r['to_change'] = (it['cf0'] - it['t0']) / 1000
            r['reaction'] = (it['cf0'] - rec) / 1000 - utt[k][1]
        rows.append(r)
    return rows


def stats(v):
    v = sorted(v)
    return {'n': len(v), 'min': v[0], 'median': statistics.median(v), 'mean': statistics.mean(v), 'max': v[-1]}


def summary(rows):
    s = {}
    for key in ('transcribe', 'analysis', 'processing', 'to_change', 'reaction'):
        vals = [r[key] for r in rows if key in r]
        if vals:
            s[key] = stats(vals)
    s['processing_le3'] = sum(1 for r in rows if r['processing'] <= 3.0)
    s['to_change_le3'] = sum(1 for r in rows if 'to_change' in r and r['to_change'] <= 3.0)
    s['to_change_values_near_3'] = sorted(round(r['to_change'], 3) for r in rows if 'to_change' in r and 2.95 <= r['to_change'] <= 3.05)
    s['analysis_le1'] = sum(1 for r in rows if r['analysis'] <= 1.0)
    s['transcribe_le1_5'] = sum(1 for r in rows if r['transcribe'] <= 1.5)
    return s


if __name__ == '__main__':
    # utterance positions of the timeline used on 10.11.2026 and for the 20 s run on 18.11.2026
    if not os.path.exists(os.path.join(HERE, 'timeline_20_used.json')):
        wav = os.path.join(HERE, 'timeline.wav')
        json.dump({'segments': segments_from_wav(wav)}, open(os.path.join(HERE, 'timeline_20_used.json'), 'w'))
    out = {}
    old = []
    for r in ('run1', 'run2', 'run3'):
        rows = run_metrics(os.path.join(OLD, r, 'log.json'), 20)
        old += rows
        out['2026-11-10 ' + r] = summary(rows)
    out['2026-11-10 all'] = summary(old)
    for r in ('int10', 'int20', 'int30', 'int60'):
        out['2026-11-18 ' + r] = summary(run_metrics(os.path.join(HERE, 'runs', r, 'log.json')))
    json.dump(out, open(os.path.join(HERE, 'metrics_summary.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for k, v in out.items():
        print(k, {kk: (round(vv['median'], 3) if isinstance(vv, dict) else vv) for kk, vv in v.items()})
