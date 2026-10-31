"""The story's spoken lines: every line of game/src/truyen.js read aloud in Vietnamese, one WAV a line, for
game/src/giong.js to play with the dialogue box and the films.

Voices: Microsoft's Vietnamese neural voices through edge-tts (online, free; pip install edge-tts), the voice, speed
and pitch of each speaker from truyen.js (TRUYEN.DAN for the narration, TRUYEN.NPC[...].giong for the others).
What is read: the line's words without anything in brackets ("(R2)"), {pet} as "bé" (the pet's own name is the
player's choice), {he} once per element (5 files), "…" as a pause.

assets/am-thanh/giong/
    <key>.wav           22050 Hz mono 16-bit, like the game's sounds (the R36S plays WAV only), loudness levelled
    _giong.json         key -> {hash of voice and words, ms}: a line is made again only when it changed
Keys: phim_<reel>_<shot> for a film shot's words, <scene>_<line> for a line, <scene>_<line>_<he> when it has {he}.

A voice ['elevenlabs', '<its name there>'] (Già Quy) is made by hand on elevenlabs.io (the free plan has no API key
here): the script does not make it, it lists the lines of that voice that are missing or whose words changed, and
--nhap takes them in once made: a folder of <key>.mp3 (the keys the list gives).

Usage: python scripts/make_giong.py               (only what changed)
       python scripts/make_giong.py --all         (every line again, ElevenLabs ones aside)
       python scripts/make_giong.py --nhap DIR    (ElevenLabs lines: DIR/<key>.mp3 -> the game's WAVs)
"""
import asyncio, hashlib, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'game', 'src', 'truyen.js')
OUT = os.path.join(ROOT, 'assets', 'am-thanh', 'giong')
LEDGER = os.path.join(OUT, '_giong.json')
HE = {'hoa': 'Hỏa', 'kim': 'Kim', 'moc': 'Mộc', 'thuy': 'Thủy', 'tho': 'Thổ'}
VUNG = {'hoa': 'Núi lửa', 'kim': 'Núi pha lê', 'moc': 'Rừng cổ thụ', 'tho': 'Hẻm vực', 'thuy': 'Hồ thác'}
# sound treatments a voice may name as its 4th item: "noi-luc", a storyteller's weight (the whole voice a semitone
# and a bit lower, more low end, a little less hiss, a short hall) - the narrator's
# "gia", an old man up close (lower still, a slight waver, dry: Già Quy); "vo-su", a martial master (a little lower,
# pressed firm and close: Sư phụ)
FX = {'noi-luc': 'rubberband=pitch=0.92,bass=g=5:f=140,equalizer=f=3200:t=q:w=1.2:g=-2,aecho=0.8:0.55:45|90:0.18|0.10',
      'gia': 'rubberband=pitch=0.9,vibrato=f=5.5:d=0.06,bass=g=4:f=150,equalizer=f=3000:t=q:w=1.2:g=-3',
      'vo-su': 'rubberband=pitch=0.95,bass=g=3:f=130,acompressor=threshold=-20dB:ratio=3:attack=5:release=80'}
# a voice's 5th item "ke-chuyen": read the way a storyteller does, phrase by phrase (the service reads a whole line in
# one flat breath): each phrase asked for on its own, a sentence's first phrase a little higher, its last lower and
# slower, and a breath between them by the punctuation (ms)
PAUSE = {',': 260, ';': 420, ':': 420, '.': 720, '!': 720, '?': 720, '...': 950}
RISE, FALL, FALL_RATE = 4, -7, -6        # Hz on the first / last phrase of a sentence, % slower on the last
TRIES = 12                           # the service now and then sends nothing back: tried again after a pause


def story():
    """TRUYEN as plain data (truyen.js run by node)."""
    js = f"require({json.dumps(SRC)}); process.stdout.write(JSON.stringify(TRUYEN))"
    return json.loads(subprocess.run(['node', '-e', js], capture_output=True, check=True, encoding='utf-8').stdout)


def spoken(words, he=None):
    s = re.sub(r'\s*\([^)]*\)', '', words)
    s = re.sub(r'(^|[.!?…]\s*)\{pet\}', lambda m: m.group(1) + 'Bé', s).replace('{pet}', 'bé')
    if he:
        s = s.replace('{he}', HE[he]).replace('{vung}', VUNG[he])
    return s.replace('…', '...').strip()


def lines(T):
    """[(key, voice, text)] for every film caption and every line of every scene."""
    out, dan = [], T['DAN']['giong']
    for reel, r in T['PHIM'].items():
        for i, sh in enumerate(r['canh']):
            if sh.get('chu'):
                out.append((f'phim_{reel}_{i}', dan, spoken(sh['chu'])))
    for c in T['CANH']:
        for i, (who, _face, words) in enumerate(c['cau']):
            voice = T['NPC'][who]['giong'] if who else dan
            if '{he}' in words or '{vung}' in words:
                out += [(f"{c['id']}_{i}_{he}", voice, spoken(words, he)) for he in HE]
            else:
                out.append((f"{c['id']}_{i}", voice, spoken(words)))
    return out


async def say(text, voice, mp3):
    import edge_tts
    name, rate, pitch = voice[:3]
    for k in range(TRIES):
        try:
            await edge_tts.Communicate(text, name, rate=rate, pitch=pitch).save(mp3)
            if os.path.getsize(mp3) > 1000:
                return
        except Exception as e:                       # NoAudioReceived, a dropped connection...
            err = e
        await asyncio.sleep(min(10, 1.5 * (k + 1)))
    raise SystemExit(f'không tạo được giọng sau {TRIES} lần: {text[:40]}… ({err})')


def phrases(text):
    """[(phrase, its closing punctuation, ends a sentence)]."""
    out = []
    for m in re.finditer(r'[^,.:;!?]+(\.\.\.|[,.:;!?])?', text):
        words, mark = m.group(0).strip(), m.group(1) or ''
        if words.strip('.,:;!? '):
            out.append((words, mark, mark in ('.', '!', '?', '...')))
    if out:
        out[-1] = (out[-1][0], out[-1][1], True)
    return out


async def say_told(text, voice, tmp, key):
    """A storyteller's reading (see PAUSE): the phrases said one by one with their rise and fall, joined with breaths
    into one WAV; its path."""
    import wave
    name, rate, pitch = voice[:3]
    base_p, base_r = int(pitch.rstrip('Hz')), int(rate.rstrip('%'))
    parts, first = [], True
    for j, (words, mark, last) in enumerate(phrases(text)):
        hz = base_p + (FALL if last else RISE if first and not last else 0)
        pct = base_r + (FALL_RATE if last else 0)
        mp3, wav = os.path.join(tmp, f'{key}_{j}.mp3'), os.path.join(tmp, f'{key}_{j}.wav')
        await say(words, [name, f'{pct:+d}%', f'{hz:+d}Hz'], mp3)
        trim = 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-af', trim, '-ar', '22050', '-ac', '1',
                        '-c:a', 'pcm_s16le', wav], check=True)
        with wave.open(wav) as w:
            parts.append((w.readframes(w.getnframes()), PAUSE.get(mark, 0)))
        first = last
    joined = os.path.join(tmp, key + '_ke.wav')
    with wave.open(joined, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(22050)
        for k, (frames, pause) in enumerate(parts):
            w.writeframes(frames)
            if k < len(parts) - 1:
                w.writeframes(b'\0\0' * (22050 * pause // 1000))
    return joined


def to_wav(mp3, wav, fx=None):
    """22050 Hz mono, the voice's treatment (FX) if it has one, levelled to the game's loudness, the silence at both
    ends trimmed; its length in ms."""
    trim = 'silenceremove=start_periods=1:start_threshold=-50dB,areverse,silenceremove=start_periods=1:start_threshold=-50dB,areverse'
    extra = f'{FX[fx]},' if fx else ''
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp3, '-af', f'{trim},{extra}loudnorm=I=-16:TP=-1.5',
                    '-ar', '22050', '-ac', '1', '-c:a', 'pcm_s16le', wav], check=True)
    import wave
    with wave.open(wav) as w:
        return round(w.getnframes() * 1000 / w.getframerate())


def line_hash(voice, text):
    return hashlib.sha1(json.dumps([voice, text], ensure_ascii=False).encode()).hexdigest()[:12]


def take_in(folder):
    """ElevenLabs lines made by hand: <folder>/<key>.mp3 -> the game's WAV and the ledger."""
    ledger = json.load(open(LEDGER, encoding='utf-8')) if os.path.exists(LEDGER) else {}
    n = 0
    for key, voice, text in lines(story()):
        mp3 = os.path.join(folder, key + '.mp3')
        if voice[0] != 'elevenlabs' or not os.path.exists(mp3):
            continue
        ledger[key] = {'hash': line_hash(voice, text), 'ms': to_wav(mp3, os.path.join(OUT, key + '.wav')), 'chu': text}
        n += 1
    json.dump(ledger, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'{n} câu ElevenLabs đã nhập')


async def main(redo):
    os.makedirs(OUT, exist_ok=True)
    old = json.load(open(LEDGER, encoding='utf-8')) if os.path.exists(LEDGER) else {}
    ledger = old if not redo else {}
    todo = lines(story())
    keep, made, waiting = {}, 0, []
    with tempfile.TemporaryDirectory() as tmp:
        for key, voice, text in todo:
            h = line_hash(voice, text)
            wav = os.path.join(OUT, key + '.wav')
            if voice[0] == 'elevenlabs':             # made by hand: kept while its words are the same, listed when due
                if old.get(key, {}).get('hash') == h and os.path.exists(wav):
                    keep[key] = old[key]
                    continue
                # words changed: the old recording would say the old words under the new ones, so it goes to _cu/
                # (kept, not played) and the line stays silent until it is made again and taken in with --nhap
                if os.path.exists(wav):
                    os.makedirs(os.path.join(OUT, '_cu'), exist_ok=True)
                    os.replace(wav, os.path.join(OUT, '_cu', key + '.wav'))
                waiting.append((key, text))
                continue
            if ledger.get(key, {}).get('hash') == h and os.path.exists(wav):
                keep[key] = ledger[key]
                continue
            if len(voice) > 4 and voice[4] == 'ke-chuyen':
                mp3 = await say_told(text, voice, tmp, key)
            else:
                mp3 = os.path.join(tmp, key + '.mp3')
                await say(text, voice, mp3)
            keep[key] = {'hash': h, 'ms': to_wav(mp3, wav, voice[3] if len(voice) > 3 else None), 'chu': text}
            made += 1
            ledger[key] = keep[key]                  # written as it goes: a stopped run keeps what it made
            json.dump(ledger, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print(f'  {key}: {keep[key]["ms"] / 1000:.1f}s  {text[:60]}')
    for f in os.listdir(OUT):                        # lines truyen.js no longer has
        if f.endswith('.wav') and f[:-4] not in keep:
            os.remove(os.path.join(OUT, f))
    json.dump(keep, open(LEDGER, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(v['ms'] for v in keep.values()) / 1000
    print(f'{OUT}: {len(keep)} câu ({made} mới), {total:.0f} giây')
    if waiting:
        print(f'cần tạo trên ElevenLabs rồi nhập bằng --nhap ({len(waiting)} câu):')
        for key, text in waiting:
            print(f'  {key}.mp3: {text}')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if '--nhap' in sys.argv:
        take_in(sys.argv[sys.argv.index('--nhap') + 1])
    else:
        asyncio.run(main('--all' in sys.argv))
