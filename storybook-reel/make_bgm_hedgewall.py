#!/usr/bin/env python3
"""《樹牆》60 秒配樂：純 Python 標準庫合成，零版權。

結構跟著故事走：
  0–32s  樹牆裡（Am / Dm 為主，低、窄、壓著）
  28–36s 轉向 G（縫出現、要出去了）
  36–60s 外面（C 大調打開，音域拉高，音量放大）

用法：python3 make_bgm_hedgewall.py bgm60.wav
"""
import wave, struct, math, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "bgm60.wav"
DUR, SR = 60.0, 44100
N = int(SR * DUR)
buf = [0.0] * N

def n2f(n): return 440.0 * (2 ** ((n - 69) / 12.0))

# (起, [和弦音], 低音)　每 4 秒一個
CHORDS = [
    (0,  [57,60,64], 45), (4,  [57,60,64], 45), (8,  [53,57,62], 38),
    (12, [57,60,64], 45), (16, [53,57,60], 41), (20, [53,57,62], 38),
    (24, [57,60,64], 45), (28, [55,59,62], 43), (32, [55,59,62], 43),
    (36, [55,60,64], 36), (40, [53,57,60], 41), (44, [55,60,64], 36),
    (48, [57,60,64], 45), (52, [53,57,60], 41), (56, [55,60,64], 36),
]

# (起, 音高, 長度)
MELODY = [
    (1.2,72,1.8),(3.4,69,1.6),(5.6,72,1.5),(7.4,74,1.6),(9.6,69,1.8),(12.0,72,1.5),
    (14.2,71,1.6),(16.4,69,1.8),(18.6,72,1.4),(20.8,74,1.6),(23.0,69,1.8),
    (25.2,72,1.5),(27.4,74,1.6),(29.6,76,1.8),(31.8,74,1.6),(33.6,71,1.8),
    (36.2,76,1.8),(38.4,79,1.6),(40.6,76,1.6),(42.8,72,1.8),(45.0,76,1.6),
    (47.2,81,2.0),(49.6,79,1.6),(51.8,76,1.8),(54.0,72,1.6),(56.2,76,2.2),(58.2,72,2.2),
]

def secgain(t):
    """穿出樹牆之後整體放開"""
    if t < 30: return 0.80
    if t > 38: return 1.15
    return 0.80 + (t - 30) / 8.0 * 0.35

PIANO = [(1,1.0),(2,0.42),(3,0.18),(4,0.09),(6,0.04)]

def add(t0, dur, f, amp, harmonics, tau, attack=0.004):
    i0, i1 = int(t0*SR), min(N, int((t0+dur)*SR))
    for i in range(max(0,i0), i1):
        t = (i-i0)/SR
        env = math.exp(-t/tau)
        if t < attack: env *= t/attack
        s = 0.0
        for k, ha in harmonics: s += ha*math.sin(2*math.pi*f*k*t)
        buf[i] += amp*env*s

def add_pad(t0, dur, f, amp, ramp=1.1):
    i0, i1 = int(t0*SR), min(N, int((t0+dur)*SR))
    for i in range(max(0,i0), i1):
        t = (i-i0)/SR
        env = min(t/ramp, 1.0, (dur-t)/ramp if dur-t < ramp else 1.0)
        if env < 0: env = 0.0
        s = (math.sin(2*math.pi*f*t)
             + 0.7*math.sin(2*math.pi*f*1.003*t)
             + 0.35*math.sin(2*math.pi*f*2*t))
        buf[i] += amp*env*s

for t0, notes, bass in CHORDS:
    g = secgain(t0)
    for n in notes:
        add_pad(t0, 4.4, n2f(n), 0.028*g)
    add(t0, 4.2, n2f(bass), 0.072*g, [(1,1.0),(2,0.22)], 2.0)
    for j, n in enumerate(notes):
        add(t0+0.12*j, 3.0, n2f(n+12), 0.017*g, PIANO, 1.4)

for t0, n, d in MELODY:
    add(t0, d+1.2, n2f(n), 0.105*secgain(t0), PIANO, 1.15)

fade = int(1.8*SR)
for i in range(fade):
    g = i/fade
    buf[i] *= g
    buf[N-1-i] *= g

peak = max(1e-9, max(abs(v) for v in buf))
gain = 0.85/peak if peak > 0.85 else 1.0
frames = b"".join(struct.pack("<h", int(max(-1,min(1,v*gain))*32767)) for v in buf)
w = wave.open(OUT,"w"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(frames); w.close()
print("bgm ->", OUT, DUR, "s")
