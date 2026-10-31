"""Combat skill sounds of HoLua, second take: real recordings instead of sounds made from noise and tones.

The element's own sound comes from CC0 recordings (assets/am-thanh/_cc0-chieu/wav/, found through Openverse, mostly
Freesound; sources in _cc0-chieu/NGUON.txt): fire whooshes, fireballs, bursts, crackling, explosions, a dragon roar,
magic charge-ups and shields. Hits and thuds stay Kenney's CC0 Impact Sounds (assets/am-thanh/_kenney/wav/). Each kind
of sound is a few of those layered: cut to the part that matters (the onset of a hit, the loudest stretch of a whoosh),
shaped, mixed, pressed a little and set to the old set's level (peak 0.9), so the game's balance does not move.

Same names and lengths as scripts/make_skill_sfx.py writes (<he>_<loai>.ogg + .wav, 22050 Hz mono), so the arena and
the regions take them as they are:
    danh (basic attack swing), ban (a shot leaves), trung (a hit lands), nang (a heavy hit), vung (an area burst),
    luot (dash / leap), khien (shield / buff), gong (ultimate charging), ult (ultimate lands)
All five elements (RECIPES).

Usage: python scripts/make_chieu_cc0.py [OUT_DIR]     (default build/thu-giong/chieu-cc0, to listen before replacing;
                                                       pass assets/am-thanh/chieu to replace the game's set)
"""
import os, subprocess, sys, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CC0 = os.path.join(ROOT, 'assets', 'am-thanh', '_cc0-chieu', 'wav')
KEN = os.path.join(ROOT, 'assets', 'am-thanh', '_kenney', 'wav')
RATE = 22050
PEAK = 0.9                      # the old set's level (every sound of it peaks at 0.9)
# the lengths of the old set: the arena times its sounds to them (an ult's blast, a dash)
LEN = {'danh': 0.30, 'ban': 0.45, 'trung': 0.40, 'nang': 1.2, 'vung': 2.6, 'luot': 0.35, 'khien': 0.6, 'gong': 1.4, 'ult': 4.2}


# ---------- reading and cutting ----------
def load(name):
    d = CC0 if os.path.exists(os.path.join(CC0, name + '.wav')) else KEN
    with wave.open(os.path.join(d, name + '.wav')) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
    return a / (np.abs(a).max() + 1e-9)


def n(t):
    return int(round(t * RATE))


def onset(x, db=-24):
    """Where the sound starts: the first sample within db of its peak."""
    th = np.abs(x).max() * 10 ** (db / 20)
    i = np.argmax(np.abs(x) >= th)
    return max(0, i - n(0.004))


def from_onset(x, dur, db=-24):
    i = onset(x, db)
    return x[i:i + n(dur)]


def loudest(x, dur):
    """The loudest stretch of dur seconds (for a whoosh or a roar: its body, not its tail)."""
    w = n(dur)
    if len(x) <= w:
        return x
    e = np.convolve(x ** 2, np.ones(n(0.02)), 'same')
    c = np.cumsum(np.concatenate([[0], e]))
    s = int(np.argmax(c[w:] - c[:-w]))
    return x[s:s + w]


def fades(x, fin=0.004, fout=0.08):
    x = x.copy()
    a, b = min(n(fin), len(x)), min(n(fout), len(x))
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b) ** 1.5
    return x


def place(total, *parts):
    """parts: (sound, start s, gain): laid on a track total seconds long."""
    out = np.zeros(n(total))
    for x, t, g in parts:
        i = n(t)
        m = min(len(x), len(out) - i)
        if m > 0:
            out[i:i + m] += x[:m] * g
    return out


def stretch(x, k):
    """Pitch and speed by k (k < 1: lower, slower), as a tape would."""
    idx = np.arange(0, len(x) - 1, k)
    return np.interp(idx, np.arange(len(x)), x)


def ffmpeg_fx(x, af):
    """Run an ffmpeg audio filter chain over x (high/low-pass, compression)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        a, b = os.path.join(tmp, 'a.wav'), os.path.join(tmp, 'b.wav')
        write_wav(a, x / (np.abs(x).max() + 1e-9) * 0.7)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', a, '-af', af, '-ar', str(RATE), '-ac', '1', b], check=True)
        with wave.open(b) as w:
            return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def write_wav(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def finish(x, dur, lo=40, hi=9500):
    """Cut to length, band-limit, press a little, fade out, set to the old set's peak."""
    x = x[:n(dur)]
    x = np.pad(x, (0, max(0, n(dur) - len(x))))
    x = ffmpeg_fx(x, f'highpass=f={lo},lowpass=f={hi},acompressor=threshold=-18dB:ratio=3:attack=3:release=120:makeup=2')
    x = fades(x[:n(dur)], 0.002, min(0.12, dur * 0.3))
    return x / (np.abs(x).max() + 1e-9) * PEAK


# ---------- the recipes ----------
def hoa():
    L = LEN
    burst, ignite, spray = load('fire-burst-flash'), load('flame-ignite'), load('fire-spray')
    crack, whoosh, calm = load('fire-crackling'), load('fire-whoosh'), load('fire-whoosh-calm')
    fb3, fb2 = load('fireball-3'), load('fireball-2')
    swoosh = load('swoosh-air')
    return {
        # a claw swipe that leaves a flick of flame
        'danh': place(L['danh'], (from_onset(swoosh, 0.3), 0, 0.8), (from_onset(burst, 0.25), 0.04, 0.6)),
        # a fireball leaving: its launch, a little crackle under it
        'ban': place(L['ban'], (from_onset(fb3, 0.45), 0, 1.0), (loudest(crack, 0.45), 0.05, 0.25)),
        # a blow landing: Kenney's punch, the flame's flash and sizzle after it
        'trung': place(L['trung'], (from_onset(load('impactPunch_medium_001'), 0.3), 0, 1.0),
                       (from_onset(burst, 0.38), 0.02, 0.55)),
        # a heavy hit: a heavy punch, a cannon boom lowered, crackling embers trailing
        'nang': place(L['nang'], (from_onset(load('impactPunch_heavy_002'), 0.5), 0, 0.9),
                      (stretch(from_onset(load('cannon-boom7'), 1.1), 0.85), 0.0, 0.8),
                      (loudest(crack, 0.9), 0.25, 0.35)),
        # an area burst: an explosion with debris, a flame burst on its front
        'vung': place(L['vung'], (from_onset(load('explosion-2'), 2.6), 0, 1.0), (from_onset(ignite, 0.9), 0, 0.6),
                      (loudest(crack, 2.0), 0.6, 0.3)),
        # a dash: the loudest stretch of a fire whoosh, short
        'luot': place(L['luot'], (loudest(whoosh, 0.35), 0, 1.0), (from_onset(swoosh, 0.3), 0, 0.4)),
        # a guard / buff: flames catching round the body, the magic shield's block under it
        'khien': place(L['khien'], (from_onset(ignite, 0.6), 0, 0.9), (from_onset(load('magic-shield-block'), 0.6), 0.03, 0.55)),
        # an ultimate charging: a magic charge-up (its rise), flames swelling with it
        'gong': place(L['gong'], (loudest(load('magic-chargeup'), 1.4), 0, 0.8), (loudest(calm, 1.4), 0, 0.55),
                      (loudest(spray, 1.2), 0.2, 0.35)),
        # the ultimate landing: a dragon's roar, the big explosion, a fireball on top, embers fading
        'ult': place(L['ult'], (loudest(load('dragon-roar'), 1.8), 0, 0.75), (from_onset(load('explosion-debris'), 3.6), 0.35, 1.0),
                     (from_onset(fb2, 1.6), 0.3, 0.5), (loudest(crack, 2.4), 1.8, 0.3)),
    }


def thuy():
    L = LEN
    splash, short, splashing = load('water-splash'), load('water-splash-short'), load('water-splashing')
    big, rock_sp, drop = load('big-splash'), load('rock-splash'), load('water-drop-splash')
    bubble, bubbles = load('bubble'), load('bubbles-03')
    swoosh = load('swoosh-air')
    return {
        # a fin's swipe that throws a little water
        'danh': place(L['danh'], (from_onset(swoosh, 0.3), 0, 0.8), (from_onset(short, 0.2), 0.05, 0.6)),
        # a water shot leaving: a quick splash, a bubble on it
        'ban': place(L['ban'], (from_onset(drop, 0.45), 0, 1.0), (from_onset(bubble, 0.35), 0.06, 0.45),
                     (from_onset(swoosh, 0.3), 0, 0.35)),
        # a hit landing: a soft heavy thud, a splash over it
        'trung': place(L['trung'], (from_onset(load('impactSoft_heavy_001'), 0.3), 0, 0.9), (from_onset(splash, 0.4), 0.01, 0.6)),
        # a heavy hit: a big splash lowered, the punch under it, water falling after
        'nang': place(L['nang'], (from_onset(load('impactPunch_heavy_001'), 0.5), 0, 0.8),
                      (stretch(from_onset(big, 1.2), 0.85), 0, 1.0), (loudest(splashing, 0.8), 0.4, 0.3)),
        # an area burst: a rock dropped in deep water, splashing spreading, bubbles rising
        'vung': place(L['vung'], (from_onset(rock_sp, 2.6), 0, 1.0), (loudest(splashing, 2.0), 0.3, 0.45),
                      (from_onset(bubbles, 1.0), 1.2, 0.35)),
        # a dash: a swoosh through a spray
        'luot': place(L['luot'], (from_onset(swoosh, 0.35), 0, 0.9), (loudest(splashing, 0.35), 0, 0.55)),
        # a guard: a bubble shell closing round the body
        'khien': place(L['khien'], (from_onset(bubbles, 0.6), 0, 0.9), (from_onset(load('magic-shield-block'), 0.6), 0.02, 0.5)),
        # an ultimate charging: focused energy, water churning and bubbling up
        'gong': place(L['gong'], (loudest(load('magical-focus'), 1.4), 0, 0.75), (loudest(splashing, 1.4), 0, 0.45),
                      (from_onset(bubbles, 1.0), 0.4, 0.4)),
        # the ultimate landing: a water dragon's roar, a huge splash, the water crashing back down
        'ult': place(L['ult'], (stretch(loudest(load('dragon-roar-1'), 1.6), 0.9), 0, 0.6), (from_onset(big, 1.7), 0.35, 1.0),
                     (from_onset(splash, 3.6), 0.6, 0.8), (loudest(splashing, 2.2), 1.8, 0.4)),
    }


def moc():
    L = LEN
    leaves, bush, rustle, shake = load('leaves-rustling'), load('bush-hit'), load('bush-rustle'), load('tree-shake')
    branch, twig, crack = load('branch-crack'), load('twig-snap'), load('wood-crack-4')
    wind, swoosh = load('wind-gust'), load('swoosh-air')
    return {
        # a swipe through leaves
        'danh': place(L['danh'], (from_onset(swoosh, 0.3), 0, 0.8), (from_onset(rustle, 0.28), 0.02, 0.6)),
        # a seed / thorn shot: a twig's snap, a whoosh
        'ban': place(L['ban'], (from_onset(twig, 0.2), 0, 1.0), (from_onset(swoosh, 0.4), 0.02, 0.6), (from_onset(rustle, 0.4), 0.05, 0.3)),
        # a hit landing: a wooden thud, leaves shaken by it
        'trung': place(L['trung'], (from_onset(load('impactWood_heavy_001'), 0.3), 0, 0.9), (from_onset(bush, 0.4), 0.02, 0.6)),
        # a heavy hit: a branch cracking, a heavy wooden thud, the tree shaking
        'nang': place(L['nang'], (from_onset(load('impactWood_heavy_003'), 0.5), 0, 0.8), (from_onset(crack, 1.2), 0.03, 0.9),
                      (from_onset(shake, 1.1), 0.15, 0.5)),
        # an area burst: roots bursting from the ground, branches cracking, leaves storming
        'vung': place(L['vung'], (stretch(from_onset(load('impactMining_002'), 0.5), 0.8), 0, 0.7),
                      (from_onset(branch, 1.5), 0.05, 0.9), (loudest(leaves, 2.4), 0.2, 0.6), (from_onset(crack, 1.4), 0.9, 0.5)),
        # a dash: a gust through leaves
        'luot': place(L['luot'], (loudest(wind, 0.35), 0, 0.7), (from_onset(rustle, 0.35), 0, 0.7)),
        # a guard: bark closing round the body, leaves settling
        'khien': place(L['khien'], (from_onset(load('impactWood_medium_002'), 0.3), 0, 0.7), (from_onset(shake, 0.6), 0.02, 0.7),
                       (from_onset(load('magic-shield-block'), 0.6), 0.03, 0.4)),
        # an ultimate charging: the forest's energy gathering, wind rising through the leaves
        'gong': place(L['gong'], (loudest(load('magical-focus'), 1.4), 0, 0.7), (loudest(wind, 1.4), 0, 0.5),
                      (loudest(leaves, 1.4), 0, 0.5)),
        # the ultimate landing: a great tree's crack and crash, roots and branches, leaves falling
        'ult': place(L['ult'], (from_onset(crack, 1.5), 0, 0.9), (stretch(from_onset(load('impactWood_heavy_000'), 0.6), 0.7), 0.3, 1.0),
                     (from_onset(branch, 1.5), 0.5, 0.8), (loudest(leaves, 3.2), 0.6, 0.6), (loudest(wind, 3.0), 0.8, 0.35)),
    }


def tho():
    L = LEN
    crumble, hit, impact = load('rock-crumble'), load('rock-hit-dirt'), load('rock-impact')
    quake, decay, boulder = load('quake-break'), load('stone-impact-decay'), load('boulder-push')
    brick, gravel, swoosh = load('brick-on-soil'), load('gravel-step'), load('swoosh-air')
    return {
        # a stone fist's swing: a heavy whoosh, grit
        'danh': place(L['danh'], (stretch(from_onset(swoosh, 0.35), 0.85), 0, 0.85), (from_onset(gravel, 0.3), 0.04, 0.5)),
        # a rock thrown: a heavy launch, gravel off it
        'ban': place(L['ban'], (from_onset(load('impactMining_000'), 0.3), 0, 0.7), (stretch(from_onset(swoosh, 0.4), 0.8), 0.02, 0.7),
                     (from_onset(gravel, 0.4), 0.05, 0.4)),
        # a hit landing: rock on rock
        'trung': place(L['trung'], (from_onset(impact, 0.4), 0, 1.0), (from_onset(load('impactPunch_heavy_000'), 0.3), 0, 0.5)),
        # a heavy hit: a boulder's slam, its long stone decay, dirt falling
        'nang': place(L['nang'], (from_onset(load('impactMining_003'), 0.6), 0, 0.9), (stretch(from_onset(impact, 0.8), 0.8), 0, 1.0),
                      (from_onset(hit, 1.2), 0.05, 0.7), (loudest(crumble, 0.9), 0.3, 0.5)),
        # an area burst: the earth breaking, rocks crumbling round it
        'vung': place(L['vung'], (from_onset(quake, 2.6), 0, 1.0), (loudest(crumble, 2.2), 0.3, 0.6), (from_onset(brick, 1.2), 0.1, 0.5)),
        # a dash: a heavy rush, gravel under the feet
        'luot': place(L['luot'], (stretch(from_onset(swoosh, 0.4), 0.85), 0, 0.8), (from_onset(gravel, 0.35), 0.02, 0.7)),
        # a guard: stone plates closing, grinding into place
        'khien': place(L['khien'], (from_onset(impact, 0.4), 0, 0.8), (loudest(boulder, 0.6), 0.05, 0.6)),
        # an ultimate charging: the ground rumbling, stones grinding, energy rising
        'gong': place(L['gong'], (loudest(boulder, 1.4), 0, 0.8), (loudest(quake, 1.4), 0, 0.6), (loudest(load('magical-focus'), 1.4), 0, 0.35)),
        # the ultimate landing: an earthquake's break, a boulder's slam, rocks raining down
        'ult': place(L['ult'], (from_onset(quake, 4.2), 0, 1.0), (from_onset(decay, 2.3), 0.3, 0.8),
                     (stretch(from_onset(hit, 1.4), 0.8), 0.35, 0.6), (loudest(crumble, 3.0), 1.2, 0.5)),
    }


def kim():
    L = LEN
    clang, clash, fast, swings = load('sword-clang'), load('sword-clash'), load('sword-swing-fast'), load('sword-swings')
    unsheath, impact, heavy, hard = load('sword-unsheath'), load('metal-impact'), load('metal-impact-heavy'), load('metal-impact-hard')
    ring, bell = load('metal-clang'), load('bell-once')
    return {
        # a blade's swing
        'danh': place(L['danh'], (from_onset(fast, 0.3), 0, 1.0)),
        # a blade thrown: its ring as it leaves, a swing
        'ban': place(L['ban'], (from_onset(unsheath, 0.45), 0, 0.8), (loudest(swings, 0.4), 0.03, 0.6)),
        # a hit landing: steel on steel
        'trung': place(L['trung'], (from_onset(clash, 0.4), 0, 1.0), (from_onset(load('impactMetal_medium_001'), 0.3), 0, 0.5)),
        # a heavy hit: a heavy metal impact, the clang ringing on
        'nang': place(L['nang'], (from_onset(heavy, 1.2), 0, 1.0), (from_onset(clang, 0.9), 0.02, 0.6), (from_onset(ring, 1.2), 0.1, 0.35)),
        # an area burst: blades striking all round, metal ringing out
        'vung': place(L['vung'], (from_onset(hard, 1.4), 0, 0.9), (from_onset(clash, 0.6), 0.25, 0.7), (from_onset(clang, 0.9), 0.5, 0.7),
                      (from_onset(load('impactMetal_heavy_002'), 0.6), 0.8, 0.7), (from_onset(ring, 1.4), 1.0, 0.5),
                      (stretch(from_onset(bell, 1.6), 0.9), 1.0, 0.45)),
        # a dash: a fast blade whoosh
        'luot': place(L['luot'], (loudest(swings, 0.35), 0, 1.0)),
        # a guard: armour plates locking, a ring
        'khien': place(L['khien'], (from_onset(load('impactPlate_medium_001'), 0.4), 0, 0.8), (from_onset(unsheath, 0.6), 0.02, 0.5),
                       (from_onset(load('magic-shield-block'), 0.6), 0.03, 0.4)),
        # an ultimate charging: a blade drawn slowly, energy humming, a bell's ring rising
        'gong': place(L['gong'], (from_onset(unsheath, 1.0), 0, 0.8), (loudest(load('magical-focus'), 1.4), 0, 0.5),
                      (from_onset(bell, 1.4), 0.3, 0.35)),
        # the ultimate landing: a great clang, a heavy impact, blades ringing, a bell fading
        'ult': place(L['ult'], (from_onset(clang, 0.9), 0, 1.0), (from_onset(heavy, 1.5), 0.05, 1.0),
                     (from_onset(load('impactBell_heavy_001'), 1.5), 0.2, 0.6), (from_onset(bell, 3.8), 0.4, 0.9),
                     (from_onset(clash, 0.6), 0.9, 0.5), (stretch(from_onset(ring, 1.4), 0.7), 1.6, 0.6),
                     (from_onset(load('impactMetal_heavy_004'), 0.8), 1.6, 0.5)),
    }


RECIPES = {'hoa': hoa, 'thuy': thuy, 'moc': moc, 'tho': tho, 'kim': kim}


def main(out):
    os.makedirs(out, exist_ok=True)
    allx = []
    for he, make in RECIPES.items():
        for loai, x in make().items():
            x = finish(x, LEN[loai])
            wav = os.path.join(out, f'{he}_{loai}.wav')
            write_wav(wav, x)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', wav, '-c:a', 'libvorbis', '-q:a', '5',
                            wav[:-4] + '.ogg'], check=True)
            allx += [x, np.zeros(n(0.5))]
            print(f'  {he}_{loai}: {len(x) / RATE:.2f}s')
    write_wav(os.path.join(out, 'nghe-thu_cc0.wav'), np.concatenate(allx))
    print(out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'thu-giong', 'chieu-cc0'))
