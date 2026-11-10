import pymupdf, re, sys
src = pymupdf.open('v2/banner.pdf'); des = pymupdf.open('v2/design.pdf')
out = pymupdf.open(); out.insert_pdf(src)
p = out[0]
before = p.get_contents()
p.show_pdf_page(p.rect, des, 0, overlay=True)
after = p.get_contents()
new = [x for x in after if x not in before and b'Do' in out.xref_stream(x)]
assert len(new) == 1, (before, after)
snippet = out.xref_stream(new[0]).strip()
orig_x = before[0]; assert len(before) == 1
body = out.xref_stream(orig_x)
anchor = b'f\nQ\nEMC\n'                              # end of the full-page white background
i = body.index(anchor) + len(anchor)
assert body[:i].count(b'Do') == 0
out.update_stream(orig_x, body[:i] + b'q\n' + snippet + b'\nQ\n' + body[i:])
# drop the now-duplicated appended stream from /Contents
out.xref_set_key(p.xref, 'Contents', f'{orig_x} 0 R')
out.set_metadata(src.metadata)
out.save(sys.argv[1], deflate=True, garbage=3)
print('ok', len(snippet))
