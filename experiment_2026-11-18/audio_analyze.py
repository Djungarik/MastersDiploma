# -*- coding: utf-8 -*-
"""Analyse volume steps and transitions: master-gain trace (5 ms) and output level (50 ms windows)."""
import json, sys, math, io

run = sys.argv[1]
D = json.load(open('runs/%s/envelope.json' % run, encoding='utf-8'))
rec = D['rec']
t, rms, step = rec['t'], rec['rms'], rec['step']
G = rec.get('gain') or []
gt, gv = [g[0] for g in G], [g[1] for g in G]
marks = rec['marks']
out = io.open('runs/%s/analysis.txt' % run, 'w', encoding='utf-8')
res = {'ua': D['ua'], 'volume': [], 'transitions': []}


def P(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    out.write(s + '\n')


def bis(arr, x):
    lo, hi = 0, len(arr)
    while lo < hi:
        m = (lo + hi) // 2
        if arr[m] < x:
            lo = m + 1
        else:
            hi = m
    return lo


def level(a, b):
    """RMS of output between times a and b."""
    i, j = bis(t, a), bis(t, b)
    v = rms[i:j]
    return math.sqrt(sum(x * x for x in v) / len(v)) if v else float('nan')


def gain_at(x):
    i = min(bis(gt, x), len(gt) - 1)
    return gv[i]


def db(x, ref):
    return 20 * math.log10(x / ref) if x > 1e-9 and ref > 1e-9 else float('-inf')


P('UA', D['ua'])
P('envelope blocks', len(t), 'gain samples', len(G))

# ---------------- volume
P('\n== volume steps')
vols = [m for m in marks if m['label'].startswith('volume ')]
for m in vols:
    v = float(m['label'].split()[1])
    t0 = m['t']
    g_before, g_after = gain_at(t0 - 0.02), gain_at(t0 + 0.5)
    # gain change between consecutive samples in the first 50 ms (jump detector)
    i0, i1 = bis(gt, t0 - 0.01), bis(gt, t0 + 0.3)
    jumps = [abs(gv[k] - gv[k - 1]) for k in range(max(i0, 1), i1)]
    k_end = next((k for k in range(i0, i1) if abs(gv[k] - v) < 0.005), None)
    settle = (gt[k_end] - t0) if k_end is not None else None
    lv = level(t0 + 0.6, t0 + 2.9)
    P('set %.2f: gain %.3f -> %.3f, reached target after %s, largest gain change between 5 ms samples %.3f, output RMS %.4f' % (
        v, g_before, g_after, ('%.0f ms' % (settle * 1000)) if settle is not None else 'n/a', max(jumps) if jumps else 0, lv))
    res['volume'].append({'set': v, 'gain_before': round(g_before, 4), 'gain_after': round(g_after, 4), 'settle_ms': round(settle * 1000) if settle is not None else None,
                          'max_jump': round(max(jumps), 4) if jumps else 0, 'out_rms': round(lv, 5)})
ref = next((x['out_rms'] for x in res['volume'] if x['set'] == 1.0), None)
if ref:
    for x in res['volume']:
        x['out_ratio'] = round(x['out_rms'] / ref, 3)
        P('   set %.2f -> output %.3f of the 100 %% level (%.1f dB)' % (x['set'], x['out_ratio'], db(x['out_rms'], ref)))

# ---------------- transitions
P('\n== transitions (master gain trace)')
trans = [m for m in marks if m['label'].startswith('crossfade') or m['label'].startswith('manual play') or m['label'].startswith('two commands')]
for m in trans:
    t0 = m['t']
    g0 = gain_at(t0 - 0.01)
    i0, i1 = bis(gt, t0 - 0.01), bis(gt, t0 + 5.0)
    seq = list(range(max(i0, 1), i1))
    jumps = [(abs(gv[k] - gv[k - 1]), k) for k in seq]
    mj, mk = max(jumps)
    # value right after the call (first sample after +15 ms)
    g_first = gain_at(t0 + 0.015)
    k_zero = next((k for k in seq if gt[k] > t0 and gv[k] <= 0.001), None)
    fade_out = (gt[k_zero] - t0) if k_zero is not None else None
    zeros = [k for k in seq if gv[k] <= 0.001]
    k_last0 = zeros[-1] if zeros else None
    silent = (gt[k_last0] - gt[zeros[0]]) if zeros else 0
    g_final = gain_at(t0 + 4.5)
    k_up = next((k for k in range(k_last0, i1) if gv[k] >= 0.99 * g_final), None) if k_last0 is not None else None
    fade_in = (gt[k_up] - gt[k_last0]) if k_up is not None else None
    l_before, l_after = level(t0 - 1.5, t0 - 0.05), level(t0 + 3.5, t0 + 5.0)
    # full transition: from the first gain decrease to the gain reaching 99 % of the final level
    k_start = next((k for k in seq if gv[k] < g0 - 0.002), None)
    total = (gt[k_up] - gt[k_start]) if (k_up is not None and k_start is not None) else None
    P('   full transition: %s' % (('%.3f s' % total) if total is not None else '-'))
    P('%-34s gain %.3f -> %.3f within 15 ms (largest 5 ms change %.3f at +%.0f ms) | gain 0 after %s | gain 0 held %.0f ms | fade-in %s | output RMS %.4f -> %.4f' % (
        m['label'], g0, g_first, mj, (gt[mk] - t0) * 1000, ('%.2f s' % fade_out) if fade_out is not None else '-', silent * 1000,
        ('%.2f s' % fade_in) if fade_in is not None else '-', l_before, l_after))
    res['transitions'].append({'label': m['label'], 'gain_before': round(g0, 4), 'gain_after_15ms': round(g_first, 4), 'max_jump': round(mj, 4),
                               'max_jump_at_ms': round((gt[mk] - t0) * 1000), 'fade_out_s': round(fade_out, 3) if fade_out is not None else None,
                               'zero_ms': round(silent * 1000), 'fade_in_s': round(fade_in, 3) if fade_in is not None else None,
                               'total_s': round(total, 3) if total is not None else None,
                               'rms_before': round(l_before, 5), 'rms_after': round(l_after, 5)})
json.dump(res, open('runs/%s/summary.json' % run, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
out.close()
