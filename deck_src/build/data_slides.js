// Slides 3-10: the eight topics requested, aligned with the welcome speech.
const { T } = require('./slides_util');

// Place a logo (or a text fallback) centred in a white tile.
function logoTile(s, x, item, bx, by, bw, bh, opts = {}) {
  if (opts.tile !== false) {
    s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: by, w: bw, h: bh, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: x.HEX.peach2, width: 0.75 }, objectName: 'logo-tile' });
  }
  const pad = opts.pad === undefined ? 0.08 : opts.pad;
  if (item && item.file && item.px) {
    const f = x.fit(item.px[0], item.px[1], bx + pad, by + pad, bw - 2 * pad, bh - 2 * pad);
    s.addImage({ path: item.file, ...f, altText: item.name || 'logo' });
  } else {
    s.addText(item ? item.name : '', { x: bx + 0.05, y: by, w: bw - 0.1, h: bh, fontSize: opts.fs || 12, bold: true, color: x.C.text2, align: 'center', valign: 'middle', margin: 0, isTextBox: true, fit: 'shrink' });
  }
}

// Lay out n tiles in a box, choosing columns so tiles stay near a target aspect.
function grid(n, bx, by, bw, bh, aspect, gap) {
  let best = null;
  for (let cols = 1; cols <= n; cols++) {
    const rows = Math.ceil(n / cols);
    let tw = (bw - gap * (cols - 1)) / cols;
    let th = tw / aspect;
    if (th * rows + gap * (rows - 1) > bh) { th = (bh - gap * (rows - 1)) / rows; tw = th * aspect; }
    if (!best || tw > best.tw) best = { cols, rows, tw, th };
  }
  const out = [];
  const totalW = best.cols * best.tw + (best.cols - 1) * gap;
  for (let i = 0; i < n; i++) {
    const r = Math.floor(i / best.cols), c = i % best.cols;
    const inRow = Math.min(best.cols, n - r * best.cols);
    const rowW = inRow * best.tw + (inRow - 1) * gap;
    out.push({ x: bx + (bw - rowW) / 2 + c * (best.tw + gap), y: by + r * (best.th + gap), w: best.tw, h: best.th });
  }
  return out;
}

const slides = [];

// 3 ─ Sponsor gratitude
slides.push({
  section: 'Sponsor Gratitude',
  notes: 'Let me begin by expressing our sincere appreciation to all our sponsors.\n\nTo our Diamond, Platinum, Gold, Silver, and Bronze sponsors, and to all our supporting partners and exhibitors, thank you. Your generous contributions help us deliver a strong technical programme and create opportunities for researchers, engineers, and students to connect with industry. We deeply appreciate your continued confidence in EPTC.',
  build: (s, x) => {
    const { C, HEX } = x;
    T(s, 'Thank You to Our Sponsors, Partners & Exhibitors');
    const tiers = x.DATA.sponsors || [
      { tier: 'Diamond', items: [] }, { tier: 'Platinum', items: [] }, { tier: 'Gold', items: [] },
      { tier: 'Silver', items: [] }, { tier: 'Bronze', items: [] },
    ];
    const rest = (x.DATA.partners || []).concat(x.DATA.exhibitors || []);
    const tierCol = { Diamond: C.text2, Platinum: C.accent2, Gold: C.accent3, Silver: HEX.grey, Bronze: C.accent5 };
    // tiered rows on the left, partners/exhibitors wall on the right
    const LX = x.MX, LW = rest.length ? 7.4 : x.W - 2 * x.MX, top = 1.7, bottom = 6.55;
    const weights = { Diamond: 1.35, Platinum: 1.2, Gold: 1.05, Silver: 0.95, Bronze: 0.9 };
    const tw = tiers.reduce((a, t) => a + (weights[t.tier] || 0.9), 0);
    const gap = 0.12, avail = bottom - top - gap * (tiers.length - 1);
    let y = top;
    tiers.forEach(t => {
      const h = avail * (weights[t.tier] || 0.9) / tw;
      x.chipCard(s, LX, y, 1.45, h, { fill: tierCol[t.tier] || C.accent1, pins: Math.max(2, Math.round(h / 0.3)), shadow: false });
      s.addText(t.tier.toUpperCase(), { x: LX, y, w: 1.45, h, fontSize: 13, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true, charSpacing: 1 });
      const n = Math.max(1, t.items.length);
      const area = { x: LX + 1.7, w: LW - 1.7 };
      const cells = grid(n, area.x, y, area.w, h, 2.6, 0.1);
      if (t.items.length) t.items.forEach((it, i) => logoTile(s, x, it, cells[i].x, cells[i].y, cells[i].w, cells[i].h));
      else s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: area.x, y, w: area.w, h, rectRadius: 0.05, fill: { color: 'FFFFFF' }, line: { color: HEX.peach2, width: 0.75, dashType: 'dash' } });
      y += h + gap;
    });
    if (rest.length) {
      const RX = LX + LW + 0.35, RW = x.W - x.MX - RX;
      s.addText('Supporting Partners & Exhibitors', { x: RX, y: top, w: RW, h: 0.35, fontSize: 14, bold: true, color: C.text2, margin: 0, isTextBox: true });
      const cells = grid(rest.length, RX, top + 0.45, RW, bottom - top - 0.45, 2.2, 0.06);
      rest.forEach((it, i) => logoTile(s, x, it, cells[i].x, cells[i].y, cells[i].w, cells[i].h, { pad: 0.04, fs: 8 }));
    }
  },
});

// 4 ─ Organising Committee
slides.push({
  section: 'Organising Committee',
  notes: 'I would also like to recognise the people who have worked tirelessly to bring this conference together.\n\nTo our Organising Committee, thank you for the many months of planning and coordination. To our Technical Programme Committee, reviewers and session chairs, thank you for contributing your time and expertise to maintaining the quality of our programme.',
  build: (s, x) => {
    const { C } = x;
    T(s, 'Our Organising Committee');
    s.addText('Thank you for the many months of planning and coordination, and to our Technical Programme Committee, reviewers and session chairs for upholding the quality of our programme.',
      { x: x.MX, y: 1.5, w: x.W - 2 * x.MX, h: 0.6, fontSize: 15, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    const oc = x.DATA.oc || [];
    if (!oc.length) return;
    const top = 2.25, bottom = 6.6;
    const cells = grid(oc.length, x.MX, top, x.W - 2 * x.MX, bottom - top, 0.78, 0.12);
    oc.forEach((m, i) => {
      const c = cells[i];
      const capH = Math.min(0.62, c.h * 0.36);
      const phH = c.h - capH;
      const phW = Math.min(c.w, phH * 0.8);
      const px = c.x + (c.w - phW) / 2;
      s.addShape(x.pres.shapes.RECTANGLE, { x: px - 0.03, y: c.y - 0.03, w: phW + 0.06, h: phH + 0.06, fill: { color: C.accent1 }, line: { type: 'none' } });
      if (m.file && m.px) s.addImage({ path: m.file, x: px, y: c.y, w: phW, h: phH, sizing: { type: 'cover', w: phW, h: phH }, altText: m.name });
      const fs = c.w < 1.3 ? 9 : 11;
      s.addText([
        { text: m.name, options: { bold: true, color: C.text2, breakLine: true } },
        { text: m.role || '', options: { color: C.text1 } },
      ], { x: c.x - 0.05, y: c.y + phH + 0.05, w: c.w + 0.1, h: capH - 0.05, fontSize: fs, align: 'center', valign: 'top', margin: 0, isTextBox: true, fit: 'shrink' });
    });
  },
});

// 5 ─ IEEE EPS, Joint Chapter, Secretariats, Volunteers
slides.push({
  section: 'Partners & Volunteers',
  notes: 'We are grateful to the IEEE Electronics Packaging Society and the IEEE RS/EPS/EDS Singapore Joint Chapter for their leadership and continued support.\n\nA special word of thanks goes to our conference secretariats, InPrep and SparkPlanners, for their dedication and hard work behind the scenes.\n\nTo our student helpers and volunteers, thank you for your energy, commitment, and warm hospitality. Please join me in giving the entire team a warm round of applause.\n\n[Pause for applause]',
  build: (s, x) => {
    const { C, HEX } = x;
    T(s, 'The Team Behind EPTC 2026');
    const lg = x.DATA.logos || {};
    const cards = [
      { h: 'IEEE Electronics Packaging Society', b: 'For their leadership and continued support', logos: [lg.ieeeEps || { name: 'IEEE EPS' }] },
      { h: 'IEEE RS/EPS/EDS Singapore Joint Chapter', b: 'For their leadership and continued support', logos: [lg.jointChapter || { name: 'IEEE RS/EPS/EDS Singapore Joint Chapter' }] },
      { h: 'Conference Secretariats', b: 'For their dedication and hard work behind the scenes', logos: [lg.inprep || { name: 'InPrep' }, lg.sparkplanners || { name: 'SparkPlanners' }] },
      { h: 'Student Helpers & Volunteers', b: 'For your energy, commitment and warm hospitality', icon: 'FaHeart' },
    ];
    const cw = 2.85, gap = 0.27, x0 = x.MX + 0.05, cy = 1.75, chh = 3.95;
    cards.forEach((cd, i) => {
      const cx = x0 + i * (cw + gap);
      x.chipCard(s, cx, cy, cw, chh, { fill: C.background2, pins: 10 });
      // logo window
      const wy = cy + 0.25, wh = 1.75;
      s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: cx + 0.2, y: wy, w: cw - 0.4, h: wh, rectRadius: 0.06, fill: { color: 'FFFFFF' }, line: { type: 'none' } });
      if (cd.icon) {
        x.iconCircle(s, x.ic[cd.icon], cx + (cw - 1.15) / 2, wy + (wh - 1.15) / 2, 1.15, C.accent1);
        x.iconCircle(s, x.ic.FaUserFriends, cx + (cw - 1.15) / 2 + 0.85, wy + (wh - 1.15) / 2 + 0.55, 0.62, C.accent2);
      } else {
        const n = cd.logos.length;
        cd.logos.forEach((l, k) => {
          const lh = (wh - 0.2) / n;
          logoTile(s, x, l, cx + 0.3, wy + 0.1 + k * lh, cw - 0.6, lh, { tile: false, pad: 0.06, fs: 14 });
        });
      }
      s.addText(cd.h, { x: cx + 0.2, y: cy + 2.15, w: cw - 0.4, h: 0.8, fontSize: 16, bold: true, color: C.text2, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
      s.addText(cd.b, { x: cx + 0.2, y: cy + 2.95, w: cw - 0.4, h: 0.8, fontSize: 14, color: C.text1, align: 'center', valign: 'top', margin: 0, isTextBox: true });
    });
    // applause call-out
    s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: x.MX + 2.6, y: 5.95, w: x.W - 2 * x.MX - 5.2, h: 0.6, rectRadius: 0.3, fill: { color: C.text2 }, line: { type: 'none' } });
    s.addImage({ data: x.ic.FaHandshake, x: x.MX + 2.9, y: 6.05, w: 0.4, h: 0.4, altText: 'icon' });
    s.addText('Please join me in a warm round of applause', { x: x.MX + 3.4, y: 5.95, w: x.W - 2 * x.MX - 6.2, h: 0.6, fontSize: 18, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  },
});

// 6 ─ Programme highlights
slides.push({
  section: 'Programme Highlights',
  notes: 'Ladies and gentlemen, artificial intelligence and high-performance computing are placing greater demands on electronics packaging. Meeting these demands requires advances in how we connect dies, deliver power, remove heat, and ensure reliability.\n\nOur four-day programme brings together research findings and industry perspectives to address these challenges.\n\nToday, we begin with four keynote addresses and two panel discussions, featuring leading voices on technology developments and industry priorities.\n\nDay Two offers six Professional Development Courses and six Fundamental Courses, alongside a poster session, providing opportunities to deepen expertise and build new knowledge.\n\nDay Three features oral and poster presentations, invited presentations and a panel discussion.\n\nDay Four continues with oral, poster and invited presentations, together with the Heterogeneous Integration Roadmap Workshop, examining future technology needs and priorities.\n\nI encourage everyone, especially our students and early-career participants, to ask questions and explore sessions beyond your own specialisation.',
  build: (s, x) => {
    const { C } = x;
    T(s, 'Programme Highlights');
    // driver strip
    s.addText([
      { text: 'AI & HPC are raising the bar. ', options: { bold: true, color: C.text2 } },
      { text: 'Our four-day programme tackles how we:', options: { color: C.text1 } },
    ], { x: x.MX, y: 1.5, w: 6.6, h: 0.5, fontSize: 16, margin: 0, valign: 'middle', isTextBox: true });
    const needs = [['FaLink', 'Connect dies'], ['FaBolt', 'Deliver power'], ['FaFire', 'Remove heat'], ['FaShieldAlt', 'Ensure reliability']];
    needs.forEach(([ico, t], i) => {
      const px = x.MX + i * 3.06, py = 2.1;
      s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: px, y: py, w: 2.85, h: 0.6, rectRadius: 0.3, fill: { color: C.background2 }, line: { type: 'none' } });
      x.iconCircle(s, x.ic[ico], px + 0.06, py + 0.06, 0.48, C.accent1);
      s.addText(t, { x: px + 0.65, y: py, w: 2.1, h: 0.6, fontSize: 16, bold: true, color: C.text2, valign: 'middle', margin: 0, isTextBox: true });
    });
    const days = [
      ['DAY 1', 'Tue 1 Dec', [['4', 'Keynote addresses'], ['2', 'Panel discussions']]],
      ['DAY 2', 'Wed 2 Dec', [['6', 'Professional Development Courses'], ['6', 'Fundamental Courses'], ['', 'Poster session']]],
      ['DAY 3', 'Thu 3 Dec', [['', 'Oral & poster presentations'], ['', 'Invited presentations'], ['', 'Panel discussion']]],
      ['DAY 4', 'Fri 4 Dec', [['', 'Oral, poster & invited presentations'], ['', 'Heterogeneous Integration Roadmap Workshop']]],
    ];
    const cw = 2.85, gap = 0.21, cy = 3.0, chh = 3.55;
    // connecting trace behind the day chips
    s.addShape(x.pres.shapes.LINE, { x: x.MX + 0.3, y: cy + 0.38, w: 4 * cw + 3 * gap - 0.6, h: 0, line: { color: C.accent3, width: 2.5 } });
    days.forEach(([d, date, items], i) => {
      const cx = x.MX + i * (cw + gap);
      x.chipCard(s, cx, cy + 0.85, cw, chh - 0.85, { fill: C.background2, pins: 7 });
      s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: cx + 0.35, y: cy, w: cw - 0.7, h: 0.76, rectRadius: 0.1, fill: { color: i % 2 ? C.accent2 : C.text2 }, line: { type: 'none' } });
      s.addText([{ text: d, options: { bold: true, fontSize: 18, breakLine: true } }, { text: date, options: { fontSize: 13 } }],
        { x: cx + 0.35, y: cy, w: cw - 0.7, h: 0.76, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
      let iy = cy + 1.05;
      items.forEach(([num, label]) => {
        const lh = label.length > 30 ? 0.7 : 0.5;
        if (num) {
          s.addText(num, { x: cx + 0.2, y: iy, w: 0.5, h: lh, fontSize: 26, bold: true, color: C.accent1, valign: 'middle', margin: 0, isTextBox: true });
          s.addText(label, { x: cx + 0.72, y: iy, w: cw - 0.9, h: lh, fontSize: 14, color: C.text1, valign: 'middle', margin: 0, isTextBox: true });
        } else {
          s.addShape(x.pres.shapes.RECTANGLE, { x: cx + 0.3, y: iy + lh / 2 - 0.06, w: 0.12, h: 0.12, fill: { color: C.accent1 }, line: { type: 'none' } });
          s.addText(label, { x: cx + 0.6, y: iy, w: cw - 0.8, h: lh, fontSize: 14, color: C.text1, valign: 'middle', margin: 0, isTextBox: true });
        }
        iy += lh + 0.1;
      });
    });
  },
});

// 7 ─ EPTEX
slides.push({
  section: 'EPTEX',
  notes: 'This year, we are also pleased to introduce EPTEX, the Electronics Packaging Technology EXPO, held alongside EPTC.\n\nEPTEX brings together Technology, Tools, and Talents to support Package Design, Prototyping and Production. Through live demonstrations and direct engagement with solution providers, it connects our technical discussions with practical applications.\n\nHighlights include sponsor and exhibitor presentations, an industry forum chaired by EDB, and expert insights and displays spanning robotics, emerging technologies, and start-up innovation. Networking activities provide further opportunities to meet potential collaborators.',
  build: (s, x) => {
    const { C, A } = x;
    // half-bleed image on the right
    const IX = 8.35;
    s.addImage({ path: A('chip_render.png'), x: IX, y: 0.63, w: x.W - IX, h: 6.12, sizing: { type: 'cover', w: x.W - IX, h: 6.12 }, altText: 'Advanced package with light traces' });
    T(s, 'Introducing EPTEX');
    s.addText('Electronics Packaging Technology EXPO, held alongside EPTC', { x: x.MX, y: 1.5, w: 7.5, h: 0.4, fontSize: 18, bold: true, color: C.accent1, margin: 0, isTextBox: true });
    // 3 Ts
    const ts = [['FaMicrochip', 'Technology'], ['FaTools', 'Tools'], ['FaUserGraduate', 'Talents']];
    ts.forEach(([ico, t], i) => {
      const cx = x.MX + i * 2.5, cy = 2.1;
      x.chipCard(s, cx, cy, 2.25, 1.0, { fill: [C.text2, C.accent2, C.accent1][i], pins: 3, shadow: false });
      s.addImage({ data: x.ic[ico], x: cx + 0.22, y: cy + 0.29, w: 0.42, h: 0.42, altText: 'icon' });
      s.addText(t, { x: cx + 0.75, y: cy, w: 1.45, h: 1.0, fontSize: 19, bold: true, color: 'FFFFFF', valign: 'middle', margin: 0, isTextBox: true });
    });
    s.addText([
      { text: 'Supporting ', options: {} },
      { text: 'Package Design, Prototyping and Production', options: { bold: true, color: C.text2 } },
      { text: ' with live demonstrations and direct engagement with solution providers.', options: {} },
    ], { x: x.MX, y: 3.25, w: 7.4, h: 0.75, fontSize: 15, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
    const hl = x.DATA.eptexHighlights || [
      ['FaMicrophone', 'Sponsor & exhibitor presentations'],
      ['FaIndustry', 'Industry forum chaired by EDB'],
      ['FaRobot', 'Expert insights & displays: robotics, emerging technologies, start-up innovation'],
      ['FaUserFriends', 'Networking with potential collaborators'],
    ];
    hl.forEach(([ico, t], i) => {
      const r = Math.floor(i / 2), c = i % 2;
      const cx = x.MX + c * 3.75, cy = 4.15 + r * 1.2;
      s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: cx, y: cy, w: 3.55, h: 1.05, rectRadius: 0.08, fill: { color: C.background2 }, line: { type: 'none' } });
      x.iconCircle(s, x.ic[ico], cx + 0.15, cy + 0.25, 0.55, C.accent1);
      s.addText(t, { x: cx + 0.82, y: cy + 0.05, w: 2.6, h: 0.95, fontSize: 14, bold: true, color: C.text2, valign: 'middle', margin: 0, isTextBox: true });
    });
  },
});

// Challenge slides share a header block; each has its own visual.
function challengeHeader(s, x, n, title, focus) {
  const { C } = x;
  T(s, title);
  s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: x.MX, y: 1.52, w: 2.1, h: 0.42, rectRadius: 0.21, fill: { color: C.accent1 }, line: { type: 'none' } });
  s.addText(`CHALLENGE ${n} OF 3`, { x: x.MX, y: 1.52, w: 2.1, h: 0.42, fontSize: 12, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true, charSpacing: 1 });
  s.addText(focus, { x: x.MX, y: 2.15, w: 6.6, h: 1.2, fontSize: 22, bold: true, color: C.text2, margin: 0, valign: 'top', isTextBox: true });
}
function detailList(s, x, items, y0) {
  const { C } = x;
  items.forEach(([ico, h, b], i) => {
    const y = y0 + i * 0.98;
    x.iconCircle(s, x.ic[ico], x.MX, y, 0.6, i % 2 ? C.accent2 : C.accent1);
    s.addText(h, { x: x.MX + 0.8, y: y - 0.04, w: 5.8, h: 0.36, fontSize: 16, bold: true, color: C.text2, margin: 0, isTextBox: true });
    s.addText(b, { x: x.MX + 0.8, y: y + 0.3, w: 5.8, h: 0.55, fontSize: 14, color: C.text1, margin: 0, valign: 'top', isTextBox: true });
  });
}
const CHALLENGE_NOTE = 'A particular highlight is the three challenges that bring creativity and engineering problem-solving into the programme.';
const CHALLENGE_CLOSE = '\n\nTogether, these challenges give participants opportunities to demonstrate their ideas and engage with real engineering problems. I encourage you to view the entries, support the participants, and join the discussions.';

// 8 ─ Art of Packaging with AI
slides.push({
  section: 'Challenges',
  notes: CHALLENGE_NOTE + '\n\nThe first, Art of Packaging with AI, brings an artistic and creative dimension to electronics packaging.',
  build: (s, x) => {
    const { C, HEX } = x;
    challengeHeader(s, x, 1, 'Art of Packaging with AI', 'Bringing an artistic and creative dimension to electronics packaging');
    const d = (x.DATA.challenges || {}).art || [
      ['FaPaintBrush', 'Create', 'Packaging technology reimagined as art, with AI as the creative tool'],
      ['FaSearch', 'View the entries', 'See how participants interpret electronics packaging'],
      ['FaComments', 'Join the discussion', 'Support the participants and share your thoughts'],
    ];
    detailList(s, x, d, 3.5);
    // visual: a "gallery" of chip-frames
    const gx = 7.9, gy = 1.6;
    const frames = [[gx, gy, 2.3, 2.3, C.text2, 'FaMicrochip'], [gx + 2.5, gy, 2.3, 1.4, C.accent1, 'FaPalette'], [gx + 2.5, gy + 1.6, 2.3, 2.6, C.accent2, 'FaRobot'], [gx, gy + 2.5, 2.3, 1.7, C.accent3, 'FaPaintBrush'], [gx, gy + 4.4, 4.8, 0.55, C.background2, null]];
    frames.forEach(([fx, fy, fw, fh, col, ico]) => {
      x.chipCard(s, fx, fy, fw, fh, { fill: col, pins: Math.max(2, Math.round(fh / 0.35)), shadow: true });
      if (ico) { const d2 = Math.min(fw, fh) * 0.42; s.addImage({ data: x.ic[ico], x: fx + (fw - d2) / 2, y: fy + (fh - d2) / 2, w: d2, h: d2, altText: 'icon' }); }
    });
    s.addText('Where engineering meets imagination', { x: gx, y: gy + 4.4, w: 4.8, h: 0.55, fontSize: 14, italic: true, bold: true, color: C.text2, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  },
});

// 9 ─ Tech Challenge - Open Category
slides.push({
  section: 'Challenges',
  notes: 'The second, the Tech Challenge, Open Category, addresses thermal management for advanced GPU and high-bandwidth memory packages in AI data centres.',
  build: (s, x) => {
    const { C, HEX } = x;
    challengeHeader(s, x, 2, 'Tech Challenge – Open Category', 'Thermal management for advanced GPU and HBM packages in AI data centres');
    const d = (x.DATA.challenges || {}).tech || [
      ['FaServer', 'The context', 'AI data-centre workloads push GPU and high-bandwidth memory (HBM) power ever higher'],
      ['FaFire', 'The problem', 'Removing heat from advanced GPU + HBM packages'],
      ['FaUsers', 'Open to all', 'Engineers and researchers demonstrate ideas on a real engineering problem'],
    ];
    detailList(s, x, d, 3.5);
    // visual: GPU + HBM package cross-section with heat arrows
    const bx = 7.6, by = 2.2, bw = 5.1;
    // heat arrows
    for (let i = 0; i < 5; i++) {
      s.addShape(x.pres.shapes.UP_ARROW, { x: bx + 0.55 + i * 0.9, y: by - 0.1, w: 0.42, h: 0.85, fill: { color: i === 2 ? C.accent2 : C.accent1, transparency: 15 }, line: { type: 'none' } });
    }
    s.addShape(x.pres.shapes.RECTANGLE, { x: bx + 0.2, y: by + 0.85, w: bw - 0.4, h: 0.3, fill: { color: HEX.pin }, line: { type: 'none' } }); // lid / heat spreader
    s.addText('Heat spreader / cooling', { x: bx + 0.2, y: by + 0.85, w: bw - 0.4, h: 0.3, fontSize: 11, bold: true, color: C.text1, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    // HBM stacks + GPU on interposer
    const ly = by + 1.25;
    const hbm = (hx) => { for (let k = 0; k < 6; k++) s.addShape(x.pres.shapes.RECTANGLE, { x: hx, y: ly + k * 0.24, w: 0.95, h: 0.2, fill: { color: k % 2 ? C.accent3 : C.accent1 }, line: { type: 'none' } }); };
    hbm(bx + 0.3); hbm(bx + bw - 1.25);
    s.addText('HBM', { x: bx + 0.3, y: ly + 1.45, w: 0.95, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: 'center', margin: 0, isTextBox: true });
    s.addText('HBM', { x: bx + bw - 1.25, y: ly + 1.45, w: 0.95, h: 0.3, fontSize: 12, bold: true, color: C.text2, align: 'center', margin: 0, isTextBox: true });
    s.addShape(x.pres.shapes.RECTANGLE, { x: bx + 1.45, y: ly + 0.35, w: bw - 2.9, h: 1.05, fill: { color: C.text2 }, line: { type: 'none' } });
    s.addText('GPU', { x: bx + 1.45, y: ly + 0.35, w: bw - 2.9, h: 1.05, fontSize: 22, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    // micro-bumps
    for (let k = 0; k < 22; k++) s.addShape(x.pres.shapes.OVAL, { x: bx + 0.32 + k * 0.205, y: ly + 1.78, w: 0.1, h: 0.1, fill: { color: HEX.grey }, line: { type: 'none' } });
    s.addShape(x.pres.shapes.RECTANGLE, { x: bx + 0.15, y: ly + 1.9, w: bw - 0.3, h: 0.32, fill: { color: C.accent2 }, line: { type: 'none' } });
    s.addText('Interposer', { x: bx + 0.15, y: ly + 1.9, w: bw - 0.3, h: 0.32, fontSize: 11, bold: true, color: 'FFFFFF', align: 'center', valign: 'middle', margin: 0, isTextBox: true });
    s.addShape(x.pres.shapes.RECTANGLE, { x: bx, y: ly + 2.27, w: bw, h: 0.42, fill: { color: C.background2 }, line: { color: HEX.peach2, width: 1 } });
    s.addText('Package substrate', { x: bx, y: ly + 2.27, w: bw, h: 0.42, fontSize: 12, bold: true, color: C.text2, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
  },
});

// 10 ─ Student Innovation Challenge
slides.push({
  section: 'Challenges',
  notes: 'The third, the Student Innovation Challenge, focuses on optimising thermal interface materials for advanced electronics packaging and reliability.' + CHALLENGE_CLOSE,
  build: (s, x) => {
    const { C, HEX } = x;
    challengeHeader(s, x, 3, 'Student Innovation Challenge', 'Optimising thermal interface materials for advanced packaging and reliability');
    const d = (x.DATA.challenges || {}).student || [
      ['FaUserGraduate', 'For students', 'The next generation tackles a real packaging problem'],
      ['FaFlask', 'The focus', 'Thermal interface materials (TIM) that improve heat flow and reliability'],
      ['FaAward', 'Support them', 'View the entries and join the discussions'],
    ];
    detailList(s, x, d, 3.5);
    // visual: package stack with TIM layers highlighted
    const bx = 7.7, bw = 4.9;
    const layers = [
      ['Heat sink', 0.75, HEX.pin, C.text1],
      ['TIM 2', 0.32, C.accent1, 'FFFFFF'],
      ['Lid / heat spreader', 0.5, HEX.grey, 'FFFFFF'],
      ['TIM 1', 0.32, C.accent1, 'FFFFFF'],
      ['Die', 0.55, C.text2, 'FFFFFF'],
      ['Substrate', 0.45, C.background2, C.text2],
    ];
    let y = 2.15;
    layers.forEach(([name, h, fill, tc], i) => {
      const inset = name === 'Die' || name === 'TIM 1' ? 1.1 : (name === 'Substrate' ? 0.3 : 0.3);
      s.addShape(x.pres.shapes.RECTANGLE, { x: bx + inset, y, w: bw - 2 * inset, h, fill: { color: fill }, line: { type: 'none' } });
      s.addText(name, { x: bx + inset, y, w: bw - 2 * inset, h, fontSize: 13, bold: true, color: tc, align: 'center', valign: 'middle', margin: 0, isTextBox: true });
      if (name === 'Heat sink') {
        for (let k = 0; k < 9; k++) s.addShape(x.pres.shapes.RECTANGLE, { x: bx + 0.4 + k * 0.5, y: y - 0.55, w: 0.18, h: 0.55, fill: { color: HEX.pin }, line: { type: 'none' } });
      }
      y += h + 0.04;
    });
    // solder balls
    for (let k = 0; k < 14; k++) s.addShape(x.pres.shapes.OVAL, { x: bx + 0.42 + k * 0.29, y: y, w: 0.18, h: 0.18, fill: { color: HEX.grey }, line: { type: 'none' } });
    // call-out
    s.addShape(x.pres.shapes.ROUNDED_RECTANGLE, { x: bx, y: y + 0.45, w: bw, h: 0.85, rectRadius: 0.08, fill: { color: C.background2 }, line: { type: 'none' } });
    s.addText([{ text: 'TIM layers ', options: { bold: true, color: C.accent1 } }, { text: 'carry heat from die to lid and lid to heat sink — where performance and reliability are won or lost.', options: { color: C.text1 } }],
      { x: bx + 0.2, y: y + 0.45, w: bw - 0.4, h: 0.85, fontSize: 14, valign: 'middle', margin: 0, isTextBox: true });
  },
});

module.exports = slides;
