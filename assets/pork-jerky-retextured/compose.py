import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
from match import beef_pieces
PLAN={1:('refs/r1',6,[('lo-10-grain-slab',-20,1)]),
      2:('refs/r2',0,[('lo-01-triangle',-20,0),('hi9',160,1),('lo-03-small-chunk',-170,1)]),
      3:('refs/r3',0,[('hi7',60,0)]),
      4:('refs/r4',0,[('lo-04-marbled-square',-60,0)])}
def Y(x): return x[...,0]*.299+x[...,1]*.587+x[...,2]*.114
TY=86.0; TC=np.array([134.,72.,52.])
for f,(src,cr,assign) in PLAN.items():
    a,pieces=beef_pieces(src,cr); a=a.astype(np.float32); al=a[...,3]/255; H,W=al.shape
    core=al>0.78
    oldcore=ndi.binary_dilation(al>0.6,iterations=4)
    dout=ndi.distance_transform_edt(~core); bins=np.arange(0,160,2); prof=[];col=[]
    for b in bins:
        sel=(dout>b)&(dout<=b+2); s2=sel&(al>0.02)
        prof.append(al[sel].mean() if sel.any() else 0); col.append(a[...,:3][s2].mean(0) if s2.any() else np.array([250,90,10.]))
    prof=np.array(prof); col=np.array(col)
    layer=np.zeros((H,W,4),np.float32)
    for m,(key,ang,fl) in zip(pieces,assign):
        im=Image.open(f'pool/{key}.png').convert('RGBA')
        if fl: im=im.transpose(Image.FLIP_LEFT_RIGHT)
        im=im.rotate(ang,expand=True,resample=Image.BICUBIC)
        c=np.array(im).astype(np.float32)
        sc=np.sqrt(m.sum()/(c[...,3]/255).sum())
        im=im.resize((int(im.width*sc),int(im.height*sc)),Image.LANCZOS); c=np.array(im).astype(np.float32)
        ca=c[...,3]/255
        # lightness/colour normalisation on the real piece
        mm=ca>0.9; mc=c[...,:3][mm].mean(0); y=Y(c[...,:3])[mm].mean()
        lg=TY/y; g=lg*(TC/(mc*lg))**0.5; g*=TY/Y(c[...,:3][mm]*g).mean()
        c[...,:3]=np.clip(c[...,:3]*g,0,255)
        by,bx=np.array(np.where(m)).mean(1); cy,cx=(np.array(np.where(ca>0.5)).mean(1))
        oy,ox=int(round(by-cy)),int(round(bx-cx))
        y0,x0=max(oy,0),max(ox,0); y1,x1=min(oy+c.shape[0],H),min(ox+c.shape[1],W)
        sub=c[y0-oy:y1-oy,x0-ox:x1-ox]; sa=sub[...,3:]/255
        dst=layer[y0:y1,x0:x1]
        dst[...,:3]=sub[...,:3]*sa+dst[...,:3]*(1-sa)
        dst[...,3:]=sa*255+dst[...,3:]*(1-sa)
        print(f,key,'scale %.2f'%sc)
    pa=layer[...,3]/255; piece=pa>0.5
    dn=ndi.distance_transform_edt(~piece); bi=np.clip((dn/2).astype(int),0,len(prof)-1)
    near=np.where(dn<bins[-1],prof[bi],0)
    t=np.clip((dout-110)/50,0,1)   # far field: keep original halo
    ga=near*(1-t)+al*t
    gc=col[bi]*(1-t[...,None])+a[...,:3]*t[...,None]
    ga=np.where(core&(dn>0),near,ga)
    A=pa+ga*(1-pa)
    rgb=(layer[...,:3]*pa[...,None]+gc*(ga*(1-pa))[...,None])/np.maximum(A,1e-6)[...,None]
    Image.fromarray(np.dstack([np.clip(rgb,0,255),np.clip(A*255,0,255)]).astype(np.uint8)).save(f'out/r{f}.png')
