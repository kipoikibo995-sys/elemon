# Tối ưu toàn bộ assets/source -> assets/r36s cho R36S. Chạy: python toi_uu_r36s.py
import os, sys, numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
ROOT=os.path.dirname(os.path.abspath(__file__)); SRC=os.path.join(ROOT,'source'); DST=os.path.join(ROOT,'r36s')
RULES=[  # (tiền tố thư mục, kiểu, giá trị, số màu, trong suốt)
 ('nen/nha-tam','size',(640,480),64,False),('nen/phong-trong','size',(640,480),64,False),('nen/khai-niem','size',(640,480),64,False),
 ('nen/ngoai-troi','size',(640,480),64,None),('do-theo-phong','scale',0.442,32,True),
 ('do-an','maxh',32,32,True),('trang-bi','maxh',32,32,True),('tinh-linh','scale',0.5,64,True),
 ('ui/_bang','scale',0.5,48,True)]
SKIP=('_cu_khong-ref','ui/r36s','ui/goc','_to_delete','_cu-khong-dung','_soat','_phuong-an','khai-niem-cu')
def rule(rel):
    for p,*r in RULES:
        if rel.startswith(p): return r
    return ('scale',0.5,48,True)
def key(a):
    r,g,b=[a[...,i].astype(int) for i in range(3)]
    m=((r>150)&(b>150)&(g<110))|((b>90)&(r>90)&(g<0.6*np.minimum(r,b))&(abs(r-b)<90))
    a[m,3]=0; return a
def one(rel):
    src=os.path.join(SRC,rel); dst=os.path.join(DST,rel); os.makedirs(os.path.dirname(dst),exist_ok=True)
    if os.path.exists(dst) and os.path.getmtime(dst)>=os.path.getmtime(src): return 'skip'
    kind,val,colors,alpha=rule(rel); im=Image.open(src).convert('RGBA'); a=np.array(im)
    if alpha is None: alpha=a[...,3].min()<255
    if alpha: a=key(a)
    im=Image.fromarray(a)
    if kind=='size': im=im.resize(val,Image.LANCZOS)
    elif kind=='scale': im=im.resize((max(1,round(im.width*val)),max(1,round(im.height*val))),Image.LANCZOS)
    elif kind=='maxh' and im.height>val: im=im.resize((max(1,round(im.width*val/im.height)),val),Image.LANCZOS)
    a=np.array(im); al=a[...,3]>110; rgb=a[...,:3].copy()
    rgb[...,0]=rgb[...,0]&0xF8; rgb[...,1]=rgb[...,1]&0xFC; rgb[...,2]=rgb[...,2]&0xF8
    p=Image.fromarray(rgb).quantize(colors-1 if alpha else colors,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    if alpha:
        idx=np.array(p); idx[~al]=colors-1; pal=p.getpalette()[:3*(colors-1)]+[255,0,255]
        p=Image.fromarray(idx.astype(np.uint8),'P'); p.putpalette(pal); p.save(dst,optimize=True,transparency=colors-1)
    else: p.save(dst,optimize=True)
    return 'ok'
if __name__=='__main__':
    files=[]
    only=[a.replace('\\','/') for a in sys.argv[1:]]
    for d,_,fs in os.walk(SRC):
        for f in fs:
            if f.lower().endswith('.png'):
                rel=os.path.relpath(os.path.join(d,f),SRC).replace('\\','/')
                if not any(s in rel for s in SKIP) and (not only or any(rel.startswith(o) for o in only)): files.append(rel)
    print(len(files),'file')
    with ProcessPoolExecutor() as ex:
        for i,(rel,r) in enumerate(zip(files,ex.map(one,files,chunksize=4))):
            if i%50==0: print(i,rel,r)
    print('xong ->',DST)
