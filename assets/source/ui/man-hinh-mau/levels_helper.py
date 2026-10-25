import sys;sys.path.insert(0,'/tmp/claude-0/s')
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from scipy import ndimage
T='/mnt/user-data/uploads/HoLua/assets/source/tinh-linh/'
def key(a):
    a=a.copy();r,g,b=[a[...,i].astype(int) for i in range(3)]
    m=((r>150)&(b>150)&(g<110))|((b>90)&(r>90)&(g<0.6*np.minimum(r,b))&(abs(r-b)<90));a[m,3]=0;return a
def first(f,cols,rows):
    im=Image.open(T+f).convert('RGBA');a=key(np.array(im));al=a[...,3]>0
    lab,n=ndimage.label(ndimage.binary_dilation(al,iterations=6));o=ndimage.find_objects(lab);sz=ndimage.sum(al,lab,range(1,n+1))
    # biggest component whose center is in the top-left grid cell
    H,W=al.shape;best=None
    for i in range(n):
        s=o[i];cy=(s[0].start+s[0].stop)/2;cx=(s[1].start+s[1].stop)/2
        if cx<W/cols and cy<H/rows and (best is None or sz[i]>sz[best]): best=i
    m=(lab==best+1)&al;b=a.copy();b[~m,3]=0;p=Image.fromarray(b);return p.crop(p.getbbox())
