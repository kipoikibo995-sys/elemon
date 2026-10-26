"""Combat background music of HoLua: an epic looping battle track, made here from scratch (no samples).

D minor, 140 BPM, 32 bars (~55 s) in four parts: drums + bass, then strings, then brass stabs and the lead tune, then
everything at full power. Taiko and kick drums, an 8th-note bass ostinato, a detuned string pad, brass stabs and a lead,
all in one hall reverb. The reverb tail is folded back onto the start so the loop has no seam.

Writes assets/am-thanh/nhac/chien-dau-8bit.ogg (and .wav). The arena now plays a real orchestral CC0 track instead
(nhac/chien-dau.ogg, from OpenGameArt's "Determined Pursuit"); this one is kept as a chiptune fallback.
Usage: python make_combat_music.py
"""
import os, wave, subprocess
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'am-thanh', 'nhac')
RATE = 22050
BPM = 140
BEAT = 60 / BPM
BARS = 32
rng = np.random.default_rng(3)


def sec(t):
    return int(round(t * RATE))


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def fft_lowpass(x, fc, width=200):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / RATE)
    X *= np.clip(1 - (f - fc) / width, 0, 1)
    return np.fft.irfft(X, len(x))


def fft_band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / RATE)
    X *= ((f >= lo) & (f <= hi))
    return np.fft.irfft(X, len(x))


def saw(f, n, detune=0.0):
    t = np.arange(n) / RATE
    ph = (f * (1 + detune)) * t
    return 2 * (ph % 1) - 1


def adsr(n, a=0.01, d=0.1, s=0.7, r=0.1):
    e = np.full(n, s)
    A, D, R = sec(a), sec(d), sec(r)
    e[:A] = np.linspace(0, 1, A) if A else e[:A]
    e[A:A + D] = np.linspace(1, s, len(e[A:A + D]))
    if R: e[-R:] *= np.linspace(1, 0, len(e[-R:]))
    return e


TOTAL = sec(BARS * 4 * BEAT)
TAIL = sec(2.5)
track = {k: np.zeros(TOTAL + TAIL) for k in ('drum', 'bass', 'pad', 'brass', 'lead')}


def put(part, t, x, gain=1.0):
    i = sec(t); m = min(len(x), len(track[part]) - i)
    if m > 0: track[part][i:i + m] += x[:m] * gain


# --- instruments ---
def kick():
    n = sec(0.35); t = np.arange(n) / RATE
    f = 45 + 90 * np.exp(-t / 0.04)
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t / 0.12) * 2.5)


def taiko(p=1.0):
    n = sec(0.7); t = np.arange(n) / RATE
    f = (60 + 50 * np.exp(-t / 0.05)) * p
    body = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-t / 0.25)
    skin = fft_band(rng.uniform(-1, 1, n), 100, 1200) * np.exp(-t / 0.03) * 0.6
    return np.tanh((body + skin) * 2)


def snare():
    n = sec(0.25); t = np.arange(n) / RATE
    nz = fft_band(rng.uniform(-1, 1, n), 1200, 7000) * np.exp(-t / 0.07)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)
    return nz * 0.9 + tone * 0.6


def hat():
    n = sec(0.06); t = np.arange(n) / RATE
    return fft_band(rng.uniform(-1, 1, n), 6000, 10000) * np.exp(-t / 0.015)


def bass_note(m, dur):
    n = sec(dur)
    x = saw(hz(m), n) + 0.6 * saw(hz(m - 12), n)
    return fft_lowpass(x, 700) * adsr(n, 0.005, 0.08, 0.6, 0.03)


def pad_chord(ms, dur):
    n = sec(dur); x = np.zeros(n)
    for m in ms:
        for d in (-0.004, 0.0, 0.005):
            x += saw(hz(m), n, d)
    x = fft_lowpass(x, 1600, 600)
    return x / len(ms) / 3 * adsr(n, 0.35, 0.2, 0.85, 0.4)


def brass(ms, dur):
    n = sec(dur); x = np.zeros(n); t = np.arange(n) / RATE
    for m in ms:
        x += saw(hz(m), n) + saw(hz(m), n, 0.003)
    bright = fft_lowpass(x, 3000, 1500) * np.exp(-t / 0.18) + fft_lowpass(x, 900, 400) * (1 - np.exp(-t / 0.18))
    return bright / len(ms) * adsr(n, 0.02, 0.1, 0.8, 0.08)


def lead(m, dur):
    n = sec(dur); t = np.arange(n) / RATE
    f = hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.25, 0, 1))
    ph = np.cumsum(f) / RATE
    x = np.where(ph % 1 < 0.35, 1.0, -1.0) * 0.6 + (2 * (ph % 1) - 1) * 0.4
    return fft_lowpass(x, 3500, 1500) * adsr(n, 0.02, 0.1, 0.8, 0.06)


# --- the score ---
# chords per bar (i - VI - VII - v in D minor, then i - VI - iv - V), 8 bars, repeated
PROG = [('D', [50, 53, 57]), ('Bb', [46, 50, 53]), ('C', [48, 52, 55]), ('A', [45, 48, 52]),
        ('D', [50, 53, 57]), ('Bb', [46, 50, 53]), ('G', [43, 46, 50]), ('A', [45, 49, 52])]
ROOT_OF = {'D': 38, 'Bb': 34, 'C': 36, 'A': 33, 'G': 31}
# lead tune, 8 bars, (midi, beats); 0 = rest
TUNE = [(74, 1.5), (72, 0.5), (74, 1), (77, 1), (76, 1.5), (74, 0.5), (72, 2),
        (70, 1.5), (72, 0.5), (74, 1), (70, 1), (69, 3), (0, 1),
        (74, 1.5), (72, 0.5), (74, 1), (79, 1), (77, 1.5), (76, 0.5), (74, 2),
        (70, 1), (74, 1), (79, 1), (77, 1), (76, 2), (73, 2)]

K, TK, SN, HT = kick(), taiko(), snare(), hat()
for bar in range(BARS):
    sect = bar // 8                            # 0: drums+bass, 1: +strings, 2: +brass+lead, 3: everything, harder
    t0 = bar * 4 * BEAT
    name, ch = PROG[bar % 8]
    # drums
    for b in range(4):
        put('drum', t0 + b * BEAT, K, 0.9 if b in (0, 2) else 0.5)
        if b in (1, 3): put('drum', t0 + b * BEAT, SN, 0.55 if sect else 0.35)
    for e in range(8):
        put('drum', t0 + e * BEAT / 2, HT, 0.25 if e % 2 else 0.15)
    put('drum', t0, TK, 0.9)
    if sect >= 1: put('drum', t0 + 2.5 * BEAT, taiko(1.2), 0.6)
    if sect == 3:
        for e in (3, 3.5): put('drum', t0 + e * BEAT, taiko(0.9), 0.7)
    if bar % 8 == 7:                          # fill into the next part
        for e in range(4): put('drum', t0 + (2 + e * 0.5) * BEAT, taiko(1 + e * 0.1), 0.7)
    # bass ostinato: root on 8ths with an octave jump
    r = ROOT_OF[name]
    for e in range(8):
        put('bass', t0 + e * BEAT / 2, bass_note(r + (12 if e in (3, 7) else 0), BEAT / 2 * 0.9), 0.55)
    # strings
    if sect >= 1: put('pad', t0, pad_chord([m + 12 for m in ch], 4 * BEAT), 0.5)
    # brass stabs on 1 and the and-of-2
    if sect >= 2:
        for b in (0, 1.5): put('brass', t0 + b * BEAT, brass(ch, BEAT * 0.45), 0.45)
        if sect == 3 and bar % 2: put('brass', t0 + 3 * BEAT, brass([m + 12 for m in ch], BEAT * 0.9), 0.35)
# lead tune over parts 2 and 3
for start_bar in (16, 24):
    t = start_bar * 4 * BEAT
    for m, d in TUNE:
        if m: put('lead', t, lead(m, d * BEAT * 0.95), 0.3 if start_bar == 16 else 0.38)
        t += d * BEAT


def reverb(x, size=2.0, wet=0.25):
    n = sec(size)
    ir = fft_lowpass(rng.uniform(-1, 1, n), 5000, 2000) * np.exp(-np.arange(n) / (n / 5))
    L = 1 << (len(x) + n).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x)]
    y /= np.abs(y).max() + 1e-9
    return x / (np.abs(x).max() + 1e-9) * (1 - wet) + y * wet


mixd = (reverb(track['drum'], 1.2, 0.2) * 0.9 + track['bass'] * 0.7 + reverb(track['pad'], 2.5, 0.4) * 0.55
        + reverb(track['brass'], 2.0, 0.3) * 0.5 + reverb(track['lead'], 2.0, 0.3) * 0.45)
# fold the tail onto the start: a seamless loop
loop = mixd[:TOTAL].copy(); loop[:TAIL] += mixd[TOTAL:TOTAL + TAIL]
loop = np.tanh(loop / (np.abs(loop).max() + 1e-9) * 1.6) / np.tanh(1.6) * 0.85

os.makedirs(OUT, exist_ok=True)
wav = os.path.join(OUT, 'chien-dau-8bit.wav')
with wave.open(wav, 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
    w.writeframes((loop * 32767).astype(np.int16).tobytes())
ogg = wav[:-4] + '.ogg'
subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', wav, '-c:a', 'libvorbis', '-q:a', '4', ogg], check=True)
print('ok', round(TOTAL / RATE, 1), 's', os.path.getsize(ogg) // 1024, 'KB')
