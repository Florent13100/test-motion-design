# Energy Market — vidéo motion design 9:16

`energy-market-9x16.mp4` : 1080×1920, 30 fps, H.264 + AAC 192 kb/s (−14 LUFS), 30 s
(la voix off se termine à ~27,6 s, puis 2 s de marge sur l'écran d'appel à l'action).

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
| 0 – 4,5 s | Accroche + courbe, +15 %/an — « Votre facture d'énergie n'arrête pas de grimper ? » |
| 4,5 – 9 s | Energy Market Group — « Chez Energy Market, on négocie pour vous. » |
| 9 – 14,5 s | Groupement d'achat — « On regroupe les entreprises de votre secteur… pour décrocher de meilleurs prix. » |
| 14,5 – 20,5 s | 4 étapes — « Envoyez votre facture : on analyse, on négocie, et vous décidez. » |
| 20,5 – 25 s | 0 € / 100 % — « Zéro euro d'honoraires, et une obligation de résultat. » |
| 25 – 30 s | CTA — « Rendez-vous sur energy-market point fr ! » |

---

# Energy Market — « On recherche des apporteurs d'affaires » (9:16, Instagram)

`energy-market-apporteur-9x16.mp4` : 1080×1920, 30 fps, H.264 + AAC, ~26 s. Même style que le visuel témoignage
(fond crème, logo, cadre marine à coins dorés, citation encadrée d'or, barre marine + pastille dorée), avec un
personnage illustré, **Thomas**, qui parle face caméra (bouche synchronisée sur la voix, clignements, gestes).

- `apporteur/video.html` : l'animation (`?t=12.5` pour figer une image).
- `apporteur/audio/script.json` : le texte de Thomas (voix `fr-FR-RemyMultilingualNeural`).
- `apporteur/audio/make_audio.py` : voix + musique synthétisée + bruitages, et génère `apporteur/timing.js`
  (calage mot à mot des sous-titres + ouverture de bouche image par image).
- Régénérer : `python3 apporteur/audio/make_audio.py` (ou `--no-tts`), puis
  `node render.js --page apporteur/video.html --audio apporteur/audio/soundtrack.wav --out energy-market-apporteur-9x16.mp4`.

| Temps | Réplique | À l'image |
|---|---|---|
| 0,8 – 3,8 s | « Salut ! Moi c'est Thomas, d'Energy Market. » | Coucou de la main |
| 4,3 – 6,1 s | « On recherche des apporteurs d'affaires. » | Bandeau « Apporteurs d'affaires » |
| 6,5 – 11,2 s | « Vous connaissez un pro ? Un commerçant, un restaurateur, un artisan ? » | Index levé, 3 pastilles métiers |
| 11,6 – 15,3 s | « Donnez-nous juste son contact, et on l'appelle de votre part. » | Téléphone + fiche contact, bulle d'appel |
| 15,7 – 18,6 s | « On négocie son contrat d'énergie, gratuitement pour lui. » | Carte contrat + « 0 € pour lui » |
| 19,0 – 20,8 s | « Et s'il signe… on vous rémunère ! » | Tampon « Contrat signé », billets, pluie de pièces |
| 21,2 – 26 s | « Rendez-vous sur energy-market.fr ! » | Pouce levé + URL |

---

# Habillage Energy Market d'une vidéo HeyGen (9:16)

`energy-market-heygen-9x16.mp4` : la vidéo avatar HeyGen (export 720p sans filigrane, image utile 3:4) recadrée dans le
cadre marine/or du visuel témoignage, avec logo, étiquettes d'étapes et sous-titres mot à mot calés sur la voix,
barre du bas + pastille dorée, pluie de pièces sur « commission », musique de fond (ducking) et écran de fin
(3 étapes + energy-market.fr), 30,1 s, −14 LUFS.

- `heygen/overlay.html` : calque transparent (étapes dans `PHASES`, sous-titres dans `CAPTIONS`).
- `heygen/make_audio.py` : voix d'origine + musique + bruitages.
- `heygen/compose.sh` : rendu du calque puis incrustation ffmpeg. Déposer la vidéo HeyGen dans `heygen/source.mp4`
  (non versionnée) puis `bash heygen/compose.sh`. Si le texte change, recaler `PHASES` (overlay.html) et
  `PHASES`/`COMMISSION_AT` (make_audio.py), et les sous-titres `CAPTIONS` (overlay.html) ; calage mot à mot obtenu avec
  faster-whisper (`word_timestamps=True`).

---

# Habillage HeyGen « Réduisez vos factures » (9:16)

`energy-market-factures-9x16.mp4` : même habillage que la vidéo apporteurs (sans « AGENCE VIRTUELLE », logo agrandi),
étapes / sous-titres / écran de fin adaptés au message (analyse gratuite, 0 € d'honoraires, diagnostic en 24 h), 27,1 s.
Dossier `heygen-factures/` (même fonctionnement que `heygen/`) : déposer la vidéo dans `heygen-factures/source.mp4`
puis `bash heygen-factures/compose.sh`.

---

# Habillage HeyGen « Pourquoi le prix de l'électricité explose » (9:16)

`energy-market-marche-9x16.mp4` : décryptage marché (58 s) avec le même habillage que « Réduisez vos factures »,
compteur animé du prix spot (≈100 puis ≈200 €/MWh), étiquettes des 3 causes (gaz, stocks, vent), solutions et
écran de fin. Dossier `heygen-marche/` : déposer la vidéo dans `heygen-marche/source.mp4` puis `bash heygen-marche/compose.sh`.

---

# Habillage HeyGen « Évitez de surpayer votre prochain contrat » (9:16)

`energy-market-contrat-9x16.mp4` (52,6 s) : même habillage, étiquettes des 2 erreurs à éviter et de la bonne méthode
en 3 étapes, sous-titres mot à mot, écran de fin « Contrat à renouveler ? ». Cadrage resserré (avatar debout, petit
dans l'image source). Dossier `heygen-contrat/` : vidéo dans `heygen-contrat/source.mp4` puis `bash heygen-contrat/compose.sh`.
