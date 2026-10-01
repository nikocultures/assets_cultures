"""Stage 25: effects -- particle tables, projectiles, code-driven world markers, landscape/building effect cross-reference.

Native sources:
  data\\engine2d\\inis\\particel\\particel.cif        [Particel] name, palette, bobmanager, maxvalency, gfxframes <valency> <bob..>, animloop, bobtype, specialtype
  data\\engine2d\\inis\\particel\\generator.cif       [ParticelGenerator] (smoke / rain / snow ...)
  data\\engine2d\\inis\\particel\\particeleffects.cif [ParticelEffect] logictype -> particelname
  code-driven libraries (production_world_compositor.hpp):
    ls_gui_bubbles.bmd  selected-Human health hearts: BOB 21 - percent/10 (11..21), palettes human_player01..10 (0x004905B9 / 0x0048B49A)
    ls_guidepost.bmd    signposts: post BOB 0 + arm BOB 1..18 (signpostArmFrame), palette tree01 or owner human_playerNN
"""
import collections, csv, glob
from PIL import Image
from common import *

OUT = ROOT / 'Shared/Effects'
USED = collections.defaultdict(lambda: collections.defaultdict(set))
VALID = collections.defaultdict(set)
rows = []
framecache = {}


def render(lib, bob, pal, folder, role):
    fr = {f['bobId']: f for f in bmd(lib)[0]}
    f = fr.get(bob)
    if f is None:
        return {'bobId': bob, 'status': 'BOB_ABSENT_IN_LIBRARY'}
    if not (f['width'] and f['height'] and f['kind']):
        return {'bobId': bob, 'status': 'EMPTY_FRAME'}
    key = (norm(lib), bob, (pal or '').lower())
    if key not in framecache:
        p = frame_planes(lib, f)
        if pal:
            img = rgba(p, palette(pal)[0], f['kind'])
            VALID[(lib, pal)].add(bob)
        else:
            img = np.dstack([p[:, :, 0]] * 3 + [p[:, :, 1]])
        out = folder / (f'bob_{bob:04d}' + (f'__{slug(pal)}' if pal else '__index_data') + '.png')
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(img, 'RGBA').save(out)
        rec = {'path': rel(out), 'kind': f['kind'], 'width': f['width'], 'height': f['height'], 'pivot': [-f['x'], -f['y']]}
        if f['kind'] == 4:
            sec = out.with_name(out.stem + '__kind4_secondary.png')
            Image.fromarray(np.dstack([p[:, :, 2]] * 3 + [p[:, :, 1]]), 'RGBA').save(sec)
            rec['kind4Secondary'] = rel(sec)
        framecache[key] = rec
    USED[lib][bob].add(role)
    return dict(framecache[key], bobId=bob, status='RENDERED')


# ---------------------------------------------------------------- particles
P = cif(r'data\engine2d\inis\particel\particel.cif')
G = cif(r'data\engine2d\inis\particel\generator.cif')
E = cif(r'data\engine2d\inis\particel\particeleffects.cif')
gens = collections.defaultdict(list)
for b in G:
    gens[str(scalar(b, 'generate', '')).lower()].append(b)
effs = collections.defaultdict(list)
for b in E:
    effs[str(scalar(b, 'particelname', '')).lower()].append(b)
for i, b in enumerate(P):
    name = str(scalar(b, 'name', i))
    lib, pal = scalar(b, 'bobmanager'), scalar(b, 'palette')
    folder = OUT / 'Particles' / f'{i:02d}_{slug(name)}'
    meta = {'particleId': i, 'nativeName': name, 'library': lib, 'palette': pal, 'definition': b, 'source': source(r'data\engine2d\inis\particel\particel.cif'),
            'generators': gens.get(name.lower(), []), 'particleEffects': effs.get(name.lower(), []), 'valencies': [], 'errors': []}
    if not lib or not has(lib):
        meta['errors'].append(f'library {lib} not in archive')
    elif pal and pal.lower() not in palette_defs():
        meta['errors'].append(f'palette {pal} not in palettes.cif')
    else:
        for args in commands(b, 'gfxframes'):
            meta['valencies'].append({'valency': args[0], 'frames': [render(lib, x, pal, folder, f'particle:{name}') for x in args[1:]]})
    meta['confidence'] = {'source': 'SOURCE_COMPLETE' if not meta['errors'] else 'PARTIAL', 'pixels': 'PIXEL_CONFIRMED per frame (Catalogs/pixel_validation.csv)',
                          'presentation': f'PRESENTATION_PARTIAL: bobtype {scalar(b, "bobtype")} blending, movement, lifetime and wind are runtime'}
    write(folder / 'metadata.json', meta)
    effkinds = ', '.join(f"particeleffect logictype {scalar(e, 'logictype')}" for e in meta['particleEffects'])
    rows.append({'EFFECT_KIND': 'particle', 'NATIVE_NAME': name, 'NATIVE_ID': i, 'SOURCE_TABLE': 'particel.cif', 'LIBRARY': lib, 'PALETTE': pal,
                 'FRAMES': sum(len(v['frames']) for v in meta['valencies']), 'BOBS': sorted({fr['bobId'] for v in meta['valencies'] for fr in v['frames']}),
                 'TRIGGERS': [scalar(g, 'name') for g in meta['generators']] + ([effkinds] if effkinds else []),
                 'SEMANTICS': 'native particle definition (name from table)', 'PREVIEW': next((fr.get('path') for v in meta['valencies'] for fr in v['frames'] if fr.get('path')), ''),
                 'METADATA': rel(folder / 'metadata.json'), 'CONFIDENCE': meta['confidence']['source']})
for b in G:
    rows.append({'EFFECT_KIND': 'particle_generator', 'NATIVE_NAME': scalar(b, 'name'), 'SOURCE_TABLE': 'generator.cif', 'TRIGGERS': [scalar(b, 'generate')],
                 'SEMANTICS': json.dumps({c['name']: c['arguments'] for c in b['commands']}), 'CONFIDENCE': 'SOURCE_COMPLETE', 'METADATA': 'Metadata/Sources/CIF/data/engine2d/inis/particel/generator.cif.json'})
for b in E:
    rows.append({'EFFECT_KIND': 'particle_effect', 'NATIVE_NAME': scalar(b, 'particelname'), 'NATIVE_ID': scalar(b, 'logictype'), 'SOURCE_TABLE': 'particeleffects.cif',
                 'SEMANTICS': json.dumps({c['name']: c['arguments'] for c in b['commands']}), 'CONFIDENCE': 'SOURCE_COMPLETE',
                 'METADATA': 'Metadata/Sources/CIF/data/engine2d/inis/particel/particeleffects.cif.json'})

# ---------------------------------------------------------------- code-driven markers
lib = r'data\engine2d\bin\bobs\ls_gui_bubbles.bmd'
folder = OUT / 'Markers/health_hearts'
hearts = {f'human_player{c:02d}': [render(lib, x, f'human_player{c:02d}', folder / f'player{c:02d}', 'marker:health_heart') for x in range(11, 22)]
          for c in range(1, 11) if f'human_player{c:02d}' in palette_defs()}
write(folder / 'metadata.json', {'library': lib, 'rule': 'BOB = 21 - healthPercent/10 (11 = full, 21 = empty); palette human_playerNN by owner colour',
                                 'evidence': 'production_world_compositor.hpp (Game 0x004905B9 load, 0x0048B49A owner colour, 0x00493656 selected-Human pass)',
                                 'frames': hearts, 'confidence': 'SOURCE_COMPLETE (code evidence); PIXEL_CONFIRMED frames'})
rows.append({'EFFECT_KIND': 'selection_marker', 'NATIVE_NAME': 'selected Human health heart', 'SOURCE_TABLE': 'code: production_world_compositor.hpp', 'LIBRARY': lib,
             'PALETTE': 'human_player01..10', 'FRAMES': 11, 'BOBS': list(range(11, 22)), 'SEMANTICS': 'BOB = 21 - health%/10', 'PREVIEW': hearts['human_player01'][0].get('path', ''),
             'METADATA': rel(folder / 'metadata.json'), 'CONFIDENCE': 'SOURCE_COMPLETE'})
lib = r'data\engine2d\bin\bobs\ls_guidepost.bmd'
folder = OUT / 'Markers/signposts'
sign = {p_: [render(lib, x, p_, folder / slug(p_), 'marker:signpost') for x in range(0, 19)] for p_ in ['tree01'] + [f'human_player{c:02d}' for c in range(1, 11)] if p_ in palette_defs()}
write(folder / 'metadata.json', {'library': lib, 'rule': 'post BOB 0 + one arm BOB per destination: signpostArmFrame(angle) in 1..18; palette tree01 (unowned) or owner human_playerNN',
                                 'evidence': 'signpost_visual.hpp signpostArmFrame; production_world_compositor.hpp signpost pass (0x004956B7 outline)', 'frames': sign,
                                 'confidence': 'SOURCE_COMPLETE (code evidence); PIXEL_CONFIRMED frames'})
rows.append({'EFFECT_KIND': 'world_marker', 'NATIVE_NAME': 'signpost', 'SOURCE_TABLE': 'code: signpost_visual.hpp', 'LIBRARY': lib, 'PALETTE': 'tree01 / human_player01..10',
             'FRAMES': 19, 'BOBS': list(range(0, 19)), 'SEMANTICS': 'post 0 + arms 1..18 by direction angle', 'PREVIEW': sign['tree01'][0].get('path', ''),
             'METADATA': rel(folder / 'metadata.json'), 'CONFIDENCE': 'SOURCE_COMPLETE'})

# ---------------------------------------------------------------- cross-reference: landscape effects and building effect points
for p in sorted(glob.glob(str(ROOT / 'Shared/Effects/Landscape/*/metadata.json'))):
    m = read(p)
    first = next((fr for v in m['valencies'] for fr in v['frames'] if fr.get('path')), {})
    rows.append({'EFFECT_KIND': 'landscape_effect', 'NATIVE_NAME': m['nativeName'], 'NATIVE_ID': m['gfxLandscapeId'], 'SOURCE_TABLE': 'landscapes.cif (editgroup effects)',
                 'LIBRARY': m['bodyLibrary'], 'PALETTE': (m['palettes'] or [''])[0], 'FRAMES': sum(len(v['frames']) for v in m['valencies']),
                 'BOBS': sorted({fr['bobId'] for v in m['valencies'] for fr in v['frames']}), 'SEMANTICS': 'GfxLandscape in native effects edit group',
                 'PREVIEW': first.get('path', ''), 'METADATA': rel(p), 'CONFIDENCE': m['confidence']['source']})
bfx = collections.defaultdict(list)
for p in glob.glob(str(ROOT / '*/Buildings/**/effects/metadata.json'), recursive=True) + glob.glob(str(ROOT / 'Other Tribes/*/Buildings/**/effects/metadata.json'), recursive=True):
    m = read(p)
    for k in ('gfxfirepoint', 'gfxsmokepoint', 'gfxholyfirepoint', 'gfxoverlaylandscape'):
        if m.get(k):
            bfx[k].append({'level': rel(Path(p).parent.parent), 'points': len(m[k])})
for k, v in bfx.items():
    rows.append({'EFFECT_KIND': 'building_effect_point', 'NATIVE_NAME': k, 'SOURCE_TABLE': 'houses.cif', 'FRAMES': '', 'TRIGGERS': [x['level'] for x in v][:400],
                 'SEMANTICS': {'gfxfirepoint': 'fire spawn points (fx fire house 0..2)', 'gfxsmokepoint': 'smoke spawn points (fx smoke)',
                               'gfxholyfirepoint': 'holy fire points (fx fire incense)', 'gfxoverlaylandscape': 'landscape overlays'}[k],
                 'METADATA': 'Catalogs/effects.json', 'CONFIDENCE': 'SOURCE_COMPLETE (points; per-level files: <level>/effects/metadata.json); PRESENTATION_PARTIAL (activation)'})

# ---------------------------------------------------------------- validation and outputs
val = []
for (lib, pal), bobs in VALID.items():
    res = validate(lib, palette(pal)[0], list(bobs), 'fx_' + pal)
    c = collections.Counter(res.values())
    val.append({'LIBRARY': lib, 'PALETTE': pal, 'FRAMES_DRAWN': len(bobs), 'PIXEL_CONFIRMED': c.get('PIXEL_CONFIRMED', 0), 'MISMATCH': c.get('PIXEL_MISMATCH', 0),
                'OTHER': sum(v for k, v in c.items() if k not in ('PIXEL_CONFIRMED', 'PIXEL_MISMATCH')), 'REFERENCE': 'production drawBobClippedBorrowed32', 'SCOPE': 'effects'})
write(ROOT / 'Metadata/Effects/validation.json', val)
write(ROOT / 'Metadata/Effects/usage.json', {lib: {str(b): sorted(v) for b, v in d.items()} for lib, d in USED.items()}, compact=True)
csvout(ROOT / 'Catalogs/effects.csv', rows)
write(ROOT / 'Catalogs/effects.json', rows)
print('effects rows', len(rows), collections.Counter(r['EFFECT_KIND'] for r in rows), 'validated', sum(v['PIXEL_CONFIRMED'] for v in val), 'mismatch', sum(v['MISMATCH'] for v in val))
