#!/usr/bin/env python3
"""Adds VB_DATA.sched (each school's real 2026 football schedule from games.js) to vb-data.js.
Run after make_vbdata.py (it calls this) or on its own: python3 tools/gridiron/vb_sched.py
sched[school] = [[week, 'YYYY-MM-DD', opponent, home 1/0, playoff 1/0], ...] sorted by date; opponent uses the Bowl's school name when it has one."""
import json,os
D=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.join(D,'..','..')
ALIAS={'Army and Navy Academy':'Army-Navy','Central Union':'Central','Christian High':'Christian','Mount Carmel':'Mt. Carmel','San Diego High':'San Diego',
       'Southwest San Diego':'Southwest SD','Southwest (El Centro)':'Southwest EC',"O'Farrell":"O'Farrell Charter"}
def main():
    p=os.path.join(D,'vb-data.js');s=open(p).read();d=json.loads(s[s.index('{'):s.rindex('}')+1])
    g=open(os.path.join(ROOT,'games.js')).read();G=json.loads(g[g.index('{'):g.rindex('}')+1])['games']
    V=set(d['schools']);nm=lambda n:ALIAS.get(n,n);S={}
    for x in sorted(G,key=lambda x:x['d']):
        h,a=nm(x['h']),nm(x['a'])
        for me,op,hm in ((h,a,1),(a,h,0)):
            if me in V:S.setdefault(me,[]).append([x['w'],x['d'],op,hm,1 if x.get('k')=='P' else 0])
    d['sched']=S;open(p,'w').write('window.VB_DATA='+json.dumps(d,separators=(',',':'))+';\n')
    print('sched for',len(S),'of',len(V),'schools')
if __name__=='__main__':main()
