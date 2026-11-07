// EPTC 2026 General Chair welcome speech deck.
const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');
const fa = require('react-icons/fa');
const { icon } = require('./icons');
const L = require('./lib');
const { applyTheme } = require(process.env.PPTX_SKILL + '/scripts/apply_theme.js');
const { HEX, W, MX, A, chipCard, iconCircle, fit } = L;
const DATA = require('./data.js');

const OUT = process.argv[2] || path.join(__dirname, '..', 'EPTC2026_GC_welcome_speech.pptx');

(async () => {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_WIDE';
  pres.title = 'EPTC 2026 General Chair Welcome Speech';
  pres.author = 'EPTC 2026 Organising Committee';
  pres.theme = { headFontFace: L.THEME.headFontFace, bodyFontFace: L.THEME.bodyFontFace };
  const C = pres.SchemeColor;
  L.defineLayouts(pres);

  const ic = {};
  for (const n of ['FaMicrochip', 'FaHandshake', 'FaUsers', 'FaPalette', 'FaRobot', 'FaThermometerHalf', 'FaGraduationCap',
    'FaLightbulb', 'FaTrophy', 'FaBolt', 'FaFire', 'FaShieldAlt', 'FaLink', 'FaChalkboardTeacher', 'FaMicrophone', 'FaRoad',
    'FaCogs', 'FaRocket', 'FaIndustry', 'FaComments', 'FaGlobeAsia', 'FaHeart', 'FaUserFriends', 'FaTools', 'FaPaintBrush',
    'FaServer', 'FaLayerGroup', 'FaCalendarAlt', 'FaMapMarkerAlt', 'FaAward', 'FaSearch', 'FaMedal', 'FaUserGraduate', 'FaFlask']) {
    ic[n] = await icon(fa[n], '#FFFFFF');
  }

  const ctx = { pres, C, ic, HEX, W, MX, A, chipCard: (...a) => chipCard(pres, ...a), iconCircle: (...a) => iconCircle(pres, ...a), fit, DATA };
  const slides = require('./slides.js');
  for (const s of slides) {
    pres.addSection({ title: s.section });
    const slide = pres.addSlide({ masterName: s.layout || 'EPTC Content', sectionTitle: s.section });
    await s.build(slide, ctx);
    if (s.notes) slide.addNotes(s.notes);
  }

  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, L.THEME);
  console.log('wrote', OUT);
})().catch(e => { console.error(e); process.exit(1); });
