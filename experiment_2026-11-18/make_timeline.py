# -*- coding: utf-8 -*-
"""Build fake-microphone timelines: 5 s lead-in, one scene centred in each slot, 10 s tail.
For interval I >= 20 the slot equals the analysis window; for I = 10 the slot is 20 s,
so every utterance (10-12 s) is split between two consecutive 10 s windows."""
import wave, sys, json, array

I = int(sys.argv[1])
slot = max(I, 20)
SR = 48000
scenes = []
for k in range(1, 21):
    w = wave.open('wav/scene%02d.wav' % k)
    assert w.getframerate() == SR and w.getnchannels() == 1 and w.getsampwidth() == 2
    scenes.append(array.array('h', w.readframes(w.getnframes())))
total = 5 + 20 * slot + 10
buf = array.array('h', bytes(2 * SR * total))
layout = []
for k, s in enumerate(scenes, 1):
    dur = len(s) / SR
    start = 5 + slot * (k - 1) + (slot - dur) / 2
    i0 = int(start * SR)
    buf[i0:i0 + len(s)] = s
    layout.append({'scene': k, 'start_s': round(start, 2), 'end_s': round(start + dur, 2)})
out = wave.open('timeline_%d.wav' % I, 'wb')
out.setnchannels(1); out.setsampwidth(2); out.setframerate(SR)
out.writeframes(buf.tobytes())
out.close()
json.dump({'interval': I, 'slot': slot, 'total_s': total, 'layout': layout}, open('timeline_%d.json' % I, 'w'), indent=1)
print('timeline_%d.wav' % I, total, 's')
