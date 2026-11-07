// Shared design system for the EPTC 2026 welcome deck.
const path = require('path');
const A = p => path.join(__dirname, '..', 'assets', p);

const THEME = {
  name: 'EPTC 2026',
  headFontFace: 'Calibri',
  bodyFontFace: 'Calibri',
  colors: {
    dk1: '3B1A0E', lt1: 'FFFFFF', dk2: '6B2412', lt2: 'FCEFE6',
    accent1: 'E06A1B', accent2: 'A63D1C', accent3: 'F3A33A',
    accent4: '6B2412', accent5: 'C9582A', accent6: '8C7A70',
    hlink: 'A63D1C', folHlink: '6B2412',
  },
};
const HEX = {
  ink: '3B1A0E', brown: '6B2412', rust: 'A63D1C', orange: 'E06A1B', amber: 'F3A33A',
  peach: 'FCEFE6', peach2: 'F8DCC8', grey: '6E5D55', pin: 'B9A79C', white: 'FFFFFF',
};

const W = 13.333, H = 7.5;
const TOP = 0.63, BOT = 7.5 - 0.75; // banner edges
const MX = 0.6; // side margin

function defineLayouts(pres) {
  const C = pres.SchemeColor;
  const num = { x: 12.78, y: 0.14, w: 0.45, h: 0.36, color: 'FFFFFF', fontFace: 'Calibri', fontSize: 14, bold: true, align: 'right' };
  pres.defineSlideMaster({
    title: 'EPTC Content',
    background: { path: A('bg_content.jpg') },
    objects: [
      { image: { path: A('logo_white.png'), x: 0.45, y: 6.93, w: 1.2, h: 0.39, altText: 'EPTC 2026 logo' } },
      { placeholder: { options: { name: 'title', type: 'title', x: MX, y: 0.82, w: W - 2 * MX, h: 0.72, fontFace: 'Calibri', fontSize: 34, bold: true, color: C.text2, align: 'left', valign: 'middle', margin: 0 }, text: '' } },
    ],
    slideNumber: { ...num },
  });
  pres.defineSlideMaster({
    title: 'EPTC Title',
    background: { path: A('bg_title.jpg') },
    objects: [],
    slideNumber: { ...num },
  });
}

// A "chip package" card: rounded body with small pins along the left and right
// edges -- the deck's recurring semiconductor motif.
function chipCard(pres, slide, x, y, w, h, opts = {}) {
  const C = pres.SchemeColor;
  const fill = opts.fill || C.background2;
  const pins = opts.pins === undefined ? Math.max(2, Math.floor(h / 0.32)) : opts.pins;
  const pinColor = opts.pinColor || C.accent6;
  const pw = 0.09, ph = 0.05;
  if (pins > 0) {
    const gap = h / (pins + 1);
    for (let i = 1; i <= pins; i++) {
      const py = y + gap * i - ph / 2;
      slide.addShape(pres.shapes.RECTANGLE, { x: x - pw + 0.01, y: py, w: pw, h: ph, fill: { color: pinColor }, line: { type: 'none' }, objectName: 'pin' });
      slide.addShape(pres.shapes.RECTANGLE, { x: x + w - 0.01, y: py, w: pw, h: ph, fill: { color: pinColor }, line: { type: 'none' }, objectName: 'pin' });
    }
  }
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h, rectRadius: opts.radius || 0.08,
    fill: { color: fill }, line: opts.line ? { color: opts.line, width: 1 } : { type: 'none' },
    shadow: opts.shadow === false ? undefined : { type: 'outer', color: '6B2412', opacity: 0.18, blur: 6, offset: 2, angle: 90 },
    objectName: opts.name || 'card',
  });
}

function iconCircle(pres, slide, data, x, y, d, color) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: color || pres.SchemeColor.accent1 }, line: { type: 'none' }, objectName: 'icon-circle' });
  const p = d * 0.24;
  slide.addImage({ data, x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p, altText: 'icon' });
}

// Fit an image of known pixel size inside a box, centred.
function fit(imgW, imgH, x, y, w, h) {
  const r = Math.min(w / imgW, h / imgH);
  const ww = imgW * r, hh = imgH * r;
  return { x: x + (w - ww) / 2, y: y + (h - hh) / 2, w: ww, h: hh };
}

module.exports = { THEME, HEX, W, H, TOP, BOT, MX, A, defineLayouts, chipCard, iconCircle, fit };
