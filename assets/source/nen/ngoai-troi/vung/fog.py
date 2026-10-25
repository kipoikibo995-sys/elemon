import sys;sys.path.insert(0,'/tmp/claude-0/s')
import numpy as np
from PIL import Image,ImageDraw,ImageFilter,ImageEnhance
from comp import comps
MAP=Image.open('/mnt/user-data/outputs/MAP_chot.png').convert('RGBA');W,H=MAP.size
O='/mnt/user-data/outputs/map-vung/';import os;os.makedirs(O,exist_ok=True)
P={'hoa':[(60,0),(830,0),(830,290),(700,400),(600,430),(450,360),(330,300),(60,250)],
   'kim':[(830,0),(1448,0),(1448,400),(1170,460),(990,420),(900,330),(830,290)],
   'moc':[(0,250),(330,300),(450,360),(560,450),(570,640),(450,700),(300,760),(0,800)],
   'thuy':[(0,800),(300,760),(450,700),(570,640),(980,690),(1080,800),(1120,1086),(0,1086)],
   'tho':[(990,420),(1170,460),(1448,400),(1448,1086),(1120,1086),(1080,800),(980,690)]}
def center_mask():
    m=Image.new('L',(W,H),0);ImageDraw.Draw(m).ellipse((725-265,545-195,725+265,545+195),fill=255);return m
C=center_mask()
masks={}
for k,poly in P.items():
    m=Image.new('L',(W,H),0);ImageDraw.Draw(m).polygon(poly,fill=255)
    m=Image.fromarray((np.array(m)&~np.array(C)).astype(np.uint8));masks[k]=m;m.save(O+'mask_'+k+'.png')
C.save(O+'mask_trung-tam.png')
rng=np.random.default_rng(7)
def clouds(mask,seed):
    r=np.random.default_rng(seed);s=4;w,h=W//s,H//s
    small=Image.new('L',(w,h),0);d=ImageDraw.Draw(small);mm=np.array(mask.resize((w,h)))
    ys,xs=np.nonzero(mm)
    for _ in range(int(len(xs)/260)+12):
        i=r.integers(len(xs));x,y=xs[i],ys[i];rad=r.integers(5,13);d.ellipse((x-rad,y-rad*0.7,x+rad,y+rad*0.7),fill=255)
    small=small.filter(ImageFilter.GaussianBlur(2)).point(lambda v:255 if v>110 else 0)
    hi=small.filter(ImageFilter.GaussianBlur(1.5)).point(lambda v:255 if v>200 else 0)
    a=np.array(small);b=np.array(hi);mmk=mm>0;a=a*mmk;b=b*mmk
    rgba=np.zeros((h,w,4),np.uint8)
    rgba[a>0]=(196,190,210,230);rgba[(a>0)&(b==0)]=(140,132,160,230);rgba[b>0]=(236,232,244,240)
    # outline
    edge=(a>0)&~np.array(Image.fromarray(a).filter(ImageFilter.MinFilter(3)))>0
    rgba[edge]=(60,52,78,255)
    return Image.fromarray(rgba).resize((W,H),Image.NEAREST)
lock=comps('SHOP1_cua-hang.png')[2]
anchor={'hoa':(400,190),'kim':(1170,250),'moc':(230,470),'thuy':(380,880),'tho':(1220,640)}
for i,(k,m) in enumerate(masks.items()):
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    # dark tint inside region
    g=ImageEnhance.Brightness(ImageEnhance.Color(MAP).enhance(0.55)).enhance(0.8)
    g=g.filter(ImageFilter.GaussianBlur(2.5))
    soft=m.filter(ImageFilter.GaussianBlur(6))
    lay.paste(g,(0,0),soft)
    fog=Image.new('RGBA',(W,H),(200,195,220,0));fa=np.array(m.filter(ImageFilter.GaussianBlur(40))).astype(float)*0.12;fog.putalpha(Image.fromarray(fa.astype(np.uint8)));lay.alpha_composite(fog)
    L=lock.resize((84,84),Image.LANCZOS);x,y=anchor[k];lay.alpha_composite(L,(x-42,y-42))
    lay.save(O+'khoa_'+k+'.png')
    # selected highlight outline
    e=m.filter(ImageFilter.MaxFilter(9));inner=m.filter(ImageFilter.MinFilter(9))
    ring=Image.fromarray(((np.array(e)>0)&~(np.array(inner)>0)).astype(np.uint8)*255).filter(ImageFilter.GaussianBlur(2))
    hl=Image.new('RGBA',(W,H),(255,214,90,0));hl.putalpha(ring.point(lambda v:min(255,v*2)));hl.save(O+'chon_'+k+'.png')
def scene(unlocked,sel=None):
    s=MAP.copy()
    for k in masks:
        if k not in unlocked: s.alpha_composite(Image.open(O+'khoa_'+k+'.png'))
    if sel: s.alpha_composite(Image.open(O+'chon_'+sel+'.png'))
    return s
a=scene([]);b=scene(['hoa'],'hoa');c=scene(['hoa','moc','thuy'],'thuy')
a.save(O+'_thu_bat-dau.png');b.save(O+'_thu_mo-hoa.png')
m=Image.new('RGB',(724*3+20,543),'white')
for j,s in enumerate([a,b,c]): m.paste(s.convert('RGB').resize((724,543),Image.LANCZOS),(j*734,0))
m.save('/mnt/user-data/outputs/map-khoa-3-buoc.jpg',quality=88)
