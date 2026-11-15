"""Offline checks for rosters.py. python3 -I tools/sections/test_rosters.py"""
import json, os, sys, tempfile, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rosters as R
import maxpreps as M

n = 0
def check(ok, msg):
    global n
    n += 1
    if not ok:
        print('FAIL:', msg); sys.exit(1)

PAGE = """<html><body><table><thead><tr><th>#</th><th>Name</th><th>Grade</th><th>Position</th><th>Height</th></tr></thead><tbody>
<tr><td>7</td><td><a href="/ca/town/alpha-lions/athletes/john-robertson/?careerid=abc123def4567"><span>John</span> Robertson</a></td><td>Sr.</td><td>QB, FS</td><td>6'1"</td></tr>
<tr><td>88</td><td><a href="/ca/town/alpha-lions/athletes/tim-oneil/?careerid=zzz999">Tim O&#x27;Neil</a></td><td>Jr.</td><td>TE/DE</td><td></td></tr>
<tr><td></td><td><a href="/athletes/x/?careerid=k1">Kai Kicker</a></td><td>So.</td><td>K, P</td><td></td></tr>
<tr><td>3</td><td><a href="/athletes/y/?careerid=n1">No Class</a></td><td></td><td>WR</td><td></td></tr>
<tr><td>1</td><td>Coach row without a link</td></tr></tbody></table></body></html>"""
r = R.parse_roster(PAGE)
check(r['abc123def4567'] == ['John Robertson', 'Sr.', 'QB,FS'], 'row: %s' % r.get('abc123def4567'))
check(r['zzz999'] == ["Tim O'Neil", 'Jr.', 'TE,DE'] and r['k1'][2] == 'K,P' and r['n1'] == ['No Class', '', 'WR'] and len(r) == 4, 'rows: %s' % r)
check(R.grade('Sr.') == 4 and R.grade('Fr.') == 1 and R.grade('') == 0, 'grades')
fp = R.football_pos
check(fp('QB,FS', 'QB', {'passYd': 900}) == ('QB', 'QB', 'DB'), 'qb')
check(fp('TE,DE', 'WR', {'recYd': 300}) == ('TE', 'TE', 'DL'), 'tight end')
check(fp('WR,CB', 'DEF', {'tkl': 40}) == ('DEF', 'DB', 'WR'), 'the side with the stats wins')
check(fp('OL,DT', 'DEF', {'tkl': 12}) == ('DEF', 'DL', ''), 'lineman')
check(fp('K,P', 'K', {'xpm': 20}) == ('K', 'K', ''), 'kicker')
check(fp('', 'RB', {'rushYd': 50}) == ('RB', 'RB', '') and fp('MLB', None, {}) == ('DEF', 'LB', ''), 'no roster position / no stats')
check(fp('WR', 'QB', {'passYd': 60, 'recYd': 500}) == ('WR', 'WR', '') and fp('WR', 'QB', {'passYd': 1500, 'recYd': 20}) == ('QB', 'QB', ''), 'trick-play passer stays WR')

# run(): addresses from the school record and from the page cache; a second run reads nothing
tmp = tempfile.mkdtemp()
data, out, cache = os.path.join(tmp, 'sections'), os.path.join(tmp, 'rosters'), os.path.join(tmp, 'cache')
os.makedirs(data); os.makedirs(cache)
A, B, C = 'mp:11111111-1111-1111-1111-111111111111', 'mp:22222222-2222-2222-2222-222222222222', 'mp:33333333-3333-3333-3333-333333333333'
UA_, UB = 'https://www.maxpreps.com/ca/town/alpha-lions/football/', 'https://www.maxpreps.com/ca/other/beta-bears/football/'
json.dump({'section': 'one', 'schools': [{'id': A, 'name': 'Alpha', 'urls': {'fb': UA_}}, {'id': B, 'name': 'Beta'}, {'id': C, 'name': 'Gamma'}], 'games': []}, open(os.path.join(data, 'one.json'), 'w'))
team = lambda sid, name, url: [0, sid[3:]] + [0] * 11 + [url, name, 'Town', 'CA']
row = [0] * 37 + [team(A, 'Alpha', UA_), team(B, 'Beta', UB)]
json.dump({'url': UA_ + 'schedule/', 'contests': [row]}, open(os.path.join(cache, 'x.json'), 'w'))
check(R.urls_from_cache(cache, 'fb').get(B) == UB and not R.urls_from_cache(cache, 'bb'), 'addresses from the page cache: %s' % R.urls_from_cache(cache, 'fb'))
class F:
    def __init__(self): self.urls = []
    def allowed(self, url): return True
    def get(self, url):
        self.urls.append(url)
        if 'beta' in url: raise M.NotFound('x')
        return PAGE
args = types.SimpleNamespace(sport='fb', data=data, out=out, cache=cache, delay=0, workers=2, max_teams=0, max_minutes=0, max_age_days=6)
f = F(); logs = []
check(R.run(args, logs.append, f) == 0 and sorted(f.urls) == [UB + 'roster/', UA_ + 'roster/'], 'both teams with an address are read: %s' % f.urls)
got = json.load(open(os.path.join(out, 'one.fb.json')))['players']
check(got['abc123def4567'] == ['John Robertson', 'Sr.', 'QB,FS', A] and len(got) == 4, 'saved: %s' % got)
f2 = F(); R.run(args, logs.append, f2)
check(f2.urls == [], 'second run reads nothing')

# v494 basketball: positions per team, last season's roster when the new one is not up (seniors out, one class up)
bp = R.basketball_team_pos([('a', 'PG', 0, {}), ('b', 'G', 0, {}), ('c', 'G', 0, {}), ('d', 'F', 0, {}), ('e', 'F', 0, {}), ('f', 'W', 0, {}),
                            ('g', '', 0, {}), ('h', 'C', 0, {}), ('i', 'G, F', 0, {}), ('j', '', 4, {'reb': 36, 'ast': 2})])
check(bp['a'] == 'PG' and bp['h'] == 'C' and bp['f'] == 'SF' and bp['j'] == 'C' and sorted(bp[x] for x in 'bci') == ['PG', 'SG', 'SG']
      and sorted(bp[x] for x in 'de') == ['PF', 'SF'] and bp['g'] == 'SG' and set(bp.values()) <= set(R.BB5) and len(bp) == 10, 'bb positions: %s' % bp)
check(R.bump('Jr.') == 'Sr.' and R.bump('Fr.') == 'So.' and R.bump('Sr.') is None and R.bump('') == '', 'class bump')
EMPTY = '<html><body><table><tr><th>Name</th></tr></table></body></html>'
UBB, UBB2 = 'https://www.maxpreps.com/ca/town/alpha-lions/basketball/', 'https://www.maxpreps.com/ca/other/beta-bears/basketball/'
json.dump({'section': 'one', 'schools': [{'id': A, 'name': 'Alpha', 'urls': {'bb': UBB}}, {'id': B, 'name': 'Beta', 'urls': {'bb': UBB2}}], 'games': []}, open(os.path.join(data, 'one.json'), 'w'))
class FB_:
    def __init__(self, new_alpha=False): self.urls, self.new = [], new_alpha
    def allowed(self, url): return True
    def get(self, url):
        self.urls.append(url)
        if 'beta' in url: return PAGE.replace('careerid=', 'careerid=b') if '25-26' not in url else EMPTY
        if '25-26' in url: return PAGE
        return PAGE.replace('Sr.', 'Fr.') if self.new else EMPTY
bargs = types.SimpleNamespace(sport='bb', data=data, out=out, cache='', delay=0, workers=2, max_teams=0, max_minutes=0, max_age_days=6, last_season='25-26')
f = FB_(); R.run(bargs, logs.append, f)
got = json.load(open(os.path.join(out, 'one.bb.json')))['players']
check(UBB + '25-26/roster/' in f.urls and UBB2 + '25-26/roster/' not in f.urls, 'falls back only when the new roster is empty: %s' % f.urls)
al = {k: v for k, v in got.items() if v[3] == A}
check('abc123def4567' not in al and al.get('zzz999') == ["Tim O'Neil", 'Sr.', 'TE,DE', A, 'ly'] and al['k1'][1] == 'Jr.' and len(al) == 3, 'last season, seniors out, class up: %s' % al)
check(got['babc123def4567'][3] == B and len(got['babc123def4567']) == 4, 'beta read from its current roster')
f = FB_(new_alpha=True); R.run(bargs, logs.append, f)
got = json.load(open(os.path.join(out, 'one.bb.json')))['players']
al = {k: v for k, v in got.items() if v[3] == A}
check(f.urls == [UBB + 'roster/'] and len(al) == 4 and all(len(v) == 4 for v in al.values()) and al['abc123def4567'][1] == 'Fr.', 'new roster replaces last season: %s %s' % (f.urls, al))
print('ok: %d checks passed' % n)
