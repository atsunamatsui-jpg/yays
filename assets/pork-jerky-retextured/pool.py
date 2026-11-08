import numpy as np, glob, os
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
from seg import segment
I='/tmp/claude-0/-home-user-yays/eaa79dd2-13a7-5736-b283-2a924eb0d92f/images/'
def save(a,m,name):
    m=ndi.binary_erosion(m,iterations=2)
    ys,xs=np.where(m); p=20
    y0,y1,x0,x1=max(ys.min()-p,0),ys.max()+p,max(xs.min()-p,0),xs.max()+p
    al=Image.fromarray((m[y0:y1,x0:x1]*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.3))
    im=Image.fromarray(a[y0:y1,x0:x1].astype(np.uint8)).convert('RGBA'); im.putalpha(al); im.save(f'pool/{name}.png'); print(name,im.size)
# hi-res single pieces: component at center
for n in (7,8,9,10):
    a,mask=segment(f'{I}{n}.jpg'); lab,_=ndi.label(mask)
    c=lab[750,1000]
    if c==0:
        s=ndi.sum(mask,lab,range(1,lab.max()+1)); c=int(np.argmax(s))+1
    save(a,lab==c,f'hi{n}')
