import numpy as np
from PIL import Image
from scipy import ndimage as ndi
POOL=['hi7','hi8','hi9','hi10','lo-01-triangle','lo-03-small-chunk','lo-04-marbled-square','lo-06-small-rect','lo-10-grain-slab']
def beef_pieces(path,close_r):
    a=np.array(Image.open(path).convert('RGBA')); al=a[...,3]/255
    core=al>0.78
    lab,n=ndi.label(core); s=ndi.sum(core,lab,range(1,n+1)); core=np.isin(lab,np.where(s>300)[0]+1)
    if close_r: core=ndi.binary_fill_holes(ndi.binary_closing(core,np.ones((3,3)),iterations=close_r))
    lab,n=ndi.label(core); return a,[lab==i for i in range(1,n+1)]
def norm_mask(m,S=128):
    ys,xs=np.where(m); cy,cx=ys.mean(),xs.mean(); r=np.sqrt(m.sum()/np.pi)
    return cy,cx,r
def iou_score(beef, cand_alpha, ang, flip):
    # beef: bool mask cropped; cand: alpha array
    im=Image.fromarray((cand_alpha>127).astype(np.uint8)*255)
    if flip: im=im.transpose(Image.FLIP_LEFT_RIGHT)
    im=im.rotate(ang,expand=True,resample=Image.NEAREST)
    c=np.array(im)>127
    # scale cand to beef area
    sc=np.sqrt(beef.sum()/c.sum())
    im=Image.fromarray(c.astype(np.uint8)*255).resize((max(1,int(c.shape[1]*sc)),max(1,int(c.shape[0]*sc))),Image.NEAREST)
    c=np.array(im)>127
    by,bx=np.array(np.where(beef)).mean(1); cy,cx=np.array(np.where(c)).mean(1)
    H,W=beef.shape; canvas=np.zeros_like(beef)
    oy,ox=int(round(by-cy)),int(round(bx-cx))
    ys,xs=np.where(c); ys=ys+oy; xs=xs+ox; ok=(ys>=0)&(ys<H)&(xs>=0)&(xs<W)
    canvas[ys[ok],xs[ok]]=True
    out=(~ok).sum()  # parts falling off canvas count as mismatch
    inter=(canvas&beef).sum(); uni=(canvas|beef).sum()+out
    return inter/uni, sc
