import numpy as np, sys
from PIL import Image
from scipy import ndimage as ndi
rng=np.random.default_rng(3)
def capsule(H,W,x0,y0,x1,y1,r0,r1):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    dx,dy=x1-x0,y1-y0; L2=dx*dx+dy*dy
    t=np.clip(((xx-x0)*dx+(yy-y0)*dy)/L2,0,1)
    px,py=x0+t*dx,y0+t*dy; r=r0+(r1-r0)*t
    return np.hypot(xx-px,yy-py)-r          # signed distance
def circle(H,W,cx,cy,r):
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32); return np.hypot(xx-cx,yy-cy)-r
def smin(a,b,k):                            # smooth union -> organic necks
    h=np.clip(0.5+0.5*(b-a)/k,0,1); return b*(1-h)+a*h-k*h*(1-h)
def render(src,dst,drips,scale):
    im0=np.array(Image.open(src).convert('RGBA')).astype(np.float32); H0,W=im0.shape[:2]
    pad=int(0.38*H0); im=np.zeros((H0+pad,W,4),np.float32); im[:H0]=im0; H=H0+pad
    al=im[...,3]/255; G=im[...,1]; R=im[...,0]
    lime=(al>0.95)&(G>R+5)
    lime=ndi.binary_opening(lime,iterations=2)
    low=np.full(W,-1)
    for x in range(W):
        ys=np.where(lime[:,x])[0]
        if len(ys): low[x]=ys.max()
    sdf=np.full((H,W),1e6,np.float32)
    for (fx,length,width,drop) in drips:
        x=int(fx*W); 
        cols=[c for c in range(max(0,x-8),min(W,x+8)) if low[c]>0]
        if not cols: continue
        y0=max(low[c] for c in cols)-int(10*scale)
        L=length*scale; w=width*scale
        # stream: from edge down, slightly wavy, ends in a bulb
        sway=rng.uniform(-0.06,0.06)*L
        d=capsule(H,W,x,y0,x+sway,y0+L,w*1.25,w*0.55)
        d=smin(d,circle(H,W,x+sway,y0+L+w*0.9,w*1.35),w*0.9)
        # pooled bead where it leaves the lime
        d=smin(d,circle(H,W,x,y0+w*0.4,w*1.7),w*0.8)
        sdf=np.minimum(sdf,d)
        if drop:    # detached falling drop (teardrop)
            cy=y0+L+w*5.0
            dd=smin(circle(H,W,x+sway,cy,w*1.15),capsule(H,W,x+sway,cy-w*2.2,x+sway,cy,w*0.15,w*1.0),w*0.6)
            sdf=np.minimum(sdf,dd)
    m=np.clip(0.5-sdf,0,1)                   # anti-aliased coverage
    inside=np.clip(-sdf,0,None)
    Rd=13*scale; ins=np.clip(inside,0,Rd); h=np.sqrt(np.clip(ins*(2*Rd)-ins**2,0,None))  # dome height
    h=ndi.gaussian_filter(h,1.2*scale)
    gy,gx=np.gradient(h); nz=np.ones_like(h)*1.4
    n=np.stack([-gx,-gy,nz],-1); n/=np.linalg.norm(n,axis=-1,keepdims=True)
    light=np.array([-0.5,-0.6,0.62]); light/=np.linalg.norm(light)
    ndl=np.clip((n*light).sum(-1),0,1)
    spec=np.clip(ndl,0,1)**45
    stripe=np.clip((-n[...,0]-0.42)/0.12,0,1)*np.clip((0.7+n[...,0])/0.12,0,1)*np.clip(1-np.abs(n[...,1])/0.5,0,1)
    spec=np.clip(spec+0.85*stripe,0,1)
    fres=1-n[...,2]                          # edges of the drop
    caus=np.clip((n[...,1]-0.25)/0.3,0,1)*np.clip(1-fres*1.2,0,1)
    # refraction: sample what is under the drop, shifted by the normal
    off=(n[...,:2]*14*scale)
    yy,xx=np.mgrid[0:H,0:W]
    sy=np.clip((yy+off[...,1]).astype(int),0,H-1); sx=np.clip((xx+off[...,0]).astype(int),0,W-1)
    under=im[sy,sx,:3]; ua=al[sy,sx][...,None]
    juice=np.array([196,228,80.0])
    base=under*ua*0.6+juice*(1-ua*0.6)     # tinted see-through
    col=base*(0.85+0.25*ndl[...,None])
    col=col*(1-0.5*caus[...,None])+np.array([238,252,160.0])*0.5*caus[...,None]
    col=col*(1-0.6*fres[...,None]**1.3)+np.array([78,125,18.0])*0.6*fres[...,None]**1.3   # darker green rim
    col=col*(1-spec[...,None])+255*spec[...,None]
    # glint highlight
    a_j=(0.46+0.55*fres**1.2+0.35*caus+0.9*spec)*m
    a_j=np.clip(a_j,0,0.97)
    # juice alpha over transparent bg: more solid so it reads; over lime: blend
    outA=al+a_j*(1-al)
    outC=(im[...,:3]*al[...,None]*(1-a_j[...,None])+col*a_j[...,None])/np.maximum(outA,1e-6)[...,None]
    res=np.dstack([np.clip(outC,0,255),outA*255]).astype(np.uint8)
    ys=np.where(res[...,3]>2)[0]; res=res[:max(H0,ys.max()+20)]
    Image.fromarray(res).save(dst)
