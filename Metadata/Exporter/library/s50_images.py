"""Stage 50: every PCX/BMP/PSD image + terrain patterns (pattern.cif) + transitions (transitions.cif).

PCX: production decodeIndexedPcx (export_pcx.exe) compared with an independent PIL decode.
Output PNGs are *indexed* (mode P) with the original palette, so indices and palette are both preserved losslessly.
BMP: no production decoder exists; decoded with PIL (SOURCE_COMPLETE, not PIXEL_CONFIRMED). Original bytes also kept.
"""
import collections, io, shutil
from PIL import Image, ImageDraw
from common import *


def place(path):
    p = norm(path)
    parts = p.split(B)
    n = parts[-1].rsplit('.', 1)[0]
    if p.startswith(r'data\engine2d\bin\textures' + B):
        return ROOT / 'Terrain/Textures' / n, 'Terrain'
    if p.startswith(r'data\engine2d\bin\palettes' + B):
        return ROOT / 'Metadata/Palettes' / parts[4] / n, 'Palette'
    if p.startswith(r'data\gui\palettes' + B):
        return ROOT / 'UI/Palettes' / n, 'UI'
    if p.startswith(r'data\gui' + B):
        return ROOT / 'UI' / ('Bitmaps' if 'bitmaps' in parts else 'Pictures') / n, 'UI'
    if p.startswith(r'data\maps' + B):
        return ROOT / 'UI/Maps' / slug(parts[2]) / slug(B.join(parts[3:-1]) or 'root') / n, 'UI'
    if p.startswith(r'data\text' + B):
        return ROOT / 'UI/Hypertext' / slug(B.join(parts[4:-1])) / n, 'UI'
    if p.startswith(r'data\edit' + B):
        return ROOT / 'UI/Editor' / n, 'UI'
    return ROOT / 'Unknown/Images' / slug(B.join(parts[:-1])) / n, 'Unknown'


def swatch(pal):
    im = Image.new('RGB', (16 * 12, 16 * 12))
    d = ImageDraw.Draw(im)
    for i in range(256):
        x, y = (i % 16) * 12, (i // 16) * 12
        d.rectangle([x, y, x + 11, y + 11], fill=tuple(int(v) for v in pal[i]))
    return im


rows, catalog = [], {}
for n, e in enumerate(INDEX.entries):
    ext = e.path.lower().rsplit('.', 1)[-1]
    if ext not in ('pcx', 'bmp', 'psd'):
        continue
    data = blob(e.path)
    base, cat = place(e.path)
    base.parent.mkdir(parents=True, exist_ok=True)
    row = {'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'FORMAT': ext.upper(), 'CATEGORY': cat, 'SHA256': source(e.path)['sha256']}
    if ext == 'pcx':
        idx, pal, st, val = pcx_decode(data, f'{n}')
        row.update(STATUS=st, VALIDATION=val)
        if idx is not None:
            im = Image.fromarray(idx, 'P')
            im.putpalette(pal.flatten().tolist())
            out = base.with_suffix('.png')
            im.save(out)
            row.update(WIDTH=idx.shape[1], HEIGHT=idx.shape[0], OUTPUT=rel(out), PALETTE_SOURCE='embedded PCX 256-colour palette')
            if cat == 'Palette' or (idx.shape[0] * idx.shape[1] <= 4):
                sw = base.parent / (base.name + '__swatch.png')
                swatch(pal).save(sw)
                (base.parent / (base.name + '.rgb')).write_bytes(pal.tobytes())
                row['SWATCH'] = rel(sw)
        catalog[norm(e.path)] = row
    elif ext == 'bmp':
        try:
            im = Image.open(io.BytesIO(data))
            im.load()
            out = base.with_suffix('.png')
            im.save(out)
            row.update(STATUS='DECODED', VALIDATION='SOURCE_COMPLETE (PIL standard BMP; no production decoder to compare)', WIDTH=im.size[0],
                       HEIGHT=im.size[1], MODE=im.mode, OUTPUT=rel(out))
        except Exception as x:
            row.update(STATUS=f'FAILED {x}', VALIDATION='UNKNOWN')
    else:
        out = base.with_suffix('.psd')
        out.write_bytes(data)
        row.update(STATUS='ORIGINAL_PRESERVED', VALIDATION='UNKNOWN (PSD not decoded; original bytes copied)', OUTPUT=rel(out))
    rows.append(row)

# loose DataX files (Pictures/*.bmp, Mouse/*.cur)
for p in sorted((DATAX / 'Pictures').glob('*')) + sorted((DATAX / 'Mouse').glob('*')):
    row = {'ENTRY_ID': '', 'ENTRY_NAME': str(p), 'FORMAT': p.suffix[1:].upper(), 'SHA256': sha_file(p)}
    if p.suffix.lower() == '.bmp':
        im = Image.open(p); im.load()
        out = ROOT / 'UI/Pictures/DataX' / (p.stem + '.png'); out.parent.mkdir(parents=True, exist_ok=True); im.save(out)
        row.update(CATEGORY='UI', STATUS='DECODED', VALIDATION='SOURCE_COMPLETE (PIL BMP)', WIDTH=im.size[0], HEIGHT=im.size[1], MODE=im.mode, OUTPUT=rel(out))
    else:
        out = ROOT / 'UI/Cursors' / p.name; out.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, out)
        row.update(CATEGORY='UI', STATUS='ORIGINAL_PRESERVED', OUTPUT=rel(out))
        try:
            im = Image.open(p); im.load()
            prev = out.with_suffix('.png'); im.save(prev)
            row.update(VALIDATION='SOURCE_COMPLETE (PIL CUR decode preview)', WIDTH=im.size[0], HEIGHT=im.size[1], PREVIEW=rel(prev))
        except Exception as x:
            row.update(VALIDATION=f'PREVIEW_FAILED {type(x).__name__}')
    rows.append(row)
csvout(ROOT / 'Catalogs/images.csv', rows)
print('images', len(rows), collections.Counter(r['STATUS'] for r in rows), collections.Counter(str(r.get('VALIDATION', ''))[:15] for r in rows))

# ---------------------------------------------------------------- terrain patterns
P = cif(r'data\engine2d\inis\patterns\pattern.cif')
TP = {scalar(b, 'type'): b for b in cif(r'data\logic\trianglepatterntypes.cif')}
textures = {}


def tex(path):
    k = norm(path)
    if k not in textures:
        idx, pal, st, val = pcx_decode(blob(path), 'tex_' + slug(stem(path)))
        textures[k] = (idx, pal)
    return textures[k]


def tri_crop(idx, pal, a, b):
    xs = [a[0], a[2], a[4], b[0], b[2], b[4]]
    ys = [a[1], a[3], a[5], b[1], b[3], b[5]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    crop = idx[y0:y1 + 1, x0:x1 + 1]
    im = Image.fromarray(crop, 'P'); im.putpalette(pal.flatten().tolist())
    mask = Image.new('L', crop.shape[::-1], 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(a[0] - x0, a[1] - y0), (a[2] - x0, a[3] - y0), (a[4] - x0, a[5] - y0)], fill=85)
    d.polygon([(b[0] - x0, b[1] - y0), (b[2] - x0, b[3] - y0), (b[4] - x0, b[5] - y0)], fill=170)
    return im, mask, [x0, y0, x1, y1]


prow = []
for pid, b in enumerate(P):
    name = str(scalar(b, 'editname', pid))
    group = str(scalar(b, 'editgroups', 'misc'))
    t = scalar(b, 'gfxtexture')
    a, bb = commands(b, 'gfxcoordsa')[0], commands(b, 'gfxcoordsb')[0]
    lt = scalar(b, 'logictype')
    folder = ROOT / 'Terrain/Patterns' / slug(group)
    folder.mkdir(parents=True, exist_ok=True)
    idx, pal = tex(t)
    im, mask, box = tri_crop(idx, pal, a, bb)
    out = folder / f'{pid:03d}_{slug(name)}.png'
    im.save(out)
    mask.save(out.with_name(out.stem + '__triangles.png'))
    meta = {'gfxPatternId': pid, 'nativeName': name, 'editGroups': commands(b, 'editgroups'), 'logicType': lt,
            'logicTypeDefinition': TP.get(lt), 'texture': t, 'textureOutput': catalog.get(norm(t), {}).get('OUTPUT'), 'triangleA': a, 'triangleB': bb,
            'cropBox': box, 'crop': rel(out), 'triangleMask': rel(out.with_name(out.stem + '__triangles.png')),
            'maskValues': {'85': 'triangle A', '170': 'triangle B'}, 'definition': b,
            'nativeReferences': {'Game.exe': ['0x0048E24E pattern.cif loader (stride 0x70)', '0x00491EA8 pattern texture resolve'], 'cpp': 'GfxPatternRegistry'},
            'confidence': {'source': 'SOURCE_COMPLETE', 'pixels': 'PIXEL_CONFIRMED texture decode', 'presentation': 'PRESENTATION_PARTIAL: texture-space crop; isometric triangle projection, lighting and transitions not applied'}}
    write(out.with_suffix('.json'), meta)
    prow.append({'PATTERN_ID': pid, 'NATIVE_NAME': name, 'EDIT_GROUP': group, 'LOGIC_TYPE': lt, 'LOGIC_TYPE_NAME': scalar(TP.get(lt, {'commands': []}), 'debugname'),
                 'TEXTURE': t, 'TRIANGLE_A': a, 'TRIANGLE_B': bb, 'CROP': rel(out), 'METADATA': rel(out.with_suffix('.json')), 'KIND': 'pattern',
                 'CONFIDENCE': 'SOURCE_COMPLETE'})
T = cif(r'data\engine2d\inis\patterntransitions\transitions.cif')
pointtypes = [b for b in T if b['section'] == 'pointtype']
for tid, b in enumerate([b for b in T if b['section'] == 'transition']):
    name = str(scalar(b, 'name'))
    meta = {'transitionId': tid, 'nativeName': name, 'pointType': scalar(b, 'pointtype'),
            'pointTypeDefinition': next((p for p in pointtypes if scalar(p, 'name') == scalar(b, 'pointtype')), None),
            'texture': scalar(b, 'gfxtexture'), 'textureAlpha': scalar(b, 'gfxtexturealpha'),
            'textureOutput': catalog.get(norm(scalar(b, 'gfxtexture')), {}).get('OUTPUT'),
            'alphaOutput': catalog.get(norm(scalar(b, 'gfxtexturealpha') or ''), {}).get('OUTPUT'),
            'trianglesA': commands(b, 'gfxcoordsa'), 'trianglesB': commands(b, 'gfxcoordsb'), 'definition': b,
            'nativeReferences': {'cpp': 'PatternTransitionRegistry (pattern_transition_registry.hpp)'},
            'confidence': {'source': 'SOURCE_COMPLETE', 'presentation': 'PRESENTATION_PARTIAL: alpha texture is blend DATA; in-world blending not baked'}}
    out = ROOT / 'Terrain/Transitions' / f'{tid:02d}_{slug(name)}.json'
    write(out, meta)
    prow.append({'PATTERN_ID': f'T{tid}', 'NATIVE_NAME': name, 'EDIT_GROUP': 'transition:' + str(scalar(b, 'pointtype')), 'LOGIC_TYPE': '', 'TEXTURE': meta['texture'],
                 'TEXTURE_ALPHA': meta['textureAlpha'], 'TRIANGLE_A': len(meta['trianglesA']), 'TRIANGLE_B': len(meta['trianglesB']), 'CROP': meta['textureOutput'],
                 'METADATA': rel(out), 'KIND': 'transition', 'CONFIDENCE': 'SOURCE_COMPLETE'})
write(ROOT / 'Terrain/Transitions/point_types.json', pointtypes)
csvout(ROOT / 'Catalogs/terrain.csv', prow)
print('patterns', sum(r['KIND'] == 'pattern' for r in prow), 'transitions', sum(r['KIND'] == 'transition' for r in prow))
