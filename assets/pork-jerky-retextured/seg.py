import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
def segment(path):
    a=np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    R,G,B=a[...,0],a[...,1],a[...,2]
    mask=((R-B)>9)&((R-G)>12)
    mask=ndi.binary_opening(mask,iterations=2)
    mask=ndi.binary_closing(mask,iterations=3)
    # fill only small holes (keep real holes in the meat)
    holes=ndi.binary_fill_holes(mask)&~mask
    hl,hn=ndi.label(holes)
    if hn:
        hs=ndi.sum(holes,hl,range(1,hn+1))
        small=np.isin(hl,np.where(hs<4000)[0]+1)
        mask|=small
    return a,mask
if __name__=='__main__':
    a,mask=segment(sys.argv[1])
    lab,n=ndi.label(mask)
    vis=a.copy(); vis[~mask]=vis[~mask]*0.3+np.array([0,255,0])*0.7
    for i,sl in enumerate(ndi.find_objects(lab),1):
        s=(lab[sl]==i).sum()
        if s>8000: print(i,s,sl[1].start,sl[0].start,sl[1].stop,sl[0].stop)
    Image.fromarray(vis.astype(np.uint8)).resize((1000,750)).save(sys.argv[2])
