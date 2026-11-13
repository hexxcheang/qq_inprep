import numpy as np, json
from PIL import Image
from scipy import ndimage
rgb=np.asarray(Image.open('v17/src29.png')).astype(int); R,G,B=rgb[...,0],rgb[...,1],rgb[...,2]; L=rgb.mean(2)
zone=np.zeros(L.shape,bool); zone[60:580,745:1145]=True
tile=zone&(B-R>6)&(L>215)                      # light blue-grey icon tiles
icon=zone&(B-R>60)&(L<215)                     # saturated blue glyphs
text=zone&(np.abs(R-B)<25)&(L<200)             # dark grey text
lab,n=ndimage.label(ndimage.binary_closing(tile|icon,iterations=2))
tiles=[s for s in ndimage.find_objects(lab) if (s[0].stop-s[0].start)>30]
out=[]
for s in sorted(tiles,key=lambda s:(s[1].start>940, s[0].start)):
    v0,v1,u0,u1=s[0].start,s[0].stop,s[1].start,s[1].stop
    cu=(u0+u1)/2
    # text lines below the tile within +/-95 px horizontally
    tz=np.zeros_like(text); tz[v1:v1+110,int(cu-95):int(cu+95)]=text[v1:v1+110,int(cu-95):int(cu+95)]
    rows=np.flatnonzero(tz.any(1)); lines=[]
    if len(rows):
        st=rows[0]; pr=rows[0]
        for r in list(rows[1:])+[10**6]:
            if r-pr>3:
                cols=np.flatnonzero(tz[st:pr+1].any(0)); lines.append([int(st),int(pr),int(cols.min()),int(cols.max())]); st=r
            pr=r
    out.append(dict(tile=[u0,v0,u1,v1], lines=lines))
    print('tile u%d-%d v%d-%d'%(u0,u1,v0,v1), 'lines', lines)
# colours
print('tile rgb', np.median(rgb[tile],0), ' icon rgb', np.percentile(rgb[icon],20,axis=0), ' text rgb', np.percentile(rgb[text],5,axis=0))
json.dump(out,open('v17/layout.json','w'))
