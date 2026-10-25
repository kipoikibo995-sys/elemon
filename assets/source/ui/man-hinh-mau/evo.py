import sys;sys.path.insert(0,'/tmp/claude-0/s')
from comp import *
from levels_helper import first
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageFilter
import numpy as np, math
F=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',s)
W,H=640,480
bg=Image.open(B+'EVO1_nen.png').convert('RGBA').resize((W,H),Image.LANCZOS)
vort=comps('EVO2_xoay.png')[:4]           # fire row
burst=comps('EVO3_bung-sang.png')
ban=comps('EVO4_banner.png');banner=ban[0];parts=ban[1:]
teen=first('HO-T1_hoa-ho_teen.png',4,4);adult=first('hoa-ho-truong-thanh-spritesheet.png',4,6)
def sz(im,h): return im.resize((max(1,im.width*h//im.height),h),Image.NEAREST)
teen=sz(teen,120);adult=sz(adult,170)
CX,FY=320,330  # center x, feet y on mandala
def white(im,k):
    a=np.array(im).astype(float);a[...,:3]=a[...,:3]*(1-k)+255*k;return Image.fromarray(a.astype(np.uint8))
def glow(im,r=8,col=(255,200,90)):
    a=np.array(im)[...,3];g=Image.fromarray(a).filter(ImageFilter.GaussianBlur(r));c=Image.new('RGBA',im.size,col+(0,));c.putalpha(g.point(lambda v:min(255,v*2)));return c
def pad(im,p):
    o=Image.new('RGBA',(im.width+2*p,im.height+2*p));o.alpha_composite(im,(p,p));return o
frames=[];rng=np.random.default_rng(3)
pts=[(rng.uniform(40,600),rng.uniform(60,440),rng.integers(0,len(parts)-1),rng.uniform(1,3)) for _ in range(18)]
def scene(t,bright=1.0):
    s=ImageEnhance.Brightness(bg).enhance(bright).copy()
    for (x,y,k,v) in pts:
        p=parts[k] if k<len(parts) else parts[0];p=p.resize((14,int(14*p.height/p.width)),Image.LANCZOS)
        s.alpha_composite(p,(int(x),int((y-t*v*4)%420+30)))
    return s
def put(s,im,cx,by):
    s.alpha_composite(im,(int(cx-im.width/2),int(by-im.height)))
def putc(s,im,cx,cy):
    s.alpha_composite(im,(int(cx-im.width/2),int(cy-im.height/2)))
T=0
# 1 calm
for i in range(8): s=scene(T,0.55+0.03*i);put(s,teen,CX,FY);frames.append((s,90));T+=1
# 2 vortex + whitening
for i in range(14):
    s=scene(T,0.8);k=i/13
    v=sz(vort[i%4],70+int(60*k));v=v.resize((int(v.width*1.6),v.height),Image.NEAREST)
    pg=pad(teen,14);s.alpha_composite(glow(pg,10),(int(CX-pg.width/2),int(FY-teen.height-14)))
    putc(s,v,CX,FY-teen.height*0.45);put(s,white(teen,k*0.95),CX,FY)
    frames.append((s,70));T+=1
# 3 pillar
for i,bi in enumerate([2,3,2,3]):
    s=scene(T,1.0);put(s,white(teen,1),CX,FY);b=sz(burst[bi],420);put(s,b,CX,FY+30);frames.append((s,60));T+=1
# 4 flash
for k in [0.5,0.85,1.0,1.0]:
    s=scene(T,1.2);b=sz(burst[4],460);putc(s,b,CX,FY-80)
    s=Image.blend(s,Image.new('RGBA',(W,H),(255,255,245,255)),k);frames.append((s,60 if k<1 else 120));T+=1
# 5 reveal adult
for i in range(10):
    k=1-i/9;s=scene(T,0.75)
    if i<6:
        r=sz(burst[5],120+i*60);r=r.resize((int(r.width*1.8),r.height));putc(s,r,CX,FY-10)
    pg=pad(adult,16);s.alpha_composite(glow(pg,12),(int(CX-pg.width/2),int(FY-adult.height-16)))
    put(s,white(adult,k*0.9),CX,FY)
    if k>0: s=Image.blend(s,Image.new('RGBA',(W,H),(255,255,245,255)),k*0.6)
    frames.append((s,70));T+=1
# 6 banner
bn=banner.resize((420,int(420*banner.height/banner.width)),Image.LANCZOS)
for i in range(22):
    s=scene(T,0.75);pg=pad(adult,16);s.alpha_composite(glow(pg,12),(int(CX-pg.width/2),int(FY-adult.height-16)));put(s,adult,CX,FY)
    y=min(20,-120+i*28);s.alpha_composite(bn,(CX-bn.width//2,y))
    d=ImageDraw.Draw(s)
    if i>=5:
        d.text((CX,y+bn.height*0.58),'TIẾN HÓA!',font=F(30),fill=(255,236,170),anchor='mm',stroke_width=3,stroke_fill=(90,30,10))
    if i>=8:
        d.text((CX,FY+40),'Hỏa Hổ  →  Trưởng thành',font=F(18),fill=(255,236,170),anchor='mm',stroke_width=3,stroke_fill=(60,20,10))
        d.text((CX,FY+66),'Sức mạnh +12   ·   Bền bỉ +8   ·   Kỹ năng mới: Hổ Hỏa Trảo',font=F(12),fill=(255,210,140),anchor='mm',stroke_width=2,stroke_fill=(40,15,5))
    frames.append((s,90 if i<21 else 2000));T+=1
out='/mnt/user-data/outputs/tien-hoa.gif'
fr=[f.convert('RGB').quantize(128,dither=Image.Dither.NONE) for f,_ in frames]
fr[0].save(out,save_all=True,append_images=fr[1:],duration=[d for _,d in frames],loop=0,optimize=True)
# storyboard
idx=[3,14,24,28,38,len(frames)-1]
m=Image.new('RGB',(W*3//2*1+0,0))
sb=Image.new('RGB',(320*3+20,240*2+10),'white')
for j,ii in enumerate(idx): sb.paste(frames[ii][0].convert('RGB').resize((320,240),Image.LANCZOS),((j%3)*330,(j//3)*250))
sb.save('/mnt/user-data/outputs/tien-hoa-6-buoc.png');print(len(frames))
