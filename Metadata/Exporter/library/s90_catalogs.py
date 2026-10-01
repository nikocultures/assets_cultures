"""Stage 90: rebuild all machine-readable catalogs + the master cross-reference from current exports.

STATUS (primary, one of): SOURCE_COMPLETE, PIXEL_CONFIRMED, MANUAL_CONFIRMED_1TO1, PARTIAL, PRESENTATION_PARTIAL,
PRESENTATION_APPROXIMATION, UNKNOWN.  PRESENTATION and CONFIDENCE columns keep the finer claims.
Every row carries ASSET_ID and BROWSER_ROUTE (page that lists it; the browser data for that page is generated from
these same rows, so route membership is exact).
"""
import collections, csv, glob
from common import *

C = ROOT / 'Catalogs'
TF = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Arabs', 5: 'Other Tribes/Weresnakes', 6: 'Other Tribes/Werewolves', 7: 'Other Tribes/Egypt'}
TNAME = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Saracens (Arabs)', 5: 'Weresnakes', 6: 'Werewolves', 7: 'Egypt'}


def rcsv(p):
    p = Path(p)
    if not p.exists():
        return []
    with p.open(encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def J(v):
    try:
        return json.loads(v) if isinstance(v, str) and v[:1] in '[{' else v
    except Exception:
        return v


def both(name, rows, fields=None):
    csvout(C / f'{name}.csv', rows, fields)
    write(C / f'{name}.json', rows, compact=True)


XF = ['ASSET_ID', 'CATEGORY', 'SUBCATEGORY', 'TRIBE_ID', 'TRIBE', 'NATIVE_NAME', 'DISPLAY_NAME', 'LOGIC_ID', 'GFX_ID', 'JOB_ID', 'GOOD_ID', 'VEHICLE_TYPE',
      'ANIMAL_TRIBE', 'ATOMIC_ID', 'ATOMIC_NAME', 'BOBSEQ', 'ARCHIVE', 'ENTRY', 'BMD', 'BOB', 'PALETTE', 'SHADOW', 'PIVOT', 'WIDTH', 'HEIGHT',
      'DIRECTIONS', 'FRAMES', 'TIMING', 'RELATED_HOUSE', 'RELATED_HUMAN', 'RELATED_GOOD', 'RELATED_VEHICLE', 'STATUS', 'PRESENTATION', 'CONFIDENCE',
      'UNKNOWN_CLASS', 'OUTPUT', 'THUMB', 'THUMB_RECT', 'METADATA', 'ATLAS', 'EVIDENCE', 'BROWSER_ROUTE', 'DETAIL_PAGE']
X = []


def add(**k):
    row = {f: k.get(f, '') for f in XF}
    for f, v in row.items():
        if isinstance(v, (list, dict)):
            row[f] = json.dumps(v, ensure_ascii=False)
        elif v is None:
            row[f] = ''
    X.append(row)
    return row


ARCH_S = str(ARCH)
LIBATLAS = {stem(r['LIBRARY']).lower(): r['ATLAS'] for r in rcsv(C / 'bmd_coverage.csv')}


def atlas(lib):
    return LIBATLAS.get(stem(lib).lower(), '') if lib else ''


# ================================================================ BUILDINGS
audit = {r['PNG']: r['STATUS'] for r in rcsv(C / 'building_pixel_audit.csv')}
houses = rcsv(C / 'houses.csv')
hrows = []
for h in houses:
    t = int(h['TRIBE'])
    meta = read(ROOT / h['METADATA']) if h['METADATA'] and (ROOT / h['METADATA']).exists() else {}
    farm = h['GFX_ID'] == '4' and h['LEVEL'] == '0'
    pix = audit.get(h['OUTPUT_PATH'] or '', '')
    status = 'PARTIAL' if h['SOURCE_EXPORT'] != 'COMPLETE' else 'MANUAL_CONFIRMED_1TO1' if farm else 'PIXEL_CONFIRMED' if pix == 'PIXEL_CONFIRMED' else 'SOURCE_COMPLETE'
    h2 = dict(h, TRIBE_NAME=TNAME[t], BODY_PIXEL_AUDIT=pix or 'NOT_APPLICABLE', STATUS=status, PRESENTATION='PRESENTATION_PARTIAL',
              ERRORS=meta.get('errors', []), BROWSER_ROUTE=f'{TF[t]}/Buildings/index.html')
    hrows.append(h2)
    add(ASSET_ID=f"bld:{h['GFX_ID']}:{h['LEVEL']}", CATEGORY='Buildings', SUBCATEGORY='House level', TRIBE_ID=t, TRIBE=TNAME[t], NATIVE_NAME=h['NAME'],
        DISPLAY_NAME=f"{h['NAME']} L{h['LEVEL']}", LOGIC_ID=h['LOGIC_ID'], GFX_ID=h['GFX_ID'], ENTRY=h['MAIN_LIBRARY'], BMD=stem(h['MAIN_LIBRARY']), BOB=h['BOB_ID'],
        PALETTE=meta.get('paletteAlternatives', []), SHADOW=f"{h['SHADOW_LIBRARY']} BOB {h['SHADOW_BOB_ID']}" if h['SHADOW_LIBRARY'] else '',
        PIVOT=[h['PIVOT_X'], h['PIVOT_Y']], WIDTH=h['WIDTH'], HEIGHT=h['HEIGHT'], TIMING='overlay ticksPerFrame in animation/animation.json',
        STATUS=status, PRESENTATION='PRESENTATION_PARTIAL', CONFIDENCE=f"body pixel audit: {pix or 'n/a'}; source export {h['SOURCE_EXPORT']}" + ('; MANUAL_CONFIRMED_1TO1 (user, 2026-10-01)' if farm else ''),
        OUTPUT=h['OUTPUT_PATH'], THUMB=h['OUTPUT_PATH'], METADATA=h['METADATA'], ATLAS=atlas(h['MAIN_LIBRARY']), ARCHIVE=ARCH_S,
        EVIDENCE='houses.cif GfxHouse; Game 0x00495B57/0x0049B930; Editor 0x0044543D', BROWSER_ROUTE=f'{TF[t]}/Buildings/index.html',
        DETAIL_PAGE=str(Path(h['METADATA']).parent.as_posix()) + '/index.html' if h['METADATA'] else '')
    lvl = Path(h['METADATA']).parent if h['METADATA'] else None
    if lvl is not None and meta.get('constructionLayers'):
        snaps = meta.get('constructionSnapshots') or []
        add(ASSET_ID=f"con:{h['GFX_ID']}:{h['LEVEL']}", CATEGORY='Construction', SUBCATEGORY='House construction', TRIBE_ID=t, TRIBE=TNAME[t], NATIVE_NAME=h['NAME'],
            DISPLAY_NAME=f"{h['NAME']} L{h['LEVEL']} construction", GFX_ID=h['GFX_ID'], LOGIC_ID=h['LOGIC_ID'], BMD=stem(h['MAIN_LIBRARY']),
            BOB=[x[2] for x in meta['constructionLayers']], STATUS='PARTIAL' if status == 'PARTIAL' else 'PRESENTATION_PARTIAL', PRESENTATION='PRESENTATION_PARTIAL',
            CONFIDENCE='native tuples + reveal planes exported; progress snapshots are body-only, checkerboard previews are PREVIEW',
            OUTPUT=snaps[-1]['path'] if snaps else '', THUMB=snaps[2]['path'] if len(snaps) > 2 else (snaps[-1]['path'] if snaps else ''),
            METADATA=(lvl / 'construction/metadata.json').as_posix(), ATLAS=atlas(h['MAIN_LIBRARY']), EVIDENCE='0x00495B57 / 0x0049DA62 / 0x0049E618',
            BROWSER_ROUTE=f'{TF[t]}/Construction/index.html', DETAIL_PAGE=lvl.as_posix() + '/index.html')
    if lvl is not None and (meta.get('shadow') or {}).get('path'):
        sp = meta['shadow']['path']
        add(ASSET_ID=f"shd:bld:{h['GFX_ID']}:{h['LEVEL']}", CATEGORY='Shadows', SUBCATEGORY='House shadow coverage', TRIBE_ID=t, TRIBE=TNAME[t], NATIVE_NAME=h['NAME'],
            DISPLAY_NAME=f"{h['NAME']} L{h['LEVEL']} shadow", GFX_ID=h['GFX_ID'], ENTRY=h['SHADOW_LIBRARY'], BMD=stem(h['SHADOW_LIBRARY']), BOB=h['SHADOW_BOB_ID'],
            STATUS='PRESENTATION_APPROXIMATION', PRESENTATION='PRESENTATION_APPROXIMATION', CONFIDENCE='coverage mask DATA; native destination darkening 0x0049B930',
            OUTPUT=sp, THUMB=sp, METADATA=(lvl / 'shadow/metadata.json').as_posix(), ATLAS=atlas(h['SHADOW_LIBRARY']), RELATED_HOUSE=f"bld:{h['GFX_ID']}:{h['LEVEL']}",
            BROWSER_ROUTE=f'{TF[t]}/Shadows/index.html', DETAIL_PAGE=lvl.as_posix() + '/index.html')
    fx = read(ROOT / lvl / 'effects/metadata.json') if lvl is not None and (ROOT / lvl / 'effects/metadata.json').exists() else {}
    npts = sum(len(fx.get(k, [])) for k in ('gfxfirepoint', 'gfxsmokepoint', 'gfxholyfirepoint', 'gfxoverlaylandscape'))
    if npts:
        add(ASSET_ID=f"fx:bld:{h['GFX_ID']}:{h['LEVEL']}", CATEGORY='Effects', SUBCATEGORY='House effect points', TRIBE_ID=t, TRIBE=TNAME[t], NATIVE_NAME=h['NAME'],
            DISPLAY_NAME=f"{h['NAME']} L{h['LEVEL']} effects ({npts} points)", GFX_ID=h['GFX_ID'], STATUS='PRESENTATION_PARTIAL', PRESENTATION='PRESENTATION_PARTIAL',
            CONFIDENCE='native fire/smoke/holy-fire points and linked shared effect definitions; activation runtime', METADATA=(lvl / 'effects/metadata.json').as_posix(),
            RELATED_HOUSE=f"bld:{h['GFX_ID']}:{h['LEVEL']}", BROWSER_ROUTE=f'{TF[t]}/Effects/index.html', DETAIL_PAGE=lvl.as_posix() + '/index.html')
both('houses', hrows)

# ================================================================ MOBILE (humans / animals / vehicles)
owners = {}
for p in glob.glob(str(ROOT / '**/metadata.json'), recursive=True):
    if '/Sheets/' in p.replace(B, '/') or 'SourceLibraries' in p:
        continue
    try:
        m = read(p)
    except Exception:
        continue
    if m.get('ownerKind') in ('human', 'animal', 'vehicle'):
        owners[(m['ownerKind'], m['tribeId'], m['typeId'])] = (m, rel(p))
human_rows, anim_rows = [], {'human': [], 'animal': [], 'vehicle': []}
owner_rows = {'human': [], 'animal': [], 'vehicle': []}
validated = set()
for p in glob.glob(str(ROOT / 'Metadata/Mobile/validation_*.json')):
    for v in read(p):
        if v['MISMATCH'] == 0 and v['OTHER'] == 0:
            validated.add((norm(v['LIBRARY']), v['PALETTE']))
LIBPATH = {stem(e.path).lower(): e.path for e in INDEX.entries if e.path.lower().endswith('.bmd')}
for (kind, tribe, typ), (m, mp) in sorted(owners.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])):
    folder = Path(mp).parent.as_posix()
    detail = folder + '/index.html'
    cat = {'human': 'Humans', 'animal': 'Animals', 'vehicle': 'Vehicles'}[kind]
    route = f'{TF[tribe]}/{cat}/index.html' if kind != 'animal' else 'Animals/index.html'
    tname = TNAME.get(tribe, m.get('tribeEnglish') or m.get('nativeTribe'))
    rs = collections.Counter(r['status'].split(':')[0].split(' (')[0] for a in m['animations'] for r in a['renders'])
    st = 'PARTIAL' if (not m['bindings'] or rs.get('RENDERED_PARTIAL_MISSING_BOBS')) else 'PIXEL_CONFIRMED'
    pres = 'PRESENTATION_APPROXIMATION' if kind == 'human' else 'PRESENTATION_PARTIAL'
    first = next((r for a in m['animations'] for r in a['renders'] if r.get('sheet')), {})
    orow = {'TRIBE_ID': tribe, 'TRIBE': tname, 'TYPE_ID': typ, 'ANIMATION_JOB_ID': m['animationJobId'], 'NATIVE_NAME': m['nativeName'], 'ENGLISH': m['englishName'],
            'SEX_AGE': m.get('sexAge'), 'NATIVE_ALLOWED': m['nativeAllowed'], 'PARENT_CHAIN': m['parentChain'],
            'BINDINGS': [{'phase': b['phase'], 'section': b['sectionOrdinal'], 'inheritedFrom': b['inheritedFrom'], 'body': [v['body'] for v in b['bodyVariants']],
                          'heads': [v['head'] for v in b['headVariants']], 'palettes': b['bodyPalettes'], 'headPalettes': b['headPalettes'], 'random': b['paletteRemaps']} for b in m['bindings']],
            'ANIMATIONS': len(m['animations']), 'RENDER_STATUS': dict(rs), 'ATOMICS_WITHOUT_GRAPHICS': len(m.get('atomicsWithoutGraphicsRecord', [])),
            'STATUS': st, 'PRESENTATION': pres, 'METADATA': mp, 'DETAIL_PAGE': detail, 'BROWSER_ROUTE': route}
    owner_rows[kind].append(orow)
    oid = f"{kind[:3]}:{tribe}:{typ}"
    add(ASSET_ID=oid, CATEGORY=cat, SUBCATEGORY={'human': 'Human job', 'animal': 'Animal life stage', 'vehicle': 'Vehicle type'}[kind], TRIBE_ID=tribe, TRIBE=tname,
        NATIVE_NAME=m['nativeName'], DISPLAY_NAME=m['englishName'] or m['nativeName'], JOB_ID=typ if kind != 'vehicle' else m['animationJobId'],
        VEHICLE_TYPE=typ if kind == 'vehicle' else '', ANIMAL_TRIBE=tribe if kind == 'animal' else '', BMD=sorted({stem(v['body']) for b in m['bindings'] for v in b['bodyVariants']}),
        PALETTE=sorted({p_ for b in m['bindings'] for p_ in b['bodyPalettes']}), STATUS=st, PRESENTATION=pres,
        CONFIDENCE=f"render status {dict(rs)}", THUMB=first.get('sheet', ''), OUTPUT=first.get('sheet', ''), METADATA=mp,
        EVIDENCE='jobgraphics.cif + animations.cif; Game 0x0048BD66/0x0048D027/0x00494AE6/0x004803D5', BROWSER_ROUTE=route, DETAIL_PAGE=detail)
    if kind == 'vehicle':
        add(ASSET_ID=f'vehdecl:{tribe}:{typ}:graphics', CATEGORY='Vehicles', SUBCATEGORY='Vehicle graphics binding', TRIBE_ID=tribe, TRIBE=tname,
            NATIVE_NAME=m['nativeName'], VEHICLE_TYPE=typ, STATUS=st, CONFIDENCE='native binding present', METADATA=mp, BROWSER_ROUTE=route, DETAIL_PAGE=detail) if False else None
    for a in m['animations']:
        dirs = {str(d['direction']): d.get('bodyBobs', d.get('status')) for d in a['directions']}
        heads = {str(d['direction']): d.get('headBobs') for d in a['directions'] if d.get('headBobs') and d.get('headBobs') != d.get('bodyBobs')}
        for r in a['renders']:
            b = next((x for x in m['bindings'] if x['phase'] == r['phase']), {})
            stt = r['status']
            if stt.startswith('RENDERED_PARTIAL'):
                s2 = 'PARTIAL'
            elif stt == 'RENDERED':
                s2 = 'PRESENTATION_APPROXIMATION' if '@' in (r.get('bodyPalette') or '') else 'PIXEL_CONFIRMED'
            elif stt.startswith('NO_DIRECT_FRAMES'):
                s2 = 'PRESENTATION_PARTIAL'
            else:
                s2 = 'SOURCE_COMPLETE'
            arow = {'TRIBE_ID': tribe, 'TRIBE': tname, 'OWNER_KIND': kind, 'TYPE_ID': typ, 'ANIMATION_JOB_ID': m['animationJobId'], 'JOB_NAME': m['nativeName'],
                    'JOB_ENGLISH': m['englishName'], 'SEX_AGE': m.get('sexAge'), 'BASE_JOB_CHAIN': m['parentChain'], 'ANIMATION_SECTION': a['animationSection'],
                    'DEFINED_FOR_JOB': a['definedForJob'], 'INHERITED': a['inherited'], 'KIND': a['kind'], 'ATOMIC_ID': a['atomicActionSelector'],
                    'ATOMIC_NAME': a['atomicName'], 'ATOMIC_LENGTH': a['atomicLength'], 'ATOMIC_EVENTS': a['atomicEvents'], 'CARRIED_GOOD': a['carriedGoodType'],
                    'CARRIED_GOOD_NAME': a['carriedGoodName'], 'IN_HOUSE_SUBID': a.get('inHouseSubId'), 'WALK_SPEED_THRESHOLD': a.get('walkSpeedThreshold'),
                    'MODE': a['mode'], 'BOBSEQ_BODY': a['bodySequence'], 'BOBSEQ_HEAD': a['headSequence'] or a['bodySequence'], 'PHASE': r['phase'],
                    'BODY_VARIANT': r['bodySelector'], 'BODY_BMD': r['bodyLibrary'], 'SHADOW_BMD': r['shadowLibrary'], 'HEAD_BMD_RENDERED': r['headLibrary'],
                    'HEAD_VARIANT_RENDERED': r.get('headSelectorRendered'), 'HEAD_VARIANTS': [f"{v['selector']}:{stem(v['head'])}" for v in b.get('headVariants', [])],
                    'BODY_PALETTE': r.get('bodyPalette'), 'HEAD_PALETTE': r.get('headPalette'), 'PALETTE_PROVENANCE': r.get('paletteProvenance'),
                    'RANDOM_PALETTES': b.get('paletteRemaps', []), 'DIRECTION_BODY_BOBS': dirs, 'DIRECTION_HEAD_BOBS': heads, 'TIMING': a['timing'],
                    'SHEET': r.get('sheet', ''), 'SHADOW_MASK': r.get('shadowMask', ''), 'CELL': [r.get('cellWidth'), r.get('cellHeight')] if r.get('cellWidth') else '',
                    'ANCHOR_IN_CELL': r.get('anchorInCell', ''), 'SHEET_ROWS_DIRECTIONS': r.get('sheetRows', ''), 'RENDER_STATUS': stt,
                    'NATIVE_COMPATIBILITY': 'COMPATIBLE' if stt.startswith('RENDERED') else stt, 'CELL_ISSUES': r.get('cellIssues', []), 'STATUS': s2,
                    'METADATA': mp, 'DETAIL_PAGE': detail}
            anim_rows[kind].append(arow)
            aid = f"{kind[:3]}anim:{tribe}:{typ}:{a['animationSection']}:{r['phase']}:{r['bodySelector']}"
            add(ASSET_ID=aid, CATEGORY={'human': 'Human animation', 'animal': 'Animal animation', 'vehicle': 'Vehicle animation'}[kind], SUBCATEGORY=a['kind'],
                TRIBE_ID=tribe, TRIBE=tname, NATIVE_NAME=m['nativeName'], DISPLAY_NAME=f"{m['englishName'] or m['nativeName']} | {a['atomicName'] or ('walk' + (' carrying ' + a['carriedGoodName'] if a['carriedGoodName'] else ''))}",
                JOB_ID=typ if kind != 'vehicle' else m['animationJobId'], VEHICLE_TYPE=typ if kind == 'vehicle' else '', ANIMAL_TRIBE=tribe if kind == 'animal' else '',
                ATOMIC_ID=a['atomicActionSelector'] if a['kind'] == 'atomic' else '', ATOMIC_NAME=a['atomicName'] or '', BOBSEQ=a['bodySequence'],
                GOOD_ID=a['carriedGoodType'] or '', BMD=stem(r['bodyLibrary']), PALETTE=r.get('bodyPalette'), SHADOW=r['shadowLibrary'],
                PIVOT=f"anchor {r.get('anchorInCell')}" if r.get('anchorInCell') else '', WIDTH=r.get('cellWidth', ''), HEIGHT=r.get('cellHeight', ''),
                DIRECTIONS=len([d for d in a['directions'] if d.get('bodyBobs')]), FRAMES=sum(len(d.get('bodyBobs', [])) for d in a['directions']), TIMING=a['timing'],
                RELATED_HUMAN=oid if kind == 'human' else '', RELATED_GOOD=f"good:{a['carriedGoodType']}" if a['carriedGoodType'] else '', RELATED_VEHICLE=oid if kind == 'vehicle' else '',
                STATUS=s2, PRESENTATION='PRESENTATION_APPROXIMATION' if kind == 'human' else 'PRESENTATION_PARTIAL', CONFIDENCE=stt + ('; ' + r.get('paletteProvenance', '') if r.get('paletteProvenance') else ''),
                OUTPUT=r.get('sheet', ''), THUMB=r.get('sheet', ''), METADATA=mp, ATLAS=atlas(r['bodyLibrary']),
                EVIDENCE=f"animations.cif section {a['animationSection']}", BROWSER_ROUTE=detail, DETAIL_PAGE=detail)
            if r.get('shadowMask'):
                add(ASSET_ID='shd:' + aid, CATEGORY='Shadows', SUBCATEGORY=f'{kind} shadow mask', TRIBE_ID=tribe, TRIBE=tname, NATIVE_NAME=m['nativeName'],
                    DISPLAY_NAME=f"{m['englishName'] or m['nativeName']} | {a['atomicName'] or 'walk'} shadow", BOBSEQ=a['bodySequence'], BMD=stem(r['shadowLibrary']),
                    STATUS='PRESENTATION_APPROXIMATION', PRESENTATION='PRESENTATION_APPROXIMATION', CONFIDENCE='kind-2 coverage mask; native destination darkening 0x0049B930',
                    OUTPUT=r['shadowMask'], THUMB=r['shadowMask'], METADATA=mp, ATLAS=atlas(r['shadowLibrary']), RELATED_HUMAN=oid if kind == 'human' else '',
                    BROWSER_ROUTE=(f'{TF[tribe]}/Shadows/index.html' if kind != 'animal' else 'Shared/Shadows/index.html'), DETAIL_PAGE=detail)
both('humans', owner_rows['human'])
both('human_job_atomic_animation', anim_rows['human'])
both('animals', owner_rows['animal'] + [dict(r, STATUS='UNKNOWN', NATIVE_DECLARATION='NATIVE_DECLARATION_NO_GRAPHICS') for r in rcsv(ROOT / 'Metadata/Mobile/atomics_without_graphics_animal.csv') if r['STATUS'].startswith('NO_GRAPHICS')])
both('animal_animations', anim_rows['animal'])
VT = {scalar(b, 'type'): b for b in cif(r'data\logic\vehicletypes.cif')}
veh = []
for r in owner_rows['vehicle']:
    veh.append(dict(r, VEHICLE_DEFINITION=VT[r['TYPE_ID']], NATIVE_DECLARATION='GRAPHICS_BOUND'))
for r in rcsv(ROOT / 'Metadata/Mobile/atomics_without_graphics_vehicle.csv'):
    t, vt = int(r['TRIBE_ID']), int(r['TYPE_ID'])
    if r['STATUS'].startswith('NO_GRAPHICS'):
        veh.append({'TRIBE_ID': t, 'TRIBE': TNAME[t], 'TYPE_ID': vt, 'ANIMATION_JOB_ID': vt + 49, 'NATIVE_NAME': scalar(VT[vt], 'name'),
                    'NATIVE_DECLARATION': 'NATIVE_DECLARATION_NO_GRAPHICS', 'STATUS': 'UNKNOWN', 'VEHICLE_DEFINITION': VT[vt],
                    'NOTE': 'tribe declares/allows the vehicle type, but vehicles/jobgraphics.cif has no binding and animations.cif no record; no preview created',
                    'BROWSER_ROUTE': f'{TF[t]}/Vehicles/index.html'})
        add(ASSET_ID=f'vehdecl:{t}:{vt}', CATEGORY='Vehicles', SUBCATEGORY='Native declaration without graphics', TRIBE_ID=t, TRIBE=TNAME[t], NATIVE_NAME=scalar(VT[vt], 'name'),
            VEHICLE_TYPE=vt, JOB_ID=vt + 49, STATUS='UNKNOWN', UNKNOWN_CLASS='UNKNOWN_GRAPHICS_BINDING', CONFIDENCE='NATIVE_DECLARATION_NO_GRAPHICS',
            METADATA='Metadata/Mobile/atomics_without_graphics_vehicle.csv', EVIDENCE='vehicletypes.cif; tribetypes.cif allowvehicle; vehicles/jobgraphics.cif',
            BROWSER_ROUTE=f'{TF[t]}/Vehicles/index.html')
both('vehicles', veh)
both('vehicle_animations', anim_rows['vehicle'])

# ================================================================ GOODS
for g in rcsv(C / 'goods.csv'):
    gid = int(g['GOOD_ID'])
    folder = Path(g['METADATA']).parent.as_posix()
    add(ASSET_ID=f'good:{gid}', CATEGORY='Goods', SUBCATEGORY='Good', NATIVE_NAME=g['NATIVE_NAME'], DISPLAY_NAME=f"Good {gid} {g['ENGLISH']}",
        GOOD_ID=gid, LOGIC_ID=g['LANDSCAPE_TYPE'], GFX_ID=g['GFX_LANDSCAPE'], BMD=stem(g['BMD']) if g['BMD'] else '', BOB=g['ICON_BOB'], PALETTE=J(g['PALETTE']) or '',
        STATUS='PIXEL_CONFIRMED' if g['ICON_PATH'] else 'SOURCE_COMPLETE', PRESENTATION='PRESENTATION_PARTIAL' if g['ICON_PATH'] else '',
        CONFIDENCE=g['CONFIDENCE'] + ('' if g['ICON_PATH'] else '; no native visual (landscape type void)'), OUTPUT=g['ICON_PATH'], THUMB=g['ICON_PATH'],
        METADATA=g['METADATA'], ATLAS=atlas(g['BMD']) if g['BMD'] else '', EVIDENCE='goodtypes.cif; Game 0x00415565 / 0x004E2661',
        RELATED_HUMAN=f"{g['CARRIED_ANIMATIONS']} carried-walk animations", BROWSER_ROUTE='Shared/Goods/index.html', DETAIL_PAGE=folder + '/index.html')

# ================================================================ LANDSCAPES / TERRAIN / EFFECTS
for l in rcsv(C / 'landscapes.csv'):
    goods = J(l['GOODS']) or []
    add(ASSET_ID=f"land:{l['GFX_LANDSCAPE_ID']}", CATEGORY='Landscapes', SUBCATEGORY=(J(l['EDIT_GROUPS']) or [['']])[0][0] if J(l['EDIT_GROUPS']) else '',
        NATIVE_NAME=l['NATIVE_NAME'], DISPLAY_NAME=l['NATIVE_NAME'], LOGIC_ID=l['LOGIC_TYPE'], GFX_ID=l['GFX_LANDSCAPE_ID'], ENTRY=l['BODY_LIBRARY'],
        BMD=stem(l['BODY_LIBRARY']) if l['BODY_LIBRARY'] else '', BOB=J(l['BOBS']), PALETTE=l['PALETTE'], SHADOW=l['SHADOW_LIBRARY'], PIVOT=J(l['PIVOT']) or '',
        WIDTH=l['WIDTH'], HEIGHT=l['HEIGHT'], FRAMES=l['FRAMES'], RELATED_GOOD=[f'good:{x}' for x in goods],
        STATUS='PARTIAL' if l['CONFIDENCE'] != 'SOURCE_COMPLETE' else ('PIXEL_CONFIRMED' if l['PALETTE'] else 'SOURCE_COMPLETE'), PRESENTATION='PRESENTATION_PARTIAL',
        CONFIDENCE=l['CONFIDENCE'] + (f"; errors {l['ERRORS']}" if l['ERRORS'] not in ('', '[]') else ''), OUTPUT=l['PREVIEW'], THUMB=l['PREVIEW'], METADATA=l['METADATA'],
        ATLAS=atlas(l['BODY_LIBRARY']), EVIDENCE='landscapes.cif GfxLandscape', BROWSER_ROUTE='Terrain/Landscapes/index.html')
for t in rcsv(C / 'terrain.csv'):
    tr = t['KIND'] == 'transition'
    add(ASSET_ID=('trans:' if tr else 'pat:') + t['PATTERN_ID'].lstrip('T'), CATEGORY='Terrain', SUBCATEGORY='Transition' if tr else 'Pattern', NATIVE_NAME=t['NATIVE_NAME'],
        DISPLAY_NAME=t['NATIVE_NAME'], LOGIC_ID=t['LOGIC_TYPE'], GFX_ID=t['PATTERN_ID'], ENTRY=t['TEXTURE'],
        STATUS='SOURCE_COMPLETE' if tr else 'PIXEL_CONFIRMED', PRESENTATION='PRESENTATION_PARTIAL',
        CONFIDENCE='texture decode pixel-confirmed; texture-space crop' if not tr else 'texture + alpha DATA; blending runtime',
        OUTPUT=t['CROP'], THUMB=t['CROP'], METADATA=t['METADATA'], EVIDENCE='pattern.cif / transitions.cif', BROWSER_ROUTE='Terrain/Transitions/index.html' if tr else 'Terrain/Patterns/index.html')
for i, e in enumerate(rcsv(C / 'effects.csv')):
    add(ASSET_ID=f"fx:{e['EFFECT_KIND']}:{e['NATIVE_ID'] or i}:{slug(e['NATIVE_NAME'])}", CATEGORY='Effects', SUBCATEGORY=e['EFFECT_KIND'], NATIVE_NAME=e['NATIVE_NAME'],
        DISPLAY_NAME=e['NATIVE_NAME'], GFX_ID=e['NATIVE_ID'], ENTRY=e['LIBRARY'], BMD=stem(e['LIBRARY']) if e['LIBRARY'] else '', BOB=J(e['BOBS']) or '', PALETTE=e['PALETTE'],
        FRAMES=e['FRAMES'], STATUS='PIXEL_CONFIRMED' if e['PREVIEW'] else 'SOURCE_COMPLETE', PRESENTATION='PRESENTATION_PARTIAL', CONFIDENCE=e['CONFIDENCE'] + '; ' + str(e['SEMANTICS'])[:200],
        OUTPUT=e['PREVIEW'], THUMB=e['PREVIEW'], METADATA=e['METADATA'], ATLAS=atlas(e['LIBRARY']) if e['LIBRARY'] else '', EVIDENCE=e['SOURCE_TABLE'],
        BROWSER_ROUTE='Shared/Effects/index.html')

# ================================================================ UI, FONTS, IMAGES
uirows = []
for u in rcsv(C / 'ui_sprites.csv'):
    ev = read(ROOT / 'UI/Sprites' / stem(u['LIBRARY']) / 'metadata' / f"bob_{int(u['BOB_ID']):04d}.json") if (ROOT / 'UI/Sprites' / stem(u['LIBRARY']) / 'metadata' / f"bob_{int(u['BOB_ID']):04d}.json").exists() else {}
    det = ev.get('evidenceDetail', [])
    tips = sorted({d['tooltip'] for d in det if d.get('tooltip')})
    usage = sorted({d.get('nearestComment') or d.get('code', '') for d in det})[:4]
    group = 'frames/borders' if any('UiSkin_DrawTiledFrame' in (d.get('nearestComment') or '') for d in det) else \
        'command icons (human actions)' if any(d.get('humanActionId') for d in det) else \
        'HUD toolbar/minimap/speed/message buttons' if any(d.get('commandId') for d in det) else \
        'main menu logos' if 'menu_logos' in u['LIBRARY'] else ('evidenced (generic)' if det else 'UNKNOWN usage')
    outs = J(u['OUTPUTS']) or []
    st = 'PIXEL_CONFIRMED' if u['STATUS'] == 'PALETTE_EVIDENCED' else ('UNKNOWN' if u['STATUS'].startswith('PALETTE_UNKNOWN') else 'SOURCE_COMPLETE')
    r = dict(u, UI_GROUP=group, TOOLTIPS=tips, USAGE=usage, PRIMARY_STATUS=st)
    uirows.append(r)
    add(ASSET_ID=f"ui:{stem(u['LIBRARY'])}:{u['BOB_ID']}", CATEGORY='UI', SUBCATEGORY=group, NATIVE_NAME=f"{stem(u['LIBRARY'])} sprite {u['BOB_ID']}",
        DISPLAY_NAME=(tips[0] if tips else f"sprite {int(u['BOB_ID']):#x}"), ENTRY=u['LIBRARY'], BMD=stem(u['LIBRARY']), BOB=u['BOB_ID'], PALETTE=J(u['PALETTES']) or '',
        PIVOT=J(u['PIVOT']), WIDTH=u['WIDTH'], HEIGHT=u['HEIGHT'], STATUS=st, UNKNOWN_CLASS='UNKNOWN_PALETTE' if st == 'UNKNOWN' else '',
        CONFIDENCE=u['STATUS'], OUTPUT=outs[0] if outs else u.get('INDEX_DATA', ''), THUMB=outs[0] if outs else u.get('INDEX_DATA', ''),
        METADATA=f"UI/Sprites/{stem(u['LIBRARY'])}/metadata/bob_{int(u['BOB_ID']):04d}.json" if ev else '', ATLAS=atlas(u['LIBRARY']),
        EVIDENCE=J(u['EVIDENCE']) or 'none', BROWSER_ROUTE='UI/Sprites/index.html')
for f in rcsv(C / 'fonts.csv'):
    dup = f['STATUS'] == 'DUPLICATE_OF'
    add(ASSET_ID=f"font:{f['ENTRY_ID']}", CATEGORY='Fonts', SUBCATEGORY='duplicate (identical bytes)' if dup else 'FNT', NATIVE_NAME=f['ENTRY_NAME'], DISPLAY_NAME=stem(f['ENTRY_NAME']),
        ENTRY=f['ENTRY_NAME'], ARCHIVE=ARCH_S, FRAMES=f.get('GLYPHS', ''), STATUS='SOURCE_COMPLETE', PRESENTATION='PRESENTATION_PARTIAL',
        CONFIDENCE=('identical bytes to ' + f['DUPLICATE_OF']) if dup else 'embedded BMD decoded by production decoder; colour from draw-time palette',
        OUTPUT=f.get('OUTPUT', ''), THUMB=f.get('OUTPUT', ''), METADATA=(f['OUTPUT'].replace('__index_data.png', '.json') if f.get('OUTPUT') else ''),
        EVIDENCE='FNT header + embedded BMD (cultures_fnt.py)', BROWSER_ROUTE='UI/Fonts/index.html')
img_route = {'Terrain': 'Terrain/Textures/index.html', 'Palette': 'Metadata/Palettes/index.html', 'UI': 'UI/Images/index.html', 'Unknown': 'Unknown/index.html'}
for im in rcsv(C / 'images.csv'):
    val = im.get('VALIDATION', '')
    st = 'PIXEL_CONFIRMED' if val.startswith('PIXEL_CONFIRMED') else 'UNKNOWN' if val.startswith('UNKNOWN') else 'SOURCE_COMPLETE'
    cur = im['FORMAT'] == 'CUR'
    add(ASSET_ID=f"img:{im['ENTRY_ID'] or slug(im['ENTRY_NAME'])}", CATEGORY='Cursors' if cur else ('Palettes' if im['CATEGORY'] == 'Palette' else 'Images'),
        SUBCATEGORY=im['CATEGORY'], NATIVE_NAME=im['ENTRY_NAME'], DISPLAY_NAME=Path(im['ENTRY_NAME'].replace(B, '/')).name, ENTRY=im['ENTRY_NAME'],
        ARCHIVE=ARCH_S if im['ENTRY_ID'] else 'loose DataX file', WIDTH=im.get('WIDTH', ''), HEIGHT=im.get('HEIGHT', ''), STATUS=st,
        UNKNOWN_CLASS='UNKNOWN_OTHER' if st == 'UNKNOWN' else '', CONFIDENCE=val, OUTPUT=im.get('OUTPUT', ''),
        THUMB=im.get('SWATCH') or im.get('PREVIEW') or (im.get('OUTPUT', '') if im.get('OUTPUT', '').endswith('.png') else ''),
        BROWSER_ROUTE='UI/Cursors/index.html' if cur else img_route.get(im['CATEGORY'], 'UI/Images/index.html'))
both('ui', uirows + [dict(f, UI_GROUP='fonts') for f in rcsv(C / 'fonts.csv')] + [dict(i, UI_GROUP='images/cursors') for i in rcsv(C / 'images.csv') if i['CATEGORY'] == 'UI'])

# ================================================================ AUDIO / FMV / DOCUMENTS / CIF / LIBRARIES
for a in rcsv(C / 'audio.csv'):
    dm = a['ARCHIVE'] == 'loose DataX file'
    unk = a['CONFIDENCE'].startswith('UNKNOWN')
    add(ASSET_ID=f"aud:{a['ENTRY_ID'] or slug(Path(a['ENTRY']).name)}", CATEGORY='Audio', SUBCATEGORY=a['CATEGORY'], NATIVE_NAME=a['ENTRY'],
        DISPLAY_NAME=Path(a['ENTRY'].replace(B, '/')).name + (' | ' + ', '.join(J(a['NATIVE_NAMES']) or [])[:120] if J(a['NATIVE_NAMES']) else ''),
        ENTRY=a['ENTRY'], ARCHIVE=a['ARCHIVE'], FRAMES=a.get('DURATION_S', ''), TIMING=f"{a.get('SAMPLE_RATE', '')} Hz {a.get('BITS', '')} bit {a.get('CHANNELS', '')} ch {a.get('FORMAT', '')}",
        STATUS='UNKNOWN' if unk else 'SOURCE_COMPLETE', UNKNOWN_CLASS='UNKNOWN_UNREFERENCED' if unk else '', CONFIDENCE=a['CONFIDENCE'], OUTPUT=a['OUTPUT'],
        METADATA=(a['OUTPUT'] + '.json') if not dm else '', EVIDENCE=a['NATIVE_SECTIONS'], BROWSER_ROUTE='Audio/index.html')
for f in rcsv(C / 'fmv.csv'):
    add(ASSET_ID=f"fmv:{f['NAME']}", CATEGORY='FMV', SUBCATEGORY='MPEG', NATIVE_NAME=f['FILE'], DISPLAY_NAME=Path(f['FILE']).name, ENTRY=f['FILE'], ARCHIVE='loose DataX file',
        WIDTH=f.get('WIDTH', ''), HEIGHT=f.get('HEIGHT', ''), TIMING=f"{f.get('FRAMERATE')} fps, ~{f.get('APPROXDURATIONSECONDS')} s", STATUS='SOURCE_COMPLETE',
        PRESENTATION='PRESENTATION_PARTIAL', CONFIDENCE=f['ROLE'], OUTPUT=f['FILE'], METADATA='FMV/index.json', EVIDENCE='Game.exe datax\\FMV\\%s\\%s.mpg, seq_%4.4d',
        BROWSER_ROUTE='FMV/index.html')
for d in rcsv(C / 'documents.csv'):
    add(ASSET_ID=f"doc:{d['ENTRY_ID']}", CATEGORY='Native documents', SUBCATEGORY=d['CATEGORY'] + ' ' + d['FORMAT'], NATIVE_NAME=d['ENTRY_NAME'],
        DISPLAY_NAME=Path(d['ENTRY_NAME'].replace(B, '/')).name, ENTRY=d['ENTRY_NAME'], ARCHIVE=ARCH_S, STATUS='SOURCE_COMPLETE', CONFIDENCE=d['STATUS'],
        OUTPUT=d['OUTPUT'], EVIDENCE=d['REFERENCES'], BROWSER_ROUTE='Metadata/Sources/index.html')
for c in rcsv(C / 'cif_index.csv'):
    rp = c['ENTRY_NAME'].replace(B, '/')
    add(ASSET_ID=f"cif:{c['ENTRY_ID']}", CATEGORY='Native definitions', SUBCATEGORY='CIF', NATIVE_NAME=c['ENTRY_NAME'], DISPLAY_NAME=Path(rp).name, ENTRY=c['ENTRY_NAME'],
        ARCHIVE=ARCH_S, STATUS='SOURCE_COMPLETE' if c['STATUS'] == 'DECODED' else 'UNKNOWN', CONFIDENCE=c['STATUS'] + ' ' + c['SECTIONS'],
        OUTPUT=f'Metadata/Sources/CIF/{rp}.txt', METADATA=f'Metadata/Sources/CIF/{rp}.json', BROWSER_ROUTE='Metadata/Sources/index.html')
for l in rcsv(C / 'bmd_coverage.csv'):
    add(ASSET_ID=f"lib:{stem(l['LIBRARY']).lower()}", CATEGORY='Source libraries', SUBCATEGORY='BMD', NATIVE_NAME=l['LIBRARY'], DISPLAY_NAME=Path(l['LIBRARY'].replace(B, '/')).name,
        ENTRY=l['LIBRARY'], ARCHIVE=ARCH_S, BMD=stem(l['LIBRARY']), FRAMES=l['FRAMES'], PALETTE=J(l['PALETTES']),
        STATUS='PARTIAL' if l['DECODE_STATUS'] != 'DECODED' else 'SOURCE_COMPLETE', CONFIDENCE=f"nonempty {l['NONEMPTY']}, mapped {l['MAPPED']}, not mapped {l['NOT_MAPPED']}; {l['STATUS_COUNTS']}",
        OUTPUT=l['ATLAS'], METADATA=l['ATLAS'], ATLAS=l['ATLAS'], BROWSER_ROUTE='Shared/SourceLibraries/index.html',
        DETAIL_PAGE=f"Shared/SourceLibraries/viewer.html#{slug(stem(l['LIBRARY']))}")

# ================================================================ UNKNOWN (frames + native stubs)
unk_rows = []
for u in rcsv(C / 'unknown_frames.csv'):
    lib = slug(stem(u['LIBRARY']))
    rect = J(u.get('RECT', '')) or ''
    r = {'UNKNOWN_CLASS': u['CLASS'], 'REASON': u['REASON'], 'ITEM': 'BMD frame', 'LIBRARY': u['LIBRARY'], 'ENTRY_ID': u['ENTRY_ID'], 'BOB_ID': u['BOB_ID'],
         'KIND': u['KIND'], 'WIDTH': u['WIDTH'], 'HEIGHT': u['HEIGHT'], 'PIVOT': u['PIVOT'], 'PAGE': u.get('PAGE', ''), 'RECT': u.get('RECT', ''),
         'COLOUR_PAGES': u.get('COLOUR_PAGES', ''), 'BOBSEQ_EVIDENCE': u.get('BOBSEQ_EVIDENCE', ''), 'POSSIBLE_EVIDENCE': u['POSSIBLE_EVIDENCE'],
         'HASH': u.get('SHA256_PLANES', ''), 'ATLAS': u['ATLAS'], 'CONFIDENCE': 'UNKNOWN'}
    unk_rows.append(r)
    seqs = J(u.get('BOBSEQ_EVIDENCE', '')) or []
    add(ASSET_ID=f"unk:{lib}:{u['BOB_ID']}", CATEGORY='Unknown', SUBCATEGORY=u['CLASS'] + (':' + u['REASON'] if u['REASON'] else ''), NATIVE_NAME=f"{stem(u['LIBRARY'])} BOB {u['BOB_ID']}",
        DISPLAY_NAME=(seqs[0].split(' [')[0] if seqs else f"{stem(u['LIBRARY'])} BOB {u['BOB_ID']}"), ENTRY=u['LIBRARY'], ARCHIVE=ARCH_S, BMD=stem(u['LIBRARY']), BOB=u['BOB_ID'],
        BOBSEQ=[s.split(' [')[0] for s in seqs], PIVOT=J(u['PIVOT']), WIDTH=u['WIDTH'], HEIGHT=u['HEIGHT'], STATUS='UNKNOWN', UNKNOWN_CLASS=u['CLASS'],
        CONFIDENCE=u['REASON'], OUTPUT=u.get('PAGE', ''), THUMB=u.get('PAGE', ''), THUMB_RECT=rect, ATLAS=u['ATLAS'], EVIDENCE=u['POSSIBLE_EVIDENCE'],
        BROWSER_ROUTE='Unknown/index.html', DETAIL_PAGE=f"Shared/SourceLibraries/viewer.html#{lib}")
stubs = []
for p in glob.glob(str(ROOT / 'Metadata/Evidence/*_buildings_errors.json')):
    for e in read(p):
        for msg in e.get('errors', [e.get('error')]):
            stubs.append({'ITEM': 'native reference', 'SOURCE': f"houses.cif GfxHouse {e['gfxId']} level {e['level']}", 'DETAIL': msg, 'RELATED': f"bld:{e['gfxId']}:{e['level']}"})
for l in rcsv(C / 'landscapes.csv'):
    for msg in J(l['ERRORS']) or []:
        stubs.append({'ITEM': 'native reference', 'SOURCE': f"landscapes.cif GfxLandscape {l['GFX_LANDSCAPE_ID']} ({l['NATIVE_NAME']})", 'DETAIL': msg, 'RELATED': f"land:{l['GFX_LANDSCAPE_ID']}"})
for kind in ('human', 'animal', 'vehicle'):
    for r in anim_rows[kind]:
        if r['RENDER_STATUS'].startswith('RENDERED_PARTIAL'):
            stubs.append({'ITEM': 'native reference', 'SOURCE': f"animations.cif section {r['ANIMATION_SECTION']} ({r['BOBSEQ_BODY']}) for tribe {r['TRIBE_ID']} {kind} {r['TYPE_ID']} {r['PHASE']} variant {r['BODY_VARIANT']}",
                          'DETAIL': f"{r['CELL_ISSUES']} in {r['BODY_BMD']}", 'RELATED': f"{kind[:3]}:{r['TRIBE_ID']}:{r['TYPE_ID']}"})
seen = set()
for s in stubs:
    k = (s['SOURCE'], s['DETAIL'])
    if k in seen:
        continue
    seen.add(k)
    unk_rows.append({'UNKNOWN_CLASS': 'UNKNOWN_NATIVE_STUB', 'REASON': 'native definition references a frame that does not exist in the declared library', 'ITEM': s['ITEM'],
                     'LIBRARY': '', 'POSSIBLE_EVIDENCE': s['SOURCE'] + ': ' + str(s['DETAIL']), 'CONFIDENCE': 'UNKNOWN', 'RELATED': s['RELATED']})
    add(ASSET_ID=f"stub:{len(seen)}", CATEGORY='Unknown', SUBCATEGORY='UNKNOWN_NATIVE_STUB', NATIVE_NAME=s['SOURCE'], DISPLAY_NAME=s['SOURCE'], STATUS='UNKNOWN',
        UNKNOWN_CLASS='UNKNOWN_NATIVE_STUB', CONFIDENCE=str(s['DETAIL'])[:300], EVIDENCE=s['SOURCE'], RELATED_HOUSE=s['RELATED'] if s['RELATED'].startswith('bld') else '',
        BROWSER_ROUTE='Unknown/index.html')
for x in X:
    if x['CATEGORY'] in ('Audio', 'Images') and x['STATUS'] == 'UNKNOWN':
        unk_rows.append({'UNKNOWN_CLASS': x['UNKNOWN_CLASS'] or 'UNKNOWN_OTHER', 'REASON': x['CONFIDENCE'], 'ITEM': x['CATEGORY'], 'LIBRARY': x['ENTRY'],
                         'POSSIBLE_EVIDENCE': x['EVIDENCE'], 'CONFIDENCE': 'UNKNOWN', 'RELATED': x['ASSET_ID']})
    if x['CATEGORY'] in ('Vehicles', 'Animals') and x['STATUS'] == 'UNKNOWN':
        unk_rows.append({'UNKNOWN_CLASS': 'UNKNOWN_GRAPHICS_BINDING', 'REASON': x['CONFIDENCE'], 'ITEM': x['CATEGORY'] + ' declaration', 'LIBRARY': '',
                         'POSSIBLE_EVIDENCE': x['EVIDENCE'], 'CONFIDENCE': 'UNKNOWN', 'RELATED': x['ASSET_ID']})
for r in rcsv(ROOT / 'Metadata/Mobile/atomics_without_graphics_animal.csv'):
    if r['STATUS'].startswith('NO_GRAPHICS'):
        t = int(r['TRIBE_ID'])
        add(ASSET_ID=f"anidecl:{t}:{r['TYPE_ID']}", CATEGORY='Animals', SUBCATEGORY='Native declaration without graphics', TRIBE_ID=t,
            TRIBE=localization(cif(r'data\text\eng\strings\gameobjects\tribes.cif')).get(t, {}).get('plural'), ANIMAL_TRIBE=t, JOB_ID=r['TYPE_ID'],
            STATUS='UNKNOWN', UNKNOWN_CLASS='UNKNOWN_GRAPHICS_BINDING', CONFIDENCE='NATIVE_DECLARATION_NO_GRAPHICS', EVIDENCE='tribetypes.cif allowjob; animals/jobgraphics.cif',
            BROWSER_ROUTE='Animals/index.html')
        unk_rows.append({'UNKNOWN_CLASS': 'UNKNOWN_GRAPHICS_BINDING', 'REASON': 'NATIVE_DECLARATION_NO_GRAPHICS', 'ITEM': 'Animal declaration', 'LIBRARY': '',
                         'POSSIBLE_EVIDENCE': f"tribe {t} job {r['TYPE_ID']}", 'CONFIDENCE': 'UNKNOWN', 'RELATED': f"anidecl:{t}:{r['TYPE_ID']}"})
both('unknown_assets', unk_rows)

# ================================================================ ARCHIVE INDEX + FILE INVENTORY (zero-discard)
byentry = collections.defaultdict(list)
for x in X:
    if x['ENTRY']:
        byentry[norm(x['ENTRY'])].append(x)
arch = []
for n, e in enumerate(INDEX.entries):
    xs = byentry.get(norm(e.path), [])
    prim = next((x for x in xs if x['CATEGORY'] in ('Source libraries', 'Native definitions', 'Native documents', 'Audio', 'Images', 'Palettes', 'Fonts')), xs[0] if xs else None)
    arch.append({'ARCHIVE': ARCH_S, 'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'OFFSET': e.offset, 'SIZE': e.size, 'FORMAT': e.path.rsplit('.', 1)[-1].upper(),
                 'CATEGORY': prim['CATEGORY'] if prim else 'UNACCOUNTED', 'ASSET_ID': prim['ASSET_ID'] if prim else '', 'STATUS': prim['STATUS'] if prim else 'UNACCOUNTED',
                 'OUTPUT': prim['OUTPUT'] if prim else '', 'BROWSER_ROUTE': prim['BROWSER_ROUTE'] if prim else '', 'USED_BY_ASSETS': len(xs),
                 'NOTES': 'ENTRY_ID is the zero-based archive table ordinal'})
both('archive_index', arch)
inv = []
before = read(ROOT / 'Metadata/Evidence/library/source_hashes_before.json')
for p in source_files():
    sp = str(p)
    xs = byentry.get(norm(sp), [])
    if p == ARCH:
        cat, st, route = 'Archive container', 'SOURCE_COMPLETE', 'Catalogs/index.html'
    elif p.parent.name == 'DM2':
        cat, st, route = 'Audio (DirectMusic)', 'SOURCE_COMPLETE', 'Audio/index.html'
    elif p.parent.name == 'Eng' and p.suffix.lower() == '.mpg':
        cat, st, route = 'FMV', 'SOURCE_COMPLETE', 'FMV/index.html'
    elif p.parent.name in ('Pictures', 'Mouse'):
        cat, st, route = 'UI', 'SOURCE_COMPLETE', 'UI/Images/index.html' if p.parent.name == 'Pictures' else 'UI/Cursors/index.html'
    elif p.parent == ORIGINAL:
        cat, st, route = 'Original binary (evidence, read-only)', 'SOURCE_COMPLETE', 'Metadata/Evidence/index.html'
    else:
        cat, st, route = 'Other loose file', 'SOURCE_COMPLETE', 'Metadata/Evidence/index.html'
    inv.append({'PATH': sp, 'SIZE': p.stat().st_size, 'SHA256': before.get(sp, ''), 'CATEGORY': cat, 'STATUS': st, 'BROWSER_ROUTE': route,
                'NOTES': 'not an asset: ' + p.name if p.name in ('t.dat',) else ''})
    if not xs and p != ARCH:
        add(ASSET_ID=f"file:{slug(p.relative_to(p.parents[1]))}", CATEGORY='Loose files', SUBCATEGORY=cat, NATIVE_NAME=sp, DISPLAY_NAME=p.name, ENTRY=sp, ARCHIVE='loose file',
            STATUS=st, CONFIDENCE='sha256 recorded; original left in place', OUTPUT=sp if p.parent.name != 'original' else '', BROWSER_ROUTE=route)
both('file_inventory', inv)

# ================================================================ PIXEL VALIDATION + MASTER
val = []
for p in glob.glob(str(ROOT / 'Metadata/Mobile/validation_*.json')) + [str(ROOT / 'Metadata/Landscapes/validation.json'), str(ROOT / 'Metadata/UI/validation.json'),
                                                                        str(ROOT / 'Metadata/Effects/validation.json')]:
    val += read(p)
ba = collections.Counter((r['LIBRARY'], r['PALETTE'], r['STATUS']) for r in rcsv(C / 'building_pixel_audit.csv'))
for (lib, pal, st), n_ in ba.items():
    val.append({'LIBRARY': lib, 'PALETTE': pal, 'FRAMES_DRAWN': n_, 'PIXEL_CONFIRMED': n_ if st == 'PIXEL_CONFIRMED' else 0, 'MISMATCH': n_ if st == 'PIXEL_MISMATCH' else 0,
                'OTHER': 0 if st in ('PIXEL_CONFIRMED', 'PIXEL_MISMATCH') else n_, 'REFERENCE': 'production drawBobClippedBorrowed32 vs saved building PNG', 'SCOPE': 'buildings'})
for im in rcsv(C / 'images.csv'):
    if im['FORMAT'] == 'PCX':
        val.append({'LIBRARY': im['ENTRY_NAME'], 'PALETTE': 'embedded', 'FRAMES_DRAWN': 1, 'PIXEL_CONFIRMED': int(im['VALIDATION'].startswith('PIXEL_CONFIRMED')),
                    'MISMATCH': int('MISMATCH' in im['VALIDATION']), 'OTHER': 0, 'REFERENCE': 'production decodeIndexedPcx vs PIL', 'SCOPE': 'pcx'})
both('pixel_validation', val)
both('asset_cross_reference', X, XF)
summary = {'rows': len(X), 'byCategory': dict(collections.Counter(x['CATEGORY'] for x in X)), 'byStatus': dict(collections.Counter(x['STATUS'] for x in X)),
           'unknownClasses': dict(collections.Counter(r['UNKNOWN_CLASS'] for r in unk_rows)), 'archiveEntries': len(arch),
           'archiveUnaccounted': [a['ENTRY_NAME'] for a in arch if a['CATEGORY'] == 'UNACCOUNTED'], 'looseFiles': len(inv),
           'pixelValidation': {'framesConfirmed': sum(int(v['PIXEL_CONFIRMED'] or 0) for v in val), 'mismatch': sum(int(v['MISMATCH'] or 0) for v in val)}}
write(C / 'catalog_summary.json', summary)
print(json.dumps(summary, indent=1)[:3000])
