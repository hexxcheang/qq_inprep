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




// Formal frame: a solid gold outer rule and a thin inner rule with concave (notched) corners.
function borderSVG() {
  const o = i(0.3), ow = i(0.05);          // outer rule inset and weight
  const n = i(0.44), nw = i(0.014);        // inner rule inset and weight
  const r = i(0.2);                        // corner notch radius
  const x0 = n, y0 = n, x1 = W - n, y1 = H - n;
  const inner = `M${x0 + r} ${y0} H${x1 - r} A${r} ${r} 0 0 0 ${x1} ${y0 + r} V${y1 - r} A${r} ${r} 0 0 0 ${x1 - r} ${y1}
    H${x0 + r} A${r} ${r} 0 0 0 ${x0} ${y1 - r} V${y0 + r} A${r} ${r} 0 0 0 ${x0 + r} ${y0} Z`;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="#FFFFFF"/>
  <rect x="${o}" y="${o}" width="${W - 2 * o}" height="${H - 2 * o}" fill="none" stroke="#A9842F" stroke-width="${ow}"/>
  <path d="${inner}" fill="none" stroke="#A9842F" stroke-width="${nw}"/>
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
