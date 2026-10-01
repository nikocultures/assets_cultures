"""Stage 95: static whole-library browser (index.html, category list pages, detail pages, atlas viewer, search index).

All pages are UTF-8 with <meta charset="utf-8">; no server needed (data is loaded as .js files, which works on file://).
Row membership per page comes from Catalogs/asset_cross_reference.csv BROWSER_ROUTE, so every catalogued asset has a page.
"""
import collections, csv, glob, html, shutil
from urllib.parse import quote
from common import *

C = ROOT / 'Catalogs'
TF = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Arabs', 5: 'Other Tribes/Weresnakes', 6: 'Other Tribes/Werewolves', 7: 'Other Tribes/Egypt'}
TNAME = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Saracens (Arabs)', 5: 'Weresnakes', 6: 'Werewolves', 7: 'Egypt'}
E = html.escape
with (C / 'asset_cross_reference.csv').open(encoding='utf-8-sig') as f:
    X = list(csv.DictReader(f))
KEEP = ['ASSET_ID', 'CATEGORY', 'SUBCATEGORY', 'TRIBE', 'NATIVE_NAME', 'DISPLAY_NAME', 'LOGIC_ID', 'GFX_ID', 'JOB_ID', 'GOOD_ID', 'VEHICLE_TYPE', 'ANIMAL_TRIBE',
        'ATOMIC_ID', 'ATOMIC_NAME', 'BOBSEQ', 'ENTRY', 'BMD', 'BOB', 'PALETTE', 'PIVOT', 'WIDTH', 'HEIGHT', 'FRAMES', 'TIMING', 'STATUS', 'PRESENTATION',
        'UNKNOWN_CLASS', 'CONFIDENCE', 'OUTPUT', 'THUMB', 'THUMB_RECT', 'METADATA', 'ATLAS', 'DETAIL_PAGE', 'EVIDENCE']
COLS = {
    'Buildings': ['DISPLAY_NAME', 'GFX_ID', 'LOGIC_ID', 'BMD', 'BOB', 'WIDTH', 'HEIGHT', 'PIVOT', 'STATUS'],
    'Construction': ['DISPLAY_NAME', 'GFX_ID', 'BMD', 'BOB', 'STATUS'],
    'Shadows': ['DISPLAY_NAME', 'SUBCATEGORY', 'BMD', 'BOB', 'BOBSEQ', 'STATUS'],
    'Effects': ['DISPLAY_NAME', 'SUBCATEGORY', 'BMD', 'PALETTE', 'FRAMES', 'STATUS'],
    'Humans': ['DISPLAY_NAME', 'NATIVE_NAME', 'TRIBE', 'JOB_ID', 'BMD', 'STATUS'],
    'Animals': ['DISPLAY_NAME', 'NATIVE_NAME', 'TRIBE', 'JOB_ID', 'BMD', 'STATUS'],
    'Vehicles': ['DISPLAY_NAME', 'NATIVE_NAME', 'TRIBE', 'VEHICLE_TYPE', 'JOB_ID', 'BMD', 'SUBCATEGORY', 'STATUS'],
    'Goods': ['DISPLAY_NAME', 'NATIVE_NAME', 'GOOD_ID', 'LOGIC_ID', 'GFX_ID', 'BMD', 'BOB', 'STATUS'],
    'Landscapes': ['DISPLAY_NAME', 'SUBCATEGORY', 'GFX_ID', 'LOGIC_ID', 'BMD', 'BOB', 'PALETTE', 'FRAMES', 'STATUS'],
    'Terrain': ['DISPLAY_NAME', 'SUBCATEGORY', 'GFX_ID', 'LOGIC_ID', 'ENTRY', 'STATUS'],
    'UI': ['DISPLAY_NAME', 'SUBCATEGORY', 'BMD', 'BOB', 'WIDTH', 'HEIGHT', 'PALETTE', 'STATUS'],
    'Fonts': ['DISPLAY_NAME', 'SUBCATEGORY', 'ENTRY', 'FRAMES', 'STATUS'],
    'Images': ['DISPLAY_NAME', 'SUBCATEGORY', 'ENTRY', 'WIDTH', 'HEIGHT', 'STATUS'],
    'Palettes': ['DISPLAY_NAME', 'ENTRY', 'STATUS'],
    'Cursors': ['DISPLAY_NAME', 'ENTRY', 'WIDTH', 'HEIGHT', 'STATUS'],
    'Audio': ['DISPLAY_NAME', 'SUBCATEGORY', 'FRAMES', 'TIMING', 'STATUS'],
    'FMV': ['DISPLAY_NAME', 'WIDTH', 'HEIGHT', 'TIMING', 'CONFIDENCE', 'STATUS'],
    'Native documents': ['DISPLAY_NAME', 'SUBCATEGORY', 'ENTRY', 'STATUS'],
    'Native definitions': ['DISPLAY_NAME', 'ENTRY', 'CONFIDENCE', 'STATUS'],
    'Source libraries': ['DISPLAY_NAME', 'FRAMES', 'PALETTE', 'CONFIDENCE', 'STATUS'],
    'Unknown': ['DISPLAY_NAME', 'UNKNOWN_CLASS', 'SUBCATEGORY', 'BMD', 'BOB', 'WIDTH', 'HEIGHT', 'EVIDENCE'],
    'Loose files': ['DISPLAY_NAME', 'SUBCATEGORY', 'ENTRY', 'STATUS'],
}
FILTERS = {'Unknown': ['UNKNOWN_CLASS', 'BMD'], 'Audio': ['SUBCATEGORY', 'STATUS'], 'Landscapes': ['SUBCATEGORY', 'BMD', 'STATUS'], 'Terrain': ['SUBCATEGORY'],
           'UI': ['SUBCATEGORY', 'STATUS'], 'Shadows': ['TRIBE', 'SUBCATEGORY'], 'Source libraries': ['STATUS']}
written = set()


def depth_prefix(rp):
    return '../' * (len(Path(rp).parts) - 1)


def u(rp, frm):
    """relative URL from page `frm` (root-relative) to root-relative path rp (quoted, keeps #fragment)."""
    if not rp:
        return ''
    if len(rp) > 2 and rp[1] == ':':
        return 'file:///' + quote(rp.replace(B, '/'))
    frag = ''
    if '#' in rp:
        rp, frag = rp.split('#', 1)
        frag = '#' + quote(frag)
    return depth_prefix(frm) + quote(rp) + frag


def crumbs_for(rp):
    parts = Path(rp).parts[:-1]
    out = [['Home', 'index.html']]
    for i in range(len(parts)):
        p = '/'.join(parts[:i + 1]) + '/index.html'
        if i < len(parts) - 1 and not (ROOT / p).exists() and p not in PAGES:
            out.append([parts[i], ''])
        else:
            out.append([parts[i], p if i < len(parts) - 1 else ''])
    return out


def shell(rp, title, body, scripts=()):
    pre = depth_prefix(rp)
    sc = ''.join(f'<script src="{quote(s) if not s.startswith(pre) else s}"></script>' for s in scripts)
    page = (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)} | Cultures asset library</title><link rel="stylesheet" href="{pre}Metadata/Browser/app.css">{sc}'
            f'<script src="{pre}Metadata/Browser/app.js"></script></head><body><header class="top"><h1><a href="{pre}index.html">Cultures | Original Asset Library</a></h1>'
            f'<div>{E(title)}</div></header><main><div id="crumbs"></div>{body}</main></body></html>\n')
    p = ROOT / rp
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page, encoding='utf-8')
    written.add(rp)


def page_js(rp, title, rows, cat, extra=None, prev=None, nxt=None):
    cols = COLS.get(cat, ['DISPLAY_NAME', 'CATEGORY', 'SUBCATEGORY', 'STATUS'])
    data = []
    for r in rows:
        d = {k: r[k] for k in KEEP if r.get(k)}
        if r['CATEGORY'] == 'Audio' and r['OUTPUT'].lower().endswith('.wav'):
            d['AUDIO'] = r['OUTPUT']
        data.append(d)
    P = {'root': depth_prefix(rp), 'title': title, 'crumbs': crumbs_for(rp), 'rows': data, 'cols': cols,
         'filters': ['TRIBE', 'STATUS'] if cat in ('Humans', 'Vehicles', 'Animals') else FILTERS.get(cat, ['STATUS']), 'prev': prev, 'next': nxt}
    js = Path(rp).with_name('index_data.js')
    (ROOT / js).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / js).write_text('window.PAGE=' + json.dumps(P, ensure_ascii=False, separators=(',', ':')) + ';', encoding='utf-8')
    shell(rp, title, (extra or '') + '<div id="list"></div>', scripts=['index_data.js'])


def hub(rp, title, cards, intro=''):
    body = (f'<p>{intro}</p>' if intro else '') + '<div class="cards">' + ''.join(
        f'<div class="card"><h3><a href="{u(link, rp)}">{E(name)}</a></h3><p>{E(desc)}</p></div>' for name, link, desc in cards) + '</div>'
    P = {'root': depth_prefix(rp), 'title': title, 'crumbs': crumbs_for(rp)}
    (ROOT / Path(rp).with_name('index_data.js')).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / Path(rp).with_name('index_data.js')).write_text('window.PAGE=' + json.dumps(P, ensure_ascii=False) + ';', encoding='utf-8')
    shell(rp, title, body, scripts=['index_data.js'])


# ---------------------------------------------------------------- detail pages: owners
owners = []
for p in glob.glob(str(ROOT / '**/metadata.json'), recursive=True):
    q = p.replace(B, '/')
    if '/Sheets/' in q or 'SourceLibraries' in q or '/Buildings/' in q or '/Metadata/' in q:
        continue
    try:
        m = read(p)
    except Exception:
        continue
    if m.get('ownerKind') in ('human', 'animal', 'vehicle'):
        owners.append(m)
owners.sort(key=lambda m: (m['ownerKind'], m['tribeId'], m['typeId']))
DETAIL_ROUTES = set()
groups = collections.defaultdict(list)
for m in owners:
    groups[(m['ownerKind'], m['tribeId'] if m['ownerKind'] != 'animal' else 0)].append(m)


def owner_page(m, prev, nxt):
    rp = m['folder'] + '/index.html'
    kind = m['ownerKind']
    oid = f"{kind[:3]}:{m['tribeId']}:{m['typeId']}"
    kv = [('Tribe', f"{m['tribeId']} {m.get('nativeTribe')} ({m.get('tribeEnglish')})"), ('Type / job ID', m['typeId']), ('Animation job ID', m['animationJobId']),
          ('Native name', m['nativeName']), ('English', m['englishName']), ('Sex / age', m.get('sexAge')), ('Native allowed', m['nativeAllowed']),
          ('Parent chain (baseatomics)', m['parentChain']), ('Confidence', json.dumps(m['confidence'], ensure_ascii=False)),
          ('Native references', json.dumps(m['nativeReferences'], ensure_ascii=False))]
    if m.get('vehicleDefinition'):
        kv.append(('Vehicle definition', ' '.join(f"{c['name']} {c['arguments']}" for c in m['vehicleDefinition']['commands'] if c['name'] != 'logicgood')))
        kv.append(('Animation job evidence', m.get('animationJobEvidence')))
    body = f'<section id="{E(oid)}"><div class="kv">' + ''.join(f'<b>{E(str(k))}</b><span>{E(str(v))}</span>' for k, v in kv) + \
        f'</div><p><a href="{u(m["folder"] + "/metadata.json", rp)}">metadata.json</a></p></section>'
    body += '<section><h2>Graphics bindings</h2><table class="grid"><tr><th>phase</th><th>section</th><th>inherited from</th><th>body variants (selector: body / shadow)</th><th>head variants</th><th>palettes</th><th>random palettes</th></tr>'
    for b in m['bindings']:
        body += (f"<tr><td>{E(b['phase'])}</td><td>{b['sectionOrdinal']}</td><td>{E(str(b['inheritedFrom'] or ''))}</td><td>" +
                 '<br>'.join(f"{v['selector']}: {E(stem(v['body']))} / {E(stem(v['shadow']) if v['shadow'] else '-')} <a href=\"{u('Shared/SourceLibraries/viewer.html#' + slug(stem(v['body'])).lower(), rp)}\">atlas</a>" for v in b['bodyVariants']) +
                 '</td><td>' + '<br>'.join(f"{v['selector']}: {E(stem(v['head']))}" for v in b['headVariants']) + f"</td><td>{E(', '.join(b['bodyPalettes'] + b['headPalettes']))}</td><td>{E(', '.join(b['paletteRemaps']))}</td></tr>")
    body += '</table></section><section><h2>Animations</h2><p class="note">Sheets: one row per native direction (0..7, only directions with frames), columns in native frame-list order, shared anchor. ' \
            'Colours use the declared base palette; runtime RNG palette ordinal, player colour and random patches are not applied (PRESENTATION_APPROXIMATION). Shadow masks are kind-2 coverage DATA.</p>'
    for a in m['animations']:
        label = a['atomicName'] or ('walk' + (f" carrying good {a['carriedGoodType']} {a['carriedGoodName']}" if a['carriedGoodType'] else ''))
        body += (f"<details open><summary><b>{E(a['kind'])} {E(str(a['atomicActionSelector'] if a['kind'] == 'atomic' else a['carriedGoodType']))}</b> {E(label)} | BobSeq {E(a['bodySequence'] or '(absolute)')}"
                 f"{' / head ' + E(a['headSequence']) if a['headSequence'] else ''} | section {a['animationSection']}{' (inherited from job ' + str(a['definedForJob']) + ')' if a['inherited'] else ''}"
                 f" | mode {a['mode']} | length {E(str(a['atomicLength']))}</summary><div class=\"sub\">{E(a['timing'])}</div><div class=\"gallery\">")
        for r in a['renders']:
            aid = f"{kind[:3]}anim:{m['tribeId']}:{m['typeId']}:{a['animationSection']}:{r['phase']}:{r['bodySelector']}"
            cap = f"{r['phase']} body {r['bodySelector']} ({stem(r['bodyLibrary'])}) palette {r.get('bodyPalette')} | {r['status']}"
            if r.get('sheet'):
                body += (f'<figure id="{E(aid)}"><a href="{u(r["sheet"], rp)}"><img loading="lazy" src="{u(r["sheet"], rp)}" alt=""></a><figcaption>{E(cap)}'
                         + (f' | <a href="{u(r["shadowMask"], rp)}">shadow mask</a>' if r.get('shadowMask') else '') + f" | cell {r.get('cellWidth')}x{r.get('cellHeight')} anchor {r.get('anchorInCell')}</figcaption></figure>")
            else:
                body += f'<figure id="{E(aid)}"><figcaption>{E(cap)}</figcaption></figure>'
        body += '</div><details><summary>direction frame lists (BOB ids)</summary><pre>' + E(json.dumps([{k: d.get(k) for k in ('direction', 'bodyBobs', 'headBobs', 'status')} for d in a['directions']], ensure_ascii=False)) + '</pre></details></details>'
    if m.get('atomicsWithoutGraphicsRecord'):
        body += '<section><h2>Atomics declared without a graphics record</h2><p>' + E(', '.join(f"{x['selector']}:{x['atomicName']}" for x in m['atomicsWithoutGraphicsRecord'])) + \
                '</p><p class="sub">0x00494AE6: lookup fails along the parent chain, then retries selector 0 at the chain root.</p></section>'
    P = {'root': depth_prefix(rp), 'crumbs': crumbs_for(rp), 'prev': prev, 'next': nxt}
    (ROOT / m['folder'] / 'index_data.js').write_text('window.PAGE=' + json.dumps(P, ensure_ascii=False) + ';', encoding='utf-8')
    shell(rp, f"{m['englishName'] or m['nativeName']} ({m.get('tribeEnglish') or m.get('nativeTribe')})", body, scripts=['index_data.js'])
    DETAIL_ROUTES.add(rp)


PAGES = set()
for k, ms in groups.items():
    for i, m in enumerate(ms):
        prev = [ms[i - 1]['englishName'] or ms[i - 1]['nativeName'], ms[i - 1]['folder'] + '/index.html'] if i else None
        nxt = [ms[i + 1]['englishName'] or ms[i + 1]['nativeName'], ms[i + 1]['folder'] + '/index.html'] if i + 1 < len(ms) else None
        owner_page(m, prev, nxt)

# ---------------------------------------------------------------- detail pages: goods
goods = sorted(glob.glob(str(ROOT / 'Shared/Goods/good_*/metadata.json')))
for i, p in enumerate(goods):
    g = read(p)
    rp = rel(Path(p).parent / 'index.html')
    kv = [('Good ID', g['goodId']), ('Native name', g['nativeName']), ('English', f"{g['english']} / {g['englishPlural']}"), ('Landscape type', g['landscapeType']),
          ('Resolved GfxLandscape', f"{g['resolvedGfxLandscape']} {g['resolvedGfxLandscapeName'] or ''}"), ('Rule', g['resolutionRule']), ('BMD', g['bodyLibrary']),
          ('Palette', g['palette']), ('Production', json.dumps(g['production'])), ('Harvest', json.dumps(g['harvest'])),
          ('Weapon / armor type', json.dumps([g['weaponType'], g['armorType']])[:400]), ('Ownership', g['ownership']), ('Confidence', json.dumps(g['confidence']))]
    body = f'<section id="good:{g["goodId"]}"><div class="kv">' + ''.join(f'<b>{E(str(k))}</b><span>{E(str(v))}</span>' for k, v in kv) + '</div></section>'
    if g['icon']:
        body += f'<section><h2>UI visual (icon)</h2><p>{E(g["icon"]["presentation"])}</p><img src="{u(g["icon"]["path"], rp)}" alt="" style="background:#8a9089"></section>'
    else:
        body += f'<section><p class="note">{E(g["iconNote"])}</p></section>'
    if g['pileValencies']:
        body += '<section><h2>World pile frames by valency</h2><div class="gallery">' + ''.join(
            f'<figure><img loading="lazy" src="{u(fr["path"], rp)}" alt=""><figcaption>valency {v["valency"]} BOB {fr["bobId"]} {fr.get("width")}x{fr.get("height")} pivot {fr.get("pivot")}'
            + (f' | <a href="{u(fr["shadowMask"], rp)}">shadow</a>' if fr.get('shadowMask') else '') + '</figcaption></figure>'
            for v in g['pileValencies'] for fr in v['frames'] if fr.get('path')) + f'</div><p><a href="{u(g["pileMetadata"], rp)}">pile landscape metadata</a></p></section>'
    ca = g['carriedVisual']['animations']
    body += f'<section><h2>Carried visual</h2><p>{E(g["carriedVisual"]["rule"])}. Human random palette: {E(str(g["carriedVisual"]["humanRandomPalette"]))}</p>'
    body += '<table class="grid"><tr><th>tribe</th><th>job</th><th>phase</th><th>sequence</th><th>sheet</th></tr>' + ''.join(
        f"<tr><td>{E(a['TRIBE_ID'])}</td><td>{E(a['TYPE_ID'])} {E(a['NATIVE_NAME'])}</td><td>{E(a['PHASE'])} body {E(a['BODY_SELECTOR'])}</td><td>{E(a['BODY_SEQUENCE'])}</td><td>"
        + (f"<a href=\"{u(a['SHEET'], rp)}\">sheet</a>" if a['SHEET'] else E(a['STATUS'])) + '</td></tr>' for a in ca) + '</table></section>'
    cons = g.get('consumers', {})
    body += '<section><h2>Consumers</h2><p>Production input of: ' + E(', '.join(f"{c['goodId']} {c['english']}" for c in cons.get('productionInputOf', [])) or 'none') +         '</p><p>Needed to build: ' + E(', '.join(sorted({f"tribe {c['tribe']} {c['houseName']}" for c in cons.get('houseConstruction', [])})) or 'none') + '</p><p>Native job relations: ' + E(', '.join(sorted({f"tribe {r['tribe']} {r['relation']} job {r['jobId']} {r['jobEnglish']}" for r in g.get('nativeJobRelations', [])})) or 'none') + \
        f'</p><p class="sub">{E(cons.get("source", ""))}</p></section>'
    body += '<section><h2>Producers / tribes</h2><pre>' + E(json.dumps(g['tribeOwnership'], indent=1, ensure_ascii=False)) + '</pre></section>'
    body += f'<p><a href="{u(rel(p), rp)}">metadata.json</a></p>'
    prev = [f"Good {read(goods[i - 1])['goodId']}", rel(Path(goods[i - 1]).parent / 'index.html')] if i else None
    nxt = [f"Good {read(goods[i + 1])['goodId']}", rel(Path(goods[i + 1]).parent / 'index.html')] if i + 1 < len(goods) else None
    (Path(p).parent / 'index_data.js').write_text('window.PAGE=' + json.dumps({'root': depth_prefix(rp), 'crumbs': crumbs_for(rp), 'prev': prev, 'next': nxt}, ensure_ascii=False) + ';', encoding='utf-8')
    shell(rp, f"Good {g['goodId']} {g['english']} ({g['nativeName']})", body, scripts=['index_data.js'])

# ---------------------------------------------------------------- detail pages: building levels
lvls = [r for r in X if r['CATEGORY'] == 'Buildings']
for i, r in enumerate(lvls):
    rp = r['DETAIL_PAGE']
    if not rp:
        continue
    m = read(ROOT / r['METADATA'])
    lvl = Path(r['METADATA']).parent.as_posix()
    kv = [('Native name', m['nativeName']), ('Tribe', m['tribe']), ('GfxHouse / logic House', f"{m['gfxHouseId']} / {m['logicHouseType']}"), ('Level', m['level']),
          ('Body BOB', f"{m['bodyBob']} in {m['bobLibrary']}"), ('Shadow', f"{m.get('shadowLibrary')} BOB {m.get('shadowBob')}"), ('Dimensions / pivot', f"{m.get('width')}x{m.get('height')} pivot {m.get('pivot')}"),
          ('Palettes', ', '.join(m['paletteAlternatives'])), ('Palette rule', m['paletteSelection']), ('Status', r['STATUS']), ('Confidence per field', json.dumps(m['confidencePerField'])),
          ('Errors', '; '.join(m.get('errors', [])) or 'none')]
    if m.get('manualValidation'):
        kv.insert(0, ('Manual validation', json.dumps(m['manualValidation'], ensure_ascii=False)))
    body = f'<section id="{E(r["ASSET_ID"])}"><div class="kv">' + ''.join(f'<b>{E(str(k))}</b><span>{E(str(v))}</span>' for k, v in kv) + '</div></section>'
    body += '<section><h2>Finished body (all native palettes)</h2><div class="gallery">' + ''.join(
        f'<figure><img loading="lazy" src="{u(fr["path"], rp)}" alt=""><figcaption>{E(str(fr.get("palette")))}</figcaption></figure>' for fr in m['baseFrames'] if fr.get('path')) + '</div></section>'
    if m.get('shadow', {}).get('path'):
        body += f'<section><h2>Shadow coverage (DATA mask)</h2><img src="{u(m["shadow"]["path"], rp)}" alt="" style="background:#c9c9c9"></section>'
    if m.get('constructionSnapshots'):
        body += '<section><h2>Construction progress (body only; PREVIEW checkerboards separate)</h2><div class="gallery">' + ''.join(
            f'<figure><img loading="lazy" src="{u(s["path"], rp)}" alt=""><figcaption>{s["progressPercent"]}%</figcaption></figure>' for s in m['constructionSnapshots']) + '</div></section>'
    pngs = sorted((ROOT / lvl).rglob('*.png'))
    body += '<section><h2>All exported files of this level</h2><details><summary>' + str(len(pngs)) + ' PNG files + metadata</summary>' + '<br>'.join(
        f'<a href="{u(rel(p_), rp)}">{E(str(p_.relative_to(ROOT / lvl)).replace(B, "/"))}</a>' for p_ in pngs) + '<br>' + '<br>'.join(
        f'<a href="{u(lvl + "/" + s, rp)}">{s}</a>' for s in ('metadata.json', 'shadow/metadata.json', 'construction/metadata.json', 'states/metadata.json', 'animation/animation.json', 'effects/metadata.json')
        if (ROOT / lvl / s).exists()) + '</details></section>'
    same = [x for x in lvls if x['TRIBE'] == r['TRIBE'] and x['DETAIL_PAGE']]
    j = same.index(r)
    prev = [same[j - 1]['DISPLAY_NAME'], same[j - 1]['DETAIL_PAGE']] if j else None
    nxt = [same[j + 1]['DISPLAY_NAME'], same[j + 1]['DETAIL_PAGE']] if j + 1 < len(same) else None
    (ROOT / rp).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / rp).with_name('index_data.js').write_text('window.PAGE=' + json.dumps({'root': depth_prefix(rp), 'crumbs': crumbs_for(rp), 'prev': prev, 'next': nxt}, ensure_ascii=False) + ';', encoding='utf-8')
    shell(rp, r['DISPLAY_NAME'], body, scripts=['index_data.js'])

# ---------------------------------------------------------------- list pages from routes
byroute = collections.defaultdict(list)
for r in X:
    byroute[r['BROWSER_ROUTE']].append(r)
TITLES = {}
for t, folder in TF.items():
    for sub in ('Buildings', 'Humans', 'Vehicles', 'Construction', 'Effects', 'Shadows', 'Goods'):
        TITLES[f'{folder}/{sub}/index.html'] = (f'{TNAME[t]} | {sub}', sub)
TITLES.update({'Animals/index.html': ('Animals', 'Animals'), 'Shared/Goods/index.html': ('Goods (shared native table)', 'Goods'),
               'Terrain/Landscapes/index.html': ('Landscape definitions', 'Landscapes'), 'Terrain/Patterns/index.html': ('Terrain patterns', 'Terrain'),
               'Terrain/Transitions/index.html': ('Terrain transitions', 'Terrain'), 'Terrain/Textures/index.html': ('Terrain textures (PCX)', 'Images'),
               'Shared/Effects/index.html': ('Effects', 'Effects'), 'UI/Sprites/index.html': ('UI sprites', 'UI'), 'UI/Fonts/index.html': ('Fonts', 'Fonts'),
               'UI/Images/index.html': ('UI images', 'Images'), 'UI/Cursors/index.html': ('Cursors', 'Cursors'), 'Metadata/Palettes/index.html': ('Palettes', 'Palettes'),
               'Audio/index.html': ('Audio', 'Audio'), 'FMV/index.html': ('FMV', 'FMV'), 'Metadata/Sources/index.html': ('Native definitions and documents', 'Native definitions'),
               'Shared/SourceLibraries/index.html': ('Source libraries (every BMD)', 'Source libraries'), 'Unknown/index.html': ('Unknown assets', 'Unknown'),
               'Shared/Shadows/index.html': ('Shadows (animals)', 'Shadows'), 'Metadata/Evidence/index.html': ('Evidence and loose files', 'Loose files'),
               'Catalogs/index.html': ('Catalogs', 'Loose files')})
for t, folder in TF.items():
    for sub in ('Buildings', 'Humans', 'Vehicles', 'Construction', 'Effects', 'Shadows'):
        byroute.setdefault(f'{folder}/{sub}/index.html', [])
tribe_goods = {}
for t, folder in TF.items():
    gi = ROOT / folder / 'Goods/index.json'
    ids = {f"good:{g['goodId']}" for g in read(gi)['goods']} if gi.exists() else set()
    tribe_goods[t] = [r for r in X if r['ASSET_ID'] in ids]
    byroute[f'{folder}/Goods/index.html'] = tribe_goods[t]
UNK_NOTE = '<p class="note">Unknown items stay visible: each row keeps its native reason (UNKNOWN_CLASS / sub-reason) and a link to the full source atlas. ' \
           'See <a href="../Unknown/census_summary.json">census_summary.json</a> and Catalogs/unknown_assets.csv.</p>'
for route, rows in byroute.items():
    if route in DETAIL_ROUTES or route in written or route == 'Catalogs/index.html' or route == 'Metadata/Evidence/index.html':
        continue
    title, cat = TITLES.get(route, (Path(route).parent.as_posix(), rows[0]['CATEGORY'] if rows else ''))
    extra = UNK_NOTE.replace('../', depth_prefix(route)) if route == 'Unknown/index.html' else ''
    if route.endswith('/Goods/index.html') and route != 'Shared/Goods/index.html':
        extra = '<p class="note">Goods are one shared native table (goodtypes.cif). This page lists the goods this tribe allows (tribetypes.cif allowgood); visuals live in Shared/Goods.</p>'
    if route == 'Audio/index.html':
        extra = '<p class="note">WAV files are bit-exact archive copies (playable). DirectMusic .sgt/.dls stay in DataX\\DM2 and are catalogued only (no browser playback).</p>'
    if route == 'FMV/index.html':
        extra = '<p class="note">Originals left in place (MPEG-1 system streams, not playable in most browsers). No decoder available here, so no thumbnails were generated.</p>'
    page_js(route, title, rows, cat, extra)
    PAGES.add(route)

# shared all-tribe lists
for sub, cat in (('Humans', 'Humans'), ('Vehicles', 'Vehicles'), ('Construction', 'Construction')):
    page_js(f'Shared/{sub}/index.html', f'{sub} (all tribes)', [r for r in X if r['CATEGORY'] == cat], cat)

# ---------------------------------------------------------------- source atlas viewer
VIEWER = '''<div class="bar"><select id="lib"></select> <input id="fq" type="search" placeholder="filter frames: BOB id, status, usage, sequence"></div>
<div id="info"></div><div id="frames"></div>
<script>
(function(){
 var libs=window.LIBS||[];var sel=document.getElementById('lib');
 sel.innerHTML=libs.map(function(l){return '<option value="'+l[0]+'">'+l[1]+' ('+l[2]+' frames)</option>'}).join('');
 function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
 function show(){var L=window.LIBRARY;if(!L)return;var q=document.getElementById('fq').value.toLowerCase().split(/\\s+/).filter(Boolean);
  var slug=sel.value;var pal=L.palettes&&L.palettes.length?L.palettes[0]:null;
  document.getElementById('info').innerHTML='<div class="kv"><b>library</b><span>'+esc(L.library)+'</span><b>archive entry</b><span>'+esc(L.source.entryId)+' offset '+esc(L.source.offset)+' sha256 '+esc(L.source.sha256)+'</span><b>decoder</b><span>'+esc(L.decoder)+'</span><b>descriptors / non-empty / mapped</b><span>'+L.frameDescriptors+' / '+L.nonemptyFrames+' / '+L.mappedFrames+'</span><b>status counts</b><span>'+esc(JSON.stringify(L.statusCounts))+'</span><b>palettes</b><span>'+esc((L.palettes||[]).join(', ')||'none (index data only)')+'</span><b>representation</b><span>'+esc(JSON.stringify(L.representation))+'</span></div><p><a href="'+slug+'/library.json">library.json</a></p>';
  var out=[],n=0;L.frames.forEach(function(f){var t=(f.bobId+' '+f.status+' '+(f.reason||'')+' '+(f.usage||[]).join(' ')+' '+(f.bobSeq||[]).join(' ')).toLowerCase();
   for(var i=0;i<q.length;i++)if(t.indexOf(q[i])<0)return; if(++n>400)return;
   var img=f.page==null?'':slug+'/page_'+('000'+f.page).slice(-4)+(pal?'__'+pal.replace(/[^\\w.-]+/g,'_'):'_index_data')+'.png';
   var r=f.rect||[0,0,0,0],s=Math.min(1,96/Math.max(r[2],r[3],1));
   out.push('<tr id="bob'+f.bobId+'"><td class="th">'+(img?'<div class="crop" style="width:'+Math.ceil(r[2]*s)+'px;height:'+Math.ceil(r[3]*s)+'px"><div style="width:'+r[2]+'px;height:'+r[3]+'px;transform:scale('+s+');transform-origin:0 0;background:url(\\''+encodeURI(img)+'\\') -'+r[0]+'px -'+r[1]+'px"></div></div>':'(no pixels)')+'</td><td>BOB '+f.bobId+'</td><td>kind '+f.kind+'</td><td>'+f.width+'x'+f.height+'<br>pivot '+esc(f.pivot)+'</td><td><span class="status">'+esc(f.status)+'</span><div class="sub">'+esc(f.reason||'')+'</div></td><td>'+esc((f.usage||[]).join(', '))+'<div class="sub">'+esc((f.bobSeq||[]).join(' | '))+'</div></td><td>'+(f.page==null?'':'<a href="'+encodeURI(slug+'/page_'+('000'+f.page).slice(-4)+'_index_data.png')+'">index page</a>')+'</td></tr>')});
  document.getElementById('frames').innerHTML='<p>'+n+' matching frames'+(n>400?' (first 400 shown)':'')+'</p><table class="grid"><tr><th>frame</th><th>BOB</th><th>kind</th><th>size</th><th>status</th><th>usage / BobSeq</th><th>page</th></tr>'+out.join('')+'</table>';}
 function load(){var slug=sel.value;location.hash=slug;window.LIBRARY=null;var s=document.createElement('script');s.src=encodeURI(slug+'/library.js');s.onload=show;document.head.appendChild(s);}
 var h=decodeURIComponent(location.hash.slice(1));if(h){sel.value=h}
 sel.addEventListener('change',load);document.getElementById('fq').addEventListener('input',show);load();
})();
</script>'''
libs = sorted([[slug(stem(r['ENTRY'])), r['DISPLAY_NAME'], r['FRAMES']] for r in X if r['CATEGORY'] == 'Source libraries'], key=lambda l: l[1].lower())
for l in libs:
    l[0] = l[0].lower() if (ROOT / 'Shared/SourceLibraries' / l[0].lower()).exists() else l[0]
(ROOT / 'Shared/SourceLibraries/viewer_libs.js').write_text('window.LIBS=' + json.dumps(libs) + ';', encoding='utf-8')
(ROOT / 'Shared/SourceLibraries/viewer_data.js').write_text('window.PAGE=' + json.dumps({'root': '../../', 'crumbs': [['Home', 'index.html'], ['Shared', 'Shared/index.html'], ['SourceLibraries', 'Shared/SourceLibraries/index.html'], ['Atlas viewer', '']]}) + ';', encoding='utf-8')
shell('Shared/SourceLibraries/viewer.html', 'Source atlas viewer', VIEWER, scripts=['viewer_libs.js', 'viewer_data.js'])

# ---------------------------------------------------------------- hubs
cnt = collections.Counter(r['CATEGORY'] for r in X)
for t, folder in TF.items():
    n = collections.Counter(r['CATEGORY'] for r in X if r['TRIBE'] == TNAME[t])
    hub(f'{folder}/index.html', TNAME[t], [
        ('Buildings', f'{folder}/Buildings/index.html', f"{n['Buildings']} house levels"),
        ('Humans', f'{folder}/Humans/index.html', f"{n['Humans']} jobs, {n['Human animation']} animation bindings"),
        ('Vehicles', f'{folder}/Vehicles/index.html', f"{n['Vehicles']} vehicle records"),
        ('Goods', f'{folder}/Goods/index.html', f"{len(tribe_goods[t])} allowed goods (shared visuals)"),
        ('Construction', f'{folder}/Construction/index.html', f"{n['Construction']} construction sets"),
        ('Effects', f'{folder}/Effects/index.html', f"{n['Effects']} effect point sets"),
        ('Shadows', f'{folder}/Shadows/index.html', f"{n['Shadows']} shadow masks")], intro=f'Native tribe ID {t}.')
hub('Other Tribes/index.html', 'Other native tribes', [(TNAME[t], f'{TF[t]}/index.html', f'tribe ID {t}') for t in (5, 6, 7)] +
    [('Animal tribes (8..41)', 'Animals/index.html', 'animal species are native tribe IDs 8..41')])
hub('Shared/index.html', 'Shared', [
    ('Humans (all tribes)', 'Shared/Humans/index.html', f"{cnt['Humans']} jobs"), ('Vehicles (all tribes)', 'Shared/Vehicles/index.html', f"{cnt['Vehicles']} records"),
    ('Goods', 'Shared/Goods/index.html', f"{cnt['Goods']} goods"), ('Animals', 'Animals/index.html', f"{cnt['Animals']} records"),
    ('Landscapes', 'Terrain/Landscapes/index.html', f"{cnt['Landscapes']} definitions"), ('Effects', 'Shared/Effects/index.html', f"{cnt['Effects']} records"),
    ('Source libraries', 'Shared/SourceLibraries/index.html', f"{cnt['Source libraries']} BMD atlases"), ('Atlas viewer', 'Shared/SourceLibraries/viewer.html', 'every frame of every BMD'),
    ('Shadows (animals)', 'Shared/Shadows/index.html', 'tribe shadows are on each tribe page'), ('Construction (all tribes)', 'Shared/Construction/index.html', f"{cnt['Construction']} sets")])
hub('Terrain/index.html', 'Terrain', [('Landscape definitions', 'Terrain/Landscapes/index.html', f"{cnt['Landscapes']} GfxLandscape"),
                                      ('Patterns', 'Terrain/Patterns/index.html', '927 GfxPattern triangles'), ('Transitions', 'Terrain/Transitions/index.html', '38 transitions'),
                                      ('Textures', 'Terrain/Textures/index.html', 'pattern/transition PCX textures')])
hub('UI/index.html', 'UI', [('Sprites', 'UI/Sprites/index.html', f"{cnt['UI']} GUI sprites (palette evidenced or index data)"), ('Fonts', 'UI/Fonts/index.html', f"{cnt['Fonts']} FNT entries"),
                            ('Images', 'UI/Images/index.html', 'GUI bitmaps, pictures, hypertext and map images'), ('Cursors', 'UI/Cursors/index.html', 'Mouse .cur files'),
                            ('Palettes', 'Metadata/Palettes/index.html', f"{cnt['Palettes']} palette PCX")])
cat_files = sorted(p.name for p in C.iterdir() if p.suffix in ('.csv', '.json') and p.name != 'index_data.js')
body = '<table class="grid"><tr><th>catalog</th><th>size</th></tr>' + ''.join(f'<tr><td><a href="{quote(n)}">{E(n)}</a></td><td>{(C / n).stat().st_size:,} bytes</td></tr>' for n in cat_files) + '</table>'
(C / 'index_data.js').write_text('window.PAGE=' + json.dumps({'root': '../', 'crumbs': [['Home', 'index.html'], ['Catalogs', '']]}) + ';', encoding='utf-8')
shell('Catalogs/index.html', 'Catalogs', body, scripts=['index_data.js'])
ev = sorted([p for p in (ROOT / 'Metadata/Evidence').rglob('*') if p.is_file() and p.suffix in ('.json', '.txt', '.md', '.cpp')] +
            [p for p in ROOT.glob('*.md')] + [p for p in ROOT.glob('*.txt')] + list((ROOT / 'Metadata/Exporter').rglob('*.py')) + list((ROOT / 'Metadata/Exporter').rglob('*.cpp')), key=lambda p: rel(p))
evrows = byroute.get('Metadata/Evidence/index.html', [])
body = '<h2>Reports, hashes, validation, exporter sources</h2><table class="grid">' + ''.join(f'<tr><td><a href="{u(rel(p), "Metadata/Evidence/index.html")}">{E(rel(p))}</a></td></tr>' for p in ev) + '</table>'
body += '<h2>Original binaries and other loose files</h2><table class="grid">' + ''.join(f"<tr id=\"{E(r['ASSET_ID'])}\"><td>{E(r['NATIVE_NAME'])}</td><td>{E(r['SUBCATEGORY'])}</td><td>{E(r['STATUS'])}</td></tr>" for r in evrows) + '</table>'
(ROOT / 'Metadata/Evidence/index_data.js').write_text('window.PAGE=' + json.dumps({'root': '../../', 'crumbs': [['Home', 'index.html'], ['Metadata', ''], ['Evidence', '']]}) + ';', encoding='utf-8')
shell('Metadata/Evidence/index.html', 'Evidence', body, scripts=['index_data.js'])

# ---------------------------------------------------------------- search index (compact: lookup tables for paths/categories/tribes/statuses)
PT, PI, CT, CI, TT, TI, ST, SI = [], {}, [], {}, [], {}, [], {}


def ix(v, tab, idx):
    if v not in idx:
        idx[v] = len(tab)
        tab.append(v)
    return idx[v]


S = []
for r in X:
    if r['CATEGORY'] == 'Shadows':
        continue  # listed on Shadows pages and owner pages; omitted from the global index to keep it small
    ids = []
    for k, lab in (('GFX_ID', 'gfxhouse ' if r['CATEGORY'] in ('Buildings', 'Construction') else 'gfx '), ('LOGIC_ID', 'logic '), ('JOB_ID', 'job '), ('GOOD_ID', 'good '),
                   ('VEHICLE_TYPE', 'vehicletype '), ('ATOMIC_ID', 'atomic '), ('ANIMAL_TRIBE', 'tribe ')):
        if r[k]:
            ids.append(lab + r[k])
    bob = r['BOB']
    if bob and not bob.startswith('['):
        ids.append('bob ' + bob)
    elif bob.startswith('[') and len(bob) < 200:
        ids += ['bob ' + b_.strip() for b_ in bob.strip('[]').split(',') if b_.strip()]
    extra = ''
    if r['CATEGORY'] == 'Goods' and r['METADATA']:
        extra = str(read(ROOT / r['METADATA']).get('englishPlural', ''))
    if r['CATEGORY'] == 'Unknown':
        parts = [r['ASSET_ID'], 'unknown', r['UNKNOWN_CLASS'], r['SUBCATEGORY'].split(':')[-1], r['BOBSEQ'] if r['BOBSEQ'] != '[]' else '', r['BMD'] + '.bmd' if r['BMD'] else r['NATIVE_NAME'][:160]] + ids
    else:
        parts = [r['ASSET_ID'], r['CATEGORY'], r['SUBCATEGORY'], r['TRIBE'], r['NATIVE_NAME'], r['DISPLAY_NAME'], r['ATOMIC_NAME'], r['BOBSEQ'], r['BMD'],
                 (r['BMD'] + '.bmd') if r['BMD'] else '', '' if r['BMD'] else r['ENTRY'], r['STATUS'], r['UNKNOWN_CLASS'], extra] + ids
    seen_, text = set(), []
    for x in parts:
        x = str(x).lower()
        if x and x not in seen_:
            seen_.add(x)
            text.append(x)
    if r['BROWSER_ROUTE'] in DETAIL_ROUTES:
        page_, mode = r['BROWSER_ROUTE'], 1          # page#<asset id>
    elif r['DETAIL_PAGE']:
        page_, mode = r['DETAIL_PAGE'], 0
    else:
        page_, mode = r['BROWSER_ROUTE'], 2          # page#q=<asset id>
    label = r['DISPLAY_NAME'] or r['NATIVE_NAME']
    S.append([r['ASSET_ID'], '' if label == r['ASSET_ID'] else label, ' | '.join(text), ix(r['CATEGORY'], CT, CI), ix(r['TRIBE'], TT, TI), ix(r['STATUS'], ST, SI),
              ix(page_, PT, PI), ix(r['THUMB'], PT, PI) if r['THUMB'] else -1, r['THUMB_RECT'], mode])
(ROOT / 'Metadata/Browser/search_index.js').write_text('window.SEARCHDB=' + json.dumps({'paths': PT, 'cats': CT, 'tribes': TT, 'status': ST, 'rows': S},
                                                                                        ensure_ascii=False, separators=(',', ':')) + ';', encoding='utf-8')

# ---------------------------------------------------------------- home
summ = read(C / 'catalog_summary.json')
census = read(ROOT / 'Unknown/census_summary.json')
cards = [('Vikings', 'Vikings/index.html', 'tribe 1'), ('Franks', 'Franks/index.html', 'tribe 2'), ('Byzantines', 'Byzantines/index.html', 'tribe 3'),
         ('Saracens / Arabs', 'Arabs/index.html', 'tribe 4 (native name saracen)'), ('Egypt', 'Other Tribes/Egypt/index.html', 'tribe 7'),
         ('Weresnake', 'Other Tribes/Weresnakes/index.html', 'tribe 5'), ('Werewolf', 'Other Tribes/Werewolves/index.html', 'tribe 6'),
         ('Animals', 'Animals/index.html', 'tribe IDs 8..41'), ('Shared', 'Shared/index.html', 'humans, vehicles, goods, effects, source libraries, shadows, construction'),
         ('Goods', 'Shared/Goods/index.html', '65 native goods'), ('Effects', 'Shared/Effects/index.html', 'particles, markers, landscape and building effects'),
         ('Terrain', 'Terrain/index.html', 'landscapes, patterns, transitions, textures'), ('UI', 'UI/index.html', 'sprites, fonts, images, cursors, palettes'),
         ('Audio', 'Audio/index.html', f"{cnt['Audio']} files"), ('FMV', 'FMV/index.html', '2 MPEG files'), ('Fonts', 'UI/Fonts/index.html', f"{cnt['Fonts']} FNT entries"),
         ('Source libraries', 'Shared/SourceLibraries/index.html', f"{census['bmdLibraries']} BMD, {census['nonemptyFrames']} non-empty frames"),
         ('Atlas viewer', 'Shared/SourceLibraries/viewer.html', 'every frame, every BMD'), ('Native definitions', 'Metadata/Sources/index.html', 'CIF tables, HLT, map DAT, TXT'),
         ('Catalogs', 'Catalogs/index.html', 'CSV / JSON catalogs'), ('Unknown', 'Unknown/index.html', f"{summ['byStatus'].get('UNKNOWN', 0)} documented unknown items"),
         ('Evidence', 'Metadata/Evidence/index.html', 'reports, hashes, validation, exporter sources')]
stat = ''.join(f'<b>{E(k)}</b><span>{v}</span>' for k, v in sorted(summ['byStatus'].items()))
body = ('<section><div id="search"></div></section><div class="cards">' + ''.join(f'<div class="card"><h3><a href="{u(l, "index.html")}">{E(n)}</a></h3><p>{E(d)}</p></div>' for n, l, d in cards) +
        f'</div><section><h2>Library status</h2><div class="kv"><b>catalogued assets</b><span>{summ["rows"]}</span>{stat}<b>archive entries accounted</b><span>{summ["archiveEntries"]} / {summ["archiveEntries"]}'
        f' (unaccounted {len(summ["archiveUnaccounted"])})</span><b>BMD frames</b><span>{census["nonemptyFrames"]} non-empty: {census["mappedFrames"]} mapped, {census["namedSequenceUnbound"]} named-sequence unbound, '
        f'{census["trueUnknownUnreferenced"]} unreferenced, {census["unsupportedKindFrames"]} unsupported kind</span><b>pixel validation</b><span>{summ["pixelValidation"]["framesConfirmed"]} confirmed, {summ["pixelValidation"]["mismatch"]} mismatches</span></div>'
        '<p class="sub">Viking Farm base: MANUAL_CONFIRMED_1TO1 (user confirmation). Previews never upscale, recolour or redraw original pixels; PRESENTATION_* statuses mark where native runtime composition is not reproduced.</p></section>')
(ROOT / 'index_data.js').write_text('window.PAGE=' + json.dumps({'root': '', 'crumbs': [['Home', '']]}) + ';', encoding='utf-8')
shell('index.html', 'Home', body, scripts=['index_data.js'])
print('pages written', len(written), 'search rows', len(S), 'detail routes', len(DETAIL_ROUTES))
