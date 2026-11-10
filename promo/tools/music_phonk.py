"""Фонк-бит 140 BPM под монтаж ролика (всё синтезируется, без чужих сэмплов → без авторских прав).

python3 music_phonk.py out.wav
Структура (1 такт = 1.714 с):
  такты 1–2  — интро: приглушённый ковбелл + подъём шума
  такт 3     — ДРОП (склейка на сайт): удар, 808, бочка, хэты
  такты 3–11 — основной бит; перед тактом 10 (игра) — брейк и снова дроп
  такт 12    — аутро: только ковбелл, финальный удар и хвост
"""
import numpy as np, wave, sys
SR = 44100; BPM = 140; BEAT = 60 / BPM; BAR = BEAT * 4; STEP = BEAT / 4
DUR = BAR * 12 + 1.6
N = int(SR * DUR)
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(42)

def put(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N or i < 0: return
    s = sig[: N - i] * gain
    L[i:i + len(s)] += s * (1 - max(0, pan)); R[i:i + len(s)] += s * (1 + min(0, pan))

def lp(x, k):  # простой однополюсный ФНЧ
    y = np.empty_like(x); a = 0.0
    for i in range(len(x)): a += k * (x[i] - a); y[i] = a
    return y

def square(f, n): t = np.arange(n) / SR; return np.sign(np.sin(2 * np.pi * f * t))

def cowbell(f, dur=0.32, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    s = square(f, n) * .6 + square(f * 1.48, n) * .4
    s = s - lp(s, .08)             # убрать низ (полосовой характер)
    s = lp(s, .35 * bright + .05)  # срезать резкий верх
    e = np.exp(-t * 9) * (1 - np.exp(-t * 900))
    return s * e * .55

def k808(f0, dur=0.75, glide=None):
    n = int(dur * SR); t = np.arange(n) / SR
    f = np.full(n, f0) if glide is None else f0 + (glide - f0) * np.minimum(1, t / .12)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR + 2 * np.exp(-t * 40))
    s = np.tanh(s * 2.6) * np.exp(-t * 2.3) * (1 - np.exp(-t * 600))
    return s * .8

def kick():
    n = int(.28 * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t * 30) + 48
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2.2) * np.exp(-t * 11) * .9

def snare():
    n = int(.32 * SR); t = np.arange(n) / SR
    no = rng.standard_normal(n); no = no - lp(no, .12)
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
    return (no * np.exp(-t * 13) * .55 + body * .35) * .9

def hat(open_=False):
    n = int((.16 if open_ else .045) * SR); t = np.arange(n) / SR
    no = rng.standard_normal(n); no = no - lp(no, .5)
    return no * np.exp(-t * (16 if open_ else 80)) * .2

def riser(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    no = rng.standard_normal(n); out = np.empty(n); a = 0.0
    k = .02 + .5 * (t / dur) ** 2
    for i in range(n): a += k[i] * (no[i] - a); out[i] = a
    return out * (t / dur) ** 1.6 * .5

def impact():
    n = int(1.6 * SR); t = np.arange(n) / SR
    no = rng.standard_normal(n); no = lp(no, .25)
    boom = np.sin(2 * np.pi * (60 * np.exp(-t * 3) + 30) * t)
    return (no * np.exp(-t * 3.2) * .35 + boom * np.exp(-t * 3) * .9)

def pad(freqs, dur):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for f in freqs:
        for d in (-.18, .18): s += ((2 * ((f * (1 + d / 100) * t) % 1) - 1))
    s = lp(lp(s, .02), .03)
    e = np.minimum(1, t / .4) * np.minimum(1, (dur - t) / .4)
    return s * e * .06

# ноты (ля минор): A4 C5 D5 E5 G4 …
NOTE = {"A3": 220.0, "C4": 261.6, "D4": 293.7, "E4": 329.6, "G4": 392.0, "A4": 440.0, "C5": 523.3, "D5": 587.3, "E5": 659.3, "G5": 784.0}
RIFF = [(0, "A4"), (3, "A4"), (6, "C5"), (8, "A4"), (10, "E5"), (12, "D5"), (14, "C5")]
RIFF2 = [(0, "A4"), (3, "A4"), (6, "C5"), (8, "G4"), (10, "D5"), (12, "C5"), (14, "E5")]
BASS = ["A3", "A3", "F3", "G3"]
BF = {"A3": 55.0, "F3": 43.65, "G3": 49.0, "C3": 65.4}

def bar_t(b): return b * BAR

# ---------- интро (такты 0–1) ----------
for b in (0, 1):
    for st, n in (RIFF if b == 0 else RIFF2): put(cowbell(NOTE[n], bright=.25 + .2 * b), bar_t(b) + st * STEP, .8, -.15)
put(pad([110, 130.8, 164.8], BAR * 2), 0, 1.0)
put(riser(BAR * 1.0), bar_t(1), .9)
for i in range(8): put(hat(), bar_t(1) + BAR * .5 + i * STEP, .3 + i * .08, .2)

# ---------- основной бит ----------
def groove(b, var=0, drums=True):
    t0 = bar_t(b)
    riff = RIFF if (b % 2 == 0) else RIFF2
    for st, n in riff: put(cowbell(NOTE[n]), t0 + st * STEP, .85, -.12)
    if var: put(cowbell(NOTE["G5"], .2), t0 + 15 * STEP, .5, .3)
    bn = BASS[b % 4]
    put(k808(BF[bn]), t0, 1.0); put(k808(BF[bn], .4, BF[bn] * 1.5), t0 + 10 * STEP, .7)
    if not drums: return
    for st in (0, 10): put(kick(), t0 + st * STEP, 1.0)
    put(snare(), t0 + 8 * STEP, 1.0, .05)
    for st in range(16):
        g = .9 if st % 4 == 2 else .55
        put(hat(st == 14), t0 + st * STEP, g, .25)
    if b % 2 == 1:  # трипольная дробь хэтов в конце такта
        for k in range(6): put(hat(), t0 + 12 * STEP + k * (STEP * 4 / 6), .5 + k * .05, .3)

put(impact(), bar_t(2), 1.0)
for b in range(2, 8): groove(b, var=b % 3 == 0)
# такт 8 (фильтры) — брейк: только ковбелл + 808, подъём к игре
groove(8, drums=False); put(riser(BAR), bar_t(8), .9)
for i in range(16): put(snare(), bar_t(8) + BAR * .5 + i * STEP / 2, .15 + i * .035)
put(impact(), bar_t(9), 1.0)
for b in range(9, 11): groove(b, var=True)
# ---------- аутро ----------
for st, n in RIFF: put(cowbell(NOTE[n], bright=.6), bar_t(11) + st * STEP, .8, -.1)
put(k808(BF["A3"], 1.4), bar_t(11), .9)
put(pad([110, 130.8, 164.8], BAR + 1.6), bar_t(11), 1.2)
put(impact(), bar_t(12), .8); put(cowbell(NOTE["A4"], .9), bar_t(12), .9)

# ---------- сведение ----------
mix = np.stack([L, R], 1)
mix = np.tanh(mix * 1.15)  # лёгкая «клиппинговая» плотность, как в фонке
mix /= np.max(np.abs(mix)) + 1e-9; mix *= .93
fade = int(.9 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
out = sys.argv[1] if len(sys.argv) > 1 else "phonk.wav"
with wave.open(out, "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype("<i2").tobytes())
print("готово:", out, round(DUR, 2), "с; такт =", round(BAR, 3), "с")
