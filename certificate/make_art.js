// Renders the decorative artwork for the Best Paper certificate (10 x 7.5 in slide):
//   assets/border.png  – full-slide golden frame (300 dpi), used as the slide background
//   assets/seal.png    – gold award seal with ribbon tails (transparent)
// Text is NOT baked in here; all wording stays as editable text boxes in the .pptx.
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const DPI = 300, W = 10 * DPI, H = 7.5 * DPI;
const A = path.join(__dirname, 'assets');

const GOLD = `
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#7A5716"/><stop offset="0.22" stop-color="#C99A2E"/>
    <stop offset="0.45" stop-color="#F7E08E"/><stop offset="0.62" stop-color="#D4A93D"/>
    <stop offset="0.82" stop-color="#9C7420"/><stop offset="1" stop-color="#E9C766"/>
  </linearGradient>
  <linearGradient id="goldH" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
    <stop offset="0" stop-color="#8E6A1C"/><stop offset="0.5" stop-color="#F2D57A"/><stop offset="1" stop-color="#8E6A1C"/>
  </linearGradient>
  <linearGradient id="goldV" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#8E6A1C"/><stop offset="0.5" stop-color="#F2D57A"/><stop offset="1" stop-color="#8E6A1C"/>
  </linearGradient>`;

const i = v => v * DPI; // inches -> px

// guilloche: interlaced sine waves along a straight band
function guillocheBand(x0, y0, len, thick, horizontal) {
  let out = '';
  const waves = 5, period = i(0.36);
  for (let k = 0; k < waves; k++) {
    const ph = (k / waves) * Math.PI * 2;
    const pts = [];
    for (let t = 0; t <= len; t += 6) {
      const o = thick / 2 + (thick / 2 - 6) * Math.sin((t / period) * Math.PI * 2 + ph);
      pts.push(horizontal ? [x0 + t, y0 + o] : [x0 + o, y0 + t]);
    }
    out += `<polyline points="${pts.map(p => p.map(n => n.toFixed(1)).join(',')).join(' ')}" fill="none" stroke="#B8902F" stroke-width="2.2" stroke-opacity="0.85"/>`;
  }
  return out;
}

// circuit trace with square pad (EPTC motif), drawn in fine gold
function trace(pts) {
  const d = 'M' + pts.map(p => p.map(i).join(' ')).join(' L');
  const [x, y] = pts.at(-1).map(i), s = i(0.07);
  return `<path d="${d}" fill="none" stroke="#C9A24A" stroke-width="4"/><rect x="${x - s / 2}" y="${y - s / 2}" width="${s}" height="${s}" fill="#fff" stroke="#C9A24A" stroke-width="4"/>`;
}

function cornerOrnament() {
  // drawn for the top-left corner, mirrored for the others
  const c = i(0.39); // centre of corner medallion on the guilloche band
  return `
    <rect x="${c - i(0.2)}" y="${c - i(0.2)}" width="${i(0.4)}" height="${i(0.4)}" fill="url(#gold)" stroke="#7A5716" stroke-width="4"/>
    <rect x="${c - i(0.14)}" y="${c - i(0.14)}" width="${i(0.28)}" height="${i(0.28)}" fill="#FFFDF7" stroke="#9C7420" stroke-width="3"/>
    <path d="M${c} ${c - i(0.11)} L${c + i(0.11)} ${c} L${c} ${c + i(0.11)} L${c - i(0.11)} ${c} Z" fill="url(#gold)" stroke="#7A5716" stroke-width="3"/>
    <circle cx="${c}" cy="${c}" r="${i(0.03)}" fill="#7A5716"/>
    <!-- art-deco stepped flourish inside the inner frame -->
    <path d="M${i(0.72)} ${i(1.55)} V${i(0.98)} Q${i(0.72)} ${i(0.72)} ${i(0.98)} ${i(0.72)} H${i(1.55)}" fill="none" stroke="url(#gold)" stroke-width="7"/>
    <path d="M${i(0.8)} ${i(1.2)} V${i(1.02)} Q${i(0.8)} ${i(0.8)} ${i(1.02)} ${i(0.8)} H${i(1.2)}" fill="none" stroke="#B8902F" stroke-width="3"/>
    <circle cx="${i(1.55)}" cy="${i(0.72)}" r="${i(0.025)}" fill="#B8902F"/><circle cx="${i(0.72)}" cy="${i(1.55)}" r="${i(0.025)}" fill="#B8902F"/>
    <path d="M${i(0.9)} ${i(0.9)} l${i(0.06)} ${i(-0.06)} l${i(0.06)} ${i(0.06)} l${i(-0.06)} ${i(0.06)} Z" fill="url(#gold)"/>`;
}

function borderSVG() {
  const o1 = i(0.15), o2 = i(0.63);        // outer band edge, inner frame edge
  const gb0 = i(0.27), gbT = i(0.24);       // guilloche band start / thickness
  const corners = [
    '', `transform="translate(${W} 0) scale(-1 1)"`, `transform="translate(0 ${H}) scale(1 -1)"`, `transform="translate(${W} ${H}) scale(-1 -1)"`,
  ].map(t => `<g ${t}>${cornerOrnament()}</g>`).join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <defs>${GOLD}
    <radialGradient id="paper" cx="0.5" cy="0.45" r="0.75">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FBF6EA"/>
    </radialGradient>
  </defs>
  <rect width="${W}" height="${H}" fill="url(#paper)"/>

  <!-- faint rosette watermark (guilloche rings) behind the recipient block -->
  <g transform="translate(${W / 2} ${i(3.65)})" opacity="0.07" fill="none" stroke="#9C7420" stroke-width="3">
    ${Array.from({ length: 36 }, (_, k) => `<ellipse rx="${i(1.6)}" ry="${i(0.55)}" transform="rotate(${k * 5})"/>`).join('')}
    ${Array.from({ length: 24 }, (_, k) => `<ellipse rx="${i(0.62)}" ry="${i(0.2)}" transform="rotate(${k * 7.5})"/>`).join('')}
    <circle r="${i(1.62)}"/><circle r="${i(1.7)}"/>
  </g>

  <!-- outer metallic band -->
  <rect x="${o1}" y="${o1}" width="${W - 2 * o1}" height="${H - 2 * o1}" fill="none" stroke="url(#gold)" stroke-width="${i(0.09)}"/>
  <rect x="${o1 + i(0.06)}" y="${o1 + i(0.06)}" width="${W - 2 * o1 - i(0.12)}" height="${H - 2 * o1 - i(0.12)}" fill="none" stroke="#7A5716" stroke-width="2"/>
  <!-- guilloche band -->
  ${guillocheBand(gb0, gb0, W - 2 * gb0, gbT, true)}
  ${guillocheBand(gb0, H - gb0 - gbT, W - 2 * gb0, gbT, true)}
  ${guillocheBand(gb0, gb0, H - 2 * gb0, gbT, false)}
  ${guillocheBand(W - gb0 - gbT, gb0, H - 2 * gb0, gbT, false)}
  <rect x="${gb0}" y="${gb0}" width="${W - 2 * gb0}" height="${H - 2 * gb0}" fill="none" stroke="#B8902F" stroke-width="3"/>
  <rect x="${gb0 + gbT}" y="${gb0 + gbT}" width="${W - 2 * (gb0 + gbT)}" height="${H - 2 * (gb0 + gbT)}" fill="none" stroke="#B8902F" stroke-width="3"/>
  <!-- inner double rule -->
  <rect x="${o2}" y="${o2}" width="${W - 2 * o2}" height="${H - 2 * o2}" fill="none" stroke="url(#gold)" stroke-width="${i(0.025)}"/>
  <rect x="${o2 + i(0.05)}" y="${o2 + i(0.05)}" width="${W - 2 * o2 - i(0.1)}" height="${H - 2 * o2 - i(0.1)}" fill="none" stroke="#C9A24A" stroke-width="2"/>

  ${corners}

  <!-- fine gold circuit traces in the lower corners (packaging motif) -->
  <g opacity="0.55">
    ${trace([[0.68, 5.2], [0.95, 5.2], [1.1, 5.35], [1.45, 5.35]])}
    ${trace([[0.68, 5.45], [0.85, 5.45], [1.0, 5.6], [1.2, 5.6]])}
    ${trace([[9.32, 5.2], [9.05, 5.2], [8.9, 5.35], [8.55, 5.35]])}
    ${trace([[9.32, 5.45], [9.15, 5.45], [9.0, 5.6], [8.8, 5.6]])}
  </g>
</svg>`;
}

function sealSVG() {
  const S = 1200, c = S / 2, n = 36;
  let burst = '';
  for (let k = 0; k < n * 2; k++) {
    const r = k % 2 ? 470 : 520, a = (k / (n * 2)) * Math.PI * 2;
    burst += `${k ? 'L' : 'M'}${(c + r * Math.cos(a)).toFixed(1)} ${(c + r * Math.sin(a)).toFixed(1)} `;
  }
  // laurel branches: leaves set along an arc on each side of the star, paired in/out
  const laurel = side => {
    const R = 228; let g = '';
    const arcPts = [];
    for (let deg = 128; deg <= 232; deg += 2) {
      const a = deg * Math.PI / 180; arcPts.push([c + side * -R * Math.cos(Math.PI - a) * -1, c + R * Math.sin(a) * -1 * -1]);
    }
    for (let k = 0, deg = 132; deg <= 228; deg += 13, k++) {
      const a = deg * Math.PI / 180;
      for (const off of [-24, 24]) {
        const r = R + off;
        let x = c + r * Math.cos(a), y = c + r * Math.sin(a) * -1;
        y = c - (y - c);                                 // left side, going from lower-left up to upper-left
        if (side < 0) x = 2 * c - x;                     // mirror for the right branch
        let rot = (side > 0 ? 1 : -1) * (180 - deg) + (off > 0 ? 28 : -28) * (side > 0 ? 1 : -1);
        g += `<ellipse cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" rx="15" ry="36" transform="rotate(${rot.toFixed(1)} ${x.toFixed(1)} ${y.toFixed(1)})" fill="url(#gold)" stroke="#6E4E12" stroke-width="3"/>`;
      }
    }
    // stem
    const pts = [];
    for (let deg = 128; deg <= 232; deg += 4) {
      const a = deg * Math.PI / 180; let x = c + R * Math.cos(a), y = c + R * Math.sin(a);
      if (side < 0) x = 2 * c - x; pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
    }
    return `<polyline points="${pts.join(' ')}" fill="none" stroke="#6E4E12" stroke-width="5"/>` + g;
  };
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${S}" height="${S + 360}" viewBox="0 0 ${S} ${S + 360}">
  <defs>${GOLD}
    <path id="ring" d="M ${c} ${c} m -360 0 a 360 360 0 1 1 720 0 a 360 360 0 1 1 -720 0"/>
  </defs>
  <!-- ribbon tails -->
  <path d="M${c - 210} ${c + 300} L${c - 330} ${S + 330} L${c - 230} ${S + 270} L${c - 160} ${S + 350} L${c - 60} ${c + 360} Z" fill="#1F2A44"/>
  <path d="M${c + 210} ${c + 300} L${c + 330} ${S + 330} L${c + 230} ${S + 270} L${c + 160} ${S + 350} L${c + 60} ${c + 360} Z" fill="#1F2A44"/>
  <path d="M${c - 205} ${c + 320} L${c - 300} ${S + 300} M${c + 205} ${c + 320} L${c + 300} ${S + 300}" stroke="#C9A24A" stroke-width="10"/>
  <!-- seal -->
  <path d="${burst}Z" fill="url(#gold)" stroke="#6E4E12" stroke-width="5"/>
  <circle cx="${c}" cy="${c}" r="440" fill="url(#gold)" stroke="#6E4E12" stroke-width="6"/>
  <circle cx="${c}" cy="${c}" r="420" fill="none" stroke="#FFF3C4" stroke-width="4" opacity="0.8"/>
  <circle cx="${c}" cy="${c}" r="300" fill="#FFFBEF" stroke="#6E4E12" stroke-width="6"/>
  <circle cx="${c}" cy="${c}" r="285" fill="none" stroke="#B8902F" stroke-width="4"/>
  <text font-family="Caladea, Cambria, serif" font-weight="700" font-size="62" letter-spacing="9" fill="#4A3409">
    <textPath href="#ring" startOffset="0">ELECTRONICS PACKAGING TECHNOLOGY CONFERENCE ★</textPath>
  </text>
  ${laurel(1)}${laurel(-1)}
  <path d="M${c} ${c - 165} l 38 92 l 100 6 l -77 64 l 25 97 l -86 -54 l -86 54 l 25 -97 l -77 -64 l 100 -6 Z" fill="url(#gold)" stroke="#6E4E12" stroke-width="5"/>
  <text x="${c}" y="${c + 170}" text-anchor="middle" font-family="Caladea, Cambria, serif" font-weight="700" font-size="60" letter-spacing="10" fill="#4A3409">EPTC</text>
</svg>`;
}

(async () => {
  fs.mkdirSync(A, { recursive: true });
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: W, height: H } });
  await p.setContent(`<body style="margin:0">${borderSVG()}</body>`);
  await p.screenshot({ path: path.join(A, 'border.png'), clip: { x: 0, y: 0, width: W, height: H } });
  await p.setViewportSize({ width: 1200, height: 1560 });
  await p.setContent(`<body style="margin:0;background:transparent">${sealSVG()}</body>`);
  await p.evaluate(() => document.fonts.ready);
  await p.screenshot({ path: path.join(A, 'seal.png'), omitBackground: true, clip: { x: 0, y: 0, width: 1200, height: 1560 } });
  await b.close();
  console.log('art written to', A);
})();
