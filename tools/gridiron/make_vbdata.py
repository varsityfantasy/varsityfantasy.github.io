#!/usr/bin/env python3
"""Builds tools/gridiron/vb-data.js (rosters for Varsity Bowl's School mode) from the football app.
Run:  python3 tools/preview/make_previews.py /tmp/vbprev && python3 tools/gridiron/make_vbdata.py /tmp/vbprev/varsity-football.html
Every player is kept (owner, Nov 27: "every single player in San Diego from each school"): all of the app's box-score players with their
season stat sums (the game turns the stats into attributes itself), plus everyone else on each team's real roster page
(data/rosters/san-diego.fb.json, tools/sections/rosters.py) with no stats: linemen (slot OL), players whose roster lists no position (slot ATH),
and backups who never made a box score. Roster-only players get a starting OVR from their class (no stats to rate them on).
A roster player listed both ways (e.g. OL,DL or CB,WR) gets one card per side, like the app's two-way cards."""
import asyncio,json,sys,os
from playwright.async_api import async_playwright
SRC=sys.argv[1] if len(sys.argv)>1 else '/tmp/vbprev/varsity-football.html'
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb-data.js')
JS='''()=>{
 const want={QB:1,RB:1,WR:1,TE:1,K:1,DL:1,LB:1,DB:1};
 const slot=p=>p.pos==='DEF'?(['CB','S','DB'].includes(p.sub)?'DB':p.sub==='DL'?'DL':'LB'):p.pos;
 const L=players().filter(p=>!p.ext&&!p.sample&&p.school&&want[slot(p)]);
 const RO=p=>ROSTER_OVR;const by={};
 L.forEach(p=>{const a=agg(p,'season'),o=ovrOf(p.key)||RO(p);const s={};for(const k in a.s)if(a.s[k])s[k]=Math.round(a.s[k]*10)/10;
  (by[p.school]=by[p.school]||{})[slot(p)]=(by[p.school][slot(p)]||[]).concat([[slot(p),p.name,o,a.n||0,s]])});
 const out={},all=[];
 for(const sc of Object.keys(by).sort()){let r=[];for(const sl in by[sc]){const a=by[sc][sl].sort((x,y)=>y[2]-x[2]);r=r.concat(a)}
  const c=schCol(sc);out[sc]={c:c?[c[0],c[1]]:['#1d4ed8','#ffffff'],r};r.forEach(x=>all.push(x.concat([sc])))}
 all.sort((x,y)=>y[2]-x[2]);
 const demo=[];const need={QB:1,RB:2,WR:3,TE:1,K:1,DL:4,LB:3,DB:4};
 for(let i=40;i<all.length&&Object.values(need).some(v=>v>0);i+=1){const x=all[i];if(need[x[0]]>0&&(i%3===0)){need[x[0]]--;demo.push(x)}}
 const col={};EXTRA.forEach(sc=>{const c=schCol(sc);if(c)col[sc]=[c[0],c[1]]});
 return {schools:out,demo,col}}'''
ROSTER_OVR=45
EXTRA=['Julian','Francis Parker','West Shores','Warner','St. Joseph Academy','Borrego Springs']
CLS_OVR={'Sr.':52,'Jr.':49,'So.':46,'Fr.':43}
SLOT={'QB':'QB','RB':'RB','HB':'RB','FB':'RB','TB':'RB','SB':'RB','WB':'RB','WR':'WR','SE':'WR','FL':'WR','TE':'TE','K':'K','P':'K','PK':'K',
 'OL':'OL','C':'OL','G':'OL','T':'OL','OT':'OL','OG':'OL','OC':'OL','LS':'OL','DL':'DL','DE':'DL','DT':'DL','NT':'DL','NG':'DL','EDGE':'DL',
 'LB':'LB','ILB':'LB','OLB':'LB','MLB':'LB','DB':'DB','CB':'DB','S':'DB','FS':'DB','SS':'DB'}
SIDE={'QB':'O','RB':'O','WR':'O','TE':'O','OL':'O','DL':'D','LB':'D','DB':'D','K':'K'}
def norm(n):
    import re,unicodedata
    n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode().lower()
    n=re.sub(r'\b(jr|sr|ii|iii|iv)\b','',n);return re.sub(r'[^a-z]','',n)
def close(a,b):
    if a==b:return True
    if abs(len(a)-len(b))>2:return False
    lim=2 if min(len(a),len(b))>=10 else 1
    prev=list(range(len(b)+1))
    for i,ca in enumerate(a,1):
        cur=[i]
        for j,cb in enumerate(b,1):cur.append(min(prev[j]+1,cur[j-1]+1,prev[j-1]+(ca!=cb)))
        prev=cur
    return prev[-1]<=lim
def roster_slots(pos):
    """'CB,WR' -> ['DB','WR']: one slot per side (offense, defense, kicker), first listed wins; ATH takes the other listed spot; none -> ATH."""
    out={}
    for x in [y.strip().upper() for y in (pos or '').split(',') if y.strip()]:
        sl=SLOT.get(x)
        if sl and SIDE[sl] not in out:out[SIDE[sl]]=sl
    return list(out.values()) or ['ATH']
def add_roster(d):
    """Adds every San Diego roster player the box scores don't already cover (see the docstring)."""
    R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..')
    P=json.load(open(os.path.join(R,'data','rosters','san-diego.fb.json')))['players']
    T={t['id']:t['name'] for t in json.load(open(os.path.join(R,'api','v1','sections','san-diego','fb','teams.json')))['teams']}
    S=d['schools'];added=0;new=[]
    have={sc:[(x[0],norm(x[1])) for x in v['r']] for sc,v in S.items()}
    for pid,(name,cls,pos,sid) in sorted(P.items(),key=lambda kv:kv[1][0]):
        sc=T.get(sid)
        if not sc or not name.strip():continue
        if sc not in S:S[sc]={'c':d['col'].get(sc,['#1d4ed8','#ffffff']),'r':[]};have[sc]=[];new.append(sc)
        nn=norm(name);sides={SIDE.get(sl,sl) for sl,n in have[sc] if close(n,nn)}   # sides this player already has a card for
        for sl in roster_slots(pos):
            if SIDE.get(sl,sl) in sides or (sl=='ATH' and sides):continue
            S[sc]['r'].append([sl,name.strip(),CLS_OVR.get(cls,ROSTER_OVR),0,{}]);have[sc].append((sl,nn));sides.add(SIDE.get(sl,sl));added+=1
    del d['col']
    print('roster players added:',added,'new schools:',new)
def small_logos(schools):
    """48 px copies of the app's school logos (logos.js) so the game can show them."""
    import re,io,base64
    from PIL import Image
    L=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','logos.js')).read()
    m=json.loads(re.search(r'window\.SCHOOL_LOGOS\s*=\s*(\{.*\})\s*;?\s*$',L,re.S).group(1));out={}
    for sc in schools:
        u=m.get(sc)
        if not u:continue
        im=Image.open(io.BytesIO(base64.b64decode(u.split(',')[1]))).convert('RGBA');im.thumbnail((48,48),Image.LANCZOS)
        b=io.BytesIO();im.save(b,'WEBP',quality=80,method=6);out[sc]='data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
    return out
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page()
        await pg.goto('file://'+SRC);await pg.wait_for_timeout(2500)
        d=await pg.evaluate(JS.replace('ROSTER_OVR',str(ROSTER_OVR)).replace('EXTRA',json.dumps(EXTRA)))
    add_roster(d)
    d['schools']=dict(sorted(d['schools'].items()))
    d['logos']=small_logos(d['schools'])
    open(OUT,'w').write('window.VB_DATA='+json.dumps(d,separators=(',',':'))+';\n')
    print(OUT,len(d['schools']),'schools',os.path.getsize(OUT)//1024,'KB',len(d['demo']),'demo cards')
asyncio.run(main())
import vb_sched;vb_sched.main()   # adds each school's real schedule (VB_DATA.sched)
