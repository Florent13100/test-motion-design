// Rend video.html image par image puis encode un MP4 1080x1920 (9:16) H.264.
// Usage : node render.js [--fps 30] [--out energy-market-9x16.mp4] [--frames dir]
//         node render.js --stills 1,5,9   (captures PNG de contrôle uniquement)
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

let chromium;
try { ({ chromium } = require('playwright')); }
catch { ({ chromium } = require(path.join(execFileSync('npm', ['root', '-g']).toString().trim(), 'playwright'))); }

const arg = (name, def) => { const i = process.argv.indexOf('--' + name); return i > -1 ? process.argv[i + 1] : def; };
const FPS = +arg('fps', 30);
const OUT = path.resolve(arg('out', 'energy-market-9x16.mp4'));
const FRAMES = path.resolve(arg('frames', fs.mkdtempSync(path.join(require('os').tmpdir(), 'frames-'))));
const STILLS = arg('stills');

function ffmpegPath() {
  if (process.env.FFMPEG) return process.env.FFMPEG;
  try { return execFileSync('python3', ['-c', 'import imageio_ffmpeg as i;print(i.get_ffmpeg_exe())']).toString().trim(); }
  catch { return 'ffmpeg'; }
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto('file://' + path.resolve(__dirname, 'video.html') + '?capture');
  await page.evaluate(() => document.fonts.ready);
  const duration = await page.evaluate(() => window.DURATION);

  fs.mkdirSync(FRAMES, { recursive: true });
  const times = STILLS ? STILLS.split(',').map(Number) : [...Array(Math.round(duration * FPS)).keys()].map(i => i / FPS);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.render(t), times[i]);
    const file = STILLS ? `still_${times[i]}.png` : `f_${String(i).padStart(5, '0')}.png`;
    await page.screenshot({ path: path.join(FRAMES, file) });
    if (!STILLS && i % FPS === 0) process.stdout.write(`\r${(i / FPS).toFixed(0)}s / ${duration}s`);
  }
  await browser.close();
  if (STILLS) { console.log('stills ->', FRAMES); return; }

  console.log('\nEncodage…');
  execFileSync(ffmpegPath(), [
    '-y', '-framerate', String(FPS), '-i', path.join(FRAMES, 'f_%05d.png'),
    '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
    '-map', '0:v', '-map', '1:a', '-shortest',
    '-c:v', 'libx264', '-profile:v', 'high', '-level', '4.1', '-preset', 'slow', '-crf', '18',
    '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', OUT,
  ], { stdio: 'inherit' });
  console.log('OK ->', OUT);
})();
