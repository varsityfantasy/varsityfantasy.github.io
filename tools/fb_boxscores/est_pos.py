"""Fill DL/LB/DB for defenders whose MaxPreps roster has no position (stats.js u == 'DEF').
The app must never show 'DEF' as a position (owner, Nov 22 2026). A logistic model trained on defenders with a known position
(S and CB count as DB) guesses it from the stat mix; same features as tools/ovr/make_ovr.py.
Used by merge.py when it writes stats.js; also runnable alone:  python3 tools/fb_boxscores/est_pos.py [write]"""
import json,os,sys
ROOT=os.path.dirname(os.path.abspath(__file__))+'/../../'
# stat array indexes (see merge.py): 9 tackles, 23 tfl, 10 sacks, 11 INT, 24 pbu, 12 forced fumbles, 13 fumble recoveries
def _f(p):
    n=0;t=tl=sk=it=pb=ff=fr=0.0
    for a in p['w'].values():
        g=lambda i:(a[i] if i<len(a) else 0)
        if not any(g(i) for i in(9,23,10,11,24,12,13)):continue
        n+=1;t+=g(9);tl+=g(23);sk+=g(10);it+=g(11);pb+=g(24);ff+=g(12);fr+=g(13)
    n=max(n,1)
    return [t/n,tl/n,sk/n,it/n,pb/n,ff/n,fr/n,sk/(t+1),tl/(t+1),it/(t+1),pb/(t+1)]
def estimate(P):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    import numpy as np
    D=[p for p in P if p['p']=='DEF']
    known=[p for p in D if p.get('u') in('DL','LB','DB','S','CB')]
    unk=[p for p in D if p.get('u') not in('DL','LB','DB','S','CB')]
    if not unk:return 0
    y=['DB' if p['u'] in('S','CB') else p['u'] for p in known]
    m=make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000)).fit(np.array([_f(p) for p in known]),y)
    for p,q in zip(unk,m.predict(np.array([_f(p) for p in unk]))):p['u']=str(q)
    return len(unk)
if __name__=='__main__':
    s=open(ROOT+'stats.js').read();i=s.index('window.MAXPREPS=')+16;j=s.index('\n',i);D=json.loads(s[i:j].rstrip().rstrip(';'))
    n=estimate(D['players']);print('estimated',n)
    if 'write' in sys.argv:open(ROOT+'stats.js','w').write(s[:i]+json.dumps(D,separators=(',',':'),ensure_ascii=False)+';'+s[j:]);print('written')
