// EPTC 2026 registration counter backdrop — 6 m x 3 m (2:1), Sands Expo & Convention Centre.
// Usage:  node build_backdrop.js
//
// The artwork is drawn in real millimetres (6000 x 3000) and written to a PDF at 1:10 scale
// (600 x 300 mm), because PDF pages cannot be 6 m wide. The printer scales it to 1000 %.
//
// Outputs (out/):
//   EPTC2026_registration_backdrop_6x3m_scale1-10_bleed.pdf  – print file, 50 mm bleed (5 mm at 1:10)
//   EPTC2026_registration_backdrop_6x3m_scale1-10.pdf        – trim size, for review
//   EPTC2026_registration_backdrop_preview.png               – screen preview
//   EPTC2026_registration_backdrop_counter_mockup.png        – preview with a 1 m counter in front

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const W = 6000, H = 3000;      // mm, finished size
const BLEED = 50;              // mm, full scale
const SCALE = 10;              // PDF is 1:SCALE
const COUNTER_H = 1000;        // mm, assumed registration counter height (mock-up only)
const OUT = path.join(__dirname, 'out');
const REPORT = new Map();   // logo print resolution at full size

const C = {
  dark: '#6B2516', mid: '#B23E19', orange: '#E8641C', ink: '#2B1A14', sub: '#5E4B43',
  trace: '#F1D5C4', hair: '#E3CBBE',
};
const TIERS = {
  diamond:  { label: 'Diamond Sponsor',  color: '#3E7CB1' },
  platinum: { label: 'Platinum Sponsors', color: '#7C8088' },
  gold:     { label: 'Gold Sponsors',     color: '#B8860B' },
  silver:   { label: 'Silver Sponsors',   color: '#8E959C' },
  bronze:   { label: 'Bronze Sponsors',   color: '#A0522D' },
};

const dataURI = f => {
  const ext = path.extname(f).slice(1).replace('jpg', 'jpeg');
  return `data:image/${ext};base64,` + fs.readFileSync(path.join(__dirname, f)).toString('base64');
};
const sponsors = JSON.parse(fs.readFileSync(path.join(__dirname, 'sponsors.json'), 'utf8'));
for (const s of sponsors) {
  if (s.file) { s.uri = dataURI(s.file); s.aspect = s.px[0] / s.px[1]; }
}

// ---- EPTC logo (vector) -----------------------------------------------------
const logoSVG = fs.readFileSync(path.join(__dirname, 'assets/eptc2026_logo_vector.svg'), 'utf8');
const logoVB = logoSVG.match(/viewBox="([^"]+)"/)[1].split(' ').map(Number);
const logoInner = logoSVG.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
function logo(x, y, w) {
  const h = w * logoVB[3] / logoVB[2];
  return { h, svg: `<svg x="${x}" y="${y}" width="${w}" height="${h}" viewBox="${logoVB.join(' ')}">${logoInner}</svg>` };
}

// ---- motifs -------------------------------------------------------------------
function trace(pts, { color = C.trace, w = 7, pad = 28, pads = 'end', fill = '#fff' } = {}) {
  const d = 'M' + pts.map(p => p.join(' ')).join(' L');
  const sq = ([x, y]) => `<rect x="${x - pad / 2}" y="${y - pad / 2}" width="${pad}" height="${pad}" fill="${fill}" stroke="${color}" stroke-width="${w}"/>`;
  const ends = pads === 'both' ? [pts[0], pts.at(-1)] : pads === 'none' ? [] : [pts.at(-1)];
  return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round"/>` + ends.map(sq).join('');
}

// Marina Bay Sands rising out of the bottom brand bar (same gradient), 100 x 40 local units.
function mbs(ox, base, s) {
  const tower = x => {
    const r = x + 10;
    return `<path d="M${x} 9.2 L${r} 9.0 L${r} 30 Q${r + 0.5} 38 ${r + 3.2} 41.5 L${x - 0.4} 41.5 Z" fill="url(#brandLocal)"/>` +
      [2.5, 5, 7.5].map(o => `<line x1="${x + o}" y1="11" x2="${x + o}" y2="40" stroke="#fff" stroke-opacity="0.16" stroke-width="0.3"/>`).join('');
  };
  return `<g transform="translate(${ox} ${base - 40 * s}) scale(${s})">
    <linearGradient id="brandLocal" gradientUnits="userSpaceOnUse" x1="${(-BLEED - ox) / s}" x2="${(W + BLEED - ox) / s}" y1="0" y2="0">
      <stop offset="0" stop-color="${C.dark}"/><stop offset="0.5" stop-color="${C.mid}"/><stop offset="1" stop-color="${C.orange}"/>
    </linearGradient>
    ${tower(16)}${tower(41)}${tower(66)}
    <path d="M3 8.1 Q9 6.1 20 5.9 L91 5.3 Q97.5 5.4 100 6.9 Q97.5 8.6 91 8.8 L20 9.5 Q9 9.6 3 8.1 Z" fill="url(#brandLocal)"/>
  </g>`;
}

// ---- sponsor wall ---------------------------------------------------------------
// Logos are sized by area (not width) so wide and square marks look equally weighted.
function placeLogo(s, cx, cy, boxW, boxH, area) {
  if (!s.file) {
    const w = boxW * 0.82, h = boxH * 0.8;
    return `<rect x="${cx - w / 2}" y="${cy - h / 2}" width="${w}" height="${h}" rx="10" fill="none" stroke="#C9B3A8" stroke-width="4" stroke-dasharray="18 12"/>
      <text x="${cx}" y="${cy + 2}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="${h * 0.34}" fill="#A68E83">${s.name === 'ASE' ? 'ASE' : 'SPONSOR'}</text>
      <text x="${cx}" y="${cy + h * 0.36}" text-anchor="middle" font-family="Inter" font-weight="600" font-size="${h * 0.2}" fill="#A68E83">logo to be supplied</text>`;
  }
  let h = Math.sqrt(area / s.aspect), w = h * s.aspect;
  const k = Math.min(1, boxW / w, boxH / h); w *= k; h *= k;
  REPORT.set(s.name, { tier: s.tier, printed_mm: Math.round(w), px: s.px[0], dpi: Math.round(s.px[0] / (w / 25.4)) });
  return `<image href="${s.uri}" x="${cx - w / 2}" y="${cy - h / 2}" width="${w}" height="${h}" preserveAspectRatio="xMidYMid meet"/>`;
}
function tierLabel(t, cx, y, span) {
  const { label, color } = TIERS[t];
  const tw = label.length * 37 + 90;
  return `<line x1="${cx - span / 2}" y1="${y - 13}" x2="${cx - tw / 2}" y2="${y - 13}" stroke="${color}" stroke-width="4"/>
    <line x1="${cx + tw / 2}" y1="${y - 13}" x2="${cx + span / 2}" y2="${y - 13}" stroke="${color}" stroke-width="4"/>
    <rect x="${cx - span / 2 - 9}" y="${y - 22}" width="18" height="18" fill="${color}"/>
    <rect x="${cx + span / 2 - 9}" y="${y - 22}" width="18" height="18" fill="${color}"/>
    <text x="${cx}" y="${y}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="40" letter-spacing="7" fill="${color}">${label.toUpperCase()}</text>`;
}
function sponsorWall(x0, y0, w, h) {
  const cx = x0 + w / 2, inner = w - 200;
  const rows = [
    // tier, label y, row centre ys, box w, box h, area (mm²), per-row counts
    ['diamond', y0 + 260, [y0 + 430], 1150, 250, 1150 * 250 * 0.62],
    ['platinum', y0 + 640, [y0 + 775], 820, 180, 820 * 180 * 0.58],
    ['gold', y0 + 945, [y0 + 1060], 640, 150, 640 * 150 * 0.55],
    ['silver', y0 + 1210, [y0 + 1318], 520, 155, 520 * 130 * 0.55],
    ['bronze', y0 + 1460, [y0 + 1557, y0 + 1700], 310, 118, 310 * 100 * 0.6],
  ];
  let g = `<rect x="${x0}" y="${y0}" width="${w}" height="${h}" rx="36" fill="#FFFFFF" stroke="${C.hair}" stroke-width="5"/>
    <text x="${cx}" y="${y0 + 135}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="68" letter-spacing="10" fill="${C.dark}">THANK YOU TO OUR SPONSORS</text>`;
  for (const [t, ly, rowYs, bw, bh, area] of rows) {
    const list = sponsors.filter(s => s.tier === t);
    g += tierLabel(t, cx, ly, inner);
    const per = Math.ceil(list.length / rowYs.length);
    rowYs.forEach((ry, ri) => {
      const items = list.slice(ri * per, ri * per + per);
      const gap = Math.min(110, (inner - items.length * bw) / Math.max(1, items.length - 1));
      const total = items.length * bw + (items.length - 1) * gap;
      items.forEach((s, i) => { g += placeLogo(s, cx - total / 2 + bw / 2 + i * (bw + gap), ry, bw, bh, area); });
    });
  }
  return g;
}

// ---- the backdrop -------------------------------------------------------------
function backdropSVG() {
  const b = BLEED;
  const L = logo(330, 250, 2340);
  const regY = 1500, regH = 330;
  const stub = 'rgba(255,255,255,0.5)';
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-b} ${-b} ${W + 2 * b} ${H + 2 * b}"
     width="${(W + 2 * b) / SCALE}mm" height="${(H + 2 * b) / SCALE}mm" style="position:absolute;left:0;top:0">
  <defs>
    <linearGradient id="brand" gradientUnits="userSpaceOnUse" x1="${-b}" x2="${W + b}" y1="0" y2="0">
      <stop offset="0" stop-color="${C.dark}"/><stop offset="0.5" stop-color="${C.mid}"/><stop offset="1" stop-color="${C.orange}"/>
    </linearGradient>
    <linearGradient id="paper" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset="0.5" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FBEDE3"/>
    </linearGradient>
    <pattern id="bga" width="64" height="64" patternUnits="userSpaceOnUse"><circle cx="32" cy="32" r="11" fill="${C.trace}"/></pattern>
  </defs>

  <rect x="${-b}" y="${-b}" width="${W + 2 * b}" height="${H + 2 * b}" fill="url(#paper)"/>

  <!-- solder-ball (BGA) texture -->
  <path d="M${-b} 70 H560 Q300 300 ${-b} 520 Z" fill="url(#bga)"/>
  <path d="M${W + b} 2000 V2780 H5200 Q5700 2600 ${W + b} 2000 Z" fill="url(#bga)"/>

  <!-- circuit traces (logo motif) -->
  ${trace([[-b, 640], [120, 640], [200, 720], [300, 720]])}
  ${trace([[-b, 800], [80, 800]])}
  ${trace([[2650, 1080], [2860, 1080], [2950, 990], [3060, 990]], { pads: 'both' })}
  ${trace([[-b, 1960], [380, 1960], [470, 2050], [900, 2050]])}
  ${trace([[1200, 1960], [1650, 1960], [1740, 2050], [2300, 2050]], { pads: 'both' })}
  ${trace([[2500, 2200], [2900, 2200], [3000, 2100], [3500, 2100]], { pads: 'both' })}
  ${trace([[3700, 2250], [4300, 2250], [4400, 2350], [4800, 2350]], { pads: 'both' })}
  ${trace([[W + b, 600], [5950, 600]])}
  ${trace([[W + b, 1500], [5960, 1500]])}

  <!-- top brand bar -->
  <rect x="${-b}" y="${-b}" width="${W + 2 * b}" height="${70 + b}" fill="url(#brand)"/>

  <!-- left: identity -->
  ${L.svg}
  <text x="1500" y="${250 + L.h + 165}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="102" fill="${C.dark}">28<tspan font-size="60" dy="-40">th</tspan><tspan dy="40"> Electronics Packaging Technology Conference</tspan></text>
  <text x="1500" y="${250 + L.h + 285}" text-anchor="middle" font-family="Inter" font-weight="600" font-size="74" fill="#8A4A32">1 – 4 December 2026  ·  Sands Expo and Convention Centre, Singapore</text>
  <text x="1500" y="${250 + L.h + 385}" text-anchor="middle" font-family="Inter" font-weight="500" font-style="italic" font-size="62" fill="${C.sub}">IEEE EPS Flagship Conference in the Asia-Pacific Region</text>

  <!-- REGISTRATION ribbon (pointed end, like a chip lead) -->
  <path d="M${-b} ${regY} H2780 L2960 ${regY + regH / 2} L2780 ${regY + regH} H${-b} Z" fill="url(#brand)"/>
  ${trace([[-b, regY + 95], [90, regY + 95], [150, regY + 155], [230, regY + 155]], { color: stub, w: 7, pad: 26, fill: C.dark })}
  ${trace([[-b, regY + 245], [140, regY + 245]], { color: stub, w: 7, pad: 26, fill: C.dark })}
  <text x="1530" y="${regY + regH / 2 + 72}" text-anchor="middle" font-family="Inter" font-weight="800" font-size="205" letter-spacing="34" fill="#FFFFFF">REGISTRATION</text>

  <!-- right: sponsor wall -->
  ${sponsorWall(3150, 170, 2700, 1800)}

  <!-- bottom brand bar with Marina Bay Sands rising out of it -->
  <rect x="${-b}" y="2790" width="${W + 2 * b}" height="${210 + b}" fill="url(#brand)"/>
  ${mbs(160, 2790, 12)}
  <text x="${W - 140}" y="2922" text-anchor="end" font-family="Inter" font-weight="600" font-size="78" letter-spacing="4" fill="#FFFFFF">eptc-ieee.net</text>
</svg>`;
}

function pageHTML(bleed, mock = false) {
  const pw = (W + 2 * BLEED) / SCALE, ph = (H + 2 * BLEED) / SCALE;
  const cw = (W + 2 * bleed) / SCALE, ch = (H + 2 * bleed) / SCALE;
  const off = (BLEED - bleed) / SCALE;
  const counter = mock ? `<div style="position:absolute;left:${(BLEED + 700) / SCALE}mm;top:${(BLEED + H - COUNTER_H) / SCALE}mm;width:${4600 / SCALE}mm;height:${COUNTER_H / SCALE}mm;background:rgba(40,40,46,.88);border-top:${12 / SCALE}mm solid #555;color:#ddd;font:600 ${60 / SCALE}mm Inter;display:flex;align-items:center;justify-content:center">registration counter (1 m high) – mock-up only</div>` : '';
  return `<!doctype html><html><head><meta charset="utf-8"><style>
    @page { size: ${cw}mm ${ch}mm; margin: 0 }
    html,body { margin:0; width:${cw}mm; height:${ch}mm; overflow:hidden; background:#fff; -webkit-print-color-adjust:exact; print-color-adjust:exact }
    .clip { position:relative; width:${cw}mm; height:${ch}mm; overflow:hidden }
    .art { position:absolute; left:-${off}mm; top:-${off}mm; width:${pw}mm; height:${ph}mm }
  </style></head><body><div class="clip"><div class="art">${backdropSVG()}${counter}</div></div></body></html>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const name = 'EPTC2026_registration_backdrop';
  for (const [bleed, file] of [[BLEED, `${name}_6x3m_scale1-${SCALE}_bleed.pdf`], [0, `${name}_6x3m_scale1-${SCALE}.pdf`]]) {
    await page.setContent(pageHTML(bleed), { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const w = (W + 2 * bleed) / SCALE, h = (H + 2 * bleed) / SCALE;
    let pdf = await page.pdf({ width: `${w}mm`, height: `${h}mm`, printBackground: true, preferCSSPageSize: true });
    try { // crop to exact mm (Chromium rounds to px) and set TrimBox
      const { PDFDocument } = require('pdf-lib');
      const doc = await PDFDocument.load(pdf); const p = doc.getPage(0); const pt = mm => mm * 72 / 25.4;
      const ph = p.getSize().height;
      p.setMediaBox(0, ph - pt(h), pt(w), pt(h)); p.setCropBox(0, ph - pt(h), pt(w), pt(h));
      if (bleed) p.setTrimBox(pt(bleed / SCALE), ph - pt(h) + pt(bleed / SCALE), pt(W / SCALE), pt(H / SCALE));
      while (doc.getPageCount() > 1) doc.removePage(1);
      pdf = await doc.save();
    } catch (e) { console.warn('pdf-lib unavailable, PDF not cropped:', e.message); }
    fs.writeFileSync(path.join(OUT, file), pdf);
  }
  // previews (trim size)
  const pxW = 3000, pxH = 1500;
  const prev = await browser.newPage({ viewport: { width: Math.round(W / SCALE * 96 / 25.4), height: Math.round(H / SCALE * 96 / 25.4) },
    deviceScaleFactor: pxW / Math.round(W / SCALE * 96 / 25.4) });
  for (const [mock, file] of [[false, `${name}_preview.png`], [true, `${name}_counter_mockup.png`]]) {
    await prev.setContent(pageHTML(0, mock), { waitUntil: 'load' });
    await prev.evaluate(() => document.fonts.ready);
    await prev.screenshot({ path: path.join(OUT, file) });
  }
  await browser.close();
  console.log('Sponsor logo resolution at full 6 m size (aim for ≥ 100 dpi, or vector):');
  for (const [n, r] of REPORT) console.log(`  ${r.dpi < 100 ? 'LOW ' : 'ok  '} ${r.tier.padEnd(8)} ${n.padEnd(20)} ${String(r.printed_mm).padStart(5)} mm wide  ${String(r.dpi).padStart(4)} dpi`);
  console.log('done ->', OUT);
})();
