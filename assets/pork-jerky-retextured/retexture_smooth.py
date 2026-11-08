import numpy as np, sys, json
from PIL import Image
from scipy import ndimage as ndi
from retex import fill_texture
rng=np.random.default_rng(7)
def smooth_mask(core, size):
    sig=max(6,0.035*size)
    f=ndi.gaussian_filter(core.astype(np.float32),sig,mode='nearest')
    # gentle organic wobble (low-frequency)
    n=ndi.gaussian_filter(rng.normal(0,1,core.shape),sig*2.5); n/=n.std()+1e-6
    n2=ndi.gaussian_filter(rng.normal(0,1,core.shape),max(2,sig*0.35)); n2/=n2.std()+1e-6
    return f>(0.5+0.07*n+0.05*n2), sig
def process(src,dst,plan,rim_dir,close_r):
    a=np.array(Image.open(src).convert('RGBA')).astype(np.float32); al=a[...,3]/255
    H,W=al.shape
    core=al>0.78
    oldcore=ndi.binary_dilation(al>0.6,iterations=4)
    lab,n=ndi.label(core); sizes=ndi.sum(core,lab,range(1,n+1))
    core=np.isin(lab,np.where(sizes>300)[0]+1)
    # glow profile vs distance outside original core
    dout=ndi.distance_transform_edt(~core)
    bins=np.arange(0,160,2); prof=[];col=[]
    for b in bins:
        sel=(dout>b)&(dout<=b+2)
        prof.append(al[sel].mean() if sel.any() else 0)
        col.append(a[...,:3][sel&(al>0.02)].mean(0) if (sel&(al>0.02)).any() else a[...,:3][(al>0.02)&~core].mean(0))
    prof=np.array(prof); col=np.array(col)
    # pieces: close cracks, smooth each separately
    if close_r: core=ndi.binary_fill_holes(ndi.binary_closing(core,structure=np.ones((3,3)),iterations=close_r))
    lab,n=ndi.label(core); new=np.zeros_like(core)
    for i in range(1,n+1):
        m=lab==i; s=np.sqrt(m.sum())
        sm,_=smooth_mask(m,s); new|=sm&ndi.binary_dilation(m,iterations=int(0.05*s)+5)
    new=ndi.binary_fill_holes(new)
    # keep straight canvas edges (pieces bleeding off canvas)
    piece=new
    # texture
    pork=np.zeros((H,W,3),np.float32)
    lab,n=ndi.label(piece); objs=ndi.find_objects(lab)
    order=sorted(range(n),key=lambda i:-(lab[objs[i]]==i+1).sum())
    for k,i in enumerate(order):
        o=objs[i]; m=lab==i+1; key,ang=plan[k%len(plan)]
        tx,sc=fill_texture((H,W),(o[0].start,o[0].stop,o[1].start,o[1].stop),key,ang); pork[m]=tx[m]
        print(' piece',key,'scale %.2f'%sc)
    dist=ndi.distance_transform_edt(np.pad(piece,1,mode='edge'))[1:-1,1:-1]
    sm=ndi.gaussian_filter(piece.astype(np.float32),6); gy,gx=np.gradient(sm); g=np.hypot(gx,gy)+1e-6
    dx,dy=rim_dir; facing=np.clip((-gx/g*dx-gy/g*dy)/np.hypot(dx,dy),0,1); facing=ndi.gaussian_filter(facing,20)
    areas=[(lab==i+1).sum() for i in range(n)]
    width=max(10,0.035*np.sqrt(max(areas)))
    wob=1+0.35*ndi.gaussian_filter(rng.normal(0,1,(H,W)),width)/0.02
    wob=np.clip(1+0.3*(wob-1)/(np.abs(wob-1).max()+1e-6),0.7,1.3)
    band=np.clip(1-dist/(width*wob),0,1)**0.7*np.clip(facing*2.4-0.6,0,1)
    noise=ndi.gaussian_filter(rng.normal(0,1,(H,W)),1.0)
    fat=np.stack([224+9*noise,186+9*noise,160+9*noise],-1)
    pork=pork*(1-0.85*band[...,None])+fat*0.85*band[...,None]
    edge=np.clip(1-dist/(width*1.2),0,1)*(1-band); pork*=(1-0.15*edge)[...,None]
    # anti-aliased alpha for piece
    pa=np.clip(ndi.gaussian_filter(piece.astype(np.float32),0.8)*1.6-0.3,0,1)
    # rebuilt glow from new silhouette
    dn=ndi.distance_transform_edt(~piece); bi=np.clip((dn/2).astype(int),0,len(prof)-1)
    ga=np.where(oldcore,prof[bi],al); ga=np.where(piece,0,ga)
    gc=np.where(oldcore[...,None],col[bi],a[...,:3])
    ga=np.where(oldcore&(dn>=bins[-1]),0,ga)
    idx=ndi.distance_transform_edt(~piece,return_distances=False,return_indices=True)
    pf=pork[idx[0],idx[1]]
    A=pa+ga*(1-pa)
    rgb=(pf*pa[...,None]+gc*(ga*(1-pa))[...,None])/np.maximum(A,1e-6)[...,None]
    Image.fromarray(np.dstack([np.clip(rgb,0,255),np.clip(A*255,0,255)]).astype(np.uint8)).save(dst)
if __name__=='__main__':
    process(sys.argv[1],sys.argv[2],json.loads(sys.argv[3]),tuple(json.loads(sys.argv[4])),int(sys.argv[5]))
