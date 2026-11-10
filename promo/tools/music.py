import numpy as np, wave, sys
SR = 44100
DUR = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
BPM = 118
beat = 60 / BPM
N = int(SR * DUR)
out = np.zeros((N, 2))
rng = np.random.default_rng(7)

def add(sig, t, pan=0.0, gain=1.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    out[i:i + len(sig), 0] += sig * (1 - max(0, pan))
    out[i:i + len(sig), 1] += sig * (1 + min(0, pan))

def env(n, a=0.005, r=0.2):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / r)
    return e

def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 18) + 42
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7) * 0.95

def clap():
    n = int(0.25 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    # полосовой «хлопок» через разность сглаживаний
    k1 = np.convolve(noise, np.ones(6) / 6, "same"); k2 = np.convolve(noise, np.ones(40) / 40, "same")
    return (k1 - k2) * np.exp(-t * 18) * 0.6

def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n); hp = noise - np.convolve(noise, np.ones(3) / 3, "same")
    return hp * np.exp(-t * (18 if open_ else 70)) * 0.25

def saw(freq, n):
    t = np.arange(n) / SR
    s = np.zeros(n)
    for k in range(1, 12):
        s += np.sin(2 * np.pi * freq * k * t) / k
    return s * 0.5

def bass(freq, length):
    n = int(length * SR)
    s = saw(freq, n)
    s = np.convolve(s, np.ones(18) / 18, "same")  # мягче
    return s * env(n, 0.004, length * 0.7) * 0.55

def pad(freqs, length):
    n = int(length * SR); t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.003 * t) for f in freqs)
    a = np.minimum(1, t / 0.25) * np.minimum(1, (length - t) / 0.3)
    return s * a * 0.07

def pluck(freq, length=0.22):
    n = int(length * SR); t = np.arange(n) / SR
    s = np.sign(np.sin(2 * np.pi * freq * t)) * 0.5 + np.sin(2 * np.pi * freq * 2 * t) * 0.3
    s = np.convolve(s, np.ones(8) / 8, "same")
    return s * np.exp(-t * 14) * 0.22

note = lambda m: 440 * 2 ** ((m - 69) / 12)
# Am – F – C – G (по такту на аккорд)
chords = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]
arp = [0, 2, 1, 2, 0, 2, 1, 2]

bars = int(DUR / (4 * beat)) + 1
for bar in range(bars):
    t0 = bar * 4 * beat
    root, ch = chords[bar % 4]
    intro = bar == 0
    add(pad([note(m) for m in ch], 4 * beat), t0, 0, 1.0)
    for b in range(4):
        tb = t0 + b * beat
        if not intro or b >= 2: add(kick(), tb, 0, 1.0)
        if b in (1, 3) and not intro: add(clap(), tb, 0.1, 1.0)
        for h in (0, 0.5):
            add(hat(open_=(h == 0.5 and b == 3)), tb + h * beat, -0.3, 1.0)
        if not intro:
            add(bass(note(root - 12), beat * 0.45), tb, 0, 1.0)
            add(bass(note(root - 12), beat * 0.4), tb + 0.5 * beat, 0, 0.8)
    for i in range(8):
        m = ch[arp[i]] + 12
        add(pluck(note(m)), t0 + i * 0.5 * beat, 0.35 if i % 2 else -0.35, 1.0)

# сайдчейн-«качание» от бочки
t = np.arange(N) / SR
duck = 1 - 0.35 * np.exp(-((t % beat) / 0.12))
out[:, 0] *= duck; out[:, 1] *= duck
# фейды
fade_in = np.minimum(1, t / 0.4); fade_out = np.minimum(1, (DUR - t) / 1.5)
out *= (fade_in * fade_out)[:, None]
out /= np.max(np.abs(out)) * 1.12
pcm = (out * 32767).astype(np.int16)
with wave.open("music.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print("ok", DUR)
