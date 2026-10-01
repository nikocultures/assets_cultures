"""Stage 30: native Good table -> pile/icon/carried visuals, producers, tribe ownership.

Evidence:
  goodtypes.cif (65 Goods), goods.cif English strings, goodgraphics.cif (graphicshumanrandompalette),
  Game 0x00415565: Good.resolvedLandscape = first *pileable* GfxLandscape with logictype == Good.landscapetype (Goods 0..55)
  Game 0x004E2661 / 0x00496D32: UI good visual = that landscape's frame group for `amount` (list: 1), BOB bounds centred, +(12,8)
  Carried visual: GfxWalkAtomic logicgoodtype == Good id (baked into the Human body sprite; Metadata/Mobile/animations_human.csv)
  Tribe ownership: tribetypes.cif allowgood / jobenablesgood / toproducegoodneedhouse.
"""
import collections, csv
from common import *

GOODS = {scalar(b, 'type'): b for b in cif(r'data\logic\goodtypes.cif')}
GTXT = localization(cif(r'data\text\eng\strings\gameobjects\goods.cif'))
GHELP = r'data\text\eng\strings\help\goodshelp.cif'
GG = {scalar(b, 'logicgood'): b for b in cif(r'data\engine2d\inis\goods\goodgraphics.cif')}
L = cif(r'data\engine2d\inis\landscapes\landscapes.cif')
TRIBES = {scalar(b, 'type'): b for b in cif(r'data\logic\tribetypes\tribetypes.cif')}
TF = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Arabs', 5: 'Other Tribes/Weresnakes', 6: 'Other Tribes/Werewolves', 7: 'Other Tribes/Egypt'}
HOUSES = {scalar(b, 'type'): b for b in cif(r'data\logic\housetypes.cif')}
HTXT = localization(cif(r'data\text\eng\strings\gameobjects\houses.cif'))
WEAP = {scalar(b, 'type'): b for b in cif(r'data\logic\weapontypes.cif')}
ARM = {scalar(b, 'type'): b for b in cif(r'data\logic\armortypes.cif')}
ATOM = [b for b in cif(r'data\logic\atomicanimations\atomicanimations.cif')]
JOBS = {scalar(b, 'type'): b for b in cif(r'data\logic\jobtypes.cif')}
JOBTXT = localization(cif(r'data\text\eng\strings\gameobjects\jobs.cif'))

landmeta = {}
for p in list((ROOT / 'Shared/Goods').rglob('metadata.json')) + list((ROOT / 'Terrain/Landscapes').rglob('metadata.json')) + \
        list((ROOT / 'Shared/Effects/Landscape').rglob('metadata.json')) + list((ROOT / 'Animals/Landscape').rglob('metadata.json')):
    m = read(p)
    if 'gfxLandscapeId' in m:
        landmeta[m['gfxLandscapeId']] = m


def first_pileable(lt):
    for i, b in enumerate(L):
        if scalar(b, 'logictype') == lt and scalar(b, 'logicispileableonmap') == 1:
            return i
    return None


carried = collections.defaultdict(list)
with (ROOT / 'Metadata/Mobile/animations_human.csv').open(encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['KIND'] == 'walk' and r['CARRIED_GOOD'] not in ('', '0', 'None'):
            carried[int(r['CARRIED_GOOD'])].append(r)

rows, xrows = [], []
tribe_goods = collections.defaultdict(list)
for g in sorted(GOODS):
    b = GOODS[g]
    name = scalar(b, 'name')
    lt = scalar(b, 'landscapetype')
    gid = first_pileable(lt) if (lt and g <= 55) else None
    lm = landmeta.get(gid) if gid is not None else None
    icon = None
    if lm:
        groups = [v for v in lm['valencies'] if v['valency'] <= 1]
        grp = groups[-1] if groups else None
        if grp and grp['frames']:
            icon = dict(grp['frames'][0], valency=grp['valency'],
                        presentation='UI: BOB bounds centred then +(12,8) (0x004E2661/0x00496D32); first frame of group (loop phase 0)')
    folder = ROOT / 'Shared/Goods' / f'good_{g:02d}_{slug(name)}'
    owners = []
    for t, tb in TRIBES.items():
        if t > 7:
            continue
        rel_ = {k: [a for a in commands(tb, k) if g in a[:2] or (k == 'jobenablesgood' and a[-1] == g)] for k in
                ('allowgood', 'jobenablesgood', 'toproducegoodneedhouse', 'needforgood', 'trainforgood', 'jobdefaultgood')}
        allowed = any(a[0] == g for a in commands(tb, 'allowgood'))
        producers = [a for a in commands(tb, 'toproducegoodneedhouse') if a[0] == g]
        if allowed or producers or any(rel_.values()):
            owners.append({'tribe': t, 'tribeName': scalar(tb, 'name'), 'allowgood': allowed,
                           'producedInHouseTypes': [{'houseType': a[1], 'houseName': scalar(HOUSES.get(a[1], {'commands': []}), 'name'),
                                                     'english': HTXT.get(a[1], {}).get('singular')} for a in producers if len(a) > 1],
                           'relations': {k: v for k, v in rel_.items() if v}})
            if allowed:
                tribe_goods[t].append(g)
    carr = carried.get(g, [])
    meta = {'goodId': g, 'nativeName': name, 'english': GTXT.get(g, {}).get('singular'), 'englishPlural': GTXT.get(g, {}).get('plural'),
            'definition': b, 'landscapeType': lt, 'resolvedGfxLandscape': gid, 'resolvedGfxLandscapeName': lm['nativeName'] if lm else None,
            'resolutionRule': 'Game 0x00415565: first pileable GfxLandscape with logictype == landscapetype (Goods 0..55 only)',
            'pileMetadata': lm['folder'] + '/metadata.json' if lm else None,
            'pileValencies': [{'valency': v['valency'], 'frames': [{k: fr.get(k) for k in ('bobId', 'path', 'shadowMask', 'width', 'height', 'pivot')} for fr in v['frames']]} for v in lm['valencies']] if lm else [],
            'icon': icon, 'iconNote': 'No separate icon sprite: native UI draws the pile landscape frame (see icon.presentation)' if icon else 'No resolvable pile landscape -> no native UI visual (UNKNOWN)',
            'palette': lm['palettes'] if lm else None, 'bodyLibrary': lm['bodyLibrary'] if lm else None,
            'harvest': {k: scalar(b, k) for k in ('landscapetoharvest', 'landscapetopickup', 'landscapetostore', 'atomicforharvesting',
                                                  'atomicforcultivating', 'atomicforplanting') if scalar(b, k) is not None},
            'production': {'productionInputGoods': commands(b, 'productioninputgoods'), 'atomicForProduction': scalar(b, 'atomicforproduction'),
                           'isProducedInHouse': scalar(b, 'isproducedinhouseflag'), 'isProducedOnMap': scalar(b, 'isproducedonmapflag')},
            'weaponType': WEAP.get(scalar(b, 'weapontype')) if scalar(b, 'weapontype') is not None else None,
            'armorType': ARM.get(scalar(b, 'armortype')) if scalar(b, 'armortype') is not None else None,
            'carriedVisual': {'rule': 'GfxWalkAtomic logicgoodtype == Good id; carried good is baked into the Human body frames (no separate overlay sprite)',
                              'humanRandomPalette': scalar(GG[g], 'graphicshumanrandompalette') if g in GG else None,
                              'humanRandomPaletteRule': 'goodgraphics.cif palette patch definition linked to the Good; runtime application site not re-derived here -> PARTIAL' if g in GG else None,
                              'animations': [{k: r[k] for k in ('TRIBE_ID', 'TYPE_ID', 'NATIVE_NAME', 'PHASE', 'BODY_SELECTOR', 'ANIMATION_SECTION', 'BODY_SEQUENCE', 'SHEET', 'STATUS')} for r in carr]},
            'consumers': {'productionInputOf': [{'goodId': og, 'nativeName': scalar(ob, 'name'), 'english': GTXT.get(og, {}).get('singular')}
                                                for og, ob in GOODS.items() if any(g in a_ for a_ in commands(ob, 'productioninputgoods'))],
                          'houseConstruction': [{'tribe': t, 'houseType': a_[0], 'houseName': scalar(HOUSES.get(a_[0], {'commands': []}), 'name'),
                                                 'english': HTXT.get(a_[0], {}).get('singular'), 'raw': a_}
                                                for t, tb in TRIBES.items() if t <= 7 for a_ in commands(tb, 'tobuildhouseneedgood') if g in a_[1:]],
                          'source': 'goodtypes.cif productioninputgoods; tribetypes.cif tobuildhouseneedgood (house, goods...)'},
            'nativeJobRelations': [{'tribe': t, 'relation': k, 'jobId': a_[0], 'jobName': scalar(JOBS.get(a_[0], {'commands': []}), 'name'),
                                    'jobEnglish': JOBTXT.get(a_[0], {}).get('singular')}
                                   for t, tb in TRIBES.items() if t <= 7 for k in ('jobdefaultgood', 'jobenablesgood') for a_ in commands(tb, k) if len(a_) == 2 and a_[1] == g],
            'tribeOwnership': owners, 'ownership': 'SHARED (Good table is global; per-tribe availability in tribeOwnership)',
            'confidence': {'nativeTable': 'SOURCE_COMPLETE', 'pile': 'PIXEL_CONFIRMED frames' if lm else 'UNKNOWN', 'icon': 'SOURCE_COMPLETE (production rule)' if icon else 'UNKNOWN',
                           'carried': 'SOURCE_COMPLETE (walk records)' if carr else 'NONE_DECLARED'},
            'source': {'goodtypes': source(r'data\logic\goodtypes.cif'), 'goodgraphics': source(r'data\engine2d\inis\goods\goodgraphics.cif')}}
    write(folder / 'metadata.json', meta)
    rows.append({'GOOD_ID': g, 'NATIVE_NAME': name, 'ENGLISH': meta['english'], 'LANDSCAPE_TYPE': lt, 'GFX_LANDSCAPE': gid,
                 'GFX_LANDSCAPE_NAME': meta['resolvedGfxLandscapeName'], 'PILE_VALENCIES': [v['valency'] for v in meta['pileValencies']],
                 'ICON_BOB': icon['bobId'] if icon else '', 'ICON_PATH': icon.get('path') if icon else '', 'BMD': meta['bodyLibrary'],
                 'PALETTE': meta['palette'], 'CARRIED_ANIMATIONS': len(carr), 'CARRIED_TRIBES': sorted({int(r['TRIBE_ID']) for r in carr}),
                 'HUMAN_RANDOM_PALETTE': meta['carriedVisual']['humanRandomPalette'], 'PRODUCED_IN_HOUSE': meta['production']['isProducedInHouse'],
                 'PRODUCTION_INPUTS': meta['production']['productionInputGoods'], 'PRODUCERS': {o['tribe']: [h['houseName'] for h in o['producedInHouseTypes']] for o in owners if o['producedInHouseTypes']},
                 'ALLOWED_TRIBES': [o['tribe'] for o in owners if o['allowgood']], 'WEAPON_TYPE': scalar(b, 'weapontype'), 'ARMOR_TYPE': scalar(b, 'armortype'),
                 'OWNERSHIP': 'SHARED', 'CONFIDENCE': 'SOURCE_COMPLETE' if lm else ('PARTIAL' if g <= 55 else 'UNKNOWN_NO_VISUAL'),
                 'METADATA': rel(folder / 'metadata.json')})
csvout(ROOT / 'Catalogs/goods.csv', rows)
write(ROOT / 'Catalogs/goods.json', rows)
for t, gs in tribe_goods.items():
    write(ROOT / TF[t] / 'Goods' / 'index.json', {'tribe': t, 'tribeName': scalar(TRIBES[t], 'name'), 'ownership': 'Goods are a shared native table; this list is the tribe allowgood set. Visuals live in Shared/Goods.',
                                                  'goods': [{'goodId': g, 'nativeName': scalar(GOODS[g], 'name'), 'english': GTXT.get(g, {}).get('singular'),
                                                             'metadata': f'Shared/Goods/good_{g:02d}_{slug(scalar(GOODS[g], "name"))}/metadata.json'} for g in gs]})
print('goods', len(rows), 'with pile', sum(1 for r in rows if r['GFX_LANDSCAPE'] is not None), 'with icon', sum(1 for r in rows if r['ICON_BOB'] != ''),
      'carried', sum(1 for r in rows if r['CARRIED_ANIMATIONS']))
for r in rows:
    if r['CONFIDENCE'] != 'SOURCE_COMPLETE':
        print(r['GOOD_ID'], r['NATIVE_NAME'], r['LANDSCAPE_TYPE'], r['CONFIDENCE'])
