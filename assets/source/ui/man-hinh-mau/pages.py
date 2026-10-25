import sys;sys.path.insert(0,'/tmp/claude-0/s')
from nine import *
from PIL import Image,ImageDraw,ImageFont
import numpy as np, math
U='/mnt/user-data/outputs/ui/';G=U+'goc/';R=U+'r36s/';FD='/mnt/user-data/outputs/doan/'
F=lambda s:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',s)
C1=(255,226,170);C2=(210,180,140);C3=(170,140,100)
cache={}
def L(p,conv=True):
    if p not in cache: cache[p]=Image.open(p).convert('RGBA')
    return cache[p]
def pet():
    a=np.array(L('/mnt/user-data/uploads/HoLua/assets/source/tinh-linh/hoa-ho-truong-thanh-spritesheet.png').crop((0,22,256,243)))
    r,g,b=a[...,0].astype(int),a[...,1].astype(int),a[...,2].astype(int);m=((r>150)&(b>150)&(g<110))|((b>90)&(r>90)&(g<0.6*np.minimum(r,b))&(abs(r-b)<90));a[m,3]=0;p=Image.fromarray(a);return p.crop(p.getbbox())
PET=pet()
def base(tab):
    sc=Image.new('RGBA',(640,480),(20,14,12,255))
    sc.alpha_composite(q(nine(L(G+'khung_panel.png'),640,420,95,26)),(0,40))
    tw=136
    for i in range(4):
        n='tab_chon' if i==tab else ('tab_cham-do' if i==0 else 'tab_thuong')
        sc.alpha_composite(q(three(L(G+n+'.png'),tw,32,40)),(42+i*(tw+4),4))
    for n,x in [('nut_L',10),('nut_R',608)]: sc.alpha_composite(L(R+n+'.png'),(x,9))
    dv=L(G+'khung_vach-chia.png');mid=dv.crop((0,int(dv.height*0.25),dv.width,int(dv.height*0.40)))
    sc.alpha_composite(q(mid.resize((8,350),Image.NEAREST)),(262,75))
    be=L(G+'be-dung_hoa.png');bw=158;bh=round(be.height*bw/be.width);be=q(be.resize((bw,bh),Image.LANCZOS))
    by=282;sc.alpha_composite(be,(132-bw//2,by))
    foot=by+int(bh*0.47)
    from PIL import ImageFilter
    sh=Image.new('L',(150,40),0);ImageDraw.Draw(sh).ellipse((25,12,125,30),fill=150);sh=sh.filter(ImageFilter.GaussianBlur(4))
    shd=Image.new('RGBA',(150,40),(0,0,0,255));shd.putalpha(sh);sc.alpha_composite(shd,(132-75,foot-22))
    H=176;p=PET.resize((PET.width*H//PET.height,H),Image.NEAREST);sc.alpha_composite(p,(132-p.width//2,foot-H+2))
    d=ImageDraw.Draw(sc)
    d.text((132,421),'Bông',fill=C1,font=F(16),anchor='mm');d.text((132,439),'Hỏa Hổ · Thiếu niên',fill=C2,font=F(11),anchor='mm')
    sc.alpha_composite(Image.new('RGBA',(640,20),(16,11,9,255)),(0,460))
    d.text((12,470),'L/R: đổi trang',fill=C3,font=F(10),anchor='lm')
    d.text((628,470),'A: đổi tên · B: quay lại' if tab==3 else 'B: quay lại',fill=C3,font=F(10),anchor='rm')
    for i,t in enumerate(['Sinh tồn','Linh khí','Thuộc tính','Hồ sơ']): d.text((42+i*(tw+4)+tw//2,20),t,fill=(255,240,210) if i==tab else C2,font=F(12),anchor='mm')
    return sc,d
def bars(sc,d,rows,y0,gap,BW=230,BH=22):
    frs=q(three(L(G+'thanh_khung.png'),BW,BH,70))
    for i,(ic,lab,col,v) in enumerate(rows):
        y=y0+i*gap
        sc.alpha_composite(L(R+'icon_'+ic+'.png').resize((32,32),Image.LANCZOS),(280,y-4))
        d.text((320,y-14),lab,fill=(240,215,170),font=F(12))
        sc.alpha_composite(frs,(320,y+3))
        fl=q(three(L(G+'thanh_fill_'+col+'.png'),BW-24,BH-8,70))
        sc.alpha_composite(fl.crop((0,0,max(1,int(fl.width*v/100)),fl.height)),(332,y+7))
        d.text((588,y+14),str(v),fill=C1,font=F(14),anchor='lm')
out='/mnt/user-data/outputs/man-hinh/';import os;os.makedirs(out,exist_ok=True)
# 1 Sinh ton
sc,d=base(0)
bars(sc,d,[('no','No','cam',72),('vui','Vui','hong',55),('sach','Sạch','xanh-duong',90),('nang-luong','Năng lượng','xanh-reu',15),('suc-khoe','Sức khỏe','do',100)],110,60)
sc.convert('RGB').save(out+'1-sinh-ton.png')
# 2 Linh khi
sc,d=base(1)
src=L(G+'linh-khi_ngu-giac.png');from scipy import ndimage
a=np.array(src);al=a[...,3]>0;lab,n=ndimage.label(al);sz=ndimage.sum(al,lab,range(1,n+1));a[lab!=(np.argmax(sz)+1),3]=0;src=Image.fromarray(a);src=src.crop(src.getbbox())
RW=250;rad=q(src.resize((RW,round(src.height*RW/src.width)),Image.LANCZOS),48)
cx=455;x0=cx-RW//2;y0=78;sc.alpha_composite(rad,(x0,y0));cy=y0+rad.height*0.555-8
# compute pentagon geometry: center ~ (cx,cy), radius ~ 100
els=[('hoa','Hỏa',80,(255,150,90)),('tho','Thổ',45,(240,180,70)),('kim','Kim',25,(230,230,230)),('thuy','Thủy',15,(120,180,255)),('moc','Mộc',35,(140,210,110))]
Rr=RW*0.30;pts=[]
for i,(k,n,v,c) in enumerate(els):
    a=-math.pi/2+i*2*math.pi/5;pts.append((cx+Rr*v/100*math.cos(a),cy+8+Rr*v/100*math.sin(a)))
ov=Image.new('RGBA',(640,480));od=ImageDraw.Draw(ov);od.polygon(pts,fill=(235,110,60,150),outline=(255,180,120,255),width=2);sc.alpha_composite(ov)
for i,(k,n,v,c) in enumerate(els):
    a=-math.pi/2+i*2*math.pi/5;x=cx+RW*0.43*math.cos(a);y=cy+8+RW*0.43*math.sin(a);lx=cx+RW*0.62*math.cos(a);ly=cy+8+RW*0.56*math.sin(a)
    ic=L(R+'he_'+k+'.png').resize((26,26),Image.LANCZOS);sc.alpha_composite(ic,(int(x-13),int(y-13)))
    d.text((lx,ly),f'{n} {v}',fill=c,font=F(12),anchor='mm')
d.text((452,438),'Vòng nét đứt = ngưỡng tiến hóa',fill=C3,font=F(10),anchor='mm')
sc.convert('RGB').save(out+'2-linh-khi.png')
# 3 Thuoc tinh
sc,d=base(2)
bars(sc,d,[('suc-manh','Sức mạnh','do',38),('nhanh-nhen','Nhanh nhẹn','cam',30),('ben-bi','Bền bỉ','xanh-reu',22),('thong-minh','Thông minh','xanh-duong',12),('tri-tue','Trí tuệ','tim',10),('tinh-than','Tinh thần','hong',25)],100,54)
sc.convert('RGB').save(out+'3-thuoc-tinh.png')
# 4 Ho so
sc,d=base(3)
card=L(G+'the-thong-tin.png')
def C(x,y,w,h): sc.alpha_composite(q(nine(card,w,h,60,12)),(x,y))
lv=L(G+'level_huy-hieu.png').resize((64,64),Image.LANCZOS);
C(282,64,340,72);sc.alpha_composite(q(lv),(292,68));d.text((324,100),'12',fill=C1,font=F(18),anchor='mm')
d.text((366,84),'Cấp độ',fill=C3,font=F(10));d.text((366,98),'Level 12',fill=C1,font=F(15))
fr=q(three(L(G+'thanh_khung.png'),150,12,70));sc.alpha_composite(fr,(460,104));fl=q(three(L(G+'thanh_fill_vang.png'),130,6,70));sc.alpha_composite(fl.crop((0,0,80,6)),(470,107));d.text((535,90),'EXP 620/1000',fill=C2,font=F(9),anchor='mm')
def info(x,y,w,icon,lab,val,valfill=C1):
    C(x,y,w,62);sc.alpha_composite(icon.resize((34,34),Image.LANCZOS),(x+10,y+14));d.text((x+52,y+16),lab,fill=C3,font=F(10));d.text((x+52,y+31),val,fill=valfill,font=F(13))
info(282,144,166,L(R+'tinh-cach_hieu-chien.png'),'Tính cách','Hiếu chiến')
C(456,144,166,62);sc.alpha_composite(L(R+'icon_suc-khoe.png').resize((34,34)),(466,158));d.text((508,160),'Thân thiết',fill=C3,font=F(10))
for i,h in enumerate(['tim-day','tim-day','tim-day','tim-nua','tim-rong']): sc.alpha_composite(L(R+'icon_'+h+'.png').resize((20,20),Image.LANCZOS),(506+i*22,176))
info(282,214,166,L(FD+'Hoa_1_roasted-chili-pepper.png'),'Thích','Ớt nướng')
info(456,214,166,L(FD+'Thuy_1_fresh-fish.png'),'Ghét','Cá tươi')
C(282,284,340,62);d.text((296,300),'Thể trạng · 18kg',fill=C3,font=F(10))
g=q(L(G+'the-trang_thanh.png').resize((180,22),Image.LANCZOS));sc.alpha_composite(g,(296,314))
nd=L(G+'the-trang_kim.png');nd=nd.resize((max(1,nd.width*22//nd.height),22),Image.LANCZOS);sc.alpha_composite(nd,(296+96,308))
d.text((612,325),'Gầy · Vừa · Mập',fill=C2,font=F(10),anchor='rm')
C(282,354,340,62);sc.alpha_composite(L(R+'icon_nha.png').resize((34,34),Image.LANCZOS),(292,368));d.text((334,370),'Nhà',fill=C3,font=F(10));d.text((334,385),'Lò rèn núi lửa',fill=C1,font=F(13));d.text((610,385),'+2/ngày',fill=(150,220,110),font=F(14),anchor='rm')
sc.convert('RGB').save(out+'4-ho-so.png')
m=Image.new('RGB',(1290,970),(255,255,255))
for i,f in enumerate(['1-sinh-ton','2-linh-khi','3-thuoc-tinh','4-ho-so']): m.paste(Image.open(out+f+'.png'),((i%2)*650,(i//2)*490))
m.save(out+'4-trang.png')
