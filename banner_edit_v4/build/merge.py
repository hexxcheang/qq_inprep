import pymupdf, numpy as np, re, sys, zlib
src = pymupdf.open('v3/banner.pdf'); des = pymupdf.open('v4/design.pdf')
out = pymupdf.open('v3/banner.pdf'); p = out[0]
xo = out.xref_get_key(p.xref, 'Resources/XObject')[1]
X166 = int(re.search(r'/X166 (\d+) 0 R', xo).group(1))
print('X166 matrix', out.xref_get_key(X166, 'Matrix'), 'bbox', out.xref_get_key(X166, 'BBox'))
before = list(p.get_contents())
# 1) let PyMuPDF build a Form XObject from the design page, then steal it
p.show_pdf_page(p.rect, des, 0, overlay=True)
snip = [x for x in p.get_contents() if x not in before and b'Do' in out.xref_stream(x)][0]
name = re.search(rb'/(\w+) Do', out.xref_stream(snip)).group(1).decode()
pxo = out.xref_get_key(p.xref, 'Resources/XObject')[1]
form = int(re.search(rf'/{name} (\d+) 0 R', pxo).group(1))
out.xref_set_key(p.xref, 'Contents', f'{before[0]} 0 R' if len(before) == 1 else '[' + ' '.join(f'{x} 0 R' for x in before) + ']')
out.xref_set_key(p.xref, 'Resources/XObject', xo)                     # restore original resources
# 2) CTM in force when the page draws X166: ".24 0 0 -.24 0 1709.04 cm"
page_stream = out.xref_stream(before[0])
m = re.match(rb'q\s+([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) cm', page_stream)
a, b, c, d, e, f = map(float, m.groups()); assert b == 0 and c == 0
assert out.xref_get_key(X166, 'Matrix')[0] == 'null'
# the design form expects default (PyMuPDF/PDF) page space; cancel the CTM inside X166
inv = f'{1/a:.6f} 0 0 {1/d:.6f} {-e/a:.6f} {-f/d:.6f} cm'
out.xref_set_key(X166, 'Resources/XObject/EDsgn', f'{form} 0 R')
body = out.xref_stream(X166)
anchor = b'0 0 4535 2268 re\nf\nQ\nQ\n'
i = body.index(anchor) + len(anchor); assert body.count(anchor) == 1
out.update_stream(X166, body[:i] + f'q {inv} /EDsgn Do Q\n'.encode() + body[i:])
# 3) soft masks so the white boxes behind three left-panel logos become transparent (logo pixels untouched)
for xr in (387, 187, 188):
    pm = pymupdf.Pixmap(out, xr)
    if pm.alpha: pm = pymupdf.Pixmap(pm, 0)
    rgb = np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, pm.n)[..., :3].astype(np.float32)
    alpha = np.clip((250 - rgb.min(2)) / 55.0, 0, 1)
    if xr == 387:                                      # keep any existing transparency
        old = pymupdf.Pixmap(out, int(out.xref_get_key(xr, 'SMask')[1].split()[0]))
        alpha = np.minimum(alpha, np.frombuffer(old.samples, np.uint8).reshape(old.height, old.width)/255.0)
    data = (alpha*255).astype(np.uint8).tobytes()
    mx = out.get_new_xref()
    out.update_object(mx, f'<</Type/XObject/Subtype/Image/Width {pm.width}/Height {pm.height}/ColorSpace/DeviceGray/BitsPerComponent 8>>')
    out.update_stream(mx, data, compress=True)
    out.xref_set_key(xr, 'SMask', f'{mx} 0 R')
out.set_metadata(src.metadata)
out.save(sys.argv[1], deflate=True, garbage=3)
print('saved', sys.argv[1])
