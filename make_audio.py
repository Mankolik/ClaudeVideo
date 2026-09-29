"""Synthesizes the 30s soundtrack (96 BPM, Am-F-C-G) with numpy. Writes audio.wav.
Scene boundaries (5, 10, 17.5, 22.5, 27.5s) sit on bar lines: one bar = 2.5s."""
import wave
import numpy as np

SR = 44100
DUR = 30.0
N = int(SR * DUR)
BEAT = 60 / 96
BAR = BEAT * 4
rng = np.random.default_rng(7)
mix = np.zeros((N, 2))


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    sig = sig[: N - i]
    mix[i:i + len(sig), 0] += sig * gain * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * gain * (1 + min(0, pan))


def lp(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += a * (x[i] - s)
        y[i] = s
    return y


def env(n, a=0.005, r=0.2, curve=3.0):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-curve * t / max(r, 1e-3))
    return e


def kick():
    n = int(SR * .45)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 7.5) * np.minimum(1, t / .002)


def clap():
    n = int(SR * .25)
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = noise - lp(noise, 900)  # highpass-ish
    e = np.exp(-t * 22) + .6 * np.exp(-((t - .012) ** 2) / 2e-5) + .6 * np.exp(-((t - .024) ** 2) / 2e-5)
    return noise * e * .5


def hat(open_=False):
    n = int(SR * (.22 if open_ else .05))
    t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    noise = noise - lp(noise, 6000)
    return noise * np.exp(-t * (14 if open_ else 90)) * .35


def pluck(m, dur=.5):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 9) + .2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 14)
    return s * env(n, .003, .16, 3.2) * .5


def bass(m, dur=.55):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .35 * np.sin(4 * np.pi * f * t)
    return np.tanh(s * 1.6) * env(n, .008, .4, 2.2) * .6


def bell(m, dur=1.6):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 3) + .3 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 6)
    return s * env(n, .002, .9, 3.0) * .35


def blip(f0, f1, dur=.12):
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = f0 + (f1 - f0) * (t / dur)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * env(n, .002, dur * .8, 4) * .4


def whoosh(dur, up=True):
    n = int(SR * dur)
    noise = rng.standard_normal(n)
    out = np.empty(n)
    s = 0.0
    for i in range(n):
        p = i / n
        cutoff = 300 + 6500 * (p ** 2 if up else (1 - p) ** 2)
        a = 1 - np.exp(-2 * np.pi * cutoff / SR)
        s += a * (noise[i] - s)
        out[i] = s
    e = np.sin(np.pi * np.linspace(0, 1, n) ** (1.5 if up else .7)) ** 1.5
    return out * e * 2.2


def impact():
    n = int(SR * .9)
    t = np.arange(n) / SR
    f = 70 * np.exp(-t * 2.2) + 32
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.4)
    nz = lp(rng.standard_normal(n), 2500) * np.exp(-t * 9) * .5
    return (s + nz) * .9


# chords: Am - F - C - G (midi notes), 2.5s per bar
CH = [[57, 60, 64], [53, 57, 60], [48, 55, 64], [55, 59, 62]]
ROOT = [33, 29, 36, 31]
ARP = [[57, 64, 60, 69], [53, 60, 57, 65], [55, 60, 64, 67], [55, 62, 59, 67]]

# --- pad (whole length, chord per bar, crossfaded) ---
tt = np.arange(N) / SR
pad = np.zeros(N)
for b in range(int(DUR / BAR) + 1):
    t0, t1 = b * BAR, (b + 1) * BAR
    i0, i1 = int(t0 * SR), min(N, int((t1 + .25) * SR))
    if i0 >= N:
        break
    seg = tt[i0:i1]
    e = np.minimum(1, (seg - t0) / .5) * np.clip((t1 + .25 - seg) / .5, 0, 1)
    for m in CH[b % 4]:
        for det in (-.12, 0, .12):
            f = hz(m + 12) * 2 ** (det / 12)
            pad[i0:i1] += (2 * ((f * seg) % 1) - 1) * e * .05
pad = lp(pad, 1400)
pad *= np.clip(tt / 1.5, 0, 1) * np.clip((DUR - tt) / 1.0, 0, 1)
mix[:, 0] += pad * .8
mix[:, 1] += pad * .8

# --- arp plucks (8ths) from t=1.25, sparse in S1 ---
t = 1.25
step = BEAT / 2
k = 0
while t < 27.5:
    bar = int(t // BAR)
    note = ARP[bar % 4][k % 4]
    vel = .5 if t < 5 else .75
    add(pluck(note + 12 if k % 8 >= 4 else note), t, vel, pan=(-.3 if k % 2 else .3))
    t += step
    k += 1

# --- drums + bass in S2..S5 ---
t = 5.0
while t < 27.5 - 1e-6:
    beat_i = int(round((t - 5.0) / BEAT))
    bar = int(t // BAR)
    add(kick(), t, .85)
    if t >= 10.0 and beat_i % 2 == 1:
        add(clap(), t, .7)
    add(hat(), t + BEAT / 2, .5 if t < 10 else .7)
    if t >= 10.0:
        add(hat(), t, .25)
    if beat_i % 4 == 3:
        add(hat(True), t + BEAT / 2, .35)
    # bass on 1 and the "and" of 2
    if beat_i % 4 == 0:
        add(bass(ROOT[bar % 4]), t, .9)
    if beat_i % 4 == 1:
        add(bass(ROOT[bar % 4] + 12), t + BEAT / 2, .6)
    t += BEAT

# soft intro heartbeat on beats 3/4 of last bar before S2 (riser)
for k in range(4):
    add(kick(), 4.375 + k * BEAT / 4 if k else 3.75, .35 + .1 * k)

# --- transitions: riser into boundary + impact on it ---
for b in [5.0, 10.0, 17.5, 22.5, 27.5]:
    add(whoosh(1.1, True), b - 1.1, .55)
    add(impact(), b, .8)
    add(whoosh(.9, False), b + .05, .35, pan=.3)

# --- scene-specific accents ---
add(blip(300, 900, .25), .2, .5)                       # logo pop
for i in range(6):
    add(blip(900 + i * 60, 1300 + i * 60, .05), 1.1 + i * .09, .18)   # wordmark letter ticks
add(bell(81, 1.4), 2.4, .55)                           # tagline chime
for i in range(12):                                    # bubble pops
    add(blip(500 + (i % 6) * 90, 1000 + (i % 6) * 90, .09), 5.3 + i * .2, .35, pan=-.5 if i % 2 == 0 else .5)
for i in range(10):                                    # counter ticks
    add(blip(1400, 1500, .03), 5.5 + i * .25, .12)
add(bell(88, 1.2), 8.2, .4)                            # counter lands
add(blip(500, 220, .12), 13.0, .7)                     # click
for i in range(14):                                    # score surge
    add(blip(500 + i * 70, 560 + i * 70, .07), 13.05 + i * .11, .22)
add(whoosh(.8, True), 14.5, .4)                        # reorder swoosh
add(bell(84, 1.2), 14.6 + .95, .45)                    # arrives at #1
add(blip(700, 1400, .18), 15.7, .5)                    # badge pop
for i, at in enumerate([.3, 1.0, 1.7, 2.4, 3.0]):      # comments arrive
    add(blip(700 + i * 110, 900 + i * 110, .1), 17.5 + at, .4, pan=.2)
for i, at in enumerate([.7, 1.3, 1.9]):                # ring sweeps
    add(whoosh(1.2, True), 22.5 + at, .25)
    add(bell([72, 76, 79][i], 1.2), 22.5 + at + 1.25, .4)
for i, m in enumerate([69, 72, 76, 81]):               # outro chord
    add(bell(m, 2.4), 27.5 + .05 * i, .5)
add(blip(300, 900, .25), 27.6, .5)

# --- master ---
mix = np.tanh(mix * 1.1)
fade = np.clip((DUR - tt) / .6, 0, 1)
mix *= fade[:, None]
mix *= .89 / np.max(np.abs(mix))
data = (mix * 32767).astype('<i2')
with wave.open('audio.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(data.tobytes())
print('wrote audio.wav', N / SR, 's')
