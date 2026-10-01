"""Stage 99: link validation, browser-completeness test, UTF-8/mojibake scan.

1. Every href/src in every generated .html under the asset root must resolve to an existing file.
2. Every path referenced from page data (index_data.js rows, crumbs, prev/next), the search index and the atlas viewer must exist.
3. Every row of Catalogs/asset_cross_reference.csv must have an existing BROWSER_ROUTE page that lists it (page data or element id),
   and an existing DETAIL_PAGE when one is declared.
4. Generated text files must not contain mojibake sequences (UTF-8 decoded as cp1252/latin-1 and re-encoded).
"""
import csv, re
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
from common import *

SKIP_DIRS = ('.claude',)
broken = []


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ('href', 'src') and v:
                self.links.append(v)
            if k == 'id' and v:
                self.ids.add(v)


def target(base_dir, link):
    if link.startswith(('http:', 'https:', 'mailto:', 'javascript:', 'data:')) or link.startswith('#'):
        return None
    if link.startswith('file:///'):
        return Path(unquote(urlsplit(link).path.lstrip('/')))
    path = unquote(urlsplit(link).path)
    return (base_dir / path).resolve() if path else None


htmls = [p for p in ROOT.rglob('*.html') if not any(s in p.parts for s in SKIP_DIRS)]
page_ids = {}
nlinks = 0
for p in htmls:
    lp = Links()
    lp.feed(p.read_text(encoding='utf-8', errors='replace'))
    page_ids[rel(p)] = lp.ids
    for l in lp.links:
        t = target(p.parent, l)
        if t is None:
            continue
        nlinks += 1
        if not t.exists():
            broken.append({'SOURCE': rel(p), 'LINK': l, 'KIND': 'html attribute'})


def jsdata(p, var):
    s = p.read_text(encoding='utf-8')
    return json.loads(s[len(f'window.{var}='):-1])


page_rows = {}
ndata = 0
for p in ROOT.rglob('index_data.js'):
    if any(s in p.parts for s in SKIP_DIRS):
        continue
    P = jsdata(p, 'PAGE')
    html_page = rel(p.with_name('index.html'))
    page_rows[html_page] = {r.get('ASSET_ID') for r in P.get('rows', [])}
    refs = [c[1] for c in P.get('crumbs', []) if c[1]] + [x[1] for x in (P.get('prev'), P.get('next')) if x]
    for r in P.get('rows', []):
        refs += [r.get(k) for k in ('OUTPUT', 'THUMB', 'METADATA', 'AUDIO') if r.get(k)]
        if r.get('DETAIL_PAGE'):
            refs.append(r['DETAIL_PAGE'].split('#')[0])
    for x in refs:
        ndata += 1
        q = Path(x) if (len(x) > 2 and x[1] == ':') else ROOT / x
        if not q.exists():
            broken.append({'SOURCE': rel(p), 'LINK': x, 'KIND': 'page data'})
SD = jsdata(ROOT / 'Metadata/Browser/search_index.js', 'SEARCHDB')
for x in SD['paths']:
    ndata += 1
    if not (ROOT / x.split('#')[0]).exists():
        broken.append({'SOURCE': 'Metadata/Browser/search_index.js', 'LINK': x, 'KIND': 'search index'})
libs = jsdata(ROOT / 'Shared/SourceLibraries/viewer_libs.js', 'LIBS')
for slug_, name, _ in libs:
    d = ROOT / 'Shared/SourceLibraries' / slug_
    if not (d / 'library.js').exists():
        broken.append({'SOURCE': 'viewer_libs.js', 'LINK': slug_ + '/library.js', 'KIND': 'atlas viewer'})
        continue
    L = read(d / 'library.json')
    pal = (L['palettes'] or [None])[0]
    for page in sorted({f['page'] for f in L['frames'] if f.get('page') is not None}):
        for f_ in [f'page_{page:04d}_index_data.png'] + ([f"page_{page:04d}__{re.sub(r'[^\w.-]+', '_', pal)}.png"] if pal else []):
            ndata += 1
            if not (d / f_).exists():
                broken.append({'SOURCE': f'{slug_}/library.json', 'LINK': f_, 'KIND': 'atlas page'})

# ---------------------------------------------------------------- completeness
with (ROOT / 'Catalogs/asset_cross_reference.csv').open(encoding='utf-8-sig') as f:
    X = list(csv.DictReader(f))
no_route = []
for r in X:
    route = r['BROWSER_ROUTE']
    ok = bool(route) and (ROOT / route).exists() and (r['ASSET_ID'] in page_rows.get(route, set()) or r['ASSET_ID'] in page_ids.get(route, set()))
    if r['DETAIL_PAGE'] and not (ROOT / r['DETAIL_PAGE'].split('#')[0]).exists():
        ok = False
    if not ok:
        no_route.append({'ASSET_ID': r['ASSET_ID'], 'CATEGORY': r['CATEGORY'], 'ROUTE': route, 'DETAIL': r['DETAIL_PAGE']})

# ---------------------------------------------------------------- mojibake / UTF-8
MOJI = re.compile('Ã[\u0080-¿ -ÿ]|Â[ -¿]|â€|Ă‰|Ă‚|Ä‚|Ĺ|â†')
bad_utf8, moji = [], []
for p in ROOT.rglob('*'):
    if not p.is_file() or any(s in p.parts for s in SKIP_DIRS) or p.suffix.lower() not in ('.html', '.js', '.json', '.csv', '.md', '.txt', '.css'):
        continue
    if 'Raw' in p.parts or p.name == 'search_index.js' or (p.parts[len(ROOT.parts)] == 'Audio' and p.suffix.lower() == '.txt'):
        continue  # Raw / Audio .txt = bit-exact original documents (not re-encoded); search index derives from checked catalogs
    b = p.read_bytes()
    try:
        s = b.decode('utf-8')
    except UnicodeDecodeError:
        bad_utf8.append(rel(p))
        continue
    m = MOJI.search(s)
    if m:
        moji.append({'FILE': rel(p), 'SAMPLE': s[max(0, m.start() - 30):m.end() + 30]})
html_meta = [rel(p) for p in htmls if '<meta charset="utf-8">' not in p.read_text(encoding='utf-8', errors='replace')[:400].lower()]
res = {'htmlPages': len(htmls), 'htmlLinksChecked': nlinks, 'dataPathsChecked': ndata, 'brokenLinks': len(broken), 'masterRows': len(X),
       'cataloguedWithoutBrowserRoute': len(no_route), 'nonUtf8TextFiles': bad_utf8, 'mojibakeFiles': len(moji), 'htmlWithoutUtf8Meta': html_meta}
write(ROOT / 'Metadata/Evidence/library/browser_validation.json', dict(res, broken=broken[:2000], noRoute=no_route[:2000], mojibake=moji[:500]))
csvout(ROOT / 'Catalogs/broken_links.csv', broken, ['SOURCE', 'LINK', 'KIND'])
print(json.dumps(res, indent=1))
for b in broken[:15]:
    print('BROKEN', b)
for n in no_route[:10]:
    print('NOROUTE', n)
for m in moji[:10]:
    print('MOJI', m)
