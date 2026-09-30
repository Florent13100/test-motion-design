"""Génère la bande-son de la vidéo : voix off (Edge TTS neuronal) + musique synthétisée
(libre de droits, composée ici) calée sur les transitions, puis mixage avec ducking.

Usage : python3 audio/make_audio.py            -> audio/soundtrack.wav
        python3 audio/make_audio.py --no-tts   (réutilise les voix déjà générées)
Dépendances : pip install edge-tts numpy scipy imageio-ffmpeg
"""
import asyncio, json, os, subprocess, sys
import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
SR = 48000
DUR = 22.0
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM
WIPES = [3.3, 6.4, 10.2, 14.6, 17.6]           # doit suivre WIPES dans video.html
CFG = json.load(open(os.path.join(HERE, 'voiceover.json'), encoding='utf-8'))

try:
    import imageio_ffmpeg
    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = 'ffmpeg'


# ---------------------------------------------------------------- voix off
def make_tts():
    import certifi
    ca = os.environ.get('TTS_CA_BUNDLE') or ('/root/.ccr/ca-bundle.crt' if os.path.exists('/root/.ccr/ca-bundle.crt') else None)
    if ca:
        certifi.where = lambda: ca
    import edge_tts

    async def run():
        for i, line in enumerate(CFG['lines'], 1):
            await edge_tts.Communicate(line['text'], CFG['voice'], rate=CFG['rate']).save(os.path.join(HERE, f'vo_{i}.mp3'))
    asyncio.run(run())


def load(path):
    raw = subprocess.run([FFMPEG, '-v', 'error', '-i', path, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def voice_track():
    v = np.zeros(N)
    for i, line in enumerate(CFG['lines'], 1):
        x = load(os.path.join(HERE, f'vo_{i}.mp3'))
        s = int(line['at'] * SR)
        e = min(N, s + len(x))
        v[s:e] += x[:e - s]
    # présence + légère compression pour une voix « radio »
    b, a = signal.butter(2, 90 / (SR / 2), 'high'); v = signal.lfilter(b, a, v)
    b, a = signal.butter(2, [2500 / (SR / 2), 5000 / (SR / 2)], 'band'); v = v + .35 * signal.lfilter(b, a, v)
    env = smooth(np.abs(v), .01)
    gain = np.where(env > .12, (.12 / np.maximum(env, 1e-9)) ** .5, 1.0)
    v = v * gain
    return v / (np.max(np.abs(v)) + 1e-9) * .9


def smooth(x, sec):
    b, a = signal.butter(1, 1 / (sec * SR * np.pi))
    return signal.filtfilt(b, a, x)


# ---------------------------------------------------------------- musique
rng = np.random.default_rng(3)
t_all = np.arange(N) / SR
midi = lambda m: 440 * 2 ** ((m - 69) / 12)

# I–V–vi–IV en do majeur, une mesure (2 s) par accord, résolution finale sur do
CHORDS = {'C': [48, 52, 55], 'G': [43, 47, 50], 'Am': [45, 48, 52], 'F': [41, 45, 48]}
PROG = ['C', 'G', 'Am', 'F', 'C', 'G', 'Am', 'F', 'C', 'G', 'C']
BAR = 4 * BEAT
DRUMS_END = 20.0


def add(buf, x, start, gain=1.0):
    s = int(start * SR)
    if s >= len(buf): return
    e = min(len(buf), s + len(x)); buf[s:e] += gain * x[:e - s]


def kick():
    t = np.arange(int(.4 * SR)) / SR
    f = 45 + 110 * np.exp(-t * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) + .3 * np.exp(-t * 300) * rng.standard_normal(len(t)) * .2


def clap():
    t = np.arange(int(.25 * SR)) / SR
    n = rng.standard_normal(len(t))
    b, a = signal.butter(2, [900 / (SR / 2), 3500 / (SR / 2)], 'band')
    env = np.exp(-t * 22) * (1 + .6 * (np.sin(2 * np.pi * 90 * t) > .9))
    return signal.lfilter(b, a, n) * env * 2.2


def hat(open_=False):
    t = np.arange(int((.18 if open_ else .05) * SR)) / SR
    b, a = signal.butter(2, 7000 / (SR / 2), 'high')
    return signal.lfilter(b, a, rng.standard_normal(len(t))) * np.exp(-t * (18 if open_ else 70))


def saw(freq, dur, detune=(0,)):
    t = np.arange(int(dur * SR)) / SR
    return sum(signal.sawtooth(2 * np.pi * freq * 2 ** (d / 1200) * t + rng.uniform(0, 6)) for d in detune) / len(detune)


def lowpass(x, fc, order=2):
    b, a = signal.butter(order, min(fc, SR / 2 - 100) / (SR / 2)); return signal.lfilter(b, a, x)


def music():
    drums = np.zeros(N); bass = np.zeros(N); pad = np.zeros(N); arp = np.zeros(N); fx = np.zeros(N)
    K, C, H, HO = kick(), clap(), hat(), hat(True)
    nbeats = int(DRUMS_END / BEAT)
    for i in range(nbeats):
        tb = i * BEAT
        add(drums, K, tb, 1.0)
        if i % 2 == 1: add(drums, C, tb, .55)
        add(drums, HO, tb + BEAT / 2, .22)
        if tb > 6.4:  # double-croches à partir de la scène 3 pour faire monter l'énergie
            add(drums, H, tb + BEAT / 4, .12); add(drums, H, tb + 3 * BEAT / 4, .12)
    add(drums, K, DRUMS_END, 1.0)                      # dernier coup sur le CTA
    add(drums, C, DRUMS_END, .5)

    for bi, name in enumerate(PROG):
        t0 = bi * BAR
        notes = CHORDS[name]
        last = bi == len(PROG) - 1
        # basse pompante en croches
        for k in range(8 if not last else 1):
            d = BEAT / 2 * .9 if not last else DUR - t0
            x = lowpass(saw(midi(notes[0] - 12), d, (-6, 6)), 420)
            x *= np.minimum(1, np.arange(len(x)) / (.004 * SR)) * np.exp(-np.arange(len(x)) / SR * (5 if not last else 1.2))
            add(bass, x, t0 + k * BEAT / 2, .5)
        # nappe
        d = BAR if not last else DUR - t0
        x = sum(lowpass(saw(midi(n + 12), d, (-9, 0, 9)), 1600) for n in notes) / 3
        env = np.minimum(1, np.arange(len(x)) / (.08 * SR)) * np.minimum(1, (len(x) - np.arange(len(x))) / (.05 * SR))
        if last: env *= np.exp(-np.arange(len(x)) / SR * 1.1)
        add(pad, x * env, t0, .22)
        # arpège pluck en double-croches (motif 1-3-5-8)
        seq = [notes[0], notes[1], notes[2], notes[0] + 12, notes[2], notes[1], notes[0] + 12, notes[2]]
        steps = 16 if not last else 4
        for k in range(steps):
            f = midi(seq[k % 8] + 24)
            tt = np.arange(int(.22 * SR)) / SR
            x = (signal.sawtooth(2 * np.pi * f * tt) * .5 + np.sin(2 * np.pi * f * tt)) * np.exp(-tt * 16)
            x = lowpass(x, 2200 + 2600 * (bi / len(PROG)))
            if t0 > 3.3 or k % 2 == 0:  # l'arpège se densifie après l'accroche
                add(arp, x, t0 + k * BEAT / 4, .16)

    # transitions : whoosh montant + impact grave sur chaque balayage
    for w in WIPES:
        L = .75
        tt = np.arange(int(L * SR)) / SR
        n = rng.standard_normal(len(tt))
        out = np.zeros_like(n)
        for j in range(0, len(tt), 1024):  # passe-bande dont la fréquence monte
            fc = 400 + 6000 * (j / len(tt)) ** 2
            b, a = signal.butter(2, [fc / (SR / 2), min(fc * 1.6, SR / 2 - 100) / (SR / 2)], 'band')
            out[j:j + 1024] = signal.lfilter(b, a, n[j:j + 1024])
        out *= (tt / L) ** 2
        add(fx, out, w - L, .35)
        ti = np.arange(int(.6 * SR)) / SR
        add(fx, np.sin(2 * np.pi * (38 + 60 * np.exp(-ti * 20)) * ti) * np.exp(-ti * 6), w, .45)

    # sidechain : la basse, la nappe et l'arpège « respirent » sur le kick
    phase = (t_all % BEAT) / BEAT
    pump = np.where(t_all < DRUMS_END, .35 + .65 * np.minimum(1, phase / .45) ** 1.5, 1)
    tonal = (bass + pad + arp) * pump

    # stéréo : arpège avec delay ping-pong, nappe élargie
    d = int(BEAT * .75 * SR)
    arpL = arp * pump; arpR = np.concatenate([np.zeros(d), arp[:-d]]) * .6 * pump
    L = drums + (bass + pad) * pump + arpL + fx + .25 * arpR
    R = drums + (bass + np.roll(pad, 300)) * pump + arpR + .4 * arpL + fx
    m = np.stack([L, R])
    m /= np.max(np.abs(m)) + 1e-9
    # fondu final
    fade = np.clip((DUR - t_all) / 1.2, 0, 1) ** 1.5
    return m * fade


def main():
    if '--no-tts' not in sys.argv:
        make_tts()
    voice = voice_track()
    mus = music()
    # ducking : la musique descend (~-6 dB) quand la voix parle
    active = smooth((np.abs(voice) > .02).astype(float), .12)
    duck = 1 - .5 * np.clip(active * 3, 0, 1)
    mix = mus * .65 * duck + voice[None, :] * 1.0
    wav = os.path.join(HERE, 'soundtrack_raw.wav')
    pcm = (np.clip(mix, -1, 1).T * 32767).astype('<i2')
    from scipy.io import wavfile
    wavfile.write(wav, SR, pcm)
    # normalisation loudness réseaux sociaux (-14 LUFS)
    out = os.path.join(HERE, 'soundtrack.wav')
    subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', wav, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(SR), out], check=True)
    os.remove(wav)
    print('OK ->', out)


if __name__ == '__main__':
    main()
