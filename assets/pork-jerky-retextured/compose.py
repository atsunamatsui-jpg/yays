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
        # natural pork-fat colour: creamy off-white with a faint pink tint
        rgb=c[...,:3]; Lf=rgb.mean(-1); Sf=rgb.max(-1)-rgb.min(-1)
        wf=np.clip((Lf-128)/40,0,1)*np.clip((0.85-Sf/np.maximum(Lf,1))/0.3,0,1)
        wf=ndi.gaussian_filter(wf,0.8)[...,None]
        tint=np.array([1.075,0.975,0.95])
        Ln=np.clip(Lf*1.06+8,0,240)[...,None]
        c[...,:3]=np.clip(rgb*(1-wf)+Ln*tint*wf,0,255)
        by,bx=np.array(np.where(m)).mean(1); cy,cx=(np.array(np.where(ca>0.5)).mean(1))
        oy,ox=int(round(by-cy)),int(round(bx-cx))
        y0,x0=max(oy,0),max(ox,0); y1,x1=min(oy+c.shape[0],H),min(ox+c.shape[1],W)
        sub=c[y0-oy:y1-oy,x0-ox:x1-ox]; sa=sub[...,3:]/255
        dst=layer[y0:y1,x0:x1]
        dst[...,:3]=sub[...,:3]*sa+dst[...,:3]*(1-sa)
        dst[...,3:]=sa*255+dst[...,3:]*(1-sa)
        print(f,key,'scale %.2f'%sc)
    # ---- edge clean-up ----
    hard=layer[...,3]>140
    st=ndi.generate_binary_structure(2,1)
    hard=ndi.binary_opening(hard,st,iterations=3)          # drop thin fibres/strands
    lab,n=ndi.label(hard); sz=ndi.sum(hard,lab,range(1,n+1))
    hard=np.isin(lab,np.where(sz>=0.01*sz.max())[0]+1)    # drop specks
    holes=ndi.binary_fill_holes(hard)&~hard; hl,hn=ndi.label(holes)
    if hn:
        hs=ndi.sum(holes,hl,range(1,hn+1)); hard|=np.isin(hl,np.where(hs<400)[0]+1)
    # trim protruding light fat lumps / strands
    disk=np.hypot(*np.mgrid[-7:8,-7:8])<=7
    opened=ndi.binary_opening(hard,disk)
    Lc=layer[...,:3].mean(-1)
    lumps=hard&~opened&ndi.binary_dilation((Lc>125)&hard,iterations=2)
    hard=hard&~lumps
    lab,n=ndi.label(hard); sz=ndi.sum(hard,lab,range(1,n+1)); hard=np.isin(lab,np.where(sz>=0.01*sz.max())[0]+1)
    hard=ndi.binary_erosion(hard,iterations=2)             # trim light fringe
    g=ndi.gaussian_filter(hard.astype(np.float32),1.6)
    newa=np.clip((g-0.5)*2.2+0.5,0,1)
    valid=layer[...,3]>200
    inner=ndi.binary_erosion(hard&valid,iterations=5)
    idx=ndi.distance_transform_edt(~inner,return_distances=False,return_indices=True)
    src=layer[...,:3][idx[0],idx[1]]
    d=ndi.distance_transform_edt(inner==0)*(1)  # distance from inner core
    mix=np.clip(d/6,0,1)*0.75
    mix=np.where(valid,mix,1.0)[...,None]
    layer[...,:3]=layer[...,:3]*(1-mix)+src*mix
    layer[...,3]=newa*255
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
