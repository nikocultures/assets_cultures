"""Stage 20: every GfxLandscape definition (landscapes.cif) -> frames, shadows, valency, transitions.

Native chain: landscapes.cif GfxLandscape (editname, logictype -> landscapetypes.cif, gfxboblibs [body, _s shadow],
gfxpalette, gfxframes <valency> <bob...>, gfxstatic/gfxloopanimation/gfxtransition ...).
Goods: goodtypes.cif landscapetype -> GfxLandscape logictype (piles).  Tribe links: misc.cif tribelandscapelinkdata /
tribehouselinkdata.  Shadows: same BOB id in the _s library, pixel kind 2, destination darkening (0x0049B930).
"""
import collections
from PIL import Image
from common import *

L = cif(r'data\engine2d\inis\landscapes\landscapes.cif')
LT = {scalar(b, 'type'): b for b in cif(r'data\logic\landscapetypes.cif')}
GOODS = {scalar(b, 'type'): b for b in cif(r'data\logic\goodtypes.cif')}
GOODTXT = localization(cif(r'data\text\eng\strings\gameobjects\goods.cif'))
LT2GOOD = collections.defaultdict(list)
for g, b in GOODS.items():
    for k in ('landscapetype', 'landscapetoharvest', 'landscapetopickup', 'landscapetostore'):
        v = scalar(b, k)
        if v is not None:
            LT2GOOD[v].append((g, k))
MISC = cif(r'data\engine2d\inis\misc\misc.cif')
TRIBELINK = collections.defaultdict(list)
for b in MISC:
    for n in commands(b, 'landscapename'):
        TRIBELINK[n[0].lower()].append({'section': b['section'], 'tribe': scalar(b, 'logictribetype'),
                                        'landscapeType': scalar(b, 'logiclandscapetype'), 'houseType': scalar(b, 'logichousetype')})
FRAMEIDX = {}


def frames_of(lib):
    if lib not in FRAMEIDX:
        FRAMEIDX[lib] = {f['bobId']: f for f in bmd(lib)[0]}
    return FRAMEIDX[lib]


def placement(b):
    group = str(scalar(b, 'editgroups', 'ungrouped'))
    lt = scalar(b, 'logictype')
    goods = [g for g, k in LT2GOOD.get(lt, [])] if lt != 1 else []
    if group in ('goods all',) and goods:
        g = goods[0]
        return ROOT / 'Shared/Goods' / f"good_{g:02d}_{slug(scalar(GOODS[g], 'name'))}" / 'piles', 'Goods'
    if group in ('effects', 'xMissionCD_effects'):
        return ROOT / 'Shared/Effects/Landscape', 'Effects'
    if group == 'animals':
        return ROOT / 'Animals/Landscape', 'Animals'
    return ROOT / 'Terrain/Landscapes' / slug(group), 'Terrain'


canon = {}
VALID = collections.defaultdict(set)
USED = collections.defaultdict(lambda: collections.defaultdict(list))
rows, xrows = [], []
for gid, b in enumerate(L):
    name = str(scalar(b, 'editname', f'landscape_{gid}'))
    base, cat = placement(b)
    folder = base / f'{gid:03d}_{slug(name)}'
    libs = commands(b, 'gfxboblibs')[0] if commands(b, 'gfxboblibs') else []
    body = libs[0] if libs else None
    shadow = libs[1] if len(libs) > 1 else None
    pals = commands(b, 'gfxpalette')[0] if commands(b, 'gfxpalette') else []
    pal = pals[0] if pals else None
    lt = scalar(b, 'logictype')
    meta = {'gfxLandscapeId': gid, 'nativeName': name, 'editGroups': commands(b, 'editgroups'), 'logicType': lt,
            'logicTypeName': scalar(LT.get(lt, {'commands': []}), 'name'), 'logicTypeDefinition': LT.get(lt),
            'goodLinks': [{'goodId': g, 'goodName': scalar(GOODS[g], 'name'), 'english': GOODTXT.get(g, {}).get('singular'), 'field': k} for g, k in LT2GOOD.get(lt, [])] if lt != 1 else [],
            'tribeLinks': TRIBELINK.get(name.lower(), []), 'bodyLibrary': body, 'shadowLibrary': shadow, 'palettes': pals,
            'static': scalar(b, 'gfxstatic'), 'loopAnimation': scalar(b, 'gfxloopanimation'), 'shadingFactor': scalar(b, 'gfxshadingfactor'),
            'userFxMatrix': scalar(b, 'gfxuserfxmatrix'), 'dynamicBackground': scalar(b, 'gfxdynamicbackground'), 'drawVoidEver': scalar(b, 'gfxdrawvoidever'),
            'transitions': commands(b, 'gfxtransition'), 'maximumValency': scalar(b, 'logicmaximumvalency'),
            'definition': b, 'source': source(r'data\engine2d\inis\landscapes\landscapes.cif'), 'valencies': [], 'errors': [],
            'category': cat, 'folder': rel(folder),
            'nativeReferences': {'Game.exe': ['0x0049B930 kind-2 shadow darkening'], 'cpp': 'GfxLandscapeRegistry; ProductionWorldCompositor static landscape path'}}
    palarr = palette(pal)[0] if pal and pal.lower() in palette_defs() else None
    if pal and palarr is None:
        meta['errors'].append(f'palette {pal} not defined in palettes.cif')
    fb = frames_of(body) if body and has(body) else {}
    fs = frames_of(shadow) if shadow and has(shadow) else {}
    if body and not has(body):
        meta['errors'].append(f'body library {body} not in archive')
    for args in commands(b, 'gfxframes'):
        val, bobs = args[0], args[1:]
        seq = []
        for pos, bob in enumerate(bobs):
            e = {'sequenceIndex': pos, 'bobId': bob}
            f = fb.get(bob)
            if f is None:
                e['status'] = 'BOB_ABSENT_IN_LIBRARY'
                meta['errors'].append(f'valency {val}: BOB {bob} absent in {body}')
            elif not (f['width'] and f['height'] and f['kind']):
                e['status'] = 'EMPTY_FRAME'
            else:
                e.update(width=f['width'], height=f['height'], pivot=[-f['x'], -f['y']], pixelKind=f['kind'])
                key = (norm(body), bob, (pal or '').lower())
                if key not in canon:
                    p = frame_planes(body, f)
                    img = rgba(p, palarr if palarr is not None else None, f['kind'])
                    if palarr is None and f['kind'] != 2:
                        img[:, :, :3] = p[:, :, :1]  # no palette: indices as grey DATA
                    out = folder / ('frames' if cat == 'Effects' else '') / f'bob_{bob:06d}.png'
                    out.parent.mkdir(parents=True, exist_ok=True)
                    Image.fromarray(img, 'RGBA').save(out)
                    c = {'path': rel(out)}
                    if f['kind'] == 4:
                        sec = out.with_name(out.stem + '__kind4_secondary.png')
                        Image.fromarray(np.dstack([p[:, :, 2]] * 3 + [p[:, :, 1]]), 'RGBA').save(sec)
                        c['kind4Secondary'] = rel(sec)
                    if palarr is not None:
                        VALID[(body, pal)].add(bob)
                    canon[key] = c
                e.update(canon[key])
                USED[body][bob].append('landscape')
                sf = fs.get(bob)
                if sf and sf['kind'] == 2 and sf['width'] and sf['height']:
                    skey = (norm(shadow), bob)
                    if skey not in canon:
                        p = frame_planes(shadow, sf)
                        out = folder / ('frames' if cat == 'Effects' else '') / f'bob_{bob:06d}__shadow_mask.png'
                        Image.fromarray(np.dstack([np.zeros_like(p[:, :, 0])] * 3 + [p[:, :, 1]]), 'RGBA').save(out)
                        canon[skey] = {'path': rel(out), 'pivot': [-sf['x'], -sf['y']]}
                    e['shadowMask'] = canon[skey]['path']
                    e['shadowPivot'] = canon[skey]['pivot']
                    USED[shadow][bob].append('landscape_shadow')
                elif shadow and sf is not None and sf['kind'] not in (0, 2):
                    e['shadowNote'] = f'shadow library frame kind {sf["kind"]} (not kind 2)'
            seq.append(e)
        meta['valencies'].append({'valency': val, 'frames': seq})
    meta['confidence'] = {'source': 'SOURCE_COMPLETE' if not meta['errors'] else 'PARTIAL',
                          'pixels': 'PIXEL_CONFIRMED per frame (Catalogs/pixel_validation.csv)' if palarr is not None else 'UNKNOWN palette: index DATA only',
                          'presentation': 'PRESENTATION_PARTIAL: lighting/shading factor, kind-4 blending, shadow darkening and animation rate not baked'}
    write(folder / 'metadata.json', meta)
    nframes = sum(len(v['frames']) for v in meta['valencies'])
    first = next((fr for v in meta['valencies'] for fr in v['frames'] if fr.get('path')), {})
    rows.append({'GFX_LANDSCAPE_ID': gid, 'NATIVE_NAME': name, 'EDIT_GROUPS': meta['editGroups'], 'LOGIC_TYPE': lt, 'LOGIC_TYPE_NAME': meta['logicTypeName'],
                 'GOODS': [g['goodId'] for g in meta['goodLinks']], 'TRIBE_LINKS': sorted({t['tribe'] for t in meta['tribeLinks']}), 'BODY_LIBRARY': body,
                 'SHADOW_LIBRARY': shadow, 'PALETTE': pal, 'VALENCIES': len(meta['valencies']), 'FRAMES': nframes,
                 'BOBS': sorted({fr['bobId'] for v in meta['valencies'] for fr in v['frames']}), 'STATIC': meta['static'], 'LOOP': meta['loopAnimation'],
                 'TRANSITIONS': len(meta['transitions']), 'CATEGORY': cat, 'WIDTH': first.get('width'), 'HEIGHT': first.get('height'),
                 'PIVOT': first.get('pivot'), 'PREVIEW': first.get('path'), 'CONFIDENCE': meta['confidence']['source'], 'ERRORS': meta['errors'],
                 'METADATA': rel(folder / 'metadata.json')})
print('landscapes', len(rows), 'unique frames', len(canon))
vrows = []
for (lib, pal), bobs in VALID.items():
    res = validate(lib, palette(pal)[0], list(bobs), 'land_' + pal)
    c = collections.Counter(res.values())
    vrows.append({'LIBRARY': lib, 'PALETTE': pal, 'FRAMES_DRAWN': len(bobs), 'PIXEL_CONFIRMED': c.get('PIXEL_CONFIRMED', 0),
                  'MISMATCH': c.get('PIXEL_MISMATCH', 0), 'OTHER': sum(v for k, v in c.items() if k not in ('PIXEL_CONFIRMED', 'PIXEL_MISMATCH')),
                  'REFERENCE': 'production drawBobClippedBorrowed32 via render_batch.exe', 'SCOPE': 'landscapes'})
write(ROOT / 'Metadata/Landscapes/validation.json', vrows)
write(ROOT / 'Metadata/Landscapes/usage.json', {lib: {str(b): sorted(set(v)) for b, v in d.items()} for lib, d in USED.items()}, compact=True)
csvout(ROOT / 'Catalogs/landscapes.csv', rows)
print('validated', sum(r['PIXEL_CONFIRMED'] for r in vrows), 'mismatch', sum(r['MISMATCH'] for r in vrows), 'other', sum(r['OTHER'] for r in vrows))
