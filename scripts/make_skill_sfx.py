"""Combat skill sounds of HoLua: one set per element (hoa, moc, thuy, tho, kim), one sound per kind of skill.

Hits and thuds come from Kenney's CC0 packs (Impact Sounds, RPG Audio) in assets/am-thanh/_kenney/wav/ (22050 Hz mono,
converted from the packs' .ogg with ffmpeg); the element's own colour (fire roar and crackle, water splash and bubbles,
leaf rustle, rock rumble, metal ring) is made here from filtered noise and tones, then layered on top.

Writes assets/am-thanh/chieu/<he>_<loai>.ogg (and .wav next to it for the R36S app), plus chieu/nghe-thu.wav with
everything one after another to listen to on the PC.
Also chieu/pet/<pet dir>_{j,k,l,gong,ult}: each pet's own set, the element's sound with the pet's real cry (CC0
creature packs, see PET_CRY) on top; and chieu/fight + chieu/ko, the announcer at the start and the end of a round.
    loai: danh (basic attack swing), ban (a shot leaves), trung (a hit lands), vung (an area / burst / field),
          luot (dash / leap), khien (shield / buff / guard), gong (ultimate charging), ult (ultimate lands),
          nang (a heavy hit: stun, knock-up, big shot)
Usage: python make_skill_sfx.py
"""
import json, os, wave, subprocess
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEN = os.path.join(ROOT, 'assets', 'am-thanh', '_kenney', 'wav')
OUT = os.path.join(ROOT, 'assets', 'am-thanh', 'chieu')
RATE = 22050
rng = np.random.default_rng(7)


def sec(t):
    return int(t * RATE)


def load(name):
    with wave.open(os.path.join(KEN, name + '.wav')) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return a / (np.abs(a).max() + 1e-9)


def fir(lo, hi, taps=255):
    """Windowed-sinc band-pass (lo=0: low-pass, hi=None: high-pass)."""
    n = np.arange(taps) - taps // 2
    def lp(fc):
        h = np.sinc(2 * fc / RATE * n) * 2 * fc / RATE
        return h * np.hamming(taps)
    h = lp(hi) if hi else np.zeros(taps)
    if not hi:
        h[taps // 2] = 1
    if lo:
        h = h - lp(lo)
    return h


def filt(x, lo, hi):
    return np.convolve(x, fir(lo, hi), 'same')


def env(n, a=0.005, d=0.3, curve=3.0):
    """Attack then exponential-ish decay over n samples."""
    t = np.arange(n) / RATE
    up = np.clip(t / max(a, 1e-4), 0, 1)
    down = np.clip(1 - (t - a) / max(d, 1e-4), 0, 1) ** curve
    return up * np.where(t < a, 1, down)


def noise(n):
    return rng.uniform(-1, 1, n)


def whoosh(dur=0.25, f0=300, f1=2500, gain=1.0):
    """Air swish: noise through a band-pass whose centre sweeps, done in short overlapping slices."""
    n = sec(dur); out = np.zeros(n); src = noise(n + 600); step = 256
    for i in range(0, n, step):
        k = i / n; fc = f0 + (f1 - f0) * k
        seg = filt(src[i:i + step + 600], fc * 0.6, fc * 1.4)[300:300 + step]
        out[i:i + step] += seg[:len(out[i:i + step])]
    shape = np.sin(np.linspace(0, np.pi, n)) ** 1.5
    return out * shape * gain


def fire(dur=0.6, gain=1.0):
    n = sec(dur)
    roar = filt(noise(n), 60, 900) * 2.5
    crack = np.zeros(n)
    for p in rng.integers(0, n - 200, int(dur * 60)):
        crack[p:p + 60] += noise(60) * np.exp(-np.arange(60) / 10) * rng.uniform(0.3, 1)
    crack = filt(crack, 1500, None)
    return (roar + crack * 1.2) * env(n, 0.03, dur, 1.6) * gain


def water(dur=0.5, bubbles=8, gain=1.0):
    n = sec(dur)
    splash = filt(noise(n), 400, 5000) * env(n, 0.005, dur * 0.6, 2.5)
    b = np.zeros(n)
    for _ in range(bubbles):
        L = sec(rng.uniform(0.03, 0.07)); p = rng.integers(0, max(1, n - L)); L = min(L, n - p); f = rng.uniform(400, 1300)
        t = np.arange(L) / RATE
        b[p:p + L] += np.sin(2 * np.pi * (f * t + 2500 * t * t)) * np.exp(-t / 0.02) * 0.6
    return (splash + b) * gain


def leaves(dur=0.5, gain=1.0):
    n = sec(dur)
    rust = filt(noise(n), 2000, 8000)
    grain = np.repeat(rng.uniform(0.2, 1, n // 400 + 1), 400)[:n]
    return rust * grain * env(n, 0.02, dur, 1.5) * gain * 1.4


def rumble(dur=0.7, gain=1.0):
    n = sec(dur)
    low = filt(noise(n), 25, 220) * 4
    grit = filt(noise(n), 800, 3000) * np.repeat(rng.uniform(0, 1, n // 300 + 1) ** 3, 300)[:n] * 0.8
    return (low + grit) * env(n, 0.01, dur, 1.4) * gain


def ring(dur=0.8, f=1400, gain=1.0):
    """Metal: a few inharmonic partials with slow decay."""
    n = sec(dur); t = np.arange(n) / RATE; out = np.zeros(n)
    for r, a in ((1, 1), (2.76, 0.6), (5.4, 0.4), (8.93, 0.25)):
        out += np.sin(2 * np.pi * f * r * t) * a * np.exp(-t / (dur * 0.35 / r ** 0.3))
    return out * gain * 0.5


def tone_rise(dur=1.0, f0=150, f1=900, gain=1.0):
    """The charge-up swell under every ultimate."""
    n = sec(dur); t = np.arange(n) / RATE
    f = f0 * (f1 / f0) ** (t / dur)
    ph = np.cumsum(f) / RATE
    s = np.sin(2 * np.pi * ph) + 0.4 * np.sin(4 * np.pi * ph * 1.01)
    return s * (t / dur) ** 1.5 * gain * 0.6


def boom(dur=1.0, f0=110, f1=32, gain=1.0):
    """Sub-bass drop: the chest punch under every big impact."""
    n = sec(dur); t = np.arange(n) / RATE
    f = f1 + (f0 - f1) * np.exp(-t / 0.08)
    s = np.sin(2 * np.pi * np.cumsum(f) / RATE)
    click = filt(noise(sec(0.02)), 0, 3000) * np.exp(-np.arange(sec(0.02)) / 60)
    s[:len(click)] += click * 0.8
    return np.tanh(s * 2.2 * np.exp(-t / (dur * 0.35))) * gain


def debris(dur=0.9, gain=1.0):
    """Small pieces falling after a blast."""
    n = sec(dur); out = np.zeros(n)
    for p in rng.integers(sec(0.05), n - 400, 26):
        L = 300; out[p:p + L] += filt(noise(L + 300), 1200, 6000)[150:150 + L] * np.exp(-np.arange(L) / 50) * rng.uniform(0.2, 0.8)
    return out * np.linspace(1, 0.2, n) * gain


def reverb(x, size=1.2, wet=0.35):
    """Big-room tail: convolve with an exponentially decaying, darkened noise burst."""
    n = sec(size)
    ir = filt(noise(n), 0, 4000) * np.exp(-np.arange(n) / (n / 5))
    ir[0] += 3
    m = len(x) + n - 1; L = 1 << (m - 1).bit_length()          # FFT convolution: the direct one is far too slow here
    y = np.fft.irfft(np.fft.rfft(x, L) * np.fft.rfft(ir, L), L)[:len(x) + n]
    y = y / (np.abs(y).max() + 1e-9)
    dry = np.concatenate([x / (np.abs(x).max() + 1e-9), np.zeros(n)])
    return dry * (1 - wet) + y * wet


def punch(x, drive=1.8):
    """Saturate and level: louder and denser, peaks rounded off."""
    x = x / (np.abs(x).max() + 1e-9)
    return np.tanh(x * drive) / np.tanh(drive)


def mix(*parts):
    n = max(len(p) for _, p in parts)
    out = np.zeros(n)
    for off, p in parts:
        o = sec(off); m = min(len(p), n - o)
        out[o:o + m] += p[:m]
    return out


def K(name, gain=1.0):
    return load(name) * gain


ELEM = {
    'hoa':  dict(tex=lambda d, g=1: fire(d, g), hit='impactPunch_medium_001', heavy='impactPunch_heavy_002', tone=900),
    'moc':  dict(tex=lambda d, g=1: leaves(d, g), hit='impactWood_medium_002', heavy='impactWood_heavy_001', tone=500),
    'thuy': dict(tex=lambda d, g=1: water(d, int(12 * d) + 4, g), hit='impactSoft_medium_001', heavy='impactSoft_heavy_002', tone=700),
    'tho':  dict(tex=lambda d, g=1: rumble(d, g), hit='impactMining_002', heavy='impactPunch_heavy_004', tone=220),
    'kim':  dict(tex=lambda d, g=1: ring(d, 1600, g), hit='impactMetal_medium_001', heavy='impactMetal_heavy_003', tone=1300),
}


def build(he):
    e = ELEM[he]; tex = e['tex']
    s = {}
    s['danh'] = mix((0, whoosh(0.18, 600, 3000, 0.9)), (0.05, tex(0.25, 0.5)))
    s['ban'] = mix((0, whoosh(0.3, 1500, 400, 0.7)), (0, tex(0.35, 0.8)))
    s['trung'] = mix((0, K(e['hit'])), (0, tex(0.3, 0.6)))
    # area / quake / burst: a real thump: sub drop + two heavy impacts + the element blowing out + debris, in a big room
    s['vung'] = punch(reverb(mix((0, boom(0.9, 120, 35, 1.0)), (0, K(e['heavy'], 0.9)), (0.02, K('impactPunch_heavy_001', 0.7)),
                                 (0, tex(1.0, 1.1)), (0.06, debris(0.8, 0.5)), (0, whoosh(0.35, 3000, 300, 0.5))), 1.6, 0.35), 2.0)
    # heavy hit (stuns, knock-ups, big shots landing)
    s['nang'] = punch(reverb(mix((0, boom(0.6, 140, 45, 0.9)), (0, K(e['heavy'])), (0, K('impactPunch_heavy_003', 0.8)),
                                 (0, tex(0.45, 0.8))), 0.6, 0.22), 2.2)
    s['luot'] = mix((0, whoosh(0.28, 400, 2200, 1.0)), (0, tex(0.3, 0.35)))
    s['khien'] = mix((0, tone_rise(0.45, e['tone'] * 0.5, e['tone'], 0.7)), (0, tex(0.5, 0.6)), (0.4, K('metalLatch', 0.4)))
    # ult charge (plays with the cut-in, ~0.9 s): a rising swell, the element building up, a reverse whoosh sucking in
    s['gong'] = punch(reverb(mix((0, tone_rise(0.9, 60, e['tone'], 1.0)), (0, tone_rise(0.9, 30, e['tone'] * 0.5, 0.7)),
                                 (0, tex(0.9, 0.9) * np.linspace(0.2, 1.2, sec(0.9))), (0.25, whoosh(0.65, 200, 4000, 0.9)),
                                 (0, rumble(0.9, 0.4) * np.linspace(0, 1, sec(0.9)))), 0.5, 0.25), 1.8)
    # ult lands: double sub drop, a stack of heavy impacts, the element exploding, a long debris tail in a huge hall
    s['ult'] = punch(reverb(mix((0, boom(1.4, 150, 28, 1.2)), (0.12, boom(1.0, 90, 30, 0.7)), (0, K(e['heavy'])),
                                (0, K('impactPunch_heavy_000', 0.9)), (0.04, K('impactPunch_heavy_002', 0.7)), (0.09, K(e['hit'], 0.6)),
                                (0, rumble(1.6, 0.9)), (0, tex(1.5, 1.4)), (0, whoosh(0.5, 4000, 150, 0.7)),
                                (0.1, debris(1.3, 0.7))), 2.6, 0.4), 2.4)
    return s


# Every pet: element, the kind of voice it has (notes only; the cry itself is picked in PET_CRY), what K and L sound
# like (ban, vung, luot, khien).
PET_SFX = {
    'hoa-ho':        ('hoa', 'roar', 150, 'luot', 'vung'),
    'hoa-quy':       ('hoa', 'growl', 85, 'luot', 'vung'),
    'hoa-ho-cao':    ('hoa', 'yowl', 520, 'ban', 'luot'),
    'viem-long':     ('hoa', 'roar', 95, 'luot', 'ban'),
    'dung-nham-ve':  ('hoa', 'groan', 60, 'vung', 'khien'),
    'hoa-linh':      ('hoa', 'shriek', 650, 'ban', 'vung'),
    'moc-hung':      ('moc', 'roar', 110, 'ban', 'vung'),
    'moc-loc':       ('moc', 'bellow', 320, 'ban', 'khien'),
    'moc-duong':     ('moc', 'yowl', 420, 'luot', 'khien'),
    'moc-tru':       ('moc', 'grunt', 140, 'luot', 'vung'),
    'thu-nhan':      ('moc', 'groan', 55, 'ban', 'khien'),
    'reu-linh':      ('moc', 'chirp', 750, 'vung', 'ban'),
    'diep-linh':     ('moc', 'chirp', 900, 'ban', 'vung'),
    'thuy-long':     ('thuy', 'roar', 125, 'ban', 'khien'),
    'thuy-sa':       ('thuy', 'growl', 105, 'luot', 'vung'),
    'thuy-giai':     ('thuy', 'hiss', 400, 'ban', 'khien'),
    'thuy-chien':    ('thuy', 'shout', 230, 'luot', 'khien'),
    'bao-thuy':      ('thuy', 'bleat', 360, 'ban', 'luot'),
    'thuy-giao':     ('thuy', 'roar', 170, 'vung', 'luot'),
    'tho-nguu':      ('tho', 'bellow', 115, 'ban', 'vung'),
    'tho-tuong':     ('tho', 'trumpet', 380, 'ban', 'vung'),
    'tho-tich':      ('tho', 'hiss', 600, 'ban', 'luot'),
    'thach-nhan':    ('tho', 'groan', 62, 'ban', 'khien'),
    'thanh-tri':     ('tho', 'groan', 75, 'khien', 'vung'),
    'tho-long':      ('tho', 'roar', 88, 'ban', 'vung'),
    'tinh-kim-hiep': ('kim', 'shout', 260, 'ban', 'vung'),
    'kim-te':        ('kim', 'roar', 130, 'ban', 'luot'),
    'kim-giap':      ('kim', 'grunt', 480, 'ban', 'khien'),
    'kim-ung':       ('kim', 'screech', 1700, 'vung', 'luot'),
    'kim-thach-nhan': ('kim', 'groan', 80, 'vung', 'vung'),
    'liem-dao':      ('kim', 'yowl', 460, 'ban', 'luot'),
}


# Real creature cries (CC0 packs "80 CC0 creature SFX" 1 and 2 by rubberduck, OpenGameArt; in
# assets/am-thanh/_cc0-voice/wav/): each pet's big cry (ult) and short cry (skills), and a pitch factor (<1 deeper/bigger).
CRY = os.path.join(ROOT, 'assets', 'am-thanh', '_cc0-voice', 'wav')
PET_CRY = {
    # Checked by measure, not by ear (scripts can't listen): the big cry at least 0.4 s, the short one 0.15-0.45 s; heavy
    # pets get dark cries (low spectral centre), small ones bright; no two pets of one element share a big cry, and a cry
    # shared across elements is pitched apart. Swap by ear on preview/dau-truong/nghe-thu.html.
    'hoa-ho': ('roar_02', 'grunt_04', 1.0),         'hoa-quy': ('grunt_07', 'grunt_02', 0.9),
    'hoa-ho-cao': ('howl', 'barking_02', 1.15),     'viem-long': ('roar_04', 'monster_09', 0.85),
    'dung-nham-ve': ('monster_04', 'grunt_07', 0.8), 'hoa-linh': ('scream_02', 'cute_04', 1.2),
    'moc-hung': ('roar_05', 'grunt_06', 0.9),       'moc-loc': ('misc_09', 'cute_01', 1.1),
    'moc-duong': ('cute_03', 'misc_08', 1.1),       'moc-tru': ('troll_01', 'grunt_05', 1.0),
    'thu-nhan': ('monster_20', 'weird_05', 0.8),    'reu-linh': ('cute_09', 'cute_06', 1.2),
    'diep-linh': ('cute_04', 'cute_05', 1.3),       'thuy-long': ('roar_06', 'monster_06', 0.95),
    'thuy-sa': ('monster_06', 'grunt_08', 1.0),     'thuy-giai': ('alien_03', 'bug_10', 0.9),
    'thuy-chien': ('human_07', 'human_03', 1.0),    'bao-thuy': ('burble_01', 'cute_02', 1.0),
    'thuy-giao': ('monster_07', 'monster_15', 1.1), 'tho-nguu': ('grunt_02', 'grunt_03', 0.9),
    'tho-tuong': ('roar_03', 'troll_03', 1.0),      'tho-tich': ('alien_04', 'bug_13', 1.1),
    'thach-nhan': ('misc_11', 'weird_09', 0.75),    'thanh-tri': ('weird_06', 'weird_04', 0.7),
    'tho-long': ('roar_04', 'monster_12', 0.7),     'tinh-kim-hiep': ('human_02', 'human_05', 0.95),
    'kim-te': ('roar_02', 'troll_01', 0.85),        'kim-giap': ('misc_13', 'cute_08', 1.0),
    'kim-ung': ('scream_01', 'attack_03', 1.15),    'kim-thach-nhan': ('monster_16', 'weird_07', 0.8),
    'liem-dao': ('alien_08', 'bug_05', 1.2),
}


def cry(name, pitch=1.0, gain=1.0):
    """A creature sample, resampled for pitch (higher pitch: shorter), normalised."""
    with wave.open(os.path.join(CRY, name + '.wav')) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64)
    on = np.argmax(np.abs(a) > np.abs(a).max() * 0.08)     # start on the sound itself: no silent lead-in delaying it
    a = a[max(0, on - 40):]
    if pitch != 1.0:
        a = np.interp(np.arange(0, len(a) - 1, pitch), np.arange(len(a)), a)
    return a / (np.abs(a).max() + 1e-9) * gain


def build_pet(name):
    global rng
    he, vk, f0, kk, lk = PET_SFX[name]
    big, small, pitch = PET_CRY[name]
    seed = sum(map(ord, name))
    rng = np.random.default_rng(seed)
    base = build(he)                        # this pet's own random textures of its element's sounds
    e = ELEM[he]
    s = {}
    # casting (on the key press): the element's swing / shot / burst and the pet's short cry, no impact; the impact is
    # its own sound, played when the blow actually lands (trung / nang below)
    s['j'] = punch(mix((0, base['danh']), (0, cry(small, pitch * 1.05, 0.7))), 1.8)
    s['k'] = punch(reverb(mix((0, base[kk]), (0, cry(small, pitch, 0.85))), 0.8, 0.2), 2.0)
    s['l'] = punch(reverb(mix((0, base[lk]), (0, cry(small, pitch * 0.95, 0.85))), 0.8, 0.2), 2.0)
    # landing a blow: the element's impact in this pet's own weight. A Kenney impact picked for it, and the whole sound
    # pitched by its size (f0: its voice; big pets thud low, small ones snap high)
    sz = float(np.clip((f0 / 250) ** 0.3, 0.75, 1.3))
    pick = lambda opts: opts[seed % len(opts)]
    light = pick(['impactPunch_medium_000', 'impactPunch_medium_001', 'impactPunch_medium_002', 'impactPunch_medium_003', 'impactPunch_medium_004'])
    heavy = pick(['impactPunch_heavy_000', 'impactPunch_heavy_001', 'impactPunch_heavy_002', 'impactPunch_heavy_003', 'impactPunch_heavy_004'])
    shift = lambda x: np.interp(np.arange(0, len(x) - 1, sz), np.arange(len(x)), x)
    s['trung'] = punch(shift(mix((0, base['trung']), (0, K(light, 0.6)))), 1.8)
    s['nang'] = punch(shift(mix((0, base['nang']), (0, K(heavy, 0.7)))), 2.0)
    # ult charge: the pet's war cry over the charge-up, deeper and stretched, in a long hall
    s['gong'] = punch(reverb(mix((0, base['gong'] * 0.8), (0.1, cry(big, pitch * 0.92, 1.1))), 2.2, 0.38), 2.2)
    # ult lands: the full cry, doubled an octave down for size, on the blast, very long tail
    s['ult'] = punch(reverb(mix((0, base['ult'] * 0.85), (0, cry(big, pitch, 1.2)), (0, cry(big, pitch * 0.5, 0.55)),
                                (0, boom(1.2, 130, 30, 0.8))), 3.0, 0.42), 2.6)
    # hurt: a short yelp in the pet's own voice (its short cry, higher and clipped), when it takes a hit
    y = cry(small, pitch * 1.3, 1.0)[:sec(0.32)]
    y = y * np.clip(np.linspace(1.4, 0, len(y)), 0, 1)
    s['dau'] = punch(reverb(y, 0.4, 0.15), 2.0)
    # knocked out: the big cry falling away, slowed down
    d = cry(big, pitch * 0.8, 1.0)
    s['nga'] = punch(reverb(d * np.linspace(1, 0.1, len(d)), 1.5, 0.3), 1.6)
    return s


def seamless(x, fade=0.4):
    """Fold the end over the start with a crossfade so the sound loops without a click."""
    f = sec(fade); out = x[:-f].copy()
    out[:f] = out[:f] * np.linspace(0, 1, f) + x[-f:] * np.linspace(1, 0, f)
    return out


def loops():
    """The sound under lasting effects (burning, cracks, whirlpools, fields): one 4 s loop per element."""
    global rng
    rng = np.random.default_rng(11)
    d = 4.4; n = sec(d)
    flat = lambda x: x / (np.abs(x).max() + 1e-9)
    hoa = flat(filt(noise(n), 60, 900)) * 0.8                    # fire: low roar + crackle
    crack = np.zeros(n)
    for p in rng.integers(0, n - 200, 260):
        crack[p:p + 60] += noise(60) * np.exp(-np.arange(60) / 10) * rng.uniform(0.2, 1)
    hoa = hoa + flat(filt(crack, 1500, None)) * 0.7
    tho = flat(filt(noise(n), 25, 200)) * 0.9                    # earth: rumble + stones cracking now and then
    for p in rng.integers(0, n - sec(0.7), 7):
        m = K(rng.choice(['impactMining_000', 'impactMining_001', 'impactMining_003', 'footstep_concrete_002']), rng.uniform(0.3, 0.6))
        tho[p:p + len(m)] += m[:n - p]
    thuy = water(d, 40, 1.0)                                      # water: churning + bubbles
    thuy = flat(thuy + filt(noise(n), 200, 1500) * 0.4)
    moc = flat(leaves(d, 1.0) + filt(noise(n), 400, 2500) * 0.25)  # wood: rustling leaves, creaking
    kim = np.zeros(n)                                              # metal: a shimmering hum with small chimes
    t = np.arange(n) / RATE
    for f, a in ((220, 0.5), (331, 0.3), (587, 0.25)):
        kim += np.sin(2 * np.pi * f * t) * a * (1 + 0.3 * np.sin(2 * np.pi * 0.7 * t))
    for p in rng.integers(0, n - sec(0.6), 6):
        r = ring(0.6, rng.uniform(1800, 2600), 0.4); kim[p:p + len(r)] += r[:n - p]
    out = {he + '_loop': seamless(flat(x) * 0.9) for he, x in (('hoa', hoa), ('tho', tho), ('thuy', thuy), ('moc', moc), ('kim', kim))}

    # one loop per kind of lasting effect (the page picks by field kind; these come on top of the element hums)
    def pops(n, count, f_lo, f_hi, dur_lo, dur_hi, gain):
        x = np.zeros(n)
        for _ in range(count):
            L = sec(rng.uniform(dur_lo, dur_hi)); p = rng.integers(0, n - L); f = rng.uniform(f_lo, f_hi); tt = np.arange(L) / RATE
            x[p:p + L] += np.sin(2 * np.pi * (f * tt + f * 2 * tt * tt)) * np.exp(-tt / (dur_hi * 0.35)) * gain
        return x
    am = lambda rate, depth: 1 - depth * 0.5 * (1 + np.sin(2 * np.pi * rate * t + rng.uniform(0, 6)))
    # lava: a deep roar, thick bubbles bursting, a hiss of steam
    lava = flat(filt(noise(n), 30, 300)) * am(0.4, 0.4) + flat(pops(n, 45, 60, 180, 0.08, 0.2, 1.0)) * 0.8 \
        + flat(filt(noise(n), 3000, 8000)) * am(0.25, 0.8) * 0.25 + flat(filt(crack, 1500, None)) * 0.3
    # big fire zone: a heavier, wider roar than the burn
    biglua = flat(filt(noise(n), 40, 1500)) * am(0.6, 0.35) * 1.0 + flat(filt(crack, 1200, None)) * 0.9
    # mud: slow fat bubbles and squelches
    bun = flat(pops(n, 30, 70, 160, 0.12, 0.3, 1.0)) + flat(filt(noise(n), 80, 500)) * am(0.3, 0.6) * 0.3
    for p in rng.integers(0, n - sec(0.7), 6):
        m = cry(str(rng.choice(['slime_02', 'slime_07', 'slime_08'])), rng.uniform(0.7, 0.9), 0.5); bun[p:p + len(m)] += m[:n - p]
    # stone wall: a low grinding of stone with a few knocks
    da = flat(filt(noise(n), 40, 400)) * am(0.5, 0.5) + flat(filt(noise(n), 600, 2500)) * am(1.3, 0.9) * 0.3
    for p in rng.integers(0, n - sec(0.7), 4):
        m = K(str(rng.choice(['impactMining_000', 'impactPlate_heavy_001', 'footstep_concrete_000'])), 0.35); da[p:p + len(m)] += m[:n - p]
    # whirlpool / vortex: water rushing round and round (a band of noise sweeping up and down twice a second)
    xo = np.zeros(n); src = noise(n + 600); step = 256
    for i in range(0, n, step):
        fc = 700 + 500 * np.sin(2 * np.pi * 2.2 * i / RATE)
        seg = filt(src[i:i + step + 600], fc * 0.5, fc * 1.6)[300:300 + step]; xo[i:i + step] += seg[:len(xo[i:i + step])]
    xoay = flat(xo) + flat(water(d, 30, 1.0)) * 0.5
    # mist: a soft cold hiss that breathes
    suong = flat(filt(noise(n), 2500, 9000)) * am(0.35, 0.7) * 0.8 + flat(filt(noise(n), 300, 1200)) * am(0.2, 0.5) * 0.3
    # roots: wood creaking and leaves stirring
    re = flat(leaves(d, 0.5))
    for p in rng.integers(0, n - sec(1.2), 4):
        m = K(str(rng.choice(['creak1', 'creak2', 'creak3'])), 0.8); re[p:p + len(m)] += m[:n - p]
    for k, x in (('lava', lava), ('lua-lon', biglua), ('bun', bun), ('da', da), ('xoay', xoay), ('suong', suong), ('re', re)):
        out['loop_' + k] = seamless(flat(x) * 0.9)
    return out


def announcer():
    """'Fight!' (Kenney Voiceover Pack Fighter, CC0) and 'K.O.' (Windows TTS 'David', made deep and huge), both in an arena hall."""
    big = lambda a, p: punch(reverb(mix((0, a), (0, np.interp(np.arange(0, len(a) - 1, p), np.arange(len(a)), a) * 0.5)), 1.8, 0.3), 1.6)
    fight = cry('fight', 0.97, 1.0)
    ko = cry('ko_tts', 0.82, 1.0)
    ko = ko[np.argmax(np.abs(ko) > 0.02):]             # trim the silence before the voice
    return {'fight': big(fight, 0.5), 'ko': mix((0, big(ko, 0.5)), (0, boom(1.0, 120, 30, 0.6)))}


def write_wav(path, x):
    x = x / (np.abs(x).max() + 1e-9) * 0.9
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((x * 32767).astype(np.int16).tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    allx = []
    for he in ELEM:
        for loai, x in build(he).items():
            p = os.path.join(OUT, f'{he}_{loai}.wav')
            write_wav(p, x)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', p, '-c:a', 'libvorbis', '-q:a', '3', p[:-4] + '.ogg'], check=True)
            allx += [x / (np.abs(x).max() + 1e-9) * 0.9, np.zeros(sec(0.35))]
    write_wav(os.path.join(OUT, 'nghe-thu.wav'), np.concatenate(allx))
    # one set per pet: <pet dir>_{j,k,l,gong,ult,dau,nga}, with its own voice
    pdir = os.path.join(OUT, 'pet'); os.makedirs(pdir, exist_ok=True); petx = []
    for name in PET_SFX:
        for loai, x in build_pet(name).items():
            p = os.path.join(pdir, f'{name}_{loai}.wav')
            write_wav(p, x)
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', p, '-c:a', 'libvorbis', '-q:a', '3', p[:-4] + '.ogg'], check=True)
            if loai in ('gong', 'ult'): petx += [x / (np.abs(x).max() + 1e-9) * 0.9, np.zeros(sec(0.3))]
    write_wav(os.path.join(pdir, 'nghe-thu-ult.wav'), np.concatenate(petx))
    for loai, x in list(announcer().items()) + list(loops().items()):
        p = os.path.join(OUT, f'{loai}.wav')
        write_wav(p, x)
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', p, '-c:a', 'libvorbis', '-q:a', '3', p[:-4] + '.ogg'], check=True)
    print('ok', len(ELEM) * 9, 'element sounds,', len(PET_SFX) * 9, 'pet sounds')
    # copy the pet sets to the arena page
    with open(os.path.join(pdir, '_cry.json'), 'w', encoding='utf-8') as f:     # for the listening page (nghe-thu.html)
        json.dump({n: {'he': PET_SFX[n][0], 'big': c[0], 'small': c[1], 'pitch': c[2]} for n, c in PET_CRY.items()}, f, indent=1)
    import shutil; dst = os.path.join(ROOT, 'preview', 'dau-truong', 'sfx', 'pet'); os.makedirs(dst, exist_ok=True)
    for fn in os.listdir(pdir):
        if fn.endswith(('.ogg', '.json')): shutil.copy(os.path.join(pdir, fn), dst)


if __name__ == '__main__':
    main()
