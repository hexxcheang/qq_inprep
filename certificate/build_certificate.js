// EPTC Best Academic Paper Award certificate — redesigned, fully editable text.
// Usage:  node make_art.js   (only if the border/seal artwork changes)
//         node build_certificate.js
// Output: out/EPTC_Best_Academic_Paper_Certificate.pptx (10 x 7.5 in, same size as the original)
//
// The golden frame is the slide background image, so it can't be nudged by accident while editing.
// Every piece of wording is its own text box (named in the Selection Pane) and can be edited directly.
const path = require('path');
const fs = require('fs');
const pptxgen = require('pptxgenjs');

const A = f => path.join(__dirname, 'assets', f);
const NAVY = '1F2A44', GOLD = '8A6614', GOLD_LINE = 'B8902F', GREY = '55514A';
const SERIF = 'Cambria', SANS = 'Calibri';

// ---- certificate wording (edit here or directly in PowerPoint) ----------------
const T = {
  confOrdinal: '26', confSuffix: 'th', conf: ' Electronics Packaging Technology Conference',
  date: [['3', ''], ['rd', 'sup'], [' – 6', ''], ['th', 'sup'], [' December 2024, Singapore', '']],
  award: 'Best Academic Paper Award',
  presented: 'is presented to',
  authors: 'Jan Albrecht and Sven Rzepka',
  affiliations: ['Fraunhofer Institute for Electronic Nanosystems, Chemnitz, Germany',
                 'Technical University of Chemnitz, Center for Micro and Nanotechnologies, Germany'],
  forPaper: 'for the paper',
  title: 'Determination of the Adhesive Strength of Monocrystalline Layers as a Thin Film on a Silicon Substrate by Means of Instrumented Indentation Testing',
  sig: [{ name: 'Dr King Jien Chui', role: 'General Chair', img: 'signature_general_chair.png' },
        { name: 'Prof Sunmi Shin', role: 'Technical Program Chair', img: 'signature_tpc_chair.png' }],
};

const imgSize = (f, h) => { // keep aspect ratio from the PNG header
  const b = fs.readFileSync(A(f)); const w = b.readUInt32BE(16), hh = b.readUInt32BE(20);
  return { w: h * w / hh, h };
};

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_4x3';                       // 10 x 7.5 in, as the original
  pres.title = 'EPTC Best Academic Paper Award Certificate';
  pres.author = 'EPTC Organising Committee';
  const s = pres.addSlide();
  s.background = { path: A('border.png') };

  const CX = 5, BOX_W = 8.0, BOX_X = CX - BOX_W / 2;
  const text = (runs, y, h, opt, name) => s.addText(runs, {
    x: BOX_X, y, w: BOX_W, h, align: 'center', valign: 'middle', margin: 0, isTextBox: true,
    fontFace: SANS, color: NAVY, objectName: name, fit: 'none', ...opt,
  });

  // logos
  const eptc = imgSize('eptc2024_logo.png', 0.72);
  s.addImage({ path: A('eptc2024_logo.png'), x: 1.18, y: 0.92, ...eptc, altText: 'EPTC 2024 logo', objectName: 'EPTC logo' });
  const eps = imgSize('ieee_eps_logo.png', 0.74);
  s.addImage({ path: A('ieee_eps_logo.png'), x: 8.82 - eps.w, y: 0.91, ...eps, altText: 'IEEE Electronics Packaging Society logo', objectName: 'IEEE EPS logo' });

  // conference
  text([{ text: T.confOrdinal, options: {} }, { text: T.confSuffix, options: { superscript: true } }, { text: T.conf, options: {} }],
    1.78, 0.32, { fontSize: 16, bold: true }, 'Conference name');
  text(T.date.map(([t, k]) => ({ text: t, options: k === 'sup' ? { superscript: true } : {} })),
    2.1, 0.26, { fontSize: 11.5, color: GREY }, 'Conference date');

  // award title
  text(T.award, 2.42, 0.62, { fontFace: SERIF, fontSize: 36, bold: true, color: GOLD, charSpacing: 1 }, 'Award title');

  // ornamental divider: two gold rules and a diamond
  const dy = 3.13;
  s.addShape(pres.shapes.LINE, { x: CX - 1.75, y: dy, w: 1.55, h: 0, line: { color: GOLD_LINE, width: 1 }, objectName: 'Divider left' });
  s.addShape(pres.shapes.LINE, { x: CX + 0.2, y: dy, w: 1.55, h: 0, line: { color: GOLD_LINE, width: 1 }, objectName: 'Divider right' });
  s.addShape(pres.shapes.DIAMOND, { x: CX - 0.09, y: dy - 0.09, w: 0.18, h: 0.18, fill: { color: 'C9A24A' }, line: { color: GOLD, width: 0.75 }, objectName: 'Divider diamond' });
  s.addShape(pres.shapes.OVAL, { x: CX - 1.82, y: dy - 0.035, w: 0.07, h: 0.07, fill: { color: GOLD_LINE }, line: { color: GOLD_LINE }, objectName: 'Divider dot left' });
  s.addShape(pres.shapes.OVAL, { x: CX + 1.75, y: dy - 0.035, w: 0.07, h: 0.07, fill: { color: GOLD_LINE }, line: { color: GOLD_LINE }, objectName: 'Divider dot right' });

  // recipients
  text(T.presented, 3.25, 0.26, { fontFace: SERIF, fontSize: 12, italic: true, color: GREY }, 'Presented to');
  text(T.authors, 3.5, 0.42, { fontFace: SERIF, fontSize: 24, bold: true }, 'Authors');
  text(T.affiliations.join('\n'), 3.94, 0.42, { fontSize: 10.5, color: GREY, lineSpacingMultiple: 1.05 }, 'Affiliations');

  // paper
  text(T.forPaper, 4.42, 0.24, { fontFace: SERIF, fontSize: 12, italic: true, color: GREY }, 'For the paper');
  s.addText(`“${T.title}”`, {
    x: CX - 3.75, y: 4.67, w: 7.5, h: 0.62, align: 'center', valign: 'top', margin: 0, isTextBox: true,
    fontFace: SERIF, fontSize: 14, italic: true, color: NAVY, lineSpacingMultiple: 1.05, objectName: 'Paper title',
  });

  // seal
  s.addImage({ path: A('seal.png'), x: CX - 0.54, y: 5.36, w: 1.08, h: 1.08 * 1560 / 1200, altText: 'Gold award seal', objectName: 'Award seal' });

  // signatures
  T.sig.forEach((g, k) => {
    const cx = k === 0 ? 2.55 : 7.45, lineY = 6.02;
    const sz = imgSize(g.img, k === 0 ? 0.6 : 0.4);
    s.addImage({ path: A(g.img), x: cx - sz.w / 2, y: lineY - sz.h - 0.03, ...sz, altText: `Signature of ${g.name}`, objectName: `Signature ${k + 1}` });
    s.addShape(pres.shapes.LINE, { x: cx - 1.15, y: lineY, w: 2.3, h: 0, line: { color: GOLD_LINE, width: 1 }, objectName: `Signature line ${k + 1}` });
    s.addText(g.name, { x: cx - 1.4, y: lineY + 0.05, w: 2.8, h: 0.28, align: 'center', margin: 0, isTextBox: true,
      fontFace: SERIF, fontSize: 13, bold: true, color: NAVY, objectName: `Signatory ${k + 1} name` });
    s.addText(g.role, { x: cx - 1.4, y: lineY + 0.32, w: 2.8, h: 0.24, align: 'center', margin: 0, isTextBox: true,
      fontFace: SANS, fontSize: 10.5, color: GREY, objectName: `Signatory ${k + 1} role` });
  });

  fs.mkdirSync(path.join(__dirname, 'out'), { recursive: true });
  const out = path.join(__dirname, 'out', 'EPTC_Best_Academic_Paper_Certificate.pptx');
  await pres.writeFile({ fileName: out });
  // drop zip folder entries (they can break opening via OneDrive/SharePoint)
  require('child_process').execFileSync('zip', ['-dq', out, '*/']);
  console.log('wrote', out);
})();
