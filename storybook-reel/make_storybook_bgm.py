#!/usr/bin/env python3
"""繪本風配樂：純 Python 標準庫合成，零版權。

和 skill 內建的 make_chiptune_bgm.py 是同一套思路（用 wave 直接寫取樣點），
但音色換成「柔和鋼琴 + 弦樂墊 + 低音」，配風格 C 的水彩／繪本畫面。

改 CHORDS 換和聲、改 MELODY 換旋律、改 DUR 對齊影片長度。
用法：python3 make_storybook_bgm.py bgm.wav 20
"""
import wave, struct, math, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "bgm.wav"
DUR = float(sys.argv[2]) if len(sys.argv) > 2 else 20.0
SR  = 44100

def n2f(n):                      # MIDI note number -> Hz
    return 440.0 * (2 ** ((n - 69) / 12.0))

# --- 和聲：Am - F - C - G，每個和弦 5 秒，溫柔不煽情 ---
CHORDS = [
    (0.0,  [57, 60, 64], 45),    # Am  (A3 C4 E4), bass A2
    (5.0,  [53, 57, 60], 41),    # F   (F3 A3 C4), bass F2
    (10.0, [55, 60, 64], 43),    # C/G (G3 C4 E4), bass G2
    (15.0, [55, 59, 62], 43),    # G   (G3 B3 D4), bass G2
]

# --- 旋律：A 小調五聲，(起始秒, 音高, 長度) ---
MELODY = [
    (0.9, 72, 1.6), (2.6, 76, 1.3), (4.1, 74, 1.4),
    (5.7, 72, 1.5), (7.4, 69, 1.6), (9.1, 72, 1.2),
    (10.6, 76, 1.6), (12.4, 79, 1.5), (14.0, 76, 1.4),
    (15.6, 74, 1.5), (17.2, 72, 1.6), (18.6, 69, 1.4),
]

N = int(SR * DUR)
buf = [0.0] * N

def add(t0, dur, f, amp, harmonics, tau, attack=0.004):
    """加一個音：泛音疊加 + 指數衰減，tau 大 = 尾韻長"""
    i0 = int(t0 * SR)
    i1 = min(N, i0 + int(dur * SR))
    for i in range(max(0, i0), i1):
        t = (i - i0) / SR
        env = math.exp(-t / tau)
        if t < attack:
            env *= t / attack
        s = 0.0
        for k, ha in harmonics:
            s += ha * math.sin(2 * math.pi * f * k * t)
        buf[i] += amp * env * s

def add_pad(t0, dur, f, amp):
    """弦樂墊：兩個微失諧正弦，慢起慢落"""
    i0, i1 = int(t0 * SR), min(N, int((t0 + dur) * SR))
    ramp = 0.9
    for i in range(max(0, i0), i1):
        t = (i - i0) / SR
        env = min(t / ramp, 1.0, (dur - t) / ramp if dur - t < ramp else 1.0)
        env = max(env, 0.0)
        s = (math.sin(2 * math.pi * f * t)
             + 0.7 * math.sin(2 * math.pi * f * 1.003 * t)
             + 0.35 * math.sin(2 * math.pi * f * 2 * t))
        buf[i] += amp * env * s

PIANO = [(1, 1.0), (2, 0.42), (3, 0.18), (4, 0.09), (6, 0.04)]

for t0, notes, bass in CHORDS:
    for n in notes:
        add_pad(t0, 5.4, n2f(n), 0.030)
    add(t0, 5.2, n2f(bass), 0.075, [(1, 1.0), (2, 0.22)], 2.2)
    # 和弦琶音，很輕，當空氣感
    for j, n in enumerate(notes):
        add(t0 + 0.12 * j, 3.4, n2f(n + 12), 0.020, PIANO, 1.5)

for t0, n, d in MELODY:
    add(t0, d + 1.2, n2f(n), 0.115, PIANO, 1.15)

# 頭尾淡入淡出
fade = int(1.6 * SR)
for i in range(fade):
    g = i / fade
    buf[i] *= g
    buf[N - 1 - i] *= g

# 軟限幅，避免爆音
peak = max(1e-9, max(abs(v) for v in buf))
gain = 0.82 / peak if peak > 0.82 else 1.0
frames = b"".join(struct.pack("<h", int(max(-1, min(1, v * gain)) * 32767)) for v in buf)

w = wave.open(OUT, "w")
w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(frames); w.close()
print("bgm ->", OUT, DUR, "s")
