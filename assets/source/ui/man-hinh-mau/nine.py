from PIL import Image
import numpy as np
def nine(src,W,H,cs,cd):
    """src image, target W,H, source corner cs px, dest corner cd px"""
    w,h=src.size;out=Image.new('RGBA',(W,H),(0,0,0,0))
    xs=[0,cs,w-cs,w];ys=[0,cs,h-cs,h];XD=[0,cd,W-cd,W];YD=[0,cd,H-cd,H]
    for i in range(3):
        for j in range(3):
            p=src.crop((xs[i],ys[j],xs[i+1],ys[j+1]));tw,th=XD[i+1]-XD[i],YD[j+1]-YD[j]
            if tw>0 and th>0: out.alpha_composite(p.resize((tw,th),Image.LANCZOS if (i!=1 and j!=1) else Image.NEAREST),(XD[i],YD[j]))
    return out
def q(im,colors=40):
    a=np.array(im);al=(a[...,3]>110).astype(np.uint8)*255
    rgb=np.array(Image.fromarray(a[...,:3]).quantize(colors,dither=Image.Dither.NONE).convert('RGB'))
    return Image.fromarray(np.dstack([rgb,al]).astype(np.uint8))
def three(src,W,H,cs):
    """horizontal 3-slice: scale height to H, keep end caps proportional"""
    w,h=src.size;k=H/h;cd=max(1,round(cs*k))
    L=src.crop((0,0,cs,h)).resize((cd,H),Image.LANCZOS);R=src.crop((w-cs,0,w,h)).resize((cd,H),Image.LANCZOS)
    M=src.crop((cs,0,w-cs,h)).resize((max(1,W-2*cd),H),Image.LANCZOS)
    o=Image.new('RGBA',(W,H));o.alpha_composite(L,(0,0));o.alpha_composite(M,(cd,0));o.alpha_composite(R,(W-cd,0));return o
