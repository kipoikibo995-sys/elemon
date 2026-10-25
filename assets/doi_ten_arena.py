# Đổi tên file Arena (tiền tố cố định) theo thứ tự job trong log.
# Dùng: python doi_ten_arena.py "code1:OK,code2:AB,..."  (AB = Arena trả 2 ảnh → tự chọn ảnh "pixel" hơn)
import os,sys,glob
import numpy as np
from PIL import Image
D=os.path.expanduser('~/mnt/Downloads')
items=[x.split(':') for x in sys.argv[1].split(',') if x]
fs=sorted([f for f in glob.glob(os.path.join(D,'*Cute_game_art*')) if not f.endswith(('.done','.loai'))],key=os.path.getmtime)
fs=list(dict.fromkeys(fs))
def frames_mask(f,cols=4,rows=2):
    a=np.asarray(Image.open(f).convert('RGB')).astype(int);r,g,b=a[...,0],a[...,1],a[...,2]
    fg=~(((r>150)&(b>150)&(g<110))|((r-g>60)&(b-g>60)&(r>110)&(b>110)))
    H,W=fg.shape;out=[]
    for j in range(rows):
        for i in range(cols):
            c=fg[j*H//rows:(j+1)*H//rows,i*W//cols:(i+1)*W//cols]
            ys,xs=np.nonzero(c)
            if len(xs)<50: out.append(None);continue
            c=c[ys.min():ys.max()+1,xs.min():xs.max()+1]
            out.append(np.asarray(Image.fromarray((c*255).astype(np.uint8)).resize((64,64),Image.NEAREST))>0)
    return out
def score(f):
    """cao hơn = tốt hơn: khung liền mạch (silhouette giống nhau giữa các khung kề) + đủ 8 khung + ít màu (pixel)"""
    m=frames_mask(f);ok=[x for x in m if x is not None]
    if len(ok)<6: return -9
    iou=[(a&b).sum()/max(1,(a|b).sum()) for a,b in zip(ok,ok[1:])]
    cont=float(np.mean(iou))-float(np.std(iou))
    a=np.asarray(Image.open(f).convert('RGB').resize((256,256),Image.NEAREST)).reshape(-1,3)//8
    colors=len(np.unique(a,axis=0))
    return cont*2 + len(ok)/8 - colors/4000
def save(src,code):
    dst=os.path.join(D,code+'.png')
    if src.endswith('.webp'): Image.open(src).save(dst);os.rename(src,src+'.done')
    else: os.rename(src,dst)
i=0
for code,kind in items:
    if os.path.exists(os.path.join(D,code+'.png')): continue
    if kind=='AB':
        if i+2>len(fs): break
        a,b=fs[i],fs[i+1];i+=2
        best,other=(a,b) if score(a)>=score(b) else (b,a)
        save(best,code);os.rename(other,other+'.loai');print(code,'<- chon',os.path.basename(best))
    else:
        if i>=len(fs): break
        save(fs[i],code);i+=1;print(code,'<-',os.path.basename(fs[i-1]))
