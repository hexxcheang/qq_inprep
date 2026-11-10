import numpy as np, pymupdf, io
from PIL import Image, ImageDraw, ImageFilter
PX0, PY0, PX1, PY1, S = 0, 86, 1010, 1131, 3
dark = np.load('v4/dark.npy').astype(np.float32); copper = np.load('v4/copper.npy').astype(np.float32)/255
gb = np.load('v4/glowboard.npy').astype(np.float32)
SH, SW = copper.shape
gy, gx = np.mgrid[0:SH, 0:SW].astype(np.float32); X = gx/S+PX0; Y = gy/S+PY0
# dark band polygon (page pt): slanted right edge and slanted bottom edge, clear of the EPTC logo (starts y=414)
BAND = [(0, 86), (996, 86), (972, 336), (0, 398)]
def to_px(pts): return [((x-PX0)*S, (y-PY0)*S) for x, y in pts]
m = Image.new('L', (SW, SH)); ImageDraw.Draw(m).polygon(to_px(BAND), fill=255)
band = np.asarray(m.filter(ImageFilter.GaussianBlur(0.8)), np.float32)/255
# light continuation: cream board with faint copper + faint glow, stronger just below the band
cream = np.array([255, 249, 243], np.float32); rust = np.array([178, 70, 30], np.float32)
near = np.clip(1 - (Y-398)/520, 0.25, 1)                  # copper fades out going down
ca = (copper*0.20*near)[..., None]
light = cream*(1-ca) + rust*ca
light += (gb*0.10*near[..., None])                         # faint warm glow on lit traces
spill = np.exp(-np.clip(Y-380, 0, None)/90)               # warm light spilling out of the band
light = light*(1-0.18*spill[..., None]) + np.array([250, 190, 150])*0.18*spill[..., None]
light = np.clip(light, 0, 255)
# panel fade (light part only): right and bottom
fx = np.clip((1000-X)/110, 0, 1); fy = np.clip((1122-Y)/70, 0, 1)
P = (fx*fx*(3-2*fx))*(fy*fy*(3-2*fy))
rgb = dark*band[..., None] + light*(1-band[..., None])
alpha = np.maximum(band, P*(1-band))
Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).save('v4/panel.jpg', quality=92, subsampling=0)
Image.fromarray((alpha*255).astype(np.uint8)).save('v4/panel_mask.png')
Image.fromarray(np.dstack([np.clip(rgb, 0, 255), alpha*255]).astype(np.uint8)).resize((SW//3, SH//3)).save('v4/panel_preview.png')
# design page: raster panel + crisp glowing edge lines (vector)
src = pymupdf.open('v3/banner.pdf'); PW, PH = src[0].rect.width, src[0].rect.height
doc = pymupdf.open(); pg = doc.new_page(width=PW, height=PH)
pg.insert_image(pymupdf.Rect(PX0, PY0, PX1, PY1), stream=open('v4/panel.jpg', 'rb').read(), mask=open('v4/panel_mask.png', 'rb').read())
sh = pg.new_shape()
for w, op, col in ((7, 0.18, (1, 0.55, 0.2)), (3.2, 0.45, (1, 0.6, 0.25)), (1.3, 1.0, (1, 0.84, 0.6))):
    sh.draw_polyline([BAND[1], BAND[2], BAND[3]]); sh.finish(color=col, width=w, stroke_opacity=op, closePath=False, lineJoin=1)
sh.commit()
for x in range(1, doc.xref_length()):
    sm = doc.xref_get_key(x, 'SMask')
    if sm[0] == 'xref':
        mx = int(sm[1].split()[0]); print('smask cs was', doc.xref_get_key(mx, 'ColorSpace'), doc.xref_object(int(doc.xref_get_key(mx, 'ColorSpace')[1].split()[0])) if doc.xref_get_key(mx, 'ColorSpace')[0]=='xref' else '')
        doc.xref_set_key(mx, 'ColorSpace', '/DeviceGray')
doc.save('v4/design.pdf', deflate=True)
print('ok')
