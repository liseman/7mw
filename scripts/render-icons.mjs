// Renders the app icon set (icon, adaptive icon, splash, favicon) from
// vector definitions. Usage: node scripts/render-icons.mjs
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const assets = path.join(__dirname, '..', 'assets');

const PAPER = '#F4EFE6';
const ORANGE = '#FF5A00';

// Blocky "7" drawn as a stroked polyline: top bar, then the diagonal.
const seven = (color) =>
  `<path d="M310 295 L714 295 L468 800" fill="none" stroke="${color}" stroke-width="150" stroke-linecap="square" stroke-linejoin="miter"/>`;

// Flat and minimal: one bold paper "7" on a solid orange field.
const iconSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <rect width="1024" height="1024" fill="${ORANGE}"/>
  ${seven(PAPER)}
</svg>`;

// Adaptive foreground: transparent background (app.json supplies the orange),
// motif shrunk into the 66% safe zone.
const adaptiveSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <g transform="translate(512 512) scale(0.62) translate(-512 -512)">
    ${seven(PAPER)}
  </g>
</svg>`;

const splashSvg = `<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024">
  <g transform="translate(512 512) scale(0.55) translate(-512 -512)">
    ${seven(ORANGE)}
  </g>
</svg>`;

async function render(svg, size, file) {
  await sharp(Buffer.from(svg)).resize(size, size).png().toFile(path.join(assets, file));
  console.log(file);
}

await render(iconSvg, 1024, 'icon.png');
await render(adaptiveSvg, 1024, 'adaptive-icon.png');
await render(splashSvg, 1024, 'splash-icon.png');
await render(iconSvg, 48, 'favicon.png');
