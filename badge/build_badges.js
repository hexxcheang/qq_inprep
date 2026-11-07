// EPTC 2026 name badge generator — A6 portrait (105 x 148 mm), lanyard style.
// Usage:  node build_badges.js
// Output: out/*.png (preview per category), out/EPTC2026_badges_A6.pdf (trim size),
//         out/EPTC2026_badges_A6_print_bleed3mm.pdf (3 mm bleed for the printer),
//         out/EPTC2026_badges_overview.png (all categories side by side).
//
// Every badge shares the same background; only the category ribbon colour changes.

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, 'out');
const LOGO = 'data:image/png;base64,' +
  fs.readFileSync(path.join(__dirname, 'eptc2026_logo.png')).toString('base64');

// ---- Category ribbon colours (edit labels/colours here) --------------------
const CATEGORIES = [
  { key: 'organising-committee', label: 'Organising Committee', bg: '#E8601C', fg: '#FFFFFF' }, // orange
  { key: 'keynote',              label: 'Keynote Speaker',      bg: '#1F5FAE', fg: '#FFFFFF' }, // blue
  { key: 'invited',              label: 'Invited Speaker',      bg: '#2E8540', fg: '#FFFFFF' }, // green
  { key: 'pdc-fc-instructor',    label: 'PDC / FC Instructor',  bg: '#6A3D9A', fg: '#FFFFFF' }, // purple
  { key: 'panelist',             label: 'Panelist',             bg: '#C2185B', fg: '#FFFFFF' }, // magenta
  { key: 'student-volunteer',    label: 'Student Volunteer',    bg: '#F5C400', fg: '#3A2A00' }, // yellow
  { key: 'delegate',             label: 'Delegate',             bg: null,      fg: '#6B2516' }, // no colour
  { key: 'student',              label: 'Student',              bg: null,      fg: '#6B2516' }, // no colour
];

// ---- Placeholder attendee text ---------------------------------------------
const NAME = 'FULL NAME';
const AFFILIATION = 'AFFILIATION';

// ---- Brand palette (from the EPTC 2026 logo / slide banners) ---------------
const C = {
  dark: '#6B2516', mid: '#B23E19', orange: '#E8641C', ink: '#2B1A14',
  sub: '#5E4B43', trace: '#F1D5C4', hair: '#E3CBBE',
};

const W = 105, H = 148; // mm, trim size

// Circuit trace: polyline with hollow square pads at the ends (logo motif).
function trace(pts, { color = C.trace, w = 0.35, pad = 1.3, pads = 'end' } = {}) {
  const d = 'M' + pts.map(p => p.join(' ')).join(' L');
  const sq = ([x, y]) =>
    `<rect x="${x - pad / 2}" y="${y - pad / 2}" width="${pad}" height="${pad}" fill="#fff" stroke="${color}" stroke-width="${w}"/>`;
  const ends = pads === 'both' ? [pts[0], pts[pts.length - 1]] : [pts[pts.length - 1]];
  return `<path d="${d}" fill="none" stroke="${color}" stroke-width="${w}" stroke-linejoin="round"/>` +
    ends.map(sq).join('');
}

// Marina Bay Sands, drawn in a 100 x 46 local box.
function mbs() {
  const tower = x => {
    const r = x + 10;
    return `<path d="M${x} 9.2 L${r} 9.0 L${r} 29 Q${r + 0.4} 37 ${r + 2.8} 40 L${x - 0.4} 40 Z" fill="url(#mbsGrad)"/>` +
      [2.5, 5, 7.5].map(o => `<line x1="${x + o}" y1="10.5" x2="${x + o}" y2="38" stroke="#fff" stroke-opacity="0.22" stroke-width="0.35"/>`).join('');
  };
  return `
    <rect x="12" y="36.5" width="74" height="3.5" fill="${C.orange}" opacity="0.28"/>
    ${tower(16)}${tower(41)}${tower(66)}
    <path d="M3 8.1 Q9 6.1 20 5.9 L91 5.3 Q97.5 5.4 100 6.9 Q97.5 8.6 91 8.8 L20 9.5 Q9 9.6 3 8.1 Z" fill="${C.dark}"/>
    <line x1="0" y1="40.4" x2="100" y2="40.4" stroke="${C.dark}" stroke-width="0.8"/>
    <path d="M8 43 H30 M40 43 H66 M74 43 H94 M18 45.3 H44 M54 45.3 H82" stroke="${C.orange}" stroke-opacity="0.45" stroke-width="0.7" stroke-linecap="round"/>`;
}

function qrPlaceholder(x, y, s) {
  const f = (fx, fy) => `
    <rect x="${fx}" y="${fy}" width="7" height="7" fill="none" stroke="#CDB8AC" stroke-width="1"/>
    <rect x="${fx + 2.25}" y="${fy + 2.25}" width="2.5" height="2.5" fill="#CDB8AC"/>`;
  return `
    <rect x="${x}" y="${y}" width="${s}" height="${s}" rx="1.6" fill="#fff" stroke="#CDB8AC" stroke-width="0.35" stroke-dasharray="1.4 0.9"/>
    ${f(x + 2.5, y + 2.5)}${f(x + s - 9.5, y + 2.5)}${f(x + 2.5, y + s - 9.5)}
    <text x="${x + s / 2}" y="${y + s / 2 + 1.1}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="3" letter-spacing="0.25" fill="#B49B8F">QR CODE</text>`;
}

function badgeSVG(cat, b) {
  const ribY = 88, ribH = 13;
  const ribbonFill = cat.bg
    ? `<rect x="${-b}" y="${ribY}" width="${W + 2 * b}" height="${ribH}" fill="${cat.bg}"/>
       <rect x="${-b}" y="${ribY}" width="${W + 2 * b}" height="0.6" fill="#000" opacity="0.10"/>
       <rect x="${-b}" y="${ribY + ribH - 0.6}" width="${W + 2 * b}" height="0.6" fill="#000" opacity="0.10"/>`
    : `<rect x="${-b}" y="${ribY}" width="${W + 2 * b}" height="${ribH}" fill="#FFFFFF"/>
       <rect x="${-b}" y="${ribY}" width="${W + 2 * b}" height="0.4" fill="${C.hair}"/>
       <rect x="${-b}" y="${ribY + ribH - 0.4}" width="${W + 2 * b}" height="0.4" fill="${C.hair}"/>`;
  // short trace stubs at both ribbon ends (same on every badge, tinted to the ribbon)
  const stubCol = cat.bg ? (cat.fg === '#FFFFFF' ? 'rgba(255,255,255,0.45)' : 'rgba(58,42,0,0.35)') : C.trace;
  const cy = ribY + ribH / 2;
  const stubs = [
    [[-b, cy - 2.2], [4, cy - 2.2], [6, cy], [9, cy]],
    [[-b, cy + 2.4], [5, cy + 2.4]],
    [[W + b, cy - 2.4], [100, cy - 2.4]],
    [[W + b, cy + 2.2], [101, cy + 2.2], [99, cy], [96, cy]],
  ].map(p => trace(p, { color: stubCol, w: 0.35, pad: 1.1 })).join('')
    .replace(/fill="#fff"/g, `fill="${cat.bg || '#fff'}"`);

  return `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-b} ${-b} ${W + 2 * b} ${H + 2 * b}"
     width="${W + 2 * b}mm" height="${H + 2 * b}mm" style="position:absolute;left:0;top:0">
  <defs>
    <linearGradient id="brand" x1="0" x2="1" y1="0" y2="0">
      <stop offset="0" stop-color="${C.dark}"/><stop offset="0.5" stop-color="${C.mid}"/><stop offset="1" stop-color="${C.orange}"/>
    </linearGradient>
    <linearGradient id="paper" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#FFFFFF"/><stop offset="0.55" stop-color="#FFFFFF"/><stop offset="1" stop-color="#FDF3EC"/>
    </linearGradient>
    <linearGradient id="mbsGrad" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="${C.orange}"/><stop offset="1" stop-color="${C.dark}"/>
    </linearGradient>
    <pattern id="bga" width="2.6" height="2.6" patternUnits="userSpaceOnUse">
      <circle cx="1.3" cy="1.3" r="0.45" fill="${C.trace}"/>
    </pattern>
  </defs>

  <!-- paper -->
  <rect x="${-b}" y="${-b}" width="${W + 2 * b}" height="${H + 2 * b}" fill="url(#paper)"/>

  <!-- top brand bar + lanyard slot guide -->
  <rect x="${-b}" y="${-b}" width="${W + 2 * b}" height="${4 + b}" fill="url(#brand)"/>
  <rect x="42.5" y="7" width="20" height="3.2" rx="1.6" fill="none" stroke="${C.hair}" stroke-width="0.25" stroke-dasharray="0.8 0.6"/>

  <!-- BGA ball-grid texture, top-right & bottom-left corners -->
  <path d="M86 4 H${W + b} V22 Q101 12 86 4 Z" fill="url(#bga)"/>

  <!-- circuit traces (logo motif) -->
  ${trace([[W + b, 26], [100, 26], [97, 29], [91, 29]])}
  ${trace([[W + b, 32.5], [95, 32.5]])}
  ${trace([[-b, 6], [7, 6], [10, 9], [14, 9]])}
  ${trace([[-b, 106], [10, 106], [14, 110], [30, 110]])}
  ${trace([[-b, 112], [5, 112]])}
  ${trace([[40, 104.5], [50, 104.5], [53.5, 108], [60, 108]], { pads: 'both' })}
  ${trace([[W + b, 128], [99.5, 128]])}

  <!-- logo -->
  <image href="${LOGO}" x="16.5" y="12" width="72" height="${72 * 208 / 634}" preserveAspectRatio="xMidYMid meet"/>

  <!-- divider under conference line -->
  <line x1="44" y1="49.3" x2="61" y2="49.3" stroke="${C.orange}" stroke-width="0.45"/>
  <rect x="42.6" y="48.6" width="1.4" height="1.4" fill="#fff" stroke="${C.orange}" stroke-width="0.35"/>
  <rect x="61" y="48.6" width="1.4" height="1.4" fill="#fff" stroke="${C.orange}" stroke-width="0.35"/>

  <!-- category ribbon -->
  ${ribbonFill}
  ${stubs}

  <!-- Marina Bay Sands (≈ 40 x 18 mm incl. label, ~5% of the badge) -->
  <g transform="translate(10 115) scale(0.40)">${mbs()}</g>

  <!-- QR code area -->
  ${qrPlaceholder(66, 105, 31)}

  <!-- bottom brand bar -->
  <rect x="${-b}" y="141" width="${W + 2 * b}" height="${7 + b}" fill="url(#brand)"/>
</svg>`;
}

function badgeHTML(cat, b) {
  const pw = W + 2 * b, ph = H + 2 * b;
  return `<!doctype html><html><head><meta charset="utf-8">
<style>
  @page { size: ${pw}mm ${ph}mm; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: ${pw}mm; height: ${ph}mm; background: #fff; }
  body { font-family: 'Inter', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { position: relative; width: ${pw}mm; height: ${ph}mm; overflow: hidden; }
  .trim { position: absolute; left: ${b}mm; top: ${b}mm; width: ${W}mm; height: ${H}mm; }
  .abs { position: absolute; left: 0; width: ${W}mm; text-align: center; }
  .conf { top: 38.6mm; color: ${C.dark}; font-weight: 600; font-size: 2.95mm; line-height: 1.32; letter-spacing: 0.01em; }
  .conf sup { font-size: 0.62em; line-height: 0; }
  .conf .when { display: block; font-weight: 500; color: #8A4A32; font-size: 2.7mm; }
  .who { top: 53mm; height: 33mm; padding: 0 7mm; display: flex; flex-direction: column; justify-content: center; align-items: center; }
  .name { font-family: 'Inter Display', 'Inter', sans-serif; font-weight: 800; color: ${C.ink}; font-size: 9mm; line-height: 1.04; letter-spacing: -0.005em; }
  .aff { margin-top: 2.4mm; font-weight: 500; color: ${C.sub}; font-size: 4.1mm; line-height: 1.2; }
  .cat { top: 88mm; height: 13mm; display: flex; align-items: center; justify-content: center; padding: 0 11mm;
         font-weight: 800; text-transform: uppercase; letter-spacing: 0.09em; font-size: 5.2mm; white-space: nowrap; color: ${cat.fg}; }
  .sg { top: 134.6mm; left: 10mm; width: 40mm; font-weight: 700; font-size: 2.3mm; letter-spacing: 0.42em; color: #A9583A; padding-left: 0.42em; }
  .foot { top: 141mm; height: 7mm; display: flex; align-items: center; justify-content: space-between; padding: 0 7mm;
          color: #fff; font-size: 2.35mm; font-weight: 600; letter-spacing: 0.04em; text-align: left; }
  .foot span:last-child { font-weight: 500; opacity: 0.95; }
</style></head><body><div class="page">
${badgeSVG(cat, b)}
<div class="trim">
  <div class="abs conf">28<sup>th</sup> Electronics Packaging Technology Conference
    <span class="when">1 – 4 December 2026 &middot; Singapore</span></div>
  <div class="abs who">
    <div class="name" id="name">${NAME}</div>
    <div class="aff" id="aff">${AFFILIATION}</div>
  </div>
  <div class="abs cat" id="cat">${cat.label}</div>
  <div class="abs sg">SINGAPORE</div>
  <div class="abs foot"><span>eptc-ieee.net</span><span>IEEE EPS Flagship Conference</span></div>
</div></div>
<script>
  // shrink-to-fit: name max 2 lines, affiliation max 2 lines, category 1 line
  const mm = 96 / 25.4;
  function fit(el, maxH, min) {
    let s = parseFloat(getComputedStyle(el).fontSize);
    while ((el.scrollHeight > maxH * mm || el.scrollWidth > el.clientWidth + 1) && s > min * mm) {
      s -= 0.2; el.style.fontSize = s + 'px';
    }
  }
  fit(document.getElementById('name'), 19.5, 5);
  fit(document.getElementById('aff'), 10.5, 2.8);
  const cat = document.getElementById('cat');
  let s = parseFloat(getComputedStyle(cat).fontSize);
  while (cat.scrollWidth > cat.clientWidth && s > 3 * mm) { s -= 0.2; cat.style.fontSize = s + 'px'; }
</script>
</body></html>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  fs.mkdirSync(path.join(OUT, 'html'), { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 3 });
  const trimPages = [], bleedPages = [];

  for (const [i, cat] of CATEGORIES.entries()) {
    const n = String(i + 1).padStart(2, '0');
    for (const b of [0, 3]) {
      const html = badgeHTML(cat, b);
      if (b === 0) fs.writeFileSync(path.join(OUT, 'html', `${n}_${cat.key}.html`), html);
      await page.setContent(html, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const pdf = await page.pdf({ width: `${W + 2 * b}mm`, height: `${H + 2 * b}mm`, printBackground: true, preferCSSPageSize: true });
      (b === 0 ? trimPages : bleedPages).push(pdf);
      if (b === 0) {
        await page.setViewportSize({ width: Math.round(W * 96 / 25.4), height: Math.round(H * 96 / 25.4) });
        await page.screenshot({ path: path.join(OUT, `${n}_${cat.key}.png`), fullPage: false, scale: 'device' });
      }
    }
  }
  // overview sheet: all categories side by side
  const imgs = CATEGORIES.map((c, i) => 'data:image/png;base64,' + fs.readFileSync(
    path.join(OUT, `${String(i + 1).padStart(2, '0')}_${c.key}.png`)).toString('base64'));
  await page.setViewportSize({ width: 1720, height: 1200 });
  await page.setContent(`<body style="margin:0;background:#ECE8E4;display:grid;grid-template-columns:repeat(4,397px);gap:28px;padding:28px">
    ${imgs.map(s => `<img src="${s}" style="width:397px;box-shadow:0 2px 10px rgba(0,0,0,.15)">`).join('')}</body>`);
  await page.screenshot({ path: path.join(OUT, 'EPTC2026_badges_overview.png'), fullPage: true });
  await browser.close();

  // merge pages with pdf-lib if present, else keep single-page PDFs
  let merged = false;
  try {
    const { PDFDocument } = require('pdf-lib');
    for (const [name, list, b] of [['EPTC2026_badges_A6.pdf', trimPages, 0], ['EPTC2026_badges_A6_print_bleed3mm.pdf', bleedPages, 3]]) {
      const doc = await PDFDocument.create();
      const pt = mm => mm * 72 / 25.4;
      for (const buf of list) {
        const src = await PDFDocument.load(buf);
        const [p] = await doc.copyPages(src, [0]);
        // Chromium rounds page size to whole px; crop to the exact mm size (content is top-left anchored)
        const { height } = p.getSize();
        const tw = pt(W + 2 * b), th = pt(H + 2 * b);
        p.setMediaBox(0, height - th, tw, th);
        p.setCropBox(0, height - th, tw, th);
        if (b) p.setTrimBox(0 + pt(b), height - th + pt(b), pt(W), pt(H));
        doc.addPage(p);
      }
      fs.writeFileSync(path.join(OUT, name), await doc.save());
    }
    merged = true;
  } catch (e) { console.warn('pdf-lib not available, writing single-page PDFs:', e.message); }
  if (!merged) {
    trimPages.forEach((buf, i) => fs.writeFileSync(path.join(OUT, `${String(i + 1).padStart(2, '0')}_${CATEGORIES[i].key}.pdf`), buf));
  }
  console.log('done ->', OUT);
})();
