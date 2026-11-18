#!/usr/bin/env python3
"""Instagram/TikTok carousel (1080x1350 PNG) from the app's real football stats.
Usage: python3 tools/social/make_posts.py [out_dir]
Needs: playwright + chrome (/usr/bin/google-chrome), fonts Anton + Barlow Condensed (npm pack @fontsource/anton @fontsource/barlow-condensed into /tmp/fonts, or set FONT_DIR).
Every player is ranked by Varsity fantasy points (PTS in index.html); the stat line sits under the name. Numbers come only from stats.js."""
import json,sys,os,re,base64,glob
R=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(R,'social_out');os.makedirs(OUT,exist_ok=True)
FD=os.environ.get('FONT_DIR','/tmp/fonts')
def font(pat):
    m=glob.glob(os.path.join(FD,'**',pat),recursive=True);return 'data:font/woff2;base64,'+base64.b64encode(open(m[0],'rb').read()).decode() if m else ''
ANTON=font('anton-latin-400-normal.woff2');B6=font('barlow-condensed-latin-600-normal.woff2');B8=font('barlow-condensed-latin-800-normal.woff2')
s=open(os.path.join(R,'stats.js')).read();D,_=json.JSONDecoder().raw_decode(s[s.index('window.MAXPREPS=')+16:])
L=open(os.path.join(R,'logos.js')).read();LOGOS,_=json.JSONDecoder().raw_decode(L[L.index('{'):])
ix=open(os.path.join(R,'index.html')).read()
ALIAS=dict(re.findall(r"'([^']+)':'([^']+)'",re.search(r"const LOGO_ALIAS=\{(.*?)\};",ix).group(1)))
PTS={k:float(v) for k,v in re.findall(r"(\w+):(-?[\d.]+)",re.search(r"const PTS=\{(.*?)\};",ix).group(1))}
F=['passYd','passTD','int','rushYd','rushTD','rec','recYd','recTD','fumLost','tkl','sack','dInt','ff','fr','dTD']
P=[]
for p in D['players']:
    if p['p']=='K':continue
    wk={int(w):dict(zip(F,l)) for w,l in p['w'].items()}
    tot={k:sum(d[k] for d in wk.values()) for k in F}
    pts={w:sum(d[k]*PTS.get(k,0) for k in F) for w,d in wk.items()}
    P.append(dict(n=p['n'],s=p['s'],pos=p['p'],sub=p.get('u') or p['p'],wk=wk,tot=tot,pts=pts,fp=sum(pts.values()),g=len(wk)))
LAST=max(w for p in P for w in p['wk'])
def logo(sch):return LOGOS.get(ALIAS.get(sch,sch)) or LOGOS.get(sch)
def line(t,pos):
    b=[]
    if pos=='DEF':
        b=[(t['tkl'],'TKL'),(t['sack'],'SACK'),(t['dInt'],'INT'),(t['ff'],'FF'),(t['fr'],'FR'),(t['dTD'],'TD')];return [f'{v:g} {k}' for v,k in b if v]
    if t['passYd']:b+=[f"{t['passYd']:,} PASS YD",f"{t['passTD']} PASS TD"][:1 if not t['passTD'] else 2]+([f"{t['int']} INT"] if t['int'] else [])
    if t['rushYd'] or t['rushTD']:b+=[f"{t['rushYd']:,} RUSH YD"]+([f"{t['rushTD']} RUSH TD"] if t['rushTD'] else [])
    if t['rec']:b+=[f"{t['rec']} REC",f"{t['recYd']:,} REC YD"]+([f"{t['recTD']} REC TD"] if t['recTD'] else [])
    return b
def esc(x):return x.replace('&','&amp;').replace('<','&lt;')
CSS=f"""@font-face{{font-family:A;src:url({ANTON})}}@font-face{{font-family:B;font-weight:600;src:url({B6})}}@font-face{{font-family:B;font-weight:800;src:url({B8})}}
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;overflow:hidden;font-family:B;color:#fff;background:#070B16}}
.s{{position:relative;width:1080px;height:1350px;padding:64px 60px 0;background:radial-gradient(1200px 700px at 110% -10%,var(--a2) 0%,transparent 60%),radial-gradient(900px 600px at -20% 110%,#13204a 0%,transparent 60%),#070B16;overflow:hidden}}
.s:before{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(115deg,rgba(255,255,255,.025) 0 2px,transparent 2px 22px);pointer-events:none}}
.big{{position:absolute;right:-30px;top:-70px;font-family:A;font-size:420px;line-height:1;color:transparent;-webkit-text-stroke:2px rgba(255,255,255,.06)}}
.tag{{display:inline-block;font-weight:800;font-size:26px;letter-spacing:4px;color:#070B16;background:var(--a);padding:6px 16px;transform:skew(-10deg)}}
h1{{font-family:A;font-weight:400;font-size:104px;line-height:.95;letter-spacing:1px;margin-top:18px;text-transform:uppercase}}h1 em{{font-style:normal;color:var(--a)}}
.sub{{font-weight:600;font-size:28px;color:#9AA6C8;letter-spacing:2px;margin-top:10px;text-transform:uppercase}}
.brand{{position:absolute;top:66px;right:60px;font-family:A;font-size:44px;letter-spacing:3px;color:#fff}}.brand i{{font-style:normal;color:var(--a)}}
.hero{{position:relative;margin-top:30px;height:250px;border-radius:26px;background:linear-gradient(120deg,var(--a) 0%,var(--a3) 100%);color:#070B16;display:flex;align-items:center;padding:0 40px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.45)}}
.hero .rk{{font-family:A;font-size:150px;line-height:1;opacity:.22;position:absolute;left:18px;top:30px}}
.hero .lg{{width:150px;height:150px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex:none;margin-left:60px;box-shadow:0 8px 24px rgba(0,0,0,.25)}}.hero .lg img{{width:118px;height:118px;object-fit:contain}}
.hero .nm{{margin-left:30px;flex:1;min-width:0}}.hero .n{{font-family:A;font-size:62px;line-height:1;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.hero .sc{{font-weight:800;font-size:26px;letter-spacing:2px;text-transform:uppercase;opacity:.75;margin-top:4px}}
.hero .st{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}.hero .st b{{font-weight:800;font-size:22px;background:rgba(7,11,22,.14);padding:4px 12px;border-radius:8px}}
.hero .pt{{text-align:right;flex:none;margin-left:18px}}.hero .pt div{{font-family:A;font-size:110px;line-height:.9}}.hero .pt span{{font-weight:800;font-size:24px;letter-spacing:4px}}
.rows{{margin-top:20px;display:flex;flex-direction:column;gap:8px}}
.r{{display:flex;align-items:center;height:76px;padding:0 26px 0 18px;border-radius:16px;background:linear-gradient(90deg,rgba(255,255,255,.075),rgba(255,255,255,.03));border:1px solid rgba(255,255,255,.06)}}
.r .k{{font-family:A;font-size:40px;width:58px;text-align:center;color:#56628A}}.r:nth-child(-n+2) .k{{color:var(--a)}}
.r .lg{{width:56px;height:56px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex:none;margin:0 18px 0 6px}}.r .lg img{{width:44px;height:44px;object-fit:contain}}
.mono{{font-family:A;color:#070B16;font-size:26px}}
.r .nm{{flex:1;min-width:0}}.r .n{{font-weight:800;font-size:31px;line-height:1.05;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.r .n small{{font-weight:600;font-size:20px;color:#7F8BB0;letter-spacing:1px;margin-left:10px}}
.r .st{{font-weight:600;font-size:20px;color:#AEB8D6;letter-spacing:.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}}
.r .pt{{text-align:right;flex:none;margin-left:16px}}.r .pt div{{font-family:A;font-size:44px;line-height:1;color:var(--a)}}.r .pt span{{font-weight:800;font-size:15px;letter-spacing:3px;color:#7F8BB0}}
.ft{{position:absolute;left:60px;right:60px;bottom:34px;display:flex;justify-content:space-between;font-weight:800;font-size:21px;letter-spacing:2px;color:#56628A;text-transform:uppercase}}.ft b{{color:var(--a)}}
"""
TH={'g':('#2EE67F','rgba(46,230,127,.22)','#B8FF5C'),'o':('#FFB627','rgba(255,182,39,.22)','#FF7A2F'),'b':('#4FC3FF','rgba(79,195,255,.22)','#7C8CFF'),'p':('#FF4F9A','rgba(255,79,154,.22)','#FF8A5C'),'v':('#B78CFF','rgba(183,140,255,.22)','#4FC3FF')}
def lgimg(sch,cls=''):
    u=logo(sch);return f'<img src="{u}">' if u else f'<span class="mono">{esc(sch[:1])}</span>'
def slide(th,tag,title,sub,big,items,unit='PTS',foot='SWIPE'):
    a,a2,a3=TH[th];h,rest=items[0],items[1:]
    rows=''.join(f'<div class="r"><div class="k">{i+2}</div><div class="lg">{lgimg(x["s"])}</div><div class="nm"><div class="n">{esc(x["n"])}<small>{esc(x["s"])} · {x["tagp"]}</small></div><div class="st">{" · ".join(x["line"])}</div></div><div class="pt"><div>{x["v"]:.1f}</div><span>{unit}</span></div></div>' for i,x in enumerate(rest))
    return f"""<div class="s" style="--a:{a};--a2:{a2};--a3:{a3}"><div class="big">{big}</div><div class="brand">VARSITY<i>.</i></div><span class="tag">{tag}</span><h1>{title}</h1><div class="sub">{sub}</div>
<div class="hero"><div class="rk">1</div><div class="lg">{lgimg(h["s"])}</div><div class="nm"><div class="n">{esc(h["n"])}</div><div class="sc">{esc(h["s"])} · {h["tagp"]}</div><div class="st">{"".join(f"<b>{z}</b>" for z in h["line"][:5])}</div></div><div class="pt"><div>{h["v"]:.1f}</div><span>FANTASY {unit}</span></div></div>
<div class="rows">{rows}</div><div class="ft"><span>Stats: MaxPreps box scores · thru Week {LAST}</span><b>{'SWIPE →' if foot=='SWIPE' else foot}</b></div></div>"""
def top(pool,val,tot,n=8):
    out=[]
    for p in sorted([p for p in pool if val(p)>0],key=val,reverse=True)[:n]:
        out.append(dict(n=p['n'],s=p['s'],v=val(p),line=line(tot(p),p['pos']),tagp=p['sub']))
    return out
season=lambda p:p['fp'];stot=lambda p:p['tot']
S=[]
wk=top(P,lambda p:p['pts'].get(LAST,0),lambda p:p['wk'][LAST])
S.append(('2_last_week',slide('o',f'WEEK {LAST}','Best players<br><em>last week</em>',f'Top fantasy scores, Week {LAST}',f'W{LAST}',wk)))
S.append(('3_season',slide('g','SEASON','Fantasy<br><em>leaders</em>','Most fantasy points, all positions','#1',top(P,season,stot))))
S.append(('4_qb',slide('b','QUARTERBACKS','Top<br><em>QBs</em>','Ranked by season fantasy points','QB',top([p for p in P if p['pos']=='QB'],season,stot))))
S.append(('5_rb',slide('p','RUNNING BACKS','Top<br><em>RBs</em>','Ranked by season fantasy points','RB',top([p for p in P if p['pos']=='RB'],season,stot))))
S.append(('6_wr',slide('v','RECEIVERS','Top<br><em>WRs &amp; TEs</em>','Ranked by season fantasy points','WR',top([p for p in P if p['pos'] in('WR','TE')],season,stot))))
S.append(('7_def',slide('g','DEFENSE','Top<br><em>defenders</em>','Ranked by season fantasy points','D',top([p for p in P if p['pos']=='DEF'],season,stot))))
# cover: last week's No. 1
h=wk[0];a,a2,a3=TH['o']
S.insert(0,('1_cover',f"""<div class="s" style="--a:{a};--a2:{a2};--a3:{a3};padding-top:90px"><div class="big" style="font-size:560px;top:-40px">{LAST}</div><div class="brand">VARSITY<i>.</i></div>
<span class="tag">SAN DIEGO FOOTBALL</span><h1 style="font-size:150px;margin-top:26px">Week {LAST}<br><em>fantasy</em><br>report</h1>
<div style="margin-top:46px;font-weight:800;font-size:30px;letter-spacing:4px;color:#9AA6C8">PLAYER OF THE WEEK</div>
<div class="hero" style="margin-top:16px"><div class="lg" style="margin-left:0">{lgimg(h['s'])}</div><div class="nm"><div class="n">{esc(h['n'])}</div><div class="sc">{esc(h['s'])} · {h['tagp']}</div><div class="st">{"".join(f"<b>{z}</b>" for z in h['line'][:5])}</div></div><div class="pt"><div>{h['v']:.1f}</div><span>FANTASY PTS</span></div></div>
<div class="rows" style="margin-top:14px">{''.join(f'<div class="r"><div class="k">{i+2}</div><div class="lg">{lgimg(x["s"])}</div><div class="nm"><div class="n">{esc(x["n"])}<small>{esc(x["s"])} · {x["tagp"]}</small></div><div class="st">{" · ".join(x["line"])}</div></div><div class="pt"><div>{x["v"]:.1f}</div><span>PTS</span></div></div>' for i,x in enumerate(wk[1:3]))}</div>
<div style="margin-top:34px;font-weight:600;font-size:30px;color:#9AA6C8">Inside: last week's best · season leaders · top QBs, RBs, WRs &amp; defenders</div>
<div class="ft"><span>{len(P):,} players · {D['games']} games</span><b>SWIPE →</b></div></div>"""))
a,a2,a3=TH['g']
S.append(('8_end',f"""<div class="s" style="--a:{a};--a2:{a2};--a3:{a3};display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 80px"><div class="big" style="font-size:600px;top:120px;right:auto;left:-40px">V</div>
<span class="tag">FREE · NO PURCHASES</span><h1 style="font-size:150px;margin-top:30px">Draft<br><em>these guys</em></h1>
<div class="sub" style="font-size:34px;margin-top:30px;letter-spacing:1px;text-transform:none;color:#C8D0EA">Build a team of real San Diego players, make your picks and beat your friends every week.</div>
<div style="margin-top:80px;font-family:A;font-size:120px;letter-spacing:6px">VARSITY<span style="color:{a}">.</span></div><div style="font-weight:800;font-size:36px;color:{a};letter-spacing:2px">varsityfantasy.github.io</div></div>"""))
from playwright.sync_api import sync_playwright
with sync_playwright() as pw:
    b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);pg=b.new_page(viewport={'width':1080,'height':1350})
    for name,html in S:
        pg.set_content(f'<html><head><style>{CSS}</style></head><body>{html}</body></html>');pg.wait_for_timeout(250);pg.evaluate("document.querySelectorAll('.hero .n,.r .n').forEach(e=>{let z=parseFloat(getComputedStyle(e).fontSize);while(e.scrollWidth>e.clientWidth&&z>18){z-=1;e.style.fontSize=z+'px'}})")
        pg.screenshot(path=os.path.join(OUT,name+'.png'));print(name)
    b.close()
print('week',LAST,[(x['n'],round(x['v'],1)) for x in wk[:3]])
