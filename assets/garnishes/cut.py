import numpy as np, os, sys
from PIL import Image
from scipy import ndimage as ndi
OUT='/home/user/yays/assets/garnishes'; os.makedirs(OUT,exist_ok=True)
def cut(name, labels):
    a=np.asarray(Image.open(f'{name}.jpg').convert('RGB')).astype(np.float32)
    S=a.max(-1)-a.min(-1); L=a.mean(-1)
    m=(S>22)|(L<195)
    m=ndi.binary_opening(m,iterations=1)
    m=ndi.binary_closing(m,iterations=2)
    holes=ndi.binary_fill_holes(m)&~m; hl,hn=ndi.label(holes)
    if hn:
        hs=ndi.sum(holes,hl,range(1,hn+1)); m|=np.isin(hl,np.where(hs<40000)[0]+1)
    lab,n=ndi.label(m); sz=ndi.sum(m,lab,range(1,n+1))
    m=np.isin(lab,np.where(sz>=25)[0]+1)
    grp,gn=ndi.label(ndi.binary_dilation(m,iterations=30))
    objs=ndi.find_objects(grp)
    items=[]
    for g in range(1,gn+1):
        gm=m&(grp==g)
        if gm.sum()<1500: continue
        ys,xs=np.where(gm); items.append((ys.mean(),xs.mean(),gm))
    # order: rows top->bottom, then left->right
    H=a.shape[0]; items.sort(key=lambda t:(int(t[0]//(H/3)),t[1]))
    for k,(cy,cx,gm) in enumerate(items):
        # soft edge + white-fringe removal
        hard=ndi.binary_erosion(gm,iterations=1)
        alpha=np.clip((ndi.gaussian_filter(hard.astype(np.float32),1.1)-0.5)*2.2+0.5,0,1)
        inner=ndi.binary_erosion(hard,iterations=4)
        if inner.sum()<50: inner=hard
        idx=ndi.distance_transform_edt(~inner,return_distances=False,return_indices=True)
        src=a[idx[0],idx[1]]; d=ndi.distance_transform_edt(~inner)
        mix=np.clip(d/5,0,1)[...,None]*0.8
        rgb=a*(1-mix)+src*mix
        ys,xs=np.where(alpha>0.01); p=12
        y0,y1,x0,x1=max(ys.min()-p,0),min(ys.max()+p,a.shape[0]),max(xs.min()-p,0),min(xs.max()+p,a.shape[1])
        out=np.dstack([rgb,alpha*255])[y0:y1,x0:x1].astype(np.uint8)
        nm=labels[k] if k<len(labels) else f'{name}-{k+1}'
        Image.fromarray(out).save(f'{OUT}/{nm}.png',dpi=(300,300)); print(nm,out.shape[1],'x',out.shape[0])
cut('habanero',['habanero-whole-1','habanero-whole-2','habanero-whole-3','habanero-half','habanero-ring','habanero-whole-4'])
cut('lime',['lime-whole','lime-slice-1','lime-slice-2','lime-half','lime-wedge-1','lime-zest','lime-wedge-2','lime-wedge-3'])
cut('honey',['honey-drizzle','honey-drip','honey-drop-small','honey-drop-medium','honey-drop-large','honey-splash'])
