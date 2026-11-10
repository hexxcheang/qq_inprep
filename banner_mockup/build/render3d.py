# Paints the banner and its stand-off logo layers (all planes parallel to the banner)
# back-to-front through a pinhole camera, so the 3D depth is geometrically correct.
import sys, os, json, math, numpy as np
from PIL import Image, ImageFilter, ImageDraw
OUT = os.path.dirname(os.path.abspath(__file__)) + '/../out/'
L = json.load(open(OUT+'layers.json')); BW, BH = L['W'], L['H']
STANDOFF = {'eptc': 40, 'lam': 22, 'ieee': 14, 'eps': 14}      # page px (banner = %d px wide)

def render(name, yaw, pitch, px, py, dist, focal, size=(3840, 2160), center=(0.5, 0.47)):
    Wo, Ho = size; cx, cy = Wo*center[0], Ho*center[1]
    cy_, sy_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    def proj(X, Y, Z):
        x, y, z = X-px, Y-py, Z
        x, z = x*cy_ + z*sy_, -x*sy_ + z*cy_             # yaw
        y, z = y*cp - z*sp, y*sp + z*cp                  # pitch
        w = dist - z
        return cx + focal*x/w, cy + focal*y/w
    def coeffs(dst, src):     # PIL wants output->input mapping
        A, b = [], []
        for (u, v), (x, y) in zip(dst, src):
            A += [[u, v, 1, 0, 0, 0, -x*u, -x*v], [0, 0, 0, u, v, 1, -y*u, -y*v]]; b += [x, y]
        return np.linalg.solve(np.array(A, float), np.array(b, float))
    canvas = Image.new('RGBA', size)
    def paint(img, X0, Y0, Z, w=None, h=None):
        w = w or img.width; h = h or img.height
        corners = [(X0, Y0), (X0+w, Y0), (X0+w, Y0+h), (X0, Y0+h)]
        dst = [proj(x, y, Z) for x, y in corners]
        us, vs = [d[0] for d in dst], [d[1] for d in dst]
        u0, v0 = max(0, int(min(us))-2), max(0, int(min(vs))-2)
        u1, v1 = min(Wo, int(max(us))+3), min(Ho, int(max(vs))+3)
        if u1 <= u0 or v1 <= v0: return
        sx, sy = img.width/w, img.height/h
        c = coeffs([(u-u0, v-v0) for u, v in dst], [((x-X0)*sx, (y-Y0)*sy) for x, y in corners])
        t = img.transform((u1-u0, v1-v0), Image.PERSPECTIVE, tuple(c), Image.BICUBIC)
        canvas.alpha_composite(t, (u0, v0))
    # --- room ---
    yy, xx = np.mgrid[0:Ho, 0:Wo].astype(np.float32)
    r = np.sqrt(((xx-cx)/Wo)**2 + ((yy-Ho*0.30)/Ho)**2)
    wall = np.clip(0.26 - 0.20*r, 0.05, 1)
    bg = np.dstack([wall*0.93, wall*0.97, wall*1.05, np.ones_like(wall)])
    canvas = Image.fromarray((np.clip(bg, 0, 1)*255).astype(np.uint8), 'RGBA')
    # floor: plane y = BH (+ wall base), extends towards camera
    fl = [proj(-3000, BH+60, 0), proj(BW+3000, BH+60, 0), proj(BW+3000, BH+60, 9000), proj(-3000, BH+60, 9000)]
    floor = Image.new('RGBA', size); d = ImageDraw.Draw(floor); d.polygon(fl, fill=(46, 40, 36, 255))
    fg = np.asarray(floor, np.float32); shade = np.clip((yy - min(p[1] for p in fl[:2]))/(Ho*0.5), 0, 1)
    fg[..., :3] *= (1 - 0.55*shade[..., None]); canvas.alpha_composite(Image.fromarray(fg.astype(np.uint8), 'RGBA'))
    # soft shadow of the backdrop on wall + metal frame (light-box edge)
    sh = Image.new('L', size); ImageDraw.Draw(sh).polygon([proj(-40, -10, -30), proj(BW+40, -10, -30), proj(BW+60, BH+70, -30), proj(-60, BH+70, -30)], fill=170)
    sh = sh.filter(ImageFilter.GaussianBlur(Wo/90)); canvas.alpha_composite(Image.merge('RGBA', [Image.new('L', size)]*3 + [sh]))
    fr = Image.new('RGBA', (8, 8)); fr = Image.linear_gradient('L').resize((BW+60, BH+60)).convert('RGB')
    fr = Image.fromarray((150 + 70*np.asarray(fr, np.float32)/255).astype(np.uint8)).convert('RGBA')
    for z in range(-26, -2, 3): paint(fr.point(lambda v: int(v*(0.62 + 0.38*(z+26)/24))), -30, -30, z)
    paint(fr, -30, -30, -2)
    # --- banner surface, then each logo's extrusion and face ---
    paint(Image.open(OUT+'surface.png').convert('RGBA'), 0, 0, 0)
    for n, dd in L['layers'].items():
        side = Image.open(OUT+f'{n}_side.png'); face = Image.open(OUT+f'{n}_face.png')
        S = STANDOFF[n]; sa = np.asarray(side, np.float32)
        for z in range(1, S+1):
            t = z/S; s = sa.copy(); s[..., :3] *= (0.62 + 0.38*t)
            paint(Image.fromarray(s.astype(np.uint8), 'RGBA'), dd['x'], dd['y'], z)
        paint(face, dd['x'], dd['y'], S+1)
    # vignette + warm ceiling wash
    v = np.clip(1 - 0.55*np.clip(r-0.25, 0, 1)**1.4, 0, 1)
    out = np.asarray(canvas.convert('RGB'), np.float32)*v[..., None]
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT+f'{name}.png', optimize=True)
    print('saved', name)

V = {
 'mockup_wide':       dict(yaw=-16, pitch=4,  px=BW/2,  py=BH*0.5,  dist=16000, focal=7600),
 'mockup_closeup_left': dict(yaw=28, pitch=6, px=1150,  py=1050,    dist=9000,  focal=11500),
 'mockup_closeup_lam':  dict(yaw=-30, pitch=8, px=3900, py=520,     dist=9000,  focal=15000),
}
for k in (sys.argv[1:] or V): render(k, **V[k])
