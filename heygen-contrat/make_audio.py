"""Bande-son de la vidéo HeyGen habillée : voix d'origine + musique synthétisée en fond (ducking)
+ bruitages calés sur l'habillage, normalisée à -14 LUFS.

Usage : python3 heygen-contrat/make_audio.py   (lit source.mp4, écrit soundtrack.wav dans ce dossier)
"""
import importlib.util, os, subprocess
import numpy as np
from scipy.io import wavfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('app_audio', os.path.join(HERE, '..', 'apporteur', 'audio', 'make_audio.py'))
A = importlib.util.module_from_spec(spec); spec.loader.exec_module(A)   # réutilise la musique de la vidéo « apporteur »

DUR = 52.6                                   # doit suivre DURATION dans overlay.html
PHASES = [4.36, 9.22, 14.68, 22.36, 26.76, 35.3, 44.1, 45.44]
COMMISSION_AT, VIDEO_END = 44.54, 49.45   # « ding » sur « gratuite »

voice = A.load(os.path.join(HERE, 'source.mp4'))
N = int(DUR * A.SR)
v = np.zeros(N); v[:min(N, len(voice))] = voice[:N]
v = v / (np.max(np.abs(v)) + 1e-9) * .9
sfx = [('whoosh', t) for t in PHASES] + [('ding', COMMISSION_AT), ('whoosh', VIDEO_END), ('pop', VIDEO_END + 1.1)]
mus = A.music(DUR, sfx)
active = A.smooth((np.abs(v) > .02).astype(float), .12)
mix = mus * .42 * (1 - .5 * np.clip(active * 3, 0, 1)) + v[None, :]
tmp = os.path.join(HERE, 'soundtrack_raw.wav')
wavfile.write(tmp, A.SR, (np.clip(mix, -1, 1).T * 32767).astype('<i2'))
out = os.path.join(HERE, 'soundtrack.wav')
subprocess.run([A.FFMPEG, '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=11', '-ar', str(A.SR), out], check=True)
os.remove(tmp)
print('OK ->', out)
