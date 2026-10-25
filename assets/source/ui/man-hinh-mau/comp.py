import numpy as np
from PIL import Image
from scipy import ndimage
B='/mnt/user-data/uploads/HoLua/assets/source/ui/_bang/'
def key(a,strict=False):
    a=a.copy();r,g,b=[a[...,i].astype(int) for i in range(3)]
    m=((r>230)&(b>230)&(g<40)) if strict else (((r>150)&(b>150)&(g<110))|((b>90)&(r>90)&(g<0.6*np.minimum(r,b))&(abs(r-b)<90)))
    a[m,3]=0;return a
def comps(f,dil=8,minfrac=0.0015,strict=False,rowtol=80):
    a=key(np.array(Image.open(B+f).convert('RGBA')),strict);al=a[...,3]>0
    lab,n=ndimage.label(ndimage.binary_dilation(al,iterations=dil));o=ndimage.find_objects(lab);sz=ndimage.sum(al,lab,range(1,n+1))
    L=[(o[i],i+1) for i in range(n) if sz[i]>minfrac*al.size]
    L.sort(key=lambda t:((t[0][0].start+t[0][0].stop)//2//rowtol, t[0][1].start))
    out=[]
    for s,l in L:
        b=a[s].copy();b[lab[s]!=l,3]=0;b[~al[s],3]=0;out.append(Image.fromarray(b.astype(np.uint8)))
    return out
