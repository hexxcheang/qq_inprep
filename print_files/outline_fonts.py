#!/usr/bin/env python3
"""Convert all text in a print PDF to vector outlines, keep CMYK values/images, re-attach the
original PDF/X OutputIntent, then verify.   Usage: python3 -I outline_fonts.py input.pdf output.pdf"""
import sys, re, subprocess, tempfile, os, numpy as np, pymupdf
src_path, out_path = sys.argv[1], sys.argv[2]
tmp = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
subprocess.run(['gs', '-q', '-o', tmp, '-sDEVICE=pdfwrite', '-dNoOutputFonts', '-dCompatibilityLevel=1.7',
                '-sColorConversionStrategy=LeaveColorUnchanged', '-dAutoRotatePages=/None',
                '-dDownsampleColorImages=false', '-dDownsampleGrayImages=false', '-dDownsampleMonoImages=false',
                '-dAutoFilterColorImages=false', '-dAutoFilterGrayImages=false',
                '-dColorImageFilter=/FlateEncode', '-dGrayImageFilter=/FlateEncode',
                '-dPassThroughJPEGImages=true', '-dPreserveOverprintSettings=true', src_path], check=True)
src, out = pymupdf.open(src_path), pymupdf.open(tmp)
m = re.search(r'/OutputIntents\s*\[\s*(\d+) 0 R', src.xref_object(src.pdf_catalog()))
if m:                                                       # re-attach the print colour profile Ghostscript drops
    oi = src.xref_object(int(m.group(1))); px = int(re.search(r'/DestOutputProfile\s+(\d+) 0 R', oi).group(1))
    nx = out.get_new_xref(); out.update_object(nx, '<< /N 4 >>'); out.update_stream(nx, src.xref_stream(px), compress=True)
    alt = src.xref_get_key(px, 'Alternate')
    if alt[0] != 'null': out.xref_set_key(nx, 'Alternate', alt[1])
    ni = out.get_new_xref(); out.update_object(ni, re.sub(r'/DestOutputProfile\s+\d+ 0 R', f'/DestOutputProfile {nx} 0 R', oi))
    out.xref_set_key(out.pdf_catalog(), 'OutputIntents', f'[{ni} 0 R]')
out.set_metadata(src.metadata); out.save(out_path, garbage=3, deflate=True); os.unlink(tmp)
# ---------------- verification ----------------
res = pymupdf.open(out_path)
fonts = sum(len(p.get_fonts()) for p in res); chars = sum(len(p.get_text().strip()) for p in res)
font_objs = sum(1 for x in range(1, res.xref_length()) if re.search(r'/Type\s*/Font\b|/FontFile', res.xref_object(x) or ''))
def render(f):
    p = pymupdf.open(f)[0]; pm = p.get_pixmap(alpha=False, colorspace=pymupdf.csCMYK)
    return np.frombuffer(pm.samples, np.uint8).reshape(pm.height, pm.width, 4).astype(int)
d = np.abs(render(src_path) - render(out_path)).max(2) > 16
tm = np.zeros(d.shape, bool)
for b in src[0].get_text('dict')['blocks']:
    if b['type'] == 0:
        x0, y0, x1, y1 = [int(v) for v in b['bbox']]; tm[max(0, y0-3):y1+3, max(0, x0-3):x1+3] = True
print(f'fonts left: {fonts}   font objects: {font_objs}   selectable text chars: {chars}')
print(f'page size unchanged: {tuple(res[0].rect) == tuple(src[0].rect)}   output intent kept: {bool(m) and "/OutputIntents" in res.xref_object(res.pdf_catalog())}')
print(f'visual differences: {int((d & tm).sum())} px at letter edges, {int((d & ~tm).sum())} px elsewhere')
