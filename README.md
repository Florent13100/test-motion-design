# Energy Market — vidéo motion design 9:16

`energy-market-9x16.mp4` : 1080×1920, 30 fps, H.264 + AAC 192 kb/s (−14 LUFS), 22 s
(la voix off se termine à ~20,2 s, puis 2 s de marge sur l'écran d'appel à l'action).

## Bande-son
- **Voix off** : voix neuronale `fr-FR-VivienneMultilingualNeural` (Edge TTS). Texte et calage dans `audio/voiceover.json`.
- **Musique** : composée par synthèse dans `audio/make_audio.py` (120 BPM, do majeur I–V–vi–IV, kick/clap/basse/arpège/nappe),
  donc libre de droits ; whoosh + impact sur chaque transition, ducking sous la voix, fondu final.
- Régénérer : `python3 audio/make_audio.py` (ou `--no-tts` pour réutiliser les voix `audio/vo_*.mp3`), puis `node render.js`.

- `video.html` : l'animation (ouvrir dans un navigateur pour un aperçu en boucle, `?t=12.5` pour figer une image).
- `render.js` : rendu image par image avec Playwright puis encodage ffmpeg (`node render.js`).
- `assets/` : logo extrait du site et police Plus Jakarta Sans.

| Temps | Scène — voix off |
|---|---|
| 0 – 3,3 s | Accroche + courbe, +15 %/an — « Votre facture d'énergie n'arrête pas de grimper ? » |
| 3,3 – 6,4 s | Energy Market Group — « Chez Energy Market, on négocie pour vous. » |
| 6,4 – 10,2 s | Groupement d'achat — « On regroupe les entreprises de votre secteur… pour décrocher de meilleurs prix. » |
| 10,2 – 14,6 s | 4 étapes — « Envoyez votre facture : on analyse, on négocie, et vous décidez. » |
| 14,6 – 17,6 s | 0 € / 100 % — « Zéro euro d'honoraires, et une obligation de résultat. » |
| 17,6 – 22 s | CTA — « Rendez-vous sur energy-market point fr ! » |
