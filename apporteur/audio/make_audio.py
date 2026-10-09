"""Bande-son de la vidéo « apporteurs d'affaires » : voix du personnage (Edge TTS neuronal)
+ musique synthétisée (libre de droits) + bruitages, et données d'animation pour la vidéo :
calage des mots (sous-titres karaoké) et enveloppe de la voix image par image (lip-sync).

Usage : python3 apporteur/audio/make_audio.py           -> soundtrack.wav + ../timing.js
        python3 apporteur/audio/make_audio.py --no-tts  (réutilise les voix vo_*.mp3 / vo_*.json)
Dépendances : pip install edge-tts numpy scipy
"""
import asyncio, json, os, subprocess, sys
import numpy as np
from scipy import signal
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
FPS = 30
CFG = json.load(open(os.path.join(HERE, 'script.json'), encoding='utf-8'))
FFMPEG = os.environ.get('FFMPEG', 'ffmpeg')
rng = np.random.default_rng(11)


# ---------------------------------------------------------------- voix
def make_tts():
    import certifi  # le proxy de l'environnement impose son propre bundle CA (à fixer avant l'import d'edge_tts)
    ca = os.environ.get('TTS_CA_BUNDLE') or ('/root/.ccr/ca-bundle.crt' if os.path.exists('/root/.ccr/ca-bundle.crt') else None)
    if ca:
        certifi.where = lambda: ca
    import edge_tts

    async def run():
        for i, line in enumerate(CFG['lines'], 1):
            c = edge_tts.Communicate(line['tts'], CFG['voice'], rate=CFG['rate'], boundary='WordBoundary')
            words = []
            with open(os.path.join(HERE, f'vo_{i}.mp3'), 'wb') as f:
                async for ch in c.stream():
                    if ch['type'] == 'audio':
                        f.write(ch['data'])
                    elif ch['type'] == 'WordBoundary':
                        words.append([round(ch['offset'] / 1e7, 3), round(ch['duration'] / 1e7, 3), ch['text']])
            json.dump(words, open(os.path.join(HERE, f'vo_{i}.json'), 'w'), ensure_ascii=False)
    asyncio.run(run())


def load(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def trim(x):
    """Coupe le silence de début/fin, renvoie (signal, décalage de début en s)."""
    idx = np.nonzero(np.abs(x) > .01)[0]
    s, e = max(0, idx[0] - int(.02 * SR)), min(len(x), idx[-1] + int(.06 * SR))
    return x[s:e], s / SR


def smooth(x, sec):
    b, a = signal.butter(1, 1 / (sec * SR * np.pi))
    return signal.filtfilt(b, a, x)


def layout():
    """Place les répliques bout à bout et renvoie la piste voix + le calage."""
    clips, t, lines = [], CFG['start'], []
    for i, line in enumerate(CFG['lines'], 1):
        x, off = trim(load(os.path.join(HERE, f'vo_{i}.mp3')))
        words = json.load(open(os.path.join(HERE, f'vo_{i}.json')))
        show = line['show'].split(' ')
        # chaque mot affiché prend l'instant du mot prononcé correspondant
        times, j = [], 0
        for w in show:  # appariement séquentiel par préfixe (« energy-market.fr » <- « energy-market point fr »)
            key = w.lower().strip('!?:,.…\u00a0')[:4]
            k = next((k for k in range(j, len(words)) if words[k][2].lower().startswith(key)), j)
            times.append(round(t + words[min(k, len(words) - 1)][0] - off, 3)); j = k + 1
        lines.append({'id': line['id'], 'start': round(t, 3), 'end': round(t + len(x) / SR, 3),
                      'words': [[w, tt] for w, tt in zip(show, times)],
                      'spoken': [[w[2], round(t + w[0] - off, 3)] for w in words]})
        clips.append((x, t))
        t += len(x) / SR + CFG['gap']
    dur = round(lines[-1]['end'] + CFG['tail'], 2)
    v = np.zeros(int(dur * SR))
    for x, s in clips:
        v[int(s * SR):int(s * SR) + len(x)] += x
    return v, lines, dur


def polish(v):
    b, a = signal.butter(2, 85 / (SR / 2), 'high'); v = signal.lfilter(b, a, v)
    b, a = signal.butter(2, [2500 / (SR / 2), 5000 / (SR / 2)], 'band'); v = v + .3 * signal.lfilter(b, a, v)
    env = smooth(np.abs(v), .01)
    v = v * np.where(env > .12, (.12 / np.maximum(env, 1e-9)) ** .5, 1.0)
    return v / (np.max(np.abs(v)) + 1e-9) * .9


def mouth_curves(v, dur):
    """Ouverture de bouche (0-1) et « rondeur » (voyelles sombres o/ou) image par image."""
    n = int(dur * FPS)
    hop = SR // FPS
    b, a = signal.butter(2, [250 / (SR / 2), 1100 / (SR / 2)], 'band'); low = signal.lfilter(b, a, v)
    b, a = signal.butter(2, [1800 / (SR / 2), 4500 / (SR / 2)], 'band'); high = signal.lfilter(b, a, v)
    op, rd = [], []
    for i in range(n):
        s = slice(i * hop, (i + 1) * hop)
        r = np.sqrt(np.mean(v[s] ** 2)) if len(v[s]) else 0
        lo = np.sqrt(np.mean(low[s] ** 2)) if len(v[s]) else 0
        hi = np.sqrt(np.mean(high[s] ** 2)) if len(v[s]) else 0
        op.append(r); rd.append(lo / (lo + hi + 1e-9))
    op = np.array(op); op = np.clip((op / (np.percentile(op[op > 0], 95) + 1e-9)) ** .7, 0, 1)
    op[op < .08] = 0
    for i in range(1, len(op)):  # attaque immédiate, relâchement plus doux
        op[i] = max(op[i], op[i - 1] * .55)
    op[op < .08] = 0
    rd = np.array(rd) * (op > 0)
    return [round(float(x), 3) for x in op], [round(float(x), 3) for x in rd]


# ---------------------------------------------------------------- musique
midi = lambda m: 440 * 2 ** ((m - 69) / 12)
BPM = 104
BEAT = 60 / BPM


def add(buf, x, start, gain=1.0):
    s = int(start * SR)
    if s >= len(buf) or s < 0: return
    e = min(len(buf), s + len(x)); buf[s:e] += gain * x[:e - s]


def lowpass(x, fc):
    b, a = signal.butter(2, min(fc, SR / 2 - 100) / (SR / 2)); return signal.lfilter(b, a, x)


def kick():
    t = np.arange(int(.35 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(50 + 90 * np.exp(-t * 30)) / SR) * np.exp(-t * 10)


def shaker():
    t = np.arange(int(.09 * SR)) / SR
    b, a = signal.butter(2, 6000 / (SR / 2), 'high')
    return signal.lfilter(b, a, rng.standard_normal(len(t))) * np.sin(np.pi * t / t[-1]) ** 2


def snap():
    t = np.arange(int(.15 * SR)) / SR
    b, a = signal.butter(2, [1200 / (SR / 2), 4000 / (SR / 2)], 'band')
    return signal.lfilter(b, a, rng.standard_normal(len(t))) * np.exp(-t * 35) * 2


def pluck(f, d=.5, bright=3000):
    t = np.arange(int(d * SR)) / SR
    x = (np.sin(2 * np.pi * f * t) + .45 * np.sin(4 * np.pi * f * t) + .2 * signal.sawtooth(2 * np.pi * f * t)) * np.exp(-t * 7)
    return lowpass(x * np.minimum(1, t / .003), bright)


def keys(notes, d):
    t = np.arange(int(d * SR)) / SR
    x = sum(np.sin(2 * np.pi * midi(m) * t) + .3 * np.sin(4 * np.pi * midi(m) * t + .5) for m in notes) / len(notes)
    return x * np.minimum(1, t / .02) * np.exp(-t * 1.6)


def ding(f0=1568):
    t = np.arange(int(1.2 * SR)) / SR
    return sum(np.sin(2 * np.pi * f0 * k * t) * np.exp(-t * (4 + 3 * k)) / k for k in (1, 2.76, 5.4)) * .6


def pop():
    t = np.arange(int(.12 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(300 + 900 * t / t[-1]) / SR) * np.exp(-t * 30)


def whoosh(L=.5):
    tt = np.arange(int(L * SR)) / SR
    n = rng.standard_normal(len(tt)); out = np.zeros_like(n)
    for j in range(0, len(tt), 1024):
        fc = 500 + 5000 * (j / len(tt)) ** 2
        b, a = signal.butter(2, [fc / (SR / 2), min(fc * 1.6, SR / 2 - 100) / (SR / 2)], 'band')
        out[j:j + 1024] = signal.lfilter(b, a, n[j:j + 1024])
    return out * (tt / L) ** 2


# Fa majeur, ambiance « bonne nouvelle » : F – C – Dm – Bb
CHORDS = [[53, 57, 60], [48, 52, 55], [50, 53, 57], [46, 50, 53]]


def music(dur, events):
    N = int(dur * SR); t_all = np.arange(N) / SR
    drums, tonal, fx = np.zeros(N), np.zeros(N), np.zeros(N)
    K, S, SN = kick(), shaker(), snap()
    end = dur - 1.6
    for i in range(int(end / BEAT)):
        tb = i * BEAT
        if tb > 1.2: add(drums, K, tb, .8)              # le beat démarre après le « Salut ! »
        if i % 2 == 1 and tb > 1.2: add(drums, SN, tb, .35)
        add(drums, S, tb + BEAT / 2, .12); add(drums, S, tb + BEAT / 4 * 3, .06)
    bar = 4 * BEAT
    nb = int(np.ceil(dur / bar))
    for b in range(nb):
        t0 = b * bar
        ch = CHORDS[b % 4] if t0 < end else CHORDS[0]
        last = t0 >= end - bar * .5
        add(tonal, keys([m + 12 for m in ch], bar if not last else dur - t0), t0, .3)
        for k in range(8 if not last else 1):           # basse en croches syncopées
            if k in (0, 3, 4, 6, 7) or last:
                add(tonal, lowpass(pluck(midi(ch[0] - 12), .35), 500), t0 + k * BEAT / 2, .55)
        motif = [0, 2, 1, 2, 0, 2, 1, 2]
        for k in range(8 if not last else 0):           # guitare / marimba
            add(tonal, pluck(midi(ch[motif[k]] + 24), .4), t0 + k * BEAT / 2 + (BEAT / 4 if k % 2 else 0), .12)
    for kind, at in events:
        if kind == 'pop': add(fx, pop(), at, .25)
        elif kind == 'whoosh': add(fx, whoosh(), at - .5, .25)
        elif kind == 'ding':
            add(fx, ding(), at, .5); add(fx, ding(2093), at + .09, .4)
    phase = (t_all % BEAT) / BEAT
    pump = .55 + .45 * np.minimum(1, phase / .4) ** 1.5
    L = drums + tonal * pump + fx
    R = drums + np.roll(tonal, 240) * pump + fx
    m = np.stack([L, R]); m /= np.max(np.abs(m)) + 1e-9
    return m * np.clip((dur - t_all) / 1.4, 0, 1) ** 1.5 * np.clip(t_all / .3, 0, 1)


def word_time(lines, lid, prefix):
    line = next(l for l in lines if l['id'] == lid)
    return next(t for w, t in line['spoken'] if prefix in w.lower())


def main():
    if '--no-tts' not in sys.argv:
        make_tts()
    raw, lines, dur = layout()
    voice = polish(raw)
    op, rd = mouth_curves(raw, dur)
    L = {l['id']: l for l in lines}
    # temps forts partagés entre l'image et le son
    events = {
        'contact': word_time(lines, 'contact', 'contact'),
        'call': word_time(lines, 'contact', 'appelle'),
        'sign': word_time(lines, 'pay', 'signe'),
        'pay': word_time(lines, 'pay', 'rémun'),
        'url': word_time(lines, 'cta', 'energy'),
    }
    sfx = [('whoosh', L[k]['start']) for k in ('hook', 'pro', 'contact', 'nego', 'pay', 'cta')]
    sfx += [('pop', events['contact']), ('pop', events['call']), ('pop', events['sign']), ('ding', events['pay']),
            ('pop', events['url'])]
    sfx += [('pop', t) for w, t in L['pro']['spoken'] if w.lower() in ('commerçant', 'restaurateur', 'artisan')]
    mus = music(dur, sfx)
    active = smooth((np.abs(voice) > .02).astype(float), .12)
    mix = mus * .5 * (1 - .45 * np.clip(active * 3, 0, 1)) + voice[None, :]
    tmp = os.path.join(HERE, 'soundtrack_raw.wav')
    wavfile.write(tmp, SR, (np.clip(mix, -1, 1).T * 32767).astype('<i2'))
    out = os.path.join(HERE, 'soundtrack.wav')
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(SR), out], check=True)
    os.remove(tmp)
    data = {'duration': dur, 'fps': FPS, 'lines': lines, 'events': events, 'mouth': op, 'round': rd}
    with open(os.path.join(HERE, '..', 'timing.js'), 'w', encoding='utf-8') as f:
        f.write('// Généré par audio/make_audio.py — ne pas éditer à la main.\nwindow.TIMING = ')
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
        f.write(';\n')
    print('OK ->', out, f'({dur} s)')
    for l in lines:
        print(f"{l['start']:6.2f}-{l['end']:6.2f} {l['id']:8s} {' '.join(w for w, _ in l['words'])}")
    print(events)


if __name__ == '__main__':
    main()
