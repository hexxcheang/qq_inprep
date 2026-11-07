// Render react-icons to PNG data URIs (white glyph by default).
const React = require('react');
const RDS = require('react-dom/server');
const sharp = require('sharp');
async function icon(Comp, color = '#FFFFFF', size = 256) {
  const svg = RDS.renderToStaticMarkup(React.createElement(Comp, { color, size }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return 'image/png;base64,' + buf.toString('base64');
}
module.exports = { icon };
