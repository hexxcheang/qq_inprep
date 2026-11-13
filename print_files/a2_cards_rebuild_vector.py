import json, subprocess, numpy as np, cv2, pymupdf
from PIL import Image, ImageFont, ImageDraw
SRC = 'v17/board.pdf'; FONT = 'fonts/Lato-Regular.ttf'
d = pymupdf.open(SRC); page = d[0]
# visible card image (xref 29): source pixel (u, v) -> page point
bb = [i['bbox'] for i in page.get_image_info(xrefs=True) if i['xref'] == 29][0]
SX, SY = (bb[2]-bb[0])/1200, (bb[3]-bb[1])/630
P = lambda u, v: (bb[0] + u*SX, bb[1] + v*SY)
rgb = np.asarray(Image.open('v17/src29.png')).astype(int)
cm = pymupdf.Pixmap(d, 29); cmyk = np.frombuffer(cm.samples, np.uint8).reshape(630, 1200, cm.n)[..., :4].astype(float)/255
layout = json.load(open('v17/layout.json'))
R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]; L = rgb.mean(2)
zone = np.zeros(L.shape, bool); zone[60:580, 745:1145] = True
def med(mask): return tuple(float(x) for x in np.median(cmyk[mask], 0))
C_WHITE = med(zone & (rgb.min(2) >= 254))
C_TILE = med(zone & (B-R > 6) & (L > 230) & (L < 247))
ic = zone & (B-R > 60) & (L < 215); C_ICON = tuple(float(x) for x in np.median(cmyk[ic & (L <= np.percentile(L[ic], 35))], 0))
tx = zone & (np.abs(R-B) < 25) & (L < 200); C_TEXT = tuple(float(x) for x in np.median(cmyk[tx & (L <= np.percentile(L[tx], 15))], 0))
print('CMYK white', np.round(C_WHITE, 3), 'tile', np.round(C_TILE, 3), 'icon', np.round(C_ICON, 3), 'text', np.round(C_TEXT, 3))
LABELS = [['Speaker &', 'attendee profiles'], ['Polls & Surveys'], ['In-app', 'announcements &', 'Notifications'],
          ['In-app messaging'], ['Agenda', 'personalization'], ['Quick & easy', 'networking']]
# ---- fit font size from ink widths (in source px)
big = ImageFont.truetype(FONT, 400)
def ink(s):  # ink bbox at 400 px
    return big.getbbox(s)
ratios = []
for card, labels in zip(layout, LABELS):
    for ln, s in zip(card['lines'], labels):
        x0, y0, x1, y1 = ink(s); ratios.append((ln[3]-ln[2]+1)/((x1-x0)/400))
size_src = float(np.median(ratios)); print('font size (source px):', round(size_src, 2), ' spread', np.round(np.percentile(ratios, [10, 90]), 2))
# ---- overlay page
ov = pymupdf.open(); op = ov.new_page(width=page.rect.width, height=page.rect.height)
sh = op.new_shape()
CARD_ROWS = [(70, 221), (239, 390), (408, 559)]
for cu0 in (753, 950):
    for v0, v1 in CARD_ROWS:
        r = pymupdf.Rect(*P(cu0, v0), *P(cu0+179, v1))
        sh.draw_rect(r, radius=4/179); sh.finish(fill=C_WHITE, color=None, width=0)
sh.commit()
for card in layout:
    u0, v0, u1, v1 = card['tile']
    sh = op.new_shape(); sh.draw_rect(pymupdf.Rect(*P(u0, v0), *P(u1, v1)), radius=0.08); sh.finish(fill=C_TILE, color=None, width=0); sh.commit()
    # ---- trace the icon glyph (16x upscale, smoothed, thresholded)
    pad = 2; reg = rgb[v0-pad:v1+pad, u0-pad:u1+pad].astype(float)
    tile_l, icon_l = np.mean([237, 244, 248]), np.mean([60, 174, 227])
    a = np.clip((tile_l - reg.mean(2))/(tile_l - icon_l), 0, 1)
    a *= ((reg[..., 2]-reg[..., 0]) > 15)      # blue only
    K = 24; up = cv2.resize(a.astype(np.float32), None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    up = cv2.GaussianBlur(up, (0, 0), K*0.75)
    m = (up > 0.5).astype(np.uint8)
    cnts, hier = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    sh = op.new_shape()
    for c in cnts:
        if cv2.contourArea(c) < K*K*1.0: continue
        c = cv2.approxPolyDP(c, K*0.035, True)[:, 0, :].astype(float)
        pts = [P(u0-pad + (x+0.5)/K, v0-pad + (y+0.5)/K) for x, y in c]
        sh.draw_polyline(pts + [pts[0]])
    sh.finish(fill=C_ICON, color=None, width=0, even_odd=True, closePath=True); sh.commit()
for card, labels in zip(layout, LABELS):
    for ln, s in zip(card['lines'], labels):
        x0, y0, x1, y1 = ink(s); k = size_src/400
        cx = (ln[2]+ln[3]+1)/2; left_src = cx - (x1+x0)/2*k            # centre the ink horizontally
        base_src = ln[0] - y0*k + big.getmetrics()[0]*k                  # ink top -> baseline
        x, y = P(left_src, base_src)
        op.insert_text((x, y), s, fontsize=size_src*SY, fontfile=FONT, fontname='LatoR', color=C_TEXT)
ov.save('v17/overlay_text.pdf')
# ---- convert the overlay's text to outlines (keeps CMYK values)
subprocess.run(['gs', '-q', '-o', 'v17/overlay.pdf', '-sDEVICE=pdfwrite', '-dNoOutputFonts', '-sColorConversionStrategy=LeaveColorUnchanged',
                '-dAutoRotatePages=/None', 'v17/overlay_text.pdf'], check=True)
ovl = pymupdf.open('v17/overlay.pdf')
page.show_pdf_page(page.rect, ovl, 0, overlay=True)
d.save('v17/board_hires_cards.pdf', garbage=3, deflate=True)
print('saved')
