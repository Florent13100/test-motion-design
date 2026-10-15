#!/usr/bin/env bash
# Habille la vidéo HeyGen « Réduisez la facture d'énergie de votre boulangerie » (heygen-boulangerie/source.mp4) aux couleurs Energy Market.
# Usage : bash heygen-boulangerie/compose.sh   -> energy-market-boulangerie-9x16.mp4
set -euo pipefail
cd "$(dirname "$0")/.."
# FRAMES=dossier : réutilise un calque déjà rendu (sinon rendu dans un dossier temporaire)
TMP=""; if [ -z "${FRAMES:-}" ]; then FRAMES=$(mktemp -d); TMP=$FRAMES; fi
python3 heygen-boulangerie/make_audio.py
[ -f "$FRAMES/f_00000.png" ] || node render.js --page heygen-boulangerie/overlay.html --transparent --frames "$FRAMES"
# -reinit_filter 0 : les PNG passent de RGBA à RGB sur l'écran de fin opaque, sans ça ffmpeg coupe la séquence.
# Vidéo source HeyGen 720x1280 plein cadre : remplit la fenêtre 1020x1568 en (30,316) de overlay.html, dernière image figée sous l'écran de fin
ffmpeg -v error -y -i heygen-boulangerie/source.mp4 -reinit_filter 0 -framerate 30 -i "$FRAMES/f_%05d.png" -i heygen-boulangerie/soundtrack.wav \
  -filter_complex "[0:v]scale=1020:1813:flags=lanczos,crop=1020:1568:0:245,fps=30,tpad=stop_mode=clone:stop_duration=4,pad=1080:1920:30:316:color=0xf7f2e9[v];[1:v]format=rgba[o];[v][o]overlay=shortest=1,format=yuv420p[out]" \
  -map "[out]" -map 2:a -t 42.4 -c:v libx264 -profile:v high -level 4.1 -preset slow -crf 18 -c:a aac -b:a 192k -movflags +faststart \
  energy-market-boulangerie-9x16.mp4
[ -n "$TMP" ] && rm -rf "$TMP"
echo "OK -> energy-market-boulangerie-9x16.mp4"
