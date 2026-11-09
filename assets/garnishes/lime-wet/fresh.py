import numpy as np
from PIL import Image
from scipy import ndimage as ndi
rng=np.random.default_rng(11)
def grade(im, lime):
    c=im[...,:3]/255.0; w=ndi.gaussian_filter(lime.astype(np.float32),2)[...,None]
    # clarity: local contrast
    blur=np.stack([ndi.gaussian_filter(c[...,k],12) for k in range(3)],-1)
    cl=np.clip(c+(c-blur)*0.45,0,1)
    # vibrance / saturation
    L=cl.mean(-1,keepdims=True); sat=np.clip(L+(cl-L)*1.12,0,1)
    # deeper rind, luminous flesh: S-curve
    out=np.clip(sat,0,1); out=out*out*(3-2*out)*0.35+out*0.65
    # push hue: flesh slightly yellow-green, rind rich green
    Lo=out.mean(-1,keepdims=True)
    dark=np.clip((0.5-Lo)/0.3,0,1)            # rind -> deep emerald
    out=out*(1-dark*np.array([0.22,0.02,0.10]))
    bright=np.clip((Lo-0.6)/0.3,0,1)          # flesh -> pale, luminous
    out=out*(1-bright*0.25)+bright*0.25*np.array([0.93,0.98,0.80])
    return im[...,:3]*(1-w)+out*255*w
def droplets(im, region, n, rmin, rmax, scale):
    H,W=region.shape; sdf=np.full((H,W),1e6,np.float32)
    ys,xs=np.where(region)
    if len(ys)==0: return im
    pick=rng.choice(len(ys),n,replace=False)
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
    rs=[]
    for i in pick:
        r=(rmin+(rmax-rmin)*rng.random()**2.2)*scale
        r=max(r,rmin*scale*0.5)
        ex=rng.uniform(0.75,1.25)
        y0,x0=ys[i],xs[i]; R=int(r*1.4)+3
        sl=(slice(max(0,y0-R),min(H,y0+R)),slice(max(0,x0-R),min(W,x0+R)))
        d=np.hypot((xx[sl]-x0)/ex,(yy[sl]-y0)*ex)-r
        sdf[sl]=np.minimum(sdf[sl],d)
    m=np.clip(0.5-sdf,0,1); inside=np.clip(-sdf,0,None)
    Rd=rmax*scale*0.8; ins=np.clip(inside,0,Rd); h=np.sqrt(np.clip(ins*(2*Rd)-ins**2,0,None))
    h=ndi.gaussian_filter(h,0.8)
    gy,gx=np.gradient(h); n_=np.stack([-gx,-gy,np.ones_like(h)*1.1],-1); n_/=np.linalg.norm(n_,axis=-1,keepdims=True)
    light=np.array([-0.5,-0.6,0.62]); light/=np.linalg.norm(light)
    ndl=np.clip((n_*light).sum(-1),0,1); spec=np.clip(ndl**22*1.2,0,1)
    fres=1-n_[...,2]
    off=n_[...,:2]*6*scale; Y,X=np.mgrid[0:H,0:W]
    sy=np.clip((Y-off[...,1]).astype(int),0,H-1); sx=np.clip((X-off[...,0]).astype(int),0,W-1)
    under=im[sy,sx,:3]
    col=under*(1.02+0.12*ndl[...,None])
    col=col*(1-0.75*fres[...,None])+under*0.35*0.75*fres[...,None]   # dark refractive rim
    # bright caustic at bottom
    caus=np.clip((n_[...,1]-0.3)/0.3,0,1)*np.clip(1-fres*1.3,0,1)
    col=col+np.array([45,50,35.0])*caus[...,None]
    col=col*(1-spec[...,None])+255*spec[...,None]
    out=im.copy(); out[...,:3]=im[...,:3]*(1-m[...,None])+np.clip(col,0,255)*m[...,None]
    return out
def sheen(im, lime, scale):
    c=im[...,:3]; L=c.mean(-1)
    w=ndi.gaussian_filter(lime.astype(np.float32),2)
    loc=ndi.gaussian_filter(L,6*scale)
    hi=np.clip((L-loc-6)/40,0,1)*w            # existing glints/ridges
    hi=ndi.gaussian_filter(hi,0.6)
    c=c+(255-c)*(hi[...,None]*0.55)           # boost wet glints
    return c
def process(src,dst,ndrops,rmin,rmax,scale,nrind=None):
    im=np.array(Image.open(src).convert('RGBA')).astype(np.float32)
    al=im[...,3]/255; G=im[...,1]; R=im[...,0]; B=im[...,2]
    lime=(al>0.97)&(G>R+4)
    lime=ndi.binary_opening(lime,iterations=2)
    im[...,:3]=grade(im,lime)
    im[...,:3]=sheen(im,lime,scale)
    # droplets on the bright cut flesh (and some on rind)
    L=im[...,:3].mean(-1)
    flesh=ndi.binary_erosion(lime,iterations=int(10*scale))&(L>120)
    rind=ndi.binary_erosion(lime,iterations=int(6*scale))&(L<=120)
    im=droplets(im,flesh,ndrops,rmin,rmax,scale)
    if rind.sum()>1000: im=droplets(im,rind,nrind if nrind else ndrops//3,rmin*0.8,rmax*0.8,scale)
    Image.fromarray(np.clip(im,0,255).astype(np.uint8)).save(dst)
