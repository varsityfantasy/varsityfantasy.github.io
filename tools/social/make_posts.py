#!/usr/bin/env python3
"""Instagram/TikTok carousel (1080x1350 PNG) from the app's real football stats.
Usage: python3 tools/social/make_posts.py [out_dir]
Needs: playwright + chrome (/usr/bin/google-chrome), fonts Anton + Barlow Condensed (npm pack @fontsource/anton @fontsource/barlow-condensed into /tmp/fonts, or set FONT_DIR).
Top 100 by season Varsity fantasy points (PTS in index.html) plus last week's best; stat line under the name, PPG under the points. Numbers come only from stats.js. No source credit on the slides (owner)."""
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
*{{margin:0;box-sizing:border-box}}body{{width:1080px;height:1350px;overflow:hidden;font-family:B;color:var(--ink);background:var(--bg0)}}
.s{{position:relative;width:1080px;height:1350px;padding:64px 60px 0;background:var(--bgimg);overflow:hidden}}
.s:before{{content:'';position:absolute;inset:0;background:repeating-linear-gradient(115deg,var(--stripe) 0 1px,transparent 1px 26px);pointer-events:none}}
.big{{position:absolute;right:-30px;top:-70px;font-family:A;font-size:420px;line-height:1;color:transparent;-webkit-text-stroke:2px var(--ghost)}}
.tag{{display:inline-block;font-weight:800;font-size:24px;letter-spacing:5px;color:var(--a);border:2px solid var(--a);padding:5px 16px}}
h1{{font-family:A;font-weight:400;font-size:104px;line-height:.95;letter-spacing:1px;margin-top:18px;text-transform:uppercase}}h1 em{{font-style:normal;color:var(--a)}}
.sub{{font-weight:600;font-size:28px;color:var(--mut);letter-spacing:2px;margin-top:10px;text-transform:uppercase}}
.brand{{position:absolute;top:66px;right:60px;font-family:A;font-size:44px;letter-spacing:3px;color:var(--ink)}}.brand i{{font-style:normal;color:var(--a)}}.brand{{font-size:38px!important}}
.hero{{position:relative;margin-top:30px;height:250px;border-radius:26px;background:var(--card);color:var(--ink);border:1px solid var(--cardb);border-left:10px solid var(--a);display:flex;align-items:center;padding:0 40px;overflow:hidden;box-shadow:var(--shadow)}}
.hero .rk{{font-family:A;font-size:150px;line-height:1;opacity:.14;color:var(--a);position:absolute;left:18px;top:30px}}
.hero .lg{{width:150px;height:150px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex:none;margin-left:60px;box-shadow:0 8px 24px rgba(0,0,0,.25)}}.hero .lg img{{width:118px;height:118px;object-fit:contain}}
.hero .nm{{margin-left:30px;flex:1;min-width:0}}.hero .n{{font-family:A;font-size:62px;line-height:1;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.hero .sc{{font-weight:800;font-size:26px;letter-spacing:2px;text-transform:uppercase;color:var(--a);margin-top:4px}}
.hero .st{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}.hero .st b{{font-weight:800;font-size:22px;background:var(--chip);border:1px solid var(--line);color:var(--ink2);padding:4px 12px;border-radius:8px}}
.hero .pt{{text-align:right;flex:none;margin-left:18px}}.hero .pt div{{font-family:A;font-size:110px;line-height:.9;color:var(--a)}}.hero .pt span{{font-weight:800;font-size:24px;letter-spacing:4px}}
.rows{{margin-top:20px;display:flex;flex-direction:column;gap:8px}}
.r{{display:flex;align-items:center;height:76px;padding:0 26px 0 18px;border-radius:16px;background:var(--row);border:1px solid var(--line)}}
.r .k{{font-family:A;font-size:40px;width:58px;text-align:center;color:var(--mut2)}}.r .k{{color:var(--mut)}}
.r .lg{{width:56px;height:56px;border-radius:50%;background:#fff;display:flex;align-items:center;justify-content:center;flex:none;margin:0 18px 0 6px}}.r .lg img{{width:44px;height:44px;object-fit:contain}}
.mono{{font-family:A;color:var(--onA);font-size:26px}}
.r .nm{{flex:1;min-width:0}}.r .n{{font-weight:800;font-size:31px;line-height:1.05;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}.r .n small{{font-weight:600;font-size:20px;color:var(--mut);letter-spacing:1px;margin-left:10px}}
.r .st{{font-weight:600;font-size:20px;color:var(--ink2);letter-spacing:.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:2px}}
.r .pt{{text-align:right;flex:none;margin-left:16px}}.r .pt div{{font-family:A;font-size:44px;line-height:1;color:var(--ink)}}.r .pt span{{font-weight:800;font-size:15px;letter-spacing:3px;color:var(--mut)}}
.hero .pg{{font-weight:800;font-size:22px;letter-spacing:1px;margin-top:6px;color:var(--ink2)}}
.c .r{{height:61px;border-radius:12px}}.c .rows{{gap:6px;margin-top:20px}}.c .r .k{{font-size:30px;width:64px}}.c .r .lg{{width:42px;height:42px;margin:0 14px 0 4px}}.c .r .lg img{{width:33px;height:33px}}.c .r .n{{font-size:25px}}.c .r .n small{{font-size:17px}}.c .r .st{{font-size:16px;margin-top:0}}.c .r .pt div{{font-size:32px}}.c .r .pt span{{font-size:16px;letter-spacing:1px;color:var(--ink2)}}.r .pt span{{color:var(--ink2)}}
.t .r{{height:63px}}.t .rows{{gap:6px}}.t .r .n{{font-size:28px}}.t .r .st{{font-size:18px}}.t .r .pt div{{font-size:38px}}.t .r .lg{{width:48px;height:48px}}.t .r .lg img{{width:38px;height:38px}}.c h1{{font-size:88px}}
.ft{{position:absolute;left:60px;right:60px;bottom:34px;display:flex;justify-content:space-between;font-weight:800;font-size:21px;letter-spacing:2px;color:var(--mut2);text-transform:uppercase}}.ft b{{color:var(--a)}}
"""

PALS={
 'navy':dict(bg0='#070C18',bgimg='radial-gradient(1100px 650px at 105% -5%,color-mix(in srgb,var(--a) 10%,transparent) 0%,transparent 60%),radial-gradient(900px 700px at -20% 115%,#13213F 0%,transparent 62%),linear-gradient(180deg,#0B1426,#070C18)',a='#E7B54A',onA='#070C18',ink='#FFFFFF',ink2='#C8D0EA',mut='#8792B5',mut2='#56628A',card='linear-gradient(120deg,#16223F,#101A31)',cardb='color-mix(in srgb,var(--a) 40%,transparent)',chip='rgba(255,255,255,.07)',row='rgba(255,255,255,.045)',line='rgba(255,255,255,.07)',stripe='rgba(255,255,255,.012)',ghost='color-mix(in srgb,var(--a) 9%,transparent)',shadow='0 20px 60px rgba(0,0,0,.45)'),
 'white':dict(bg0='#F4F2EC',bgimg='linear-gradient(180deg,#F7F5EF,#ECE9E0)',a='#D62839',onA='#FFFFFF',ink='#0D1117',ink2='#3A4150',mut='#7A7F8C',mut2='#9A9EA8',card='#FFFFFF',cardb='#E2DED3',chip='#F3F1EB',row='#FFFFFF',line='#E4E0D6',stripe='rgba(0,0,0,.0)',ghost='rgba(0,0,0,.05)',shadow='0 14px 40px rgba(20,20,30,.10)'),
 'volt':dict(bg0='#0B0B0C',bgimg='radial-gradient(900px 600px at 100% 0%,rgba(212,255,58,.08),transparent 60%),#0B0B0C',a='#D4FF3A',onA='#0B0B0C',ink='#FFFFFF',ink2='#C9CCD1',mut='#80858F',mut2='#5A5E66',card='#17181A',cardb='rgba(212,255,58,.5)',chip='#232427',row='#141517',line='#26282C',stripe='rgba(255,255,255,.0)',ghost='rgba(255,255,255,.04)',shadow='0 20px 60px rgba(0,0,0,.5)'),
 'royal':dict(bg0='#081A4A',bgimg='radial-gradient(1000px 700px at 100% 0%,#1C3FA0 0%,transparent 60%),linear-gradient(180deg,#0A1E55,#061238)',a='#FFFFFF',onA='#0A1E55',ink='#FFFFFF',ink2='#C9D6FF',mut='#8EA3D9',mut2='#6C83C2',card='linear-gradient(120deg,#163A9C,#0F2A78)',cardb='rgba(255,255,255,.35)',chip='rgba(255,255,255,.10)',row='rgba(255,255,255,.07)',line='rgba(255,255,255,.12)',stripe='rgba(255,255,255,.0)',ghost='rgba(255,255,255,.06)',shadow='0 20px 60px rgba(0,0,20,.45)'),
}
PAL=PALS[os.environ.get('PALETTE','navy')]
CSS+='body{'+';'.join(f'--{k}:{v}' for k,v in PAL.items())+'}'
MILD={'g':'#8FC1A3','o':'#D6B46E','b':'#86AED6','p':'#D49A96','v':'#A9A0D8'}   # sage, muted gold, steel blue, dusty rose, lavender
TH={k:((MILD[k] if os.environ.get('PALETTE','navy')=='navy' else PAL['a']),'','') for k in 'gobpv'}
def lgimg(sch,cls=''):
    u=logo(sch);return f'<img src="{u}">' if u else f'<span class="mono">{esc(sch[:1])}</span>'
def slide(th,tag,title,sub,big,items,unit='PTS',foot='SWIPE',start=1,hero=True):
    a,a2,a3=TH[th]
    if not hero:return page(th,tag,title,sub,big,items,start)
    h,rest=items[0],items[1:]
    rows=''.join(f'<div class="r"><div class="k">{i+2}</div><div class="lg">{lgimg(x["s"])}</div><div class="nm"><div class="n">{esc(x["n"])}<small>{esc(x["s"])} · {x["tagp"]}</small></div><div class="st">{" · ".join(x["line"])}</div></div><div class="pt"><div>{x["v"]:.1f}</div><span>{(f'{x["ppg"]:.1f} PPG' if x.get("ppg") else unit)}</span></div></div>' for i,x in enumerate(rest))
    return f"""<div class="s{' t' if len(items)>8 else ''}" style="--a:{a};--a2:{a2};--a3:{a3}"><div class="big">{big}</div><div class="brand">VARSITY<i>.</i></div><span class="tag">{tag}</span><h1>{title}</h1><div class="sub">{sub}</div>
<div class="hero"><div class="rk">1</div><div class="lg">{lgimg(h["s"])}</div><div class="nm"><div class="n">{esc(h["n"])}</div><div class="sc">{esc(h["s"])} · {h["tagp"]}</div><div class="st">{"".join(f"<b>{z}</b>" for z in h["line"][:5])}</div></div><div class="pt"><div>{h["v"]:.1f}</div><span>FANTASY {unit}</span>{(f'<p class="pg">{h["ppg"]:.1f} PPG · {h["g"]} GP</p>' if h.get("ppg") else '')}</div></div>
<div class="rows">{rows}</div><div class="ft"><span>varsityfantasy.github.io · thru Week {LAST}</span><b>{'SWIPE →' if foot=='SWIPE' else foot}</b></div></div>"""
def page(th,tag,title,sub,big,items,start):
    a,a2,a3=TH[th]
    rows=''.join(f'<div class="r"><div class="k">{start+i}</div><div class="lg">{lgimg(x["s"])}</div><div class="nm"><div class="n">{esc(x["n"])}<small>{esc(x["s"])} · {x["tagp"]}</small></div><div class="st">{" · ".join(x["line"])}</div></div><div class="pt"><div>{x["v"]:.1f}</div><span>{x["ppg"]:.1f} PPG</span></div></div>' for i,x in enumerate(items))
    return f'''<div class="s c" style="--a:{a};--a2:{a2};--a3:{a3}"><div class="big">{big}</div><div class="brand">VARSITY<i>.</i></div><span class="tag">{tag}</span><h1>{title}</h1><div class="sub">{sub}</div><div class="rows">{rows}</div><div class="ft"><span>varsityfantasy.github.io · thru Week {LAST}</span><b>SWIPE →</b></div></div>'''
def top(pool,val,tot,n=8,ppg=False):
    out=[]
    for p in sorted([p for p in pool if val(p)>0],key=val,reverse=True)[:n]:
        out.append(dict(n=p['n'],s=p['s'],v=val(p),line=line(tot(p),p['pos']),tagp=p['sub'],g=p['g'],ppg=(p['fp']/p['g'] if ppg else 0)))
    return out
season=lambda p:p['fp'];stot=lambda p:p['tot']
S=[]
wk=top(P,lambda p:p['pts'].get(LAST,0),lambda p:p['wk'][LAST])
S.append(('02_last_week',slide('o',f'WEEK {LAST}','Best players<br><em>last week</em>',f'Top fantasy scores, Week {LAST}',f'W{LAST}',wk)))
T=top(P,season,stot,100,True)
S.append(('03_top_1_10',slide('g','TOP 100','Fantasy<br><em>top 100</em>','Season fantasy points · No. 1 to 10','#1',T[:10])))
TC=['b','p','v','o','b','p']
for k,st in enumerate(range(10,100,15)):
    S.append((f'{k+4:02d}_top_{st+1}_{st+15}',slide(TC[k],'TOP 100',f'No. {st+1}<em>–{st+15}</em>','Season fantasy points',str(st+1),T[st:st+15],start=st+1,hero=False)))
# cover: the title is the top 100; No. 1-3 of the season under it
a,a2,a3=TH['o'];h=T[0]
S.insert(0,('01_cover',f"""<div class="s" style="--a:{a};--a2:{a2};--a3:{a3};padding-top:80px"><div class="big" style="font-size:600px;top:-60px">100</div><div class="brand">VARSITY<i>.</i></div>
<span class="tag">SAN DIEGO FOOTBALL · WEEK {LAST}</span>
<h1 style="font-size:215px;line-height:.86;margin-top:34px">Top 100<br><em>fantasy</em><br>players</h1>
<div class="sub" style="margin-top:22px;font-size:30px">Ranked by season fantasy points</div>
<div class="hero" style="margin-top:44px"><div class="rk">1</div><div class="lg">{lgimg(h['s'])}</div><div class="nm"><div class="n">{esc(h['n'])}</div><div class="sc">{esc(h['s'])} · {h['tagp']}</div><div class="st">{"".join(f"<b>{z}</b>" for z in h['line'][:5])}</div></div><div class="pt"><div>{h['v']:.1f}</div><span>FANTASY PTS</span><p class="pg">{h['ppg']:.1f} PPG · {h['g']} GP</p></div></div>
<div class="rows">{''.join(f'<div class="r"><div class="k">{i+2}</div><div class="lg">{lgimg(x["s"])}</div><div class="nm"><div class="n">{esc(x["n"])}<small>{esc(x["s"])} · {x["tagp"]}</small></div><div class="st">{" · ".join(x["line"])}</div></div><div class="pt"><div>{x["v"]:.1f}</div><span>{x["ppg"]:.1f} PPG</span></div></div>' for i,x in enumerate(T[1:3]))}</div>
<div class="ft"><span>varsityfantasy.github.io · thru Week {LAST}</span><b>SWIPE →</b></div></div>"""))
a,a2,a3=TH['g']
S.append(('99_end',f"""<div class="s" style="--a:{a};--a2:{a2};--a3:{a3};display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 80px"><div class="big" style="font-size:600px;top:120px;right:auto;left:-40px">V</div>
<span class="tag">FREE TO PLAY</span><h1 style="font-size:150px;margin-top:30px">Draft<br><em>these guys</em></h1>
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
