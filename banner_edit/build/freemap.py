import pymupdf, numpy as np
from PIL import Image
from scipy import ndimage
d=pymupdf.open('v2/banner.pdf'); p=d[0]
Z=1.0
pix=p.get_pixmap(matrix=pymupdf.Matrix(Z,Z),alpha=False)
a=np.frombuffer(pix.samples,np.uint8).reshape(pix.height,pix.width,3).astype(np.int16)
content=(a.min(2)<246)
opaque_boxes=np.zeros_like(content)
for i in p.get_image_info(xrefs=True):
    x0,y0,x1,y1=[int(round(v*Z)) for v in i['bbox']]
    opaque=True
    if i['has-mask'] and i['xref']:
        sm=d.xref_get_key(i['xref'],'SMask')[1]
        try:
            mx=int(sm.split()[0]); m=pymupdf.Pixmap(d,mx); mv=np.frombuffer(m.samples,np.uint8)
            opaque = mv.mean()>230
        except Exception as e: opaque=False
    if opaque: opaque_boxes[max(0,y0):y1,max(0,x0):x1]=True
content|=opaque_boxes
np.save('v2/content.npy',content)
dist=ndimage.distance_transform_edt(~content)
np.save('v2/dist.npy',dist.astype(np.float32))
vis=np.asarray(Image.fromarray((a).astype(np.uint8)).convert('RGB')).copy()
free=dist>40
vis[free]=(vis[free]*0.5+np.array([0,200,120])*0.5).astype(np.uint8)
vis[opaque_boxes & (a.min(2)>=246)] = [255,0,255]
Image.fromarray(vis).resize((1700,850)).save('v2/freemap.png')
print(pix.width,pix.height)
