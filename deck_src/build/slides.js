// Slide definitions. Each entry: { section, layout?, notes, build(slide, ctx) }.
const { T } = require('./slides_util');

// Lead text under the slide title.
function lead(slide, ctx, text, opts = {}) {
  slide.addText(text, {
    x: ctx.MX, y: 1.52, w: opts.w || ctx.W - 2 * ctx.MX, h: opts.h || 0.5, fontSize: 16, color: ctx.C.text1,
    margin: 0, valign: 'top', isTextBox: true, ...opts,
  });
}

const slides = [];

// 1 ─ Title
slides.push({
  section: 'Welcome',
  layout: 'EPTC Title',
  notes: 'Distinguished guests, industry leaders, colleagues, sponsors, and friends, good morning.',
  build: (s, x) => {
    const { pres, C, A } = x;
    // photo set into a "package" frame
    const ph = 5.25, pw = ph * 1334 / 1600, fx = 0.85;
    x.chipCard(s, fx, 0.95, pw + 0.3, ph + 0.3, { fill: C.text2, pins: 14, pinColor: x.HEX.amber, radius: 0.12 });
    s.addImage({ path: A('chair.jpg'), x: fx + 0.15, y: 1.1, w: pw, h: ph, altText: 'Prof. Yeow Kheng LIM, General Chair of EPTC 2026' });

    const RX = 6.05, RW = 6.7;
    s.addImage({ path: A('logo_trans.png'), x: RX, y: 1.05, w: 4.4, h: 4.4 * 208 / 634, altText: 'EPTC 2026 logo' });
    s.addText('WELCOME SPEECH', { x: RX, y: 2.75, w: RW, h: 0.7, fontSize: 40, bold: true, color: C.accent2, charSpacing: 2, margin: 0, isTextBox: true });
    s.addText('General Chair, EPTC 2026', { x: RX, y: 3.5, w: RW, h: 0.45, fontSize: 20, color: C.accent1, bold: true, margin: 0, isTextBox: true });
    s.addText('Prof. Yeow Kheng LIM', { x: RX, y: 4.0, w: RW, h: 0.6, fontSize: 32, bold: true, color: C.text1, margin: 0, isTextBox: true });
    s.addText('National University of Singapore', { x: RX, y: 4.6, w: RW, h: 0.45, fontSize: 20, color: x.HEX.grey, margin: 0, isTextBox: true });
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: RX, y: 5.45, w: 6.3, h: 0.9, rectRadius: 0.12, fill: { color: C.background2 }, line: { type: 'none' } });
    s.addText([
      { text: '28th IEEE Electronics Packaging Technology Conference', options: { bold: true, color: C.text2, breakLine: true } },
      { text: '1–4 December 2026   |   Singapore', options: { color: C.text1 } },
    ], { x: RX + 0.25, y: 5.45, w: 5.9, h: 0.9, fontSize: 16, valign: 'middle', margin: 0, isTextBox: true });
  },
});

// 2 ─ Welcome
slides.push({
  section: 'Welcome',
  notes: 'On behalf of the Organising Committee, it is my great pleasure to welcome you to Singapore and to the 28th IEEE Electronics Packaging Technology Conference, EPTC 2026.\n\nTo our returning delegates, welcome back. To those joining us for the first time, we are delighted to have you here. Your participation makes EPTC a valuable meeting place for the global electronics packaging community.',
  build: (s, x) => {
    const { C } = x;
    T(s, 'Welcome to EPTC 2026');
    s.addText([
      { text: 'Welcome to Singapore and to the ', options: {} },
      { text: '28th IEEE Electronics Packaging Technology Conference', options: { bold: true, color: C.text2 } },
      { text: '.', options: {} },
    ], { x: x.MX, y: 1.75, w: 6.2, h: 1.1, fontSize: 22, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    // returning / first-time chips
    const rows = [
      ['FaHandshake', 'Returning delegates', 'Welcome back.'],
      ['FaUserFriends', 'First-time participants', 'We are delighted to have you here.'],
      ['FaGlobeAsia', 'A global meeting place', 'Your participation makes EPTC a valuable meeting place for the electronics packaging community.'],
    ];
    rows.forEach(([ico, h, b], i) => {
      const y = 3.05 + i * 1.12;
      x.iconCircle(s, x.ic[ico], x.MX, y, 0.72, i === 1 ? C.accent2 : C.accent1);
      s.addText(h, { x: x.MX + 0.95, y: y - 0.02, w: 5.3, h: 0.38, fontSize: 18, bold: true, color: C.text2, margin: 0, isTextBox: true });
      s.addText(b, { x: x.MX + 0.95, y: y + 0.36, w: 5.3, h: 0.62, fontSize: 14, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    });
    // right: key facts as chip cards
    const facts = x.DATA.welcomeFacts || [
      ['28th', 'edition of EPTC'],
      ['4 days', '1–4 December 2026'],
      ['Singapore', 'IEEE EPS flagship conference in Asia Pacific'],
    ];
    const cx = 7.55, cw = 5.1, ch = 1.38;
    facts.forEach(([big, small], i) => {
      const y = 1.8 + i * (ch + 0.32);
      x.chipCard(s, cx, y, cw, ch, { fill: i === 0 ? C.text2 : C.background2, pins: 4 });
      const dark = i === 0;
      s.addText(big, { x: cx + 0.35, y, w: 2.3, h: ch, fontSize: big.length > 6 ? 28 : 36, bold: true, color: dark ? 'FFFFFF' : C.accent2, valign: 'middle', margin: 0, isTextBox: true, fit: 'shrink' });
      s.addText(small, { x: cx + 2.65, y, w: cw - 2.9, h: ch, fontSize: 16, color: dark ? 'FFFFFF' : C.text1, valign: 'middle', margin: 0, isTextBox: true });
    });
  },
});

// == DATA SLIDES ==
slides.push(...require('./data_slides.js'));

// 11 ─ Closing
slides.push({
  section: 'Closing',
  layout: 'EPTC Title',
  notes: 'Please also take time to visit our exhibitors. Share the challenges you face and explore the solutions on display. A conversation here could become your next research partnership or engineering breakthrough.\n\nFinally, thank you to every speaker, author, and delegate for contributing your time and ideas.\n\nOn behalf of the Organising Committee, I officially welcome you to EPTC 2026 and EPTEX.\n\nI wish you a rewarding conference, productive discussions, and an enjoyable stay in Singapore.\n\nThank you.',
  build: (s, x) => {
    const { C, A } = x;
    s.addImage({ path: A('logo_trans.png'), x: (x.W - 3.6) / 2, y: 0.95, w: 3.6, h: 3.6 * 208 / 634, altText: 'EPTC 2026 logo' });
    s.addText('Welcome to EPTC 2026 & EPTEX', { x: 0.6, y: 2.25, w: x.W - 1.2, h: 0.8, fontSize: 40, bold: true, color: C.text2, align: 'center', margin: 0, isTextBox: true });
    s.addText('Thank you to every speaker, author and delegate for contributing your time and ideas.', { x: 1.5, y: 3.05, w: x.W - 3, h: 0.45, fontSize: 18, color: C.text1, align: 'center', margin: 0, isTextBox: true });
    const cards = [
      ['FaLightbulb', 'A rewarding conference', C.accent1],
      ['FaComments', 'Productive discussions', C.accent2],
      ['FaMapMarkerAlt', 'An enjoyable stay in Singapore', C.text2],
    ];
    const cw = 3.6, gap = 0.45, x0 = (x.W - (3 * cw + 2 * gap)) / 2;
    cards.forEach(([ico, t, col], i) => {
      const cx = x0 + i * (cw + gap), cy = 3.9;
      x.chipCard(s, cx, cy, cw, 1.75, { fill: col, pins: 4, pinColor: x.HEX.pin });
      s.addImage({ data: x.ic[ico], x: cx + (cw - 0.55) / 2, y: cy + 0.28, w: 0.55, h: 0.55, altText: 'icon' });
      s.addText(t, { x: cx + 0.2, y: cy + 0.95, w: cw - 0.4, h: 0.6, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    });
    s.addText('THANK YOU', { x: 0.6, y: 5.9, w: x.W - 1.2, h: 0.55, fontSize: 24, bold: true, color: C.accent2, align: 'center', charSpacing: 6, margin: 0, isTextBox: true });
  },
});

module.exports = slides;
module.exports.T = T;
module.exports.lead = lead;
