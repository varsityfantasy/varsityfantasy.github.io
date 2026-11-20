#!/usr/bin/env python3
"""Builds tools/gridiron/vb-data.js (rosters for Varsity Bowl's School mode) from the football app.
Run:  python3 tools/preview/make_previews.py /tmp/vbprev && python3 tools/gridiron/make_vbdata.py /tmp/vbprev/varsity-football.html
Per school and slot it keeps the best players by OVR with their season stat sums; the game turns the stats into attributes itself."""
import asyncio,json,sys,os
from playwright.async_api import async_playwright
SRC=sys.argv[1] if len(sys.argv)>1 else '/tmp/vbprev/varsity-football.html'
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb-data.js')
JS='''()=>{
 const want={QB:2,RB:2,WR:4,TE:2,K:1,DL:5,LB:4,DB:5};
 const slot=p=>p.pos==='DEF'?(['CB','S','DB'].includes(p.sub)?'DB':p.sub==='DL'?'DL':'LB'):p.pos;
 const L=players().filter(p=>!p.ext&&!p.sample&&p.school&&want[slot(p)]);
 const by={};
 L.forEach(p=>{const a=agg(p,'season'),o=ovrOf(p.key)||0;if(!o)return;const s={};for(const k in a.s)if(a.s[k])s[k]=Math.round(a.s[k]*10)/10;
  (by[p.school]=by[p.school]||{})[slot(p)]=(by[p.school][slot(p)]||[]).concat([[slot(p),p.name,o,a.n||0,s]])});
 const out={},all=[];
 for(const sc of Object.keys(by).sort()){let r=[];for(const sl in by[sc]){const a=by[sc][sl].sort((x,y)=>y[2]-x[2]).slice(0,want[sl]);r=r.concat(a)}
  const c=schCol(sc);out[sc]={c:c?[c[0],c[1]]:['#1d4ed8','#ffffff'],r};r.forEach(x=>all.push(x.concat([sc])))}
 all.sort((x,y)=>y[2]-x[2]);
 const demo=[];const need={QB:1,RB:2,WR:3,TE:1,K:1,DL:4,LB:3,DB:4};
 for(let i=40;i<all.length&&Object.values(need).some(v=>v>0);i+=1){const x=all[i];if(need[x[0]]>0&&(i%3===0)){need[x[0]]--;demo.push(x)}}
 return {schools:out,demo}}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        pg=await b.new_page()
        await pg.goto('file://'+SRC);await pg.wait_for_timeout(2500)
        d=await pg.evaluate(JS)
    open(OUT,'w').write('window.VB_DATA='+json.dumps(d,separators=(',',':'))+';\n')
    print(OUT,len(d['schools']),'schools',os.path.getsize(OUT)//1024,'KB',len(d['demo']),'demo cards')
asyncio.run(main())
