# Builds slide backgrounds: banners + faint circuit-trace (semicon) pattern.
import random, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
D = '/tmp/claude-0/-home-user-qq-inprep/9a5e68ab-0d3a-5449-a1c3-0bcf27d05568/scratchpad/'
W, H = 2667, 1500  # 200 dpi for 13.333 x 7.5 in

# 1. top banner: remove baked-in page number "2"
top = cv2.imread(D + 'assets/3.png', cv2.IMREAD_UNCHANGED)
bgr = top[:, :, :3].copy()
box = bgr[25:70, 1650:1688]
m = np.zeros(bgr.shape[:2], np.uint8)
sub = (box.min(axis=2) > 175).astype(np.uint8) * 255
m[25:70, 1650:1688] = sub
m = cv2.dilate(m, np.ones((5, 5), np.uint8), iterations=2)
m[:6, :] = 0
fixed = cv2.inpaint(bgr, m, 6, cv2.INPAINT_TELEA)
top[:, :, :3] = fixed
cv2.imwrite(D + 'assets/top_banner_clean.png', top)

topI = Image.open(D + 'assets/top_banner_clean.png').convert('RGBA')
botI = Image.open(D + 'assets/4.png').convert('RGBA')
th = round(W * topI.height / topI.width)
bh = round(W * botI.height / botI.width)
topI = topI.resize((W, th), Image.LANCZOS)
botI = botI.resize((W, bh), Image.LANCZOS)
print('top h px', th, 'in', th / 200, 'bottom h px', bh, 'in', bh / 200)

def circuit(img, seed, regions, color=(244, 222, 206), width=3):
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img)
    for (x0, y0, x1, y1, n) in regions:
        for _ in range(n):
            x = rnd.randint(x0, x1); y = rnd.randint(y0, y1)
            pts = [(x, y)]
            dirx = rnd.choice([-1, 1])
            for seg in range(rnd.randint(2, 4)):
                if seg % 2 == 0:
                    L = rnd.randint(60, 260); x += dirx * L
                else:
                    L = rnd.randint(30, 110); dy = rnd.choice([-1, 1]) * L
                    x += dirx * abs(dy); y += dy  # 45 degree jog
                pts.append((x, y))
            d.line(pts, fill=color, width=width, joint='curve')
            for (px, py) in (pts[0], pts[-1]):
                r = 9
                d.ellipse([px - r, py - r, px + r, py + r], outline=color, width=width)
    return img

def make(name, regions, seed):
    base = Image.new('RGBA', (W, H), (255, 255, 255, 255))
    circuit(base, seed, regions)
    base.alpha_composite(topI, (0, 0))
    base.alpha_composite(botI, (0, H - bh))
    base.convert('RGB').save(D + 'assets/' + name, quality=92)

# content background: traces hug the left and right edges, leaving the centre clean
make('bg_content.jpg', [(0, 160, 420, H - 200, 14), (W - 420, 160, W, H - 200, 14)], 7)
# title background: denser traces on the right half
make('bg_title.jpg', [(1300, 160, W, H - 200, 40), (0, 160, 300, H - 200, 6)], 11)
