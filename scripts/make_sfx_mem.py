"""Soft sounds of Elemon (the user found the 8-bit set harsh, 25/10): bells, kalimba, marimba, a music box, soft
pops and airy whooshes, with a little room echo and the top end rounded off. Nothing is sampled; the same file names
as make_sfx_8bit.py, so the game uses them as they are (the 8-bit set is kept in assets/am-thanh/_8bit/).

Writes assets/am-thanh/ (22050 Hz, mono, 16-bit WAV, read by the R36S app and by the browser page):
    nhac/ngay.wav, nhac/dem.wav        room music by day (kalimba over a soft pad) and by night (music box), looping
    sfx/<name>.wav                     one per action
and assets/am-thanh/nghe-thu.wav: everything one after another, to listen to on the PC.
Usage: python make_sfx_mem.py
"""
import os, shutil, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'am-thanh')
RATE = 22050
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def t(dur):
    return np.arange(int(dur * RATE)) / RATE


def env(n, attack=0.004, decay=0.3):
    """Quick rise, then a smooth exponential fall (time constant `decay` seconds)."""
    x = np.arange(n) / RATE
    a = np.clip(x / max(attack, 1e-4), 0, 1)
    return a * np.exp(-x / decay)


def fade(x, ms=12):
    k = min(len(x), int(ms * RATE / 1000))
    if k:
        x[-k:] *= np.linspace(1, 0, k)
    return x


# ---- instruments ----
def bell(m, dur=1.2, vol=0.3, decay=0.5):
    """A small bell: a few inharmonic partials, the high ones dying first."""
    f, x = hz(m), t(dur)
    out = sum(a * np.sin(2 * np.pi * f * r * x) * np.exp(-x / (decay * d))
              for r, a, d in ((1, 1, 1), (2.0, 0.35, 0.6), (2.76, 0.22, 0.35), (5.4, 0.08, 0.15)))
    return fade(out * np.clip(x / 0.003, 0, 1) * vol)


def kalimba(m, dur=0.9, vol=0.3):
    f, x = hz(m), t(dur)
    out = (np.sin(2 * np.pi * f * x) * np.exp(-x / 0.45) + 0.25 * np.sin(2 * np.pi * f * 5.9 * x) * np.exp(-x / 0.05))
    return fade(out * np.clip(x / 0.002, 0, 1) * vol)


def marimba(m, dur=0.6, vol=0.3):
    f, x = hz(m), t(dur)
    out = np.sin(2 * np.pi * f * x) * np.exp(-x / 0.25) + 0.3 * np.sin(2 * np.pi * f * 4 * x) * np.exp(-x / 0.04)
    return fade(out * np.clip(x / 0.002, 0, 1) * vol)


def musicbox(m, dur=1.0, vol=0.25):
    f, x = hz(m), t(dur)
    out = (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(2 * np.pi * f * 3 * x) * np.exp(-x / 0.12)) * np.exp(-x / 0.6)
    return fade(out * np.clip(x / 0.002, 0, 1) * vol)


def pad(ms, dur, vol=0.08):
    """A soft chord: detuned sines that swell in and out."""
    x = t(dur)
    out = sum(np.sin(2 * np.pi * hz(m) * x * d) for m in ms for d in (0.998, 1.002))
    sw = np.sin(np.pi * np.clip(x / dur, 0, 1)) ** 1.5
    return out / (2 * len(ms)) * sw * vol


def pop(f0, f1, dur=0.09, vol=0.3):
    """A soft bubble pop: a sine gliding from f0 to f1."""
    x = t(dur)
    f = f0 * (f1 / f0) ** (x / dur)
    ph = 2 * np.pi * np.cumsum(f) / RATE
    return fade(np.sin(ph) * env(len(x), 0.003, dur / 3) * vol)


def lowpass(x, k=0.15):
    y, a = np.empty_like(x), 0.0
    for i, v in enumerate(x):
        a += k * (v - a); y[i] = a
    return y


def whoosh(dur=0.35, vol=0.25, bright=0.12):
    """Air moving: noise swelling in and out, its brightness rising then falling."""
    n = int(dur * RATE)
    x = rng.standard_normal(n)
    y, a = np.empty(n), 0.0
    for i in range(n):
        k = bright * (0.3 + 0.7 * np.sin(np.pi * i / n)); a += k * (x[i] - a); y[i] = a
    return y * np.sin(np.pi * np.arange(n) / n) ** 2 * vol * 2.5


def thump(f=110, dur=0.18, vol=0.5):
    """A padded knock: a low sine dropping in pitch, with a breath of noise at the start."""
    x = t(dur)
    fr = f * (0.55 + 0.45 * np.exp(-x / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(fr) / RATE) * np.exp(-x / 0.06)
    click = lowpass(rng.standard_normal(len(x)), 0.25) * np.exp(-x / 0.008) * 0.6
    return fade((body + click) * vol)


def at(parts, total=None):
    """Mix (start seconds, sound) pairs."""
    n = int((total or max(s + len(p) / RATE for s, p in parts)) * RATE) + 1
    out = np.zeros(n)
    for s, p in parts:
        i = int(s * RATE); out[i:i + len(p)] += p[:max(0, n - i)]
    return out


def room(x, wet=0.22):
    """A small room: a few soft echoes."""
    out = np.concatenate([x, np.zeros(int(0.35 * RATE))])
    for d, g in ((0.043, 0.5), (0.071, 0.35), (0.113, 0.25), (0.167, 0.15)):
        i = int(d * RATE); out[i:i + len(x)] += x * g * wet / 0.5
    return out


# ---- the sounds of actions ----
def sfx():
    s = {}
    s['menu'] = pop(1500, 1250, 0.05, 0.16)
    s['chon'] = at([(0, kalimba(88, 0.5, 0.26)), (0.07, kalimba(95, 0.6, 0.22))])
    s['quay-lai'] = at([(0, pop(900, 620, 0.1, 0.22)), (0.06, kalimba(79, 0.35, 0.12))])
    s['chuyen'] = whoosh(0.32, 0.12, 0.08)
    s['doi-phong'] = at([(0, whoosh(0.4, 0.13, 0.08)), (0.12, bell(84, 0.8, 0.12))])
    s['doi-pet'] = at([(0, kalimba(76, 0.5, 0.2)), (0.08, kalimba(83, 0.6, 0.2))])
    s['buoc-1'] = thump(160, 0.07, 0.16)
    s['buoc-2'] = thump(140, 0.07, 0.14)
    s['chay'] = at([(0, thump(170, 0.06, 0.15)), (0.11, thump(150, 0.06, 0.13))])
    munch = lambda: lowpass(rng.standard_normal(int(0.05 * RATE)), 0.1) * env(int(0.05 * RATE), 0.002, 0.015) * 0.5
    s['an'] = at([(0, munch()), (0.09, munch()), (0.02, pop(420, 300, 0.08, 0.15))])
    s['vui'] = at([(0, kalimba(84, 0.6, 0.22)), (0.1, kalimba(88, 0.6, 0.22)), (0.2, kalimba(91, 0.8, 0.24))])
    s['thang'] = at([(0, bell(72, 1.4, 0.18)), (0.12, bell(76, 1.4, 0.18)), (0.24, bell(79, 1.4, 0.2)),
                     (0.38, bell(84, 1.8, 0.24)), (0.38, pad([72, 76, 79], 1.6, 0.12))])
    s['dam'] = at([(0, thump(95, 0.22, 0.55)), (0, whoosh(0.08, 0.12, 0.1))])
    s['don-he'] = at([(0, whoosh(0.2, 0.14, 0.2)), (0.05, pop(700, 1100, 0.08, 0.1))])
    s['chieu'] = whoosh(0.28, 0.2, 0.22)
    s['trung-don'] = at([(0, thump(80, 0.25, 0.5)), (0.03, pop(400, 220, 0.18, 0.16))])
    s['guc'] = at([(0, marimba(67, 0.5, 0.25)), (0.18, marimba(64, 0.5, 0.25)), (0.36, marimba(60, 0.9, 0.28))])
    s['ngu'] = at([(0, musicbox(79, 0.9, 0.18)), (0.3, musicbox(76, 0.9, 0.16)), (0.6, musicbox(72, 1.3, 0.16))])
    s['thuc-day'] = at([(0, bell(79, 0.8, 0.16)), (0.12, bell(86, 1.0, 0.18))])
    sigh = lowpass(rng.standard_normal(int(0.5 * RATE)), 0.06) * np.sin(np.pi * np.arange(int(0.5 * RATE)) / int(0.5 * RATE)) * 0.5
    s['met'] = at([(0, sigh), (0, pop(330, 220, 0.45, 0.12))])
    wob = t(0.6); s['om'] = fade(np.sin(2 * np.pi * (220 + 12 * np.sin(2 * np.pi * 5 * wob)) * wob) * env(len(wob), 0.05, 0.3) * 0.18)
    s['no'] = at([(0, thump(60, 0.6, 0.45)), (0, whoosh(0.6, 0.18, 0.1)), (0.05, bell(96, 1.2, 0.1))])
    s['ngay'] = at([(0, bell(84, 1.2, 0.16)), (0.15, bell(91, 1.4, 0.16))])
    s['dem'] = at([(0, bell(79, 1.4, 0.14)), (0.2, bell(74, 1.6, 0.14))])
    s['xu'] = at([(0, bell(88, 0.5, 0.16, 0.25)), (0.07, bell(93, 0.7, 0.18, 0.3))])
    s['loi'] = at([(0, pop(260, 230, 0.12, 0.25)), (0.14, pop(240, 200, 0.14, 0.25))])
    s['sach'] = at([(i * 0.06, bell(m, 0.6, 0.09, 0.25)) for i, m in enumerate((96, 100, 103, 108, 103))])
    s['tien-hoa'] = at([(i * 0.11, bell(m, 1.0, 0.12)) for i, m in enumerate((72, 76, 79, 84, 88, 91, 96))] +
                       [(0, whoosh(1.0, 0.12, 0.08)), (0.3, pad([72, 79, 84], 1.2, 0.1))])
    return {k: room(v) for k, v in s.items()}


# ---- room music ----
def day_theme():
    """84 bpm, 8 bars: a kalimba melody on the C major pentatonic over a slow pad, a soft marimba bass."""
    beat = 60 / 84
    chords = [[60, 64, 67], [57, 60, 64], [65, 69, 72], [67, 71, 74]] * 2
    tune = [(0, 79), (1, 76), (1.5, 79), (2, 81), (3, 79), (4, 76), (5, 74), (6, 72), (7, 74),
            (8, 76), (9, 79), (9.5, 81), (10, 84), (11, 81), (12, 79), (13, 76), (14, 74), (15, 72)]
    parts = []
    for b, ch in enumerate(chords):
        parts.append((b * 2 * beat, pad(ch, 2 * beat + 0.3, 0.09)))
        parts.append((b * 2 * beat, marimba(ch[0] - 12, 0.6, 0.18)))
        parts.append(((b * 2 + 1) * beat, marimba(ch[2] - 12, 0.5, 0.12)))
    for b, m in tune:
        parts.append((b * beat, kalimba(m, 0.9, 0.2)))
    return loop(at(parts, 16 * beat + 1.0), 16 * beat)


def night_theme():
    """60 bpm, 6 bars of 3: a music-box lullaby over a very soft pad."""
    beat = 1.0
    chords = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [57, 60, 64], [53, 57, 60], [52, 55, 59]]
    tune = [(0, 76), (1, 72), (2, 74), (3, 72), (4, 69), (5, 72), (6, 74), (7, 71), (8, 67),
            (9, 76), (10, 72), (11, 74), (12, 72), (13, 69), (14, 65), (15, 64), (16, 67), (17, 69)]
    parts = [(b * 3 * beat, pad(ch, 3 * beat + 0.5, 0.07)) for b, ch in enumerate(chords)]
    parts += [(b * beat, musicbox(m, 1.6, 0.16)) for b, m in tune]
    return loop(at(parts, 18 * beat + 1.5), 18 * beat)


def loop(x, length):
    """Fold the tail back over the start so the music loops without a seam."""
    n = int(length * RATE)
    y = x[:n].copy()
    tail = x[n:]
    y[:len(tail)] += tail[:n]
    return y


def write(path, x, peak=0.6):
    x = np.asarray(x, np.float64)
    m = np.abs(x).max() or 1
    x = np.clip(x / m * peak, -1, 1)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((x * 32767).astype('<i2').tobytes())


# loudness of each kind of sound (the game sets its own volume too): menus quiet, rewards fuller
PEAK = {'menu': 0.35, 'buoc-1': 0.3, 'buoc-2': 0.3, 'chay': 0.35, 'chuyen': 0.35, 'chon': 0.5, 'quay-lai': 0.45}


def main():
    keep = os.path.join(OUT, '_8bit')
    if not os.path.exists(keep):                     # the old 8-bit set, once
        for kind in ('sfx', 'nhac'):
            os.makedirs(os.path.join(keep, kind), exist_ok=True)
            for f in os.listdir(os.path.join(OUT, kind)):
                if f in ('ngay.wav', 'dem.wav') or kind == 'sfx':
                    if f.endswith('.wav'):
                        shutil.copy(os.path.join(OUT, kind, f), os.path.join(keep, kind, f))
    s = sfx()
    for name, x in s.items():
        write(os.path.join(OUT, 'sfx', name + '.wav'), x, PEAK.get(name, 0.6))
    write(os.path.join(OUT, 'nhac', 'ngay.wav'), day_theme(), 0.45)
    write(os.path.join(OUT, 'nhac', 'dem.wav'), night_theme(), 0.4)
    gap = np.zeros(int(0.35 * RATE))
    write(os.path.join(OUT, 'nghe-thu.wav'), np.concatenate([np.concatenate([x, gap]) for x in s.values()] +
                                                            [day_theme()[:int(8 * RATE)], gap, night_theme()[:int(8 * RATE)]]))
    print(f'{len(s)} tiếng + 2 bản nhạc -> {OUT}')


if __name__ == '__main__':
    main()
