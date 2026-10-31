"""The game's everyday sounds (assets/am-thanh/sfx/<name>.wav), second take: real CC0 sounds instead of the 8-bit
blips of scripts/make_sfx_8bit.py, same names so every call in the game keeps working.

Sources, all CC0 (no credit needed, commercial use allowed):
    Kenney UI Audio + Interface Sounds  (assets/am-thanh/_kenney/wav/ui_*.wav): clicks, confirm, back, error, switches
    Kenney Impact Sounds + RPG Audio    (_kenney/wav/): punches, soft thuds, footsteps on grass, coins
    rubberduck's creature packs         (assets/am-thanh/_cc0-chieu/wav/cr_*.wav, from _cc0-voice): the pet's eat,
                                        cute chirps, burp, cough, snore, breath, hurt
    Openverse (mostly Freesound)        (_cc0-chieu/wav/, sources in _cc0-chieu/NGUON.txt): crunching, a coin, sparkles,
                                        a fanfare, a level-up, birdsong, an owl, splashes, a body fall
Each is cut, layered and set to a level by its kind: UI sounds clear but short (PEAK_UI), care sounds a little softer.
The cutting and mixing helpers are the combat sounds' (scripts/make_chieu_cc0.py).

Usage: python scripts/make_sfx_cc0.py [OUT_DIR]   (default build/thu-giong/sfx-cc0; assets/am-thanh/sfx replaces the game's)
"""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_chieu_cc0 import (load, from_onset, loudest, place, stretch, ffmpeg_fx, fades, write_wav, n, RATE, ROOT)

PEAK_UI, PEAK_CARE, PEAK_BIG = 0.8, 0.7, 0.85


def finish(x, peak, lo=60, hi=11000):
    """Band-limit, press a little, trim the silence after it, fade out, set the peak."""
    x = ffmpeg_fx(x, f'highpass=f={lo},lowpass=f={hi},acompressor=threshold=-20dB:ratio=2.5:attack=2:release=100:makeup=1.5')
    e = np.abs(x)
    last = len(x) - int(np.argmax(e[::-1] > e.max() * 0.02))       # the end of what is heard
    x = fades(x[:max(n(0.05), last + n(0.03))], 0.002, 0.04)
    return x / (np.abs(x).max() + 1e-9) * peak


def sounds():
    swoosh, wind = load('swoosh-air'), load('wind-gust')
    S = {}
    # ---------- the interface ----------
    S['menu'] = (from_onset(load('ui_click_003'), 0.12), PEAK_UI)                              # moving through a menu
    S['chon'] = (from_onset(load('ui_confirmation_001'), 0.5), PEAK_UI)                        # choosing
    S['quay-lai'] = (from_onset(load('ui_back_002'), 0.4), PEAK_UI)                            # B, back
    S['loi'] = (from_onset(load('ui_error_004'), 0.5), PEAK_UI)                                # can't do that
    S['doi-phong'] = (place(0.8, (from_onset(load('ui_maximize_003'), 0.5), 0, 0.9),           # another room
                            (loudest(swoosh, 0.4), 0.05, 0.5)), PEAK_UI)
    S['doi-pet'] = (place(0.8, (from_onset(load('ui_select_003'), 0.3), 0, 0.9),               # another pet
                          (from_onset(load('cr_cute_02'), 0.6), 0.12, 0.45)), PEAK_UI)
    S['chuyen'] = (place(0.6, (loudest(wind, 0.6), 0, 0.6), (from_onset(swoosh, 0.45), 0.08, 0.8)), PEAK_CARE)   # a screen change
    S['xu'] = (place(0.9, (from_onset(load('coin-pickup'), 0.5), 0, 1.0),                      # coins
                     (from_onset(load('handleCoins'), 0.8), 0.05, 0.4)), PEAK_UI)
    # ---------- footsteps (soft: they repeat) ----------
    S['buoc-1'] = (from_onset(load('footstep_grass_000'), 0.25), 0.45)
    S['buoc-2'] = (from_onset(load('footstep_grass_001'), 0.25), 0.4)
    S['chay'] = (from_onset(load('footstep_grass_002'), 0.2), 0.42)
    # ---------- looking after the pet ----------
    S['an'] = (place(0.5, (from_onset(load('crunch'), 0.3), 0, 1.0), (from_onset(load('cr_eat_01'), 0.5), 0.05, 0.7)), PEAK_CARE)
    S['vui'] = (from_onset(load('cr_cute_03'), 1.3), PEAK_CARE)
    S['no'] = (place(1.4, (from_onset(load('cr_burp_01'), 0.7), 0, 1.0), (from_onset(load('cr_cute_05'), 0.8), 0.55, 0.7)), PEAK_CARE)
    S['met'] = (from_onset(load('cr_breath_02'), 0.9), PEAK_CARE)
    S['om'] = (from_onset(load('cr_cough_01'), 0.95), PEAK_CARE)
    S['ngu'] = (place(2.2, (from_onset(load('cr_breath'), 1.0), 0, 0.7), (from_onset(load('cr_snore'), 1.6), 0.6, 1.0)), PEAK_CARE)
    S['thuc-day'] = (place(1.5, (from_onset(load('cr_ooh'), 1.0), 0, 1.0), (loudest(load('bird-chirp'), 1.2), 0.3, 0.35)), PEAK_CARE)
    S['sach'] = (place(1.2, (from_onset(load('tiny-splash'), 0.8), 0, 0.8), (from_onset(load('water-bubble'), 0.8), 0.1, 0.5),
                       (from_onset(load('gleam-chime'), 1.0), 0.25, 0.55)), PEAK_CARE)
    # ---------- the day ----------
    S['ngay'] = (place(1.9, (loudest(load('bird-chirp'), 1.9), 0, 0.9), (from_onset(load('chime-notify'), 0.4), 0, 0.5)), PEAK_CARE)
    S['dem'] = (place(2.1, (from_onset(load('owl'), 1.5), 0.1, 1.0), (from_onset(load('glimmer'), 2.0), 0, 0.3)), PEAK_CARE)
    # ---------- training and fights outside the arena ----------
    S['dam'] = (place(0.5, (from_onset(swoosh, 0.2), 0, 0.5), (from_onset(load('impactPunch_medium_002'), 0.4), 0.06, 1.0)), PEAK_BIG)
    S['don-he'] = (place(0.55, (from_onset(swoosh, 0.3), 0, 0.7), (from_onset(load('impactSoft_medium_001'), 0.35), 0.1, 0.9),
                         (from_onset(load('glimmer'), 0.4), 0.1, 0.35)), PEAK_BIG)
    S['chieu'] = (place(0.65, (loudest(load('magical-focus'), 0.65), 0, 1.0), (from_onset(swoosh, 0.4), 0.2, 0.5)), PEAK_BIG)
    S['trung-don'] = (place(0.6, (from_onset(load('impactPunch_heavy_001'), 0.4), 0, 1.0),
                            (from_onset(load('cr_hurt_02'), 0.5), 0.05, 0.5)), PEAK_BIG)
    S['guc'] = (place(1.6, (from_onset(load('cr_die_02'), 1.0), 0, 0.6), (from_onset(load('body-fall'), 0.8), 0.5, 1.0)), PEAK_BIG)
    # ---------- the big moments ----------
    S['thang'] = (from_onset(load('fanfare-short'), 3.4), PEAK_BIG)
    S['tien-hoa'] = (place(2.4, (loudest(load('magic-chargeup'), 1.6), 0, 0.7), (from_onset(load('level-up'), 2.0), 0.5, 1.0),
                           (from_onset(load('gleam-chime'), 1.6), 0.8, 0.5)), PEAK_BIG)
    return S


def main(out):
    os.makedirs(out, exist_ok=True)
    allx = []
    for name, (x, peak) in sounds().items():
        x = finish(x, peak)
        write_wav(os.path.join(out, name + '.wav'), x)
        allx += [x, np.zeros(n(0.6))]
        print(f'  {name}: {len(x) / RATE:.2f}s')
    write_wav(os.path.join(out, 'nghe-thu_sfx-cc0.wav'), np.concatenate(allx))
    print(out, len(allx) // 2, 'tiếng')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'build', 'thu-giong', 'sfx-cc0'))
