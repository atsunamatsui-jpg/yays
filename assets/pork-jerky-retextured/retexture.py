import numpy as np, sys
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
I='/tmp/claude-0/-home-user-yays/eaa79dd2-13a7-5736-b283-2a924eb0d92f/images/'
TEX={'t7':(7,(680,470,1450,1110)),'t9':(9,(450,450,1500,990)),'t10':(10,(330,560,1600,1000)),
     't6a':(6,(1170,260,1540,540)),'t6b':(6,(470,820,900,1140)),'t8':(8,(620,600,1280,1000))}
def tex(k): n,b=TEX[k]; return Image.open(f'{I}{n}.jpg').convert('RGB').crop(b)
def fill_texture(shape_hw, bbox, key, angle):
    H,W=shape_hw; y0,y1,x0,x1=bbox; h,w=y1-y0,x1-x0
    t=tex(key).rotate(angle,expand=True,resample=Image.BICUBIC)
    # crop away rotated corners: take central inscribed region
    a=np.deg2rad(angle%180); tw,th=tex(key).size
    c,s=abs(np.cos(a)),abs(np.sin(a))
    # largest axis-aligned rect inside rotated rect (approx)
    iw=(tw*c-th*s)/(c*c-s*s) if abs(c*c-s*s)>0.3 else min(tw,th)*0.7
    ih=(th*c-tw*s)/(c*c-s*s) if abs(c*c-s*s)>0.3 else min(tw,th)*0.7
    iw,ih=max(iw,50),max(ih,50)
    cx,cy=t.width/2,t.height/2
    t=t.crop((int(cx-iw/2),int(cy-ih/2),int(cx+iw/2),int(cy+ih/2)))
    sc=max(w/t.width,h/t.height)*1.02
    t=t.resize((int(t.width*sc)+1,int(t.height*sc)+1),Image.LANCZOS)
    out=np.zeros((H,W,3),np.float32)
    ox=(t.width-w)//2; oy=(t.height-h)//2
    out[y0:y1,x0:x1]=np.asarray(t)[oy:oy+h,ox:ox+w]
    return out, sc
def process(src, dst, plan, rim_dir=(0.3,1.0)):
    a=np.array(Image.open(src).convert('RGBA')).astype(np.float32)
    al=a[...,3]/255
    core=al>0.78
    core=ndi.binary_closing(core,iterations=3)
    lab,n=ndi.label(core); objs=ndi.find_objects(lab)
    sizes=[(lab[o]==i+1).sum() for i,o in enumerate(objs)]
    rgb=a[...,:3].copy()
    beefL=a[...,:3].mean(-1)
    pork=np.zeros_like(rgb); piece=np.zeros(al.shape,bool)
    order=np.argsort(sizes)[::-1]
    k=0
    if len(plan)==1 and plan[0][0]!='each':
        keep=[i for i in order if sizes[i]>=300]
        m=np.isin(lab,[i+1 for i in keep]); ys,xs=np.where(m)
        bb=(ys.min(),ys.max()+1,xs.min(),xs.max()+1)
        tx,sc=fill_texture(al.shape,bb,plan[0][0],plan[0][1]); pork[m]=tx[m]; piece|=m; k=1
        print(' union',bb,plan[0],'scale %.2f'%sc); order=[]
    for idx in order:
        if sizes[idx]<1500: continue
        o=objs[idx]; m=lab==idx+1
        key,ang=plan[k%len(plan)]; k+=1
        bb=(o[0].start,o[0].stop,o[1].start,o[1].stop)
        tx,sc=fill_texture(al.shape,bb,key,ang)
        pork[m]=tx[m]; piece|=m
        print(' piece',bb,'tex',key,'scale %.2f'%sc)
    # merge small fragments into nearest texture by dilation
    piece_d=core
    # fat rim: inner band on edges facing rim_dir
    dist=ndi.distance_transform_edt(piece)
    sm=ndi.gaussian_filter(piece.astype(np.float32),6)
    gy,gx=np.gradient(sm); g=np.hypot(gx,gy)+1e-6
    nx,ny=-gx/g,-gy/g   # outward normal
    dx,dy=rim_dir; dn=np.hypot(dx,dy)
    facing=np.clip((nx*dx+ny*dy)/dn,0,1)
    facing=ndi.gaussian_filter(facing,15)
    width=max(8,0.03*np.sqrt(piece.sum()/max(k,1)))
    band=np.clip(1-(dist/width),0,1)*np.clip(facing*2.2-0.5,0,1)
    noise=ndi.gaussian_filter(np.random.default_rng(1).normal(0,1,al.shape),1.2)
    fat=np.stack([226+8*noise,192+8*noise,168+8*noise],-1)
    # rim also slightly translucent-pink toward meat
    pork=pork*(1-band[...,None]*0.85)+fat*(band[...,None]*0.85)
    # subtle edge darkening for thickness
    edge=np.clip(1-dist/ (width*1.5),0,1)*(1-band)
    pork*= (1-0.18*edge)[...,None]
    # keep a little of the original fold shading
    bl=ndi.gaussian_filter(beefL,40); ref=np.median(bl[piece]) if piece.any() else 1
    pork*=np.clip(1+0.12*(bl/ref-1),0.9,1.1)[...,None]
    # composite: inside piece use pork; blend near soft alpha boundary
    w=np.clip((al-0.55)/0.3,0,1)*ndi.binary_dilation(piece,iterations=3)
    pork_full=pork.copy()
    # extend pork colours outward a few px for antialias zone
    idx=ndi.distance_transform_edt(~piece,return_distances=False,return_indices=True)
    pork_full=pork[idx[0],idx[1]]
    out=rgb*(1-w[...,None])+pork_full*w[...,None]
    res=np.dstack([np.clip(out,0,255),a[...,3]]).astype(np.uint8)
    Image.fromarray(res).save(dst)
if __name__=='__main__':
    import json
    process(sys.argv[1],sys.argv[2],json.loads(sys.argv[3]),tuple(json.loads(sys.argv[4])) if len(sys.argv)>4 else (0.3,1.0))
