"""The room's music by day and by night (assets/am-thanh/nhac/ngay.wav, dem.wav), second take: CC0 recordings from
OpenGameArt instead of the 8-bit loops of scripts/make_sfx_8bit.py, same names so the game plays them as before
(r36s/js/am-thanh.js: ngay by day, dem with the lights out and under the films).

Each track is cut to a stretch of LOOP_MAX seconds at most (the R36S holds the whole of it in memory), its tail laid
over its head for XFADE seconds so the loop has no seam, then set to the old loops' level (RMS ~0.1: under the voices
and sounds). 22050 Hz mono WAV like every sound of the game.

Tracks (assets/am-thanh/nhac/_cc0/, all CC0, sources in _cc0/NGUON.txt); ngay and dem take CHOICE's:
    a-new-town            "A New Town (RPG Theme)", cynicmusic: a calm harp solo                (day)
    medieval-exploration  "Medieval: Exploration": a medieval exploration theme                (day)
    forest-whisper        "Forest Whisper Theme": loops by itself                               (night)
    rising-moon           "Fantasy: Rising Moon": a fantasy track for a windy night             (night)
Usage: python scripts/make_nhac_cc0.py [OUT_DIR]   (default build/thu-giong/nhac-cc0: every track, to listen;
                                                    assets/am-thanh/nhac writes ngay.wav and dem.wav for the game)
"""
import os, subprocess, sys, tempfile, wave
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'assets', 'am-thanh', 'nhac', '_cc0')
RATE = 22050
LOOP_MAX = 90            # s
XFADE = 3.0              # s of tail laid over the head
RMS = 0.10
TRACKS = {'a-new-town': 'a-new-town.mp3', 'medieval-exploration': 'medieval-exploration.mp3',
          'forest-whisper': 'forest-whisper/Forest Whisper Theme/Forest Whisper.wav', 'rising-moon': 'rising-moon.mp3'}
SEAMLESS = {'forest-whisper'}                       # already loops: kept whole
CHOICE = {'ngay': 'a-new-town', 'dem': 'forest-whisper'}


def read(path):
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, 'a.wav')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', path, '-ac', '1', '-ar', str(RATE), out], check=True)
        with wave.open(out) as w:
            return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768


def loop(x, name):
    """A seamless loop: silence at both ends cut, at most LOOP_MAX s, the tail crossfaded into the head."""
    e = np.abs(x); th = e.max() * 0.01
    a, b = int(np.argmax(e > th)), len(x) - int(np.argmax(e[::-1] > th))
    x = x[a:b]
    if name in SEAMLESS:
        return x
    total = min(len(x), int(LOOP_MAX * RATE))
    x, f = x[:total], int(XFADE * RATE)
    t = np.linspace(0, np.pi / 2, f)
    body = x[:total - f].copy()
    body[:f] = x[:f] * np.sin(t) + x[total - f:total] * np.cos(t)      # equal-power: the end runs into the start
    return body


def level(x):
    x = x * (RMS / (np.sqrt((x ** 2).mean()) + 1e-9))
    p = np.abs(x).max()
    return x * (0.95 / p) if p > 0.95 else x


def write(path, x):
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes())


def main(out):
    os.makedirs(out, exist_ok=True)
    game = os.path.normcase(os.path.abspath(out)) == os.path.normcase(os.path.join(ROOT, 'assets', 'am-thanh', 'nhac'))
    made = {}
    for name, f in TRACKS.items():
        if game and name not in CHOICE.values():
            continue
        made[name] = level(loop(read(os.path.join(SRC, f)), name))
        print(f'  {name}: {len(made[name]) / RATE:.0f}s')
    if game:
        for slot, name in CHOICE.items():
            write(os.path.join(out, slot + '.wav'), made[name])
            print(f'  {slot}.wav <- {name}')
    else:
        for name, x in made.items():
            write(os.path.join(out, name + '.wav'), x)
            # the loop point heard: its last 6 s running into its first 6 s
            write(os.path.join(out, name + '_cho-noi.wav'), np.concatenate([x[-6 * RATE:], x[:6 * RATE]]))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'thu-giong', 'nhac-cc0'))
