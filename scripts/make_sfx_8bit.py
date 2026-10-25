"""8-bit sounds of HoLua, made from scratch the way an NES makes them: pulse waves (12.5/25/50 % duty),
a triangle wave and a noise channel, each note with its own little envelope. Nothing is sampled.

Writes assets/am-thanh/ (22050 Hz, mono, 16-bit WAV, read by the R36S app and usable by any page):
    nhac/ngay.wav, nhac/dem.wav        room music by day and by night, loops seamlessly
    sfx/<name>.wav                     one per action (see SFX), plus menu sounds and footsteps
and assets/am-thanh/nghe-thu.wav: everything one after another, to listen to on the PC.
Usage: python make_sfx_8bit.py
"""
import os, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'am-thanh')
RATE = 22050


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def phase(freq, n):
    """Running phase (cycles) of a tone whose frequency may change every sample."""
    f = np.broadcast_to(np.asarray(freq, np.float64), (n,))
    return np.cumsum(f) / RATE


def pulse(freq, n, duty=0.5):
    return np.where((phase(freq, n) % 1.0) < duty, 1.0, -1.0)


def triangle(freq, n):
    p = phase(freq, n) % 1.0
    # the NES triangle steps through 32 levels: keep the steps, they are the sound
    return np.round((4 * np.abs(p - 0.5) - 1) * 7.5) / 7.5


def noise(n, rate=8000, short=False, seed=1):
    """NES noise: a 15-bit shift register clocked at `rate` Hz (short mode = metallic buzz)."""
    reg, out = seed, np.empty(n)
    step, acc, v = rate / RATE, 0.0, 1.0
    tap = 6 if short else 1
    for i in range(n):
        acc += step
        while acc >= 1.0:
            bit = (reg ^ (reg >> tap)) & 1
            reg = (reg >> 1) | (bit << 14)
            v = 1.0 if reg & 1 else -1.0
            acc -= 1.0
        out[i] = v
    return out


def env(n, attack=0.005, decay=None, sustain=1.0, release=0.02):
    """Linear attack, exponential decay towards `sustain`, linear release at the end."""
    t = np.arange(n) / RATE
    e = np.minimum(1.0, t / max(attack, 1e-4))
    if decay:
        e = e * (sustain + (1 - sustain) * np.exp(-t / decay))
    r = int(release * RATE)
    if 0 < r < n:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def sec(s):
    return max(1, int(s * RATE))


def mix(*parts):
    """Add sounds of different lengths, each placed at (offset seconds, samples)."""
    n = max(sec(o) + len(x) for o, x in parts)
    out = np.zeros(n)
    for o, x in parts:
        out[sec(o):sec(o) + len(x)] += x
    return out


def tone(m, dur, wave='pulse', duty=0.25, vol=0.3, slide=0.0, **e):
    """One note: midi number m (or a frequency in Hz when float < 0), `slide` semitones over the note."""
    n = sec(dur)
    f = hz(m) * 2 ** (np.linspace(0, slide, n) / 12)
    w = triangle(f, n) if wave == 'tri' else pulse(f, n, duty)
    return w * env(n, **e) * vol


def hiss(dur, vol=0.3, rate=8000, rate_end=None, short=False, seed=1, **e):
    n = sec(dur)
    if rate_end:                       # a sweep: rebuild in pieces so the clock can change
        parts, k = [], 16
        for i in range(k):
            r = rate + (rate_end - rate) * i / (k - 1)
            parts.append(noise(n // k + (1 if i < n % k else 0), r, short, seed + i))
        x = np.concatenate(parts)
    else:
        x = noise(n, rate, short, seed)
    return x * env(n, **e) * vol


def seq(notes, beat, **kw):
    """Notes in a row: [(midi or None, beats), ...]."""
    parts, t = [], 0.0
    for m, b in notes:
        if m is not None:
            parts.append((t, tone(m, b * beat * 0.95, **kw)))
        t += b * beat
    return mix(*parts) if parts else np.zeros(sec(t)), t


# ---------------------------------------------------------------- sound effects

def sfx():
    S = {}
    S['menu'] = tone(84, 0.045, duty=0.25, vol=0.25, release=0.01)
    S['chon'] = mix((0, tone(79, 0.06, vol=0.25)), (0.06, tone(86, 0.09, vol=0.25, decay=0.05)))
    S['quay-lai'] = mix((0, tone(79, 0.06, vol=0.22)), (0.06, tone(72, 0.09, vol=0.22, decay=0.05)))
    S['doi-phong'] = mix(*[(i * 0.035, tone(m, 0.05, duty=0.125, vol=0.2)) for i, m in enumerate((72, 76, 79, 84, 88))])
    S['doi-pet'] = tone(70, 0.14, duty=0.5, vol=0.22, slide=14, decay=0.06)
    S['buoc-1'] = hiss(0.035, vol=0.18, rate=1800, decay=0.008, release=0.005)
    S['buoc-2'] = hiss(0.035, vol=0.15, rate=2200, seed=7, decay=0.008, release=0.005)
    S['chay'] = hiss(0.025, vol=0.16, rate=4200, seed=3, decay=0.006, release=0.004)
    S['an'] = mix(*[(i * 0.13, hiss(0.07, vol=0.3, rate=3000 + 900 * i, short=False, seed=i + 2, decay=0.03))
                    for i in range(3)], (0.4, tone(76, 0.08, vol=0.15)), (0.48, tone(81, 0.12, vol=0.15, decay=0.06)))
    S['vui'] = mix(*[(i * 0.07, tone(m, 0.09, duty=0.25, vol=0.22, decay=0.08)) for i, m in enumerate((72, 76, 79, 84, 79, 84, 88))])
    S['thang'], _ = seq([(67, 0.5), (72, 0.5), (76, 0.5), (79, 1), (76, 0.5), (79, 2.5)], 0.11, duty=0.5, vol=0.2, decay=0.25, sustain=0.5)
    S['thang'] = mix((0, S['thang']), (0, seq([(55, 1.5), (60, 1.5), (64, 2.5)], 0.11, wave='tri', vol=0.3)[0]))
    S['dam'] = mix((0, hiss(0.09, vol=0.4, rate=9000, rate_end=2000, decay=0.03)), (0, tone(60, 0.1, duty=0.5, vol=0.2, slide=-12, decay=0.04)))
    S['don-he'] = mix((0, hiss(0.12, vol=0.38, rate=6000, rate_end=1200, decay=0.05)),
                      (0.02, tone(52, 0.18, duty=0.5, vol=0.25, slide=-16, decay=0.08)))
    # a charge rising, then the blast
    S['chieu'] = mix((0, tone(48, 0.45, duty=0.125, vol=0.15, slide=24, attack=0.2)),
                     (0, hiss(0.45, vol=0.12, rate=1500, rate_end=12000, attack=0.3)),
                     (0.45, hiss(0.5, vol=0.45, rate=7000, rate_end=500, decay=0.15)),
                     (0.45, tone(40, 0.4, wave='tri', vol=0.4, slide=-10, decay=0.15)))
    S['trung-don'] = mix((0, hiss(0.06, vol=0.35, rate=5000, decay=0.02)), (0.02, tone(64, 0.2, duty=0.5, vol=0.22, slide=-9, decay=0.1)))
    S['guc'] = mix((0, tone(67, 0.7, duty=0.25, vol=0.2, slide=-24, decay=0.4)), (0.6, hiss(0.25, vol=0.25, rate=900, decay=0.1)))
    S['ngu'] = mix(*[(i * 0.32, tone(m, 0.3, wave='tri', vol=0.3, decay=0.2)) for i, m in enumerate((79, 76, 72))],
                   *[(1.0 + i * 0.18, tone(m, 0.12, duty=0.125, vol=0.07, decay=0.06)) for i, m in enumerate((84, 86, 88))])
    S['thuc-day'] = mix(*[(i * 0.1, tone(m, 0.12, wave='tri', vol=0.3, decay=0.1)) for i, m in enumerate((72, 76, 79, 84))])
    S['met'] = tone(64, 0.5, duty=0.125, vol=0.18, slide=-5, decay=0.3)
    S['om'] = mix(*[(i * 0.16, tone(m, 0.15, duty=0.125, vol=0.16, slide=-2, decay=0.08)) for i, m in enumerate((66, 65, 63))])
    S['no'] = mix((0, hiss(0.08, vol=0.3, rate=7000, decay=0.03)), (0.08, S['vui']))
    S['ngay'] = mix(*[(i * 0.09, tone(m, 0.35, wave='tri', vol=0.28, decay=0.15)) for i, m in enumerate((72, 79, 84, 91))])
    S['dem'] = mix(*[(i * 0.11, tone(m, 0.4, wave='tri', vol=0.28, decay=0.2)) for i, m in enumerate((84, 79, 75, 72))])
    # the game's own moments (the R36S build of the test page, r36s/js/am-thanh.js)
    S['xu'] = mix((0, tone(83, 0.06, duty=0.5, vol=0.22)), (0.06, tone(88, 0.28, duty=0.5, vol=0.22, decay=0.12)))
    S['loi'] = mix((0, tone(57, 0.09, duty=0.25, vol=0.22)), (0.1, tone(53, 0.16, duty=0.25, vol=0.22, decay=0.1)))
    S['sach'] = mix(*[(i * 0.05, tone(m, 0.09, wave='tri', vol=0.22, decay=0.05)) for i, m in enumerate((88, 91, 95, 100, 95, 100, 103))])
    S['chuyen'] = hiss(0.28, vol=0.1, rate=1200, rate_end=9000, attack=0.1, release=0.12)
    S['tien-hoa'] = mix((0, tone(48, 1.0, duty=0.125, vol=0.16, slide=36, attack=0.3, release=0.1)),
                        (0, tone(55, 1.0, duty=0.25, vol=0.08, slide=36, attack=0.4, release=0.1)),
                        (0.2, hiss(0.8, vol=0.1, rate=2000, rate_end=14000, attack=0.4)))
    return S


# ---------------------------------------------------------------- music

def drums(bars, beat, kick_beats=(0, 2), hat=True, vol=1.0):
    parts = []
    for b in range(bars):
        for q in range(4):
            t = (b * 4 + q) * beat
            if q in kick_beats:
                parts.append((t, tone(45, 0.12, wave='tri', vol=0.35 * vol, slide=-14, decay=0.05)))
            if hat:
                parts.append((t + beat / 2, hiss(0.03, vol=0.06 * vol, rate=11000, short=True, decay=0.01)))
    return parts


def loop_len(x, n):
    """Exactly n samples: cut, or pad with silence, so the loop point lands on the bar."""
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros(n - len(x))])


def day_theme():
    bpm = 132
    beat = 60 / bpm
    e = 0.5
    lead = [76, 79, 84, 79, 76, 79, 81, 79,  81, 84, 88, 84, 81, 79, 76, 79,
            77, 81, 84, 81, 77, 81, 84, 86,  86, 83, 79, 83, 86, None, 79, 83,
            84, 88, 91, 88, 84, 79, 76, 79,  88, 86, 84, 81, 84, None, 81, 79,
            77, 81, 84, 81, 79, 83, 86, 83]
    tail = [(84, 1), (79, 0.5), (76, 0.5), (72, 1), (None, 1)]
    mel, _ = seq([(m, e) for m in lead] + tail, beat, duty=0.25, vol=0.16, decay=0.18, sustain=0.45)
    roots = [48, 45, 41, 43, 48, 45, (41, 43), 48]
    bass_notes = []
    for r in roots:
        if isinstance(r, tuple):
            bass_notes += [(r[0], 1), (r[0] + 12, 1), (r[1], 1), (r[1] + 12, 1)]
        else:
            bass_notes += [(r, 1), (r + 12, 1), (r + 7, 1), (r + 12, 1)]
    bass, _ = seq(bass_notes, beat, wave='tri', vol=0.3, decay=0.2, sustain=0.6)
    n = sec(32 * beat)
    return loop_len(mix((0, mel), (0, bass), *drums(8, beat)), n)


def night_theme():
    bpm = 84
    beat = 60 / bpm
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62), (57, 60, 64), (53, 57, 60), (50, 53, 57), (52, 56, 59)]
    arp = []
    for c in chords:
        arp += [(c[0], 0.5), (c[1], 0.5), (c[2], 0.5), (c[1] + 12, 0.5), (c[2], 0.5), (c[1], 0.5), (c[0] + 12, 0.5), (c[1], 0.5)]
    arps, _ = seq(arp, beat, duty=0.125, vol=0.06, decay=0.12, sustain=0.2)
    lead = [(76, 2), (72, 1), (74, 1), (77, 2), (76, 1), (72, 1), (76, 3), (79, 1), (74, 4),
            (76, 2), (81, 1), (79, 1), (77, 2), (76, 1), (74, 1), (77, 2), (74, 2), (76, 3), (None, 1)]
    mel, _ = seq(lead, beat, wave='tri', vol=0.26, decay=0.6, sustain=0.5, attack=0.02)
    bass, _ = seq([(c[0] - 12, 4) for c in chords], beat, wave='tri', vol=0.18, decay=1.2, sustain=0.4)
    n = sec(32 * beat)
    return loop_len(mix((0, arps), (0, mel), (0, bass), *drums(8, beat, kick_beats=(0,), hat=False, vol=0.6)), n)


def write(path, x, peak=0.7):
    x = np.asarray(x, np.float64)
    m = np.abs(x).max()
    if m > peak:
        x = x * peak / m
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767).astype('<i2').tobytes())


def main():
    S = sfx()
    for name, x in S.items():
        write(os.path.join(OUT, 'sfx', name + '.wav'), x)
    day, night = day_theme(), night_theme()
    write(os.path.join(OUT, 'nhac', 'ngay.wav'), day, peak=0.5)
    write(os.path.join(OUT, 'nhac', 'dem.wav'), night, peak=0.5)
    gap = np.zeros(sec(0.35))
    demo = [day[:sec(8)] * 0.7, gap] + [p for x in S.values() for p in (x, gap)] + [night[:sec(8)] * 0.7]
    write(os.path.join(OUT, 'nghe-thu.wav'), np.concatenate(demo))
    print(f'{len(S)} tiếng + 2 bài nhạc ({len(day) / RATE:.1f} s, {len(night) / RATE:.1f} s) -> {OUT}')


if __name__ == '__main__':
    main()
