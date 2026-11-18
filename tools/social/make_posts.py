#!/usr/bin/env python3
"""Instagram/TikTok carousel pictures built from the app's real football stats (stats.js, MaxPreps box scores).
Usage: python3 tools/social/make_posts.py [out_dir]   -> 1080x1350 PNGs: cover, top 10 passing/rushing/receiving/fantasy, best games of the latest week, end card.
Every number is computed here from stats.js; nothing is typed by hand. Scoring = PTS in index.html."""
import json,sys,os
from PIL import Image,ImageDraw,ImageFont
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(R,'social_out'); os.makedirs(OUT,exist_ok=True)
s=open(os.path.join(R,'stats.js')).read(); D,_=json.JSONDecoder().raw_decode(s[s.index('window.MAXPREPS=')+16:])
F=['passYd','passTD','int','rushYd','rushTD','rec','recYd','recTD','fumLost','tkl','sack','dInt','ff','fr','dTD']
PTS={'passYd':.04,'passTD':4,'int':-2,'rushYd':.1,'rushTD':6,'rec':1,'recYd':.1,'recTD':6,'fumLost':-2,'tkl':1.25,'sack':3,'dInt':5,'ff':4,'fr':3,'dTD':6}
P=[]
for p in D['players']:
    tot={k:0 for k in F}; wk={}
    for w,l in p['w'].items():
        d=dict(zip(F,l)); wk[int(w)]=d
        for k in F: tot[k]+=d[k]
    pts={w:sum(d[k]*PTS[k] for k in F) for w,d in wk.items()}
    P.append(dict(n=p['n'],s=p['s'],tot=tot,wk=wk,pts=pts,fp=sum(pts.values()),g=len(wk)))
last=max(w for p in P for w in p['wk'])
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
def f(sz): return ImageFont.truetype(FONT,sz)
BG=(14,20,38);PANEL=(24,33,58);GREEN=(46,214,120);GOLD=(255,196,56);WHITE=(240,243,250);MUT=(140,152,182);RED=(240,96,96)
W,H=1080,1350
def fit(d,t,sz,mx):
    while d.textlength(t,font=f(sz))>mx and sz>16: sz-=2
    return f(sz)
def base(title,sub):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle([0,0,W,12],fill=GREEN)
    d.text((60,70),title,font=fit(d,title,76,700),fill=WHITE);d.text((60,160),sub,font=f(30),fill=MUT)
    d.text((W-60,92),'VARSITY',font=f(36),fill=GREEN,anchor='ra')
    d.text((60,H-70),'SOURCE: MAXPREPS BOX SCORES  ·  THROUGH WEEK %d'%last,font=f(24),fill=MUT)
    d.text((W-60,H-70),'SWIPE FOR MORE ›',font=f(24),fill=GREEN,anchor='ra');return im,d
def board(fn,title,sub,key,label,det):
    rows=sorted([p for p in P if key(p)>0],key=key,reverse=True)[:10]
    im,d=base(title,sub);y=225
    for i,p in enumerate(rows):
        d.rounded_rectangle([50,y,W-50,y+92],14,fill=PANEL)
        d.text((100,y+48),str(i+1),font=f(46),fill=GOLD if i<3 else MUT,anchor='mm')
        d.text((160,y+16),p['n'].upper(),font=fit(d,p['n'].upper(),38,520),fill=WHITE)
        d.text((160,y+62),p['s'].upper(),font=f(24),fill=MUT)
        d.text((W-80,y+14),label(key(p)),font=f(46),fill=GREEN,anchor='ra')
        d.text((W-80,y+66),det(p),font=f(22),fill=MUT,anchor='ra');y+=100
    im.save(os.path.join(OUT,fn));print(fn,[(p['n'],p['s'],key(p)) for p in rows[:3]])
# cover
im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);d.rectangle([0,0,W,12],fill=GREEN)
d.text((W//2,420),'SAN DIEGO',font=f(120),fill=WHITE,anchor='mm');d.text((W//2,550),'FOOTBALL',font=f(120),fill=GREEN,anchor='mm')
d.text((W//2,680),'STAT LEADERS',font=f(120),fill=WHITE,anchor='mm');d.text((W//2,800),'THROUGH WEEK %d'%last,font=f(44),fill=GOLD,anchor='mm')
d.text((W//2,930),'{:,} player lines  ·  {} games tracked'.format(len(P),D['games']),font=f(34),fill=MUT,anchor='mm')
d.text((W//2,1180),'VARSITY',font=f(64),fill=GREEN,anchor='mm');d.text((W//2,1240),'Fantasy for high school sports',font=f(28),fill=MUT,anchor='mm')
im.save(os.path.join(OUT,'1_cover.png'))
board('2_passing.png','TOP PASSERS','PASSING YARDS, SEASON','passYd'.__class__ and (lambda p:p['tot']['passYd']),lambda v:'{:,} YDS'.format(v),lambda p:'%d TD · %d INT · %d GP'%(p['tot']['passTD'],p['tot']['int'],p['g']))
board('3_rushing.png','TOP RUSHERS','RUSHING YARDS, SEASON',lambda p:p['tot']['rushYd'],lambda v:'{:,} YDS'.format(v),lambda p:'%d TD · %d GP'%(p['tot']['rushTD'],p['g']))
board('4_receiving.png','TOP RECEIVERS','RECEIVING YARDS, SEASON',lambda p:p['tot']['recYd'],lambda v:'{:,} YDS'.format(v),lambda p:'%d REC · %d TD · %d GP'%(p['tot']['rec'],p['tot']['recTD'],p['g']))
off=lambda p:p['tot']['passYd']+p['tot']['rushYd']+p['tot']['recYd']>0
fp=lambda p:round(p['fp'],1) if off(p) else 0
board('5_fantasy.png','FANTASY LEADERS','VARSITY FANTASY POINTS, SEASON',fp,lambda v:'%.1f PTS'%v,lambda p:'%.1f PER GAME · %d GP'%(p['fp']/max(1,p['g']),p['g']))
# best games of the latest week
G=sorted([(p['pts'][last],p) for p in P if last in p['pts'] and off(p)],key=lambda x:-x[0])[:10]
im,d=base('WEEK %d TOP GAMES'%last,'BEST FANTASY GAMES OF THE WEEK');y=225
for i,(v,p) in enumerate(G):
    t=p['wk'][last];bits=[]
    if t['passYd']:bits.append('%d PASS YD, %d TD'%(t['passYd'],t['passTD']))
    if t['rushYd']:bits.append('%d RUSH YD, %d TD'%(t['rushYd'],t['rushTD']))
    if t['recYd']:bits.append('%d REC, %d YD, %d TD'%(t['rec'],t['recYd'],t['recTD']))
    d.rounded_rectangle([50,y,W-50,y+92],14,fill=PANEL);d.text((100,y+48),str(i+1),font=f(46),fill=GOLD if i<3 else MUT,anchor='mm')
    d.text((160,y+16),p['n'].upper(),font=fit(d,p['n'].upper(),38,420),fill=WHITE);d.text((160,y+62),p['s'].upper(),font=f(24),fill=MUT)
    d.text((W-80,y+14),'%.1f PTS'%v,font=f(46),fill=GREEN,anchor='ra');d.text((W-80,y+66),' · '.join(bits)[:46],font=fit(d,' · '.join(bits),22,470),fill=MUT,anchor='ra');y+=100
im.save(os.path.join(OUT,'6_week_top_games.png'));print('week',last,[(p['n'],round(v,1)) for v,p in G[:3]])
# end card
im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);d.rectangle([0,0,W,12],fill=GREEN)
d.text((W//2,480),'DRAFT THESE',font=f(110),fill=WHITE,anchor='mm');d.text((W//2,610),'PLAYERS',font=f(110),fill=GREEN,anchor='mm')
d.text((W//2,760),'Build a team, make your picks,',font=f(40),fill=MUT,anchor='mm');d.text((W//2,815),'beat your friends. Free.',font=f(40),fill=MUT,anchor='mm')
d.text((W//2,1000),'VARSITY',font=f(90),fill=GREEN,anchor='mm');d.text((W//2,1080),'varsityfantasy.github.io',font=f(36),fill=GOLD,anchor='mm')
im.save(os.path.join(OUT,'7_end.png'))
