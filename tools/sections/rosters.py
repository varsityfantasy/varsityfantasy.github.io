"""Team rosters for every section: each player's real position(s) and class year, read from the team's roster page.

    python3 tools/sections/rosters.py --sport fb [--cache .mpcache] [--delay 0.5] [--workers 4] [--max-teams N] [--max-minutes M] [--max-age-days 6]

Box scores carry no positions, so until now a section's positions were guessed from the stats (no tight ends, no real DL / LB / DB, no grades).
San Diego has always taken them from the roster page (tools/fb_boxscores/collect.js, step 3: every table row that links a careerid is
[number, name, class, positions]); this is the same read for every team the collector knows, so every section gets the same positions.
Team addresses come from the school record ('urls', saved by the collector since v493) or, for data collected before that, from the
collector's page cache (--cache: every cached schedule page lists the teams on it with their address).
Writes data/rosters/<section>.<sport>.json  {players: {career id: [name, class, positions, school id]}}
and    data/rosters/<sport>.done.json       {school id: date read}  (a team is read again after --max-age-days).
build_api.py merges it into players.json / weekly.json (position, defensive group, grade, full name)."""
import argparse, datetime, glob, html.parser, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import maxpreps as M  # noqa: E402

SPORT_WORD = {'fb': 'football', 'bb': 'basketball'}
GR = {'fr': 1, 'so': 2, 'jr': 3, 'sr': 4}
CLASS_RE = re.compile(r'^(fr|so|jr|sr)(\.|eshman|phomore|unior|enior)?$', re.I)
POS_RE = re.compile(r'^[A-Za-z]{1,4}$')


class _Rows(html.parser.HTMLParser):
    """Every <tr> as (cells' text, career id of the first athlete link in it)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.cells, self.cur, self.cid, self.link_cell = [], None, None, None, None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells, self.cid, self.link_cell = [], None, None
        elif tag in ('td', 'th') and self.cells is not None:
            self.cur = []
        elif tag == 'a' and self.cells is not None and self.cid is None:
            m = re.search(r'careerid=([\w-]+)', dict(attrs).get('href') or '')
            if m:
                self.cid, self.link_cell = m.group(1), len(self.cells)

    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cur is not None:
            self.cells.append(re.sub(r'\s+', ' ', ''.join(self.cur)).strip())
            self.cur = None
        elif tag == 'tr' and self.cells is not None:
            if self.cid:
                self.rows.append((self.cells, self.cid, self.link_cell))
            self.cells = None

    def handle_data(self, data):
        if self.cur is not None:
            self.cur.append(data)


def clean_pos(s):
    """'QB, FS' / 'WR/CB' -> 'QB,FS' (upper case, only position-looking words)."""
    return ','.join(p.upper() for p in re.split(r'[,/\s]+', s or '') if POS_RE.match(p))


def parse_roster(page):
    """-> {career id: [name, class ('Fr.' 'So.' 'Jr.' 'Sr.' or ''), positions 'QB,FS']} from a roster page."""
    pr = _Rows()
    pr.feed(page)
    out = {}
    for cells, cid, li in pr.rows:
        if li is None or li >= len(cells) or not cells[li]:
            continue
        name = re.sub(r'\s*Claimed profile\s*$', '', cells[li], flags=re.I).strip()  # MaxPreps badge text, not part of the name
        rest = cells[li + 1:]
        ci = next((i for i, c in enumerate(rest) if CLASS_RE.match(c)), None)
        cls = ''
        if ci is not None:
            cls = rest[ci][:2].capitalize() + '.'
            pos = clean_pos(rest[ci + 1]) if ci + 1 < len(rest) else ''
        else:
            pos = clean_pos(rest[1]) if len(rest) > 1 else ''
        out[cid] = [name, cls, pos]
    return out


def grade(cls):
    return GR.get((cls or '')[:2].lower(), 0)


OFF = {'QB': 'QB', 'RB': 'RB', 'HB': 'RB', 'TB': 'RB', 'FB': 'RB', 'WR': 'WR', 'SB': 'WR', 'SE': 'WR', 'FL': 'WR', 'TE': 'TE'}
DEF = {'DL': 'DL', 'DE': 'DL', 'DT': 'DL', 'NT': 'DL', 'NG': 'DL', 'LB': 'LB', 'ILB': 'LB', 'OLB': 'LB', 'MLB': 'LB',
       'CB': 'DB', 'S': 'DB', 'SS': 'DB', 'FS': 'DB', 'DB': 'DB'}
KICK = {'K', 'P'}


def football_pos(positions, guess, t):
    """Position for the app from the roster's list and the stats-based guess (players.guess_pos) -> (pos, sub, alt).
    pos: QB RB WR TE DEF K.  sub: DL / LB / DB for a defender when the roster says ('' = the app guesses from stats), else pos.
    alt: his position on the other side of the ball, for a two-way player's second card ('' when the roster lists none).
    The side with the stats wins: a 'WR, CB' whose stats are all tackles is a DB whose other card would be WR."""
    ps = [p for p in (positions or '').split(',') if p]
    o = next((OFF[p] for p in ps if p in OFF), '')
    d = next((DEF[p] for p in ps if p in DEF), '')
    k = any(p in KICK for p in ps)
    g = lambda key: t.get(key, 0)
    if guess == 'K' or (k and not o and not d and not guess):
        return 'K', 'K', ''
    if guess == 'QB':
        if not o or g('passYd') > g('rushYd') + g('recYd'):
            o = 'QB'
        return o, o, d
    if guess in ('RB', 'WR'):
        o = o if o and o != 'QB' else guess
        return o, o, d
    if guess == 'DEF':
        return 'DEF', d, o
    if o:
        return o, o, d
    if d:
        return 'DEF', d, ''
    if k:
        return 'K', 'K', ''
    return 'RB', 'RB', ''


def urls_from_cache(cache, sport):
    """{school id: team address} from the collector's cached schedule pages."""
    out = {}
    word = SPORT_WORD[sport]
    for fn in glob.glob(os.path.join(cache or '', '*.json')):
        try:
            c = json.load(open(fn))
        except (ValueError, OSError):
            continue
        for sid, t in M.teams_in(c.get('contests')).items():
            m = M.TEAM_URL_RE.match(t.get('url') or '')
            if m and m.group(1) == word:
                out.setdefault(sid, t['url'])
    return out


def run(a, log=print, fetcher=None):
    sport = a.sport
    secs = {}
    for fn in sorted(os.listdir(a.data)):
        if fn.endswith('.json') and fn != 'index.json':
            d = json.load(open(os.path.join(a.data, fn), encoding='utf-8'))
            secs[d.get('section') or fn[:-5]] = d
    cached = urls_from_cache(a.cache, sport) if a.cache else {}
    teams = []   # (section, school id, address)
    for sid, d in secs.items():
        for sc in d.get('schools', []):
            u = (sc.get('urls') or {}).get(sport) or cached.get(sc['id'])
            if u and M.TEAM_URL_RE.match(u):
                teams.append((sid, sc['id'], u))
    n_all = sum(len(d.get('schools', [])) for d in secs.values())
    os.makedirs(a.out, exist_ok=True)
    done_path = os.path.join(a.out, sport + '.done.json')
    done = json.load(open(done_path)) if os.path.exists(done_path) else {}
    store = {}
    for sid in secs:
        p = os.path.join(a.out, '%s.%s.json' % (sid, sport))
        store[sid] = json.load(open(p, encoding='utf-8'))['players'] if os.path.exists(p) else {}
    today = datetime.date.today()
    old = lambda s: (today - datetime.date.fromisoformat(s)).days >= a.max_age_days
    todo = [t for t in teams if t[1] not in done or old(done[t[1]])]
    log('rosters %s: %d schools, %d with a team address (%d from the page cache), %d to read' % (sport, n_all, len(teams), sum(1 for t in teams if t[1] in cached), len(todo)))
    if a.max_teams:
        todo = todo[:a.max_teams]
    fetcher = fetcher or M.Fetcher(delay=a.delay, cache=None, max_age_h=0, log=log)
    stat = {'read': 0, 'empty': 0, 'notfound': 0, 'players': 0}
    stop, t0, diag = None, time.time(), ''

    def save():
        now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        for sid, pl in store.items():
            if pl:
                tmp = os.path.join(a.out, '%s.%s.json.tmp' % (sid, sport))
                json.dump({'section': sid, 'sport': sport, 'synced': now, 'players': pl}, open(tmp, 'w', encoding='utf-8'), sort_keys=True, ensure_ascii=False, separators=(',', ':'))
                os.replace(tmp, os.path.join(a.out, '%s.%s.json' % (sid, sport)))
        json.dump(done, open(done_path + '.tmp', 'w'), sort_keys=True, separators=(',', ':'))
        os.replace(done_path + '.tmp', done_path)

    import concurrent.futures, random

    def fetch_one(t):
        try:
            page = fetcher.get(t[2] + 'roster/') if getattr(fetcher, 'get', None) else fetcher._open(t[2] + 'roster/')
            time.sleep(a.delay * random.uniform(0.8, 1.2) if a.delay else 0)
            return ('ok', page)
        except M.NotFound:
            return ('notfound',)
        except M.Blocked as e:
            return ('blocked', str(e))

    if todo and not fetcher.allowed(todo[0][2] + 'roster/'):
        stop, todo = 'robots.txt disallows roster pages', []
    workers = max(1, a.workers)
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
    for start in range(0, len(todo), workers * 6):
        if stop:
            break
        if a.max_minutes and time.time() - t0 > a.max_minutes * 60:
            stop = 'time limit (%s min)' % a.max_minutes
            break
        batch = todo[start:start + workers * 6]
        for t, res in zip(batch, pool.map(fetch_one, batch)):
            if res[0] == 'blocked':
                stop = 'STOPPED: %s' % res[1]
                break
            if res[0] == 'notfound':
                stat['notfound'] += 1
                done[t[1]] = today.isoformat()
                continue
            R = parse_roster(res[1])
            stat['read'] += 1
            if not R:
                stat['empty'] += 1
                if not diag:   # what the page does hold, so the parser can be fixed from the run's own report
                    pg = res[1]
                    i = pg.find('careerid')
                    diag = 'first empty page %sroster/: %d chars, %d <tr>, %d careerid, near the first one: %r' % (
                        t[2], len(pg), pg.count('<tr'), pg.count('careerid'), pg[max(0, i - 300):i + 200] if i >= 0 else pg[:300])
                if stat['read'] >= 30 and stat['empty'] == stat['read']:
                    stop = 'STOPPED: the first %d roster pages had no player rows (page format changed?)' % stat['read']
                    break
                continue
            for cid, (name, cls, pos) in R.items():
                store[t[0]][cid] = [name, cls, pos, t[1]]
            stat['players'] += len(R)
            done[t[1]] = today.isoformat()
        if (start // (workers * 6)) % 10 == 9:
            save()
            log('  %d/%d rosters, %d players so far' % (min(len(todo), start + len(batch)), len(todo), stat['players']))
    pool.shutdown(wait=True)
    save()
    with_pos = sum(1 for pl in store.values() for v in pl.values() if v[2])
    with_cls = sum(1 for pl in store.values() for v in pl.values() if v[1])
    total = sum(len(pl) for pl in store.values())
    log('rosters done: %s. read %d, no player rows %d, not found %d; %d players on file, %d with a position, %d with a class' % (
        stop or 'all teams read', stat['read'], stat['empty'], stat['notfound'], total, with_pos, with_cls))
    if diag:
        log('  ' + diag)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sport', required=True, choices=['fb', 'bb'])
    ap.add_argument('--data', default=os.path.join(ROOT, 'data', 'sections'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'data', 'rosters'))
    ap.add_argument('--cache', default='')
    ap.add_argument('--delay', type=float, default=0.5)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--max-teams', type=int, default=0)
    ap.add_argument('--max-minutes', type=float, default=0)
    ap.add_argument('--max-age-days', type=int, default=6)
    return run(ap.parse_args())


if __name__ == '__main__':
    sys.exit(main())
