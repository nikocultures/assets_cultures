"""Stage 60: UI sprite libraries (data\\gui\\lang\\eng\\bobs\\*.bmd) and fonts (*.fnt).

Palette per GUI sprite is taken ONLY from production draw-call evidence (literal sprite id + palette member in
production_gameplay_ui.hpp / production_frontend.cpp, whose palette members are loaded from named PCX files).
Sprites without such evidence are exported as palette-index DATA (palette UNKNOWN), never with a guessed palette.
Fonts: 16-byte FNT header + embedded BMD record decoded by the production BMD decoder; glyph colour is draw-time
palette dependent, so glyphs are exported as index DATA plus metrics.
"""
import collections, re, struct
from PIL import Image
from common import *

SRC = Path(r'E:\cultures\cpp-reconstruction\source')
FILES = [SRC / 'include/cultures/ui/production_gameplay_ui.hpp', SRC / 'src/ui/production_frontend.cpp']
PALVAR = {
    'production_gameplay_ui.hpp': {'framePalette_': r'data\gui\palettes\frame.pcx', 'iconPalette_': r'data\gui\palettes\IconsLeft.pcx',
                                   'contextPalette_': r'data\gui\palettes\Context.pcx', 'hitpointBarPalette_': r'data\gui\palettes\bar_hitpoints.pcx',
                                   'needBarPalette_': r'data\gui\palettes\bar_standart.pcx', 'disabledBarPalette_': r'data\gui\palettes\bar_disabled.pcx',
                                   'defaultSpritePalette_': r'data\gui\palettes\bg_normal.pcx', 'papyrusPalette_': r'data\gui\palettes\papyrus.pcx'},
    'production_frontend.cpp': {'logoPalette_': r'data\engine2d\bin\palettes\gui\menu_funatics.pcx', 'campaignPalette_': r'data\gui\palettes\campaignmap.pcx',
                                'markerPalette_': r'data\gui\palettes\campaignbuttons.pcx', 'edgePalette_': r'data\gui\palettes\bg_normal.pcx',
                                'framePalette_': r'data\gui\palettes\frame.pcx', 'iconPalette_': r'data\gui\palettes\IconsLeft.pcx',
                                'fontPalette_': r'data\gui\palettes\font_white.pcx'}}
LIT = r'(0x[0-9A-Fa-f]+|\d+)'
PATTERNS = [
    ('gui', re.compile(r'drawSprite(?:Clipped)?\(\s*surface\s*,\s*' + LIT + r'\s*,.*?(\w+Palette_)')),
    ('gui', re.compile(r'drawButton\(\s*surface\s*,[^,]+,\s*' + LIT + r'\s*,\s*(\w+Palette_)')),
    ('gui', re.compile(r'drawImageWidget\(\s*surface\s*,[^,]+,\s*' + LIT + r'\s*,\s*(\w+Palette_)')),
    ('gui', re.compile(r'nativeBar\(\s*\d+\s*,\s*' + LIT + r'\s*,()')),  # lambda draws the icon with iconPalette_
    ('frontend', re.compile(r'sprite\((gui_|logos_)\s*,\s*' + LIT + r'\s*,.*?(\w+Palette_)')),
]
evidence = collections.defaultdict(list)
for f in FILES:
    lines = f.read_text(encoding='utf-8', errors='replace').split('\n')
    for i, line in enumerate(lines):
        for kind, rx in PATTERNS:
            for m in rx.finditer(line):
                g = m.groups()
                if kind == 'frontend':
                    lib = 'ls_gui_window' if g[0] == 'gui_' else 'ls_menu_logos'
                    sid, var = g[1], g[2]
                else:
                    lib, sid, var = 'ls_gui_window', g[0], (g[1] or 'iconPalette_')
                pal = PALVAR[f.name].get(var)
                ctx = next((lines[j].strip() for j in range(i, max(i - 6, -1), -1) if lines[j].strip().startswith('//')), '')
                evidence[(lib, int(sid, 0))].append({'file': f.name, 'line': i + 1, 'paletteMember': var, 'palette': pal,
                                                      'code': line.strip()[:220], 'nearestComment': ctx[:220]})
# multi-line calls: same patterns over the whole text, call text without ';'
for f in FILES:
    text = f.read_text(encoding='utf-8', errors='replace')
    for kind, rx in PATTERNS[:3]:
        mrx = re.compile(rx.pattern.replace('.*?', r'[^;]*?').replace(r'[^,]+', r'[^,;]+'), re.S)
        for m in mrx.finditer(text):
            sid, var = m.group(1), m.group(2)
            line = text.count('\n', 0, m.start()) + 1
            key = ('ls_gui_window', int(sid, 0))
            if any(e['file'] == f.name and e['line'] == line for e in evidence[key]):
                continue
            evidence[key].append({'file': f.name, 'line': line, 'paletteMember': var, 'palette': PALVAR[f.name].get(var),
                                  'code': ' '.join(m.group(0).split())[:220], 'nearestComment': 'multi-line call'})
GUI_HPP = FILES[0]
gtext = GUI_HPP.read_text(encoding='utf-8', errors='replace')
MAINTXT = localization(cif(r'data\text\eng\strings\ingamegui\ingameguimain.cif'))
for table in ('kOriginalLeftToolbar', 'kOriginalMinimapControls', 'kOriginalTopButton'):
    start = gtext.index(f'{table}{{')
    body = gtext[start:gtext.index('};', start)]
    line0 = gtext.count('\n', 0, start) + 1
    for m in re.finditer(r'\{\{[^}]*\}\s*,\s*' + LIT + r'\s*,\s*' + LIT + r'\s*,\s*(-?\w+)', body) if table != 'kOriginalTopButton' else \
            re.finditer(r'\{[^}]*\}\s*,\s*' + LIT + r'\s*,\s*' + LIT + r'\s*,\s*(-?\w+)', body):
        sid, cmd, tip = int(m.group(1), 0), int(m.group(2), 0), int(m.group(3), 0)
        evidence[('ls_gui_window', sid)].append({'file': GUI_HPP.name, 'line': line0, 'paletteMember': 'iconPalette_', 'palette': PALVAR[GUI_HPP.name]['iconPalette_'],
                                                 'code': f'{table}: sprite {sid:#x} command {cmd:#x} tooltip {tip}',
                                                 'tooltip': MAINTXT.get(tip, {}).get('singular'), 'commandId': cmd})
for fn, note in (('simulationSpeedIconFor', 'game speed band icon (0x004A299B)'), ('messageFilterIconFor', 'message filter level icon (0x004A2A55)')):
    start = gtext.index(fn + '(')
    body = gtext[start:gtext.index('}', start)]
    for m in re.finditer(r'return\s+' + LIT, body):
        evidence[('ls_gui_window', int(m.group(1), 0))].append({'file': GUI_HPP.name, 'line': gtext.count('\n', 0, start) + 1, 'paletteMember': 'iconPalette_',
                                                                 'palette': PALVAR[GUI_HPP.name]['iconPalette_'], 'code': f'{fn} -> {m.group(1)}', 'nearestComment': note})
SAP = SRC / 'include/cultures/ui/selection_action_panel.hpp'
stext = SAP.read_text(encoding='utf-8', errors='replace')
for m in re.finditer(r'case\s+(\d+)\s*:\s*return\s+' + LIT, stext):
    evidence[('ls_gui_window', int(m.group(2), 0))].append({'file': SAP.name, 'line': stext.count('\n', 0, m.start()) + 1, 'paletteMember': 'contextPalette_',
                                                            'palette': PALVAR[GUI_HPP.name]['contextPalette_'],
                                                            'code': f'humanActionSprite(action {m.group(1)}) -> {m.group(2)}; drawn at production_gameplay_ui.hpp widget.spriteId, contextPalette_',
                                                            'humanActionId': int(m.group(1)), 'commandId': int(m.group(1)) + 3000})
# UiSkin_DrawTiledFrame (0x004E2445), skin_tiled_frame.hpp frameAtlasBases: corners with frame.pcx, edges with bg_normal.pcx
for style, (edge, corner) in {'1': (5, 0), '5': (13, 21), 'other': (13, 9)}.items():
    for k in range(4):
        evidence[('ls_gui_window', edge + k)].append({'file': 'skin_tiled_frame.hpp', 'line': 52, 'paletteMember': 'defaultSpritePalette_/edgePalette_',
                                                      'palette': r'data\gui\palettes\bg_normal.pcx', 'code': f'frame style {style} edge {k}', 'nearestComment': 'UiSkin_DrawTiledFrame 0x004E2445 edges'})
        evidence[('ls_gui_window', corner + k)].append({'file': 'skin_tiled_frame.hpp', 'line': 52, 'paletteMember': 'framePalette_',
                                                        'palette': r'data\gui\palettes\frame.pcx', 'code': f'frame style {style} corner {k}', 'nearestComment': 'UiSkin_DrawTiledFrame 0x004E2445 corners'})
LIBS = {'ls_gui_window': r'data\gui\lang\eng\bobs\ls_gui_window.bmd', 'ls_menu_logos': r'data\gui\lang\eng\bobs\ls_menu_logos.bmd'}
rows, VALID = [], collections.defaultdict(set)
for libkey, lib in LIBS.items():
    frames, _ = bmd(lib)
    for f in frames:
        bob = f['bobId']
        ev = evidence.get((libkey, bob), [])
        pals = sorted({e['palette'] for e in ev if e['palette']})
        base = ROOT / 'UI/Sprites' / libkey
        row = {'LIBRARY': lib, 'BOB_ID': bob, 'KIND': f['kind'], 'WIDTH': f['width'], 'HEIGHT': f['height'], 'PIVOT': [-f['x'], -f['y']],
               'EVIDENCE': [f"{e['file']}:{e['line']}" for e in ev], 'PALETTES': pals, 'OUTPUTS': []}
        if not (f['width'] and f['height'] and f['kind']):
            row['STATUS'] = 'EMPTY_FRAME'
            rows.append(row)
            continue
        p = frame_planes(lib, f)
        for pal in pals:
            arr = pcx_palette(pal)
            out = base / slug(stem(pal)) / f'bob_{bob:04d}.png'
            out.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(rgba(p, arr, f['kind']), 'RGBA').save(out)
            row['OUTPUTS'].append(rel(out))
            VALID[(lib, pal)].add(bob)
        data = base / '_index_data' / f'bob_{bob:04d}.png'
        data.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.dstack([p[:, :, 0]] * 3 + [p[:, :, 1]]), 'RGBA').save(data)
        row['INDEX_DATA'] = rel(data)
        row['STATUS'] = 'PALETTE_EVIDENCED' if pals else 'PALETTE_UNKNOWN (index data only)'
        row['CONFIDENCE'] = 'PIXEL_CONFIRMED' if pals else 'UNKNOWN'
        write(base / 'metadata' / f'bob_{bob:04d}.json', dict(row, evidenceDetail=ev, source=source(lib), descriptor=f))
        rows.append(row)
val = []
for (lib, pal), bobs in VALID.items():
    r = validate(lib, pcx_palette(pal), list(bobs), 'ui_' + stem(pal))
    c = collections.Counter(r.values())
    val.append({'LIBRARY': lib, 'PALETTE': pal, 'FRAMES_DRAWN': len(bobs), 'PIXEL_CONFIRMED': c.get('PIXEL_CONFIRMED', 0), 'MISMATCH': c.get('PIXEL_MISMATCH', 0),
                'OTHER': sum(v for k, v in c.items() if k not in ('PIXEL_CONFIRMED', 'PIXEL_MISMATCH')), 'REFERENCE': 'production drawBobClippedBorrowed32', 'SCOPE': 'ui'})
write(ROOT / 'Metadata/UI/validation.json', val)
write(ROOT / 'Metadata/UI/sprite_evidence.json', {f'{k[0]}:{k[1]}': v for k, v in sorted(evidence.items())})
csvout(ROOT / 'Catalogs/ui_sprites.csv', rows)
print('ui sprites', len(rows), collections.Counter(r['STATUS'] for r in rows), 'validated', sum(v['PIXEL_CONFIRMED'] for v in val), 'mismatch', sum(v['MISMATCH'] for v in val))

# ---------------------------------------------------------------- fonts
frows = []
seen = {}
for n, e in enumerate(INDEX.entries):
    if not e.path.lower().endswith('.fnt'):
        continue
    data = blob(e.path)
    h = hashlib.sha256(data).hexdigest()
    row = {'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'SHA256': h}
    if h in seen:
        row.update(STATUS='DUPLICATE_OF', DUPLICATE_OF=seen[h])
        frows.append(row)
        continue
    seen[h] = e.path
    magic, ver, field08, line_h = struct.unpack_from('<4I', data)
    row.update(MAGIC=hex(magic), VERSION=ver, FIELD_08=field08, LINE_HEIGHT=line_h)
    d = CACHE / 'fnt' / f'{n}'
    d.mkdir(parents=True, exist_ok=True)
    (d / 'embedded.bmd').write_bytes(data[16:])
    r = subprocess.run([str(PLANES_EXE), str(d / 'embedded.bmd'), str(d)], capture_output=True)
    if r.returncode:
        row['STATUS'] = f'PRODUCTION_DECODE_FAILED {r.returncode}'
        frows.append(row)
        continue
    fr = json.loads((d / 'frames.json').read_text())
    planes = (d / 'frames.planes').read_bytes()
    cw = max([g['width'] for g in fr] + [1]); ch = max([g['height'] for g in fr] + [1])
    sheet = np.zeros((ch * ((len(fr) + 15) // 16), cw * 16, 4), np.uint8)
    glyphs = []
    for i, g in enumerate(fr):
        ch_code = 0x20 + i
        gl = {'frameIndex': i, 'code': ch_code, 'char': chr(ch_code) if ch_code < 0x7F else f'0x{ch_code:02X} (cp1252: {bytes([ch_code]).decode("cp1252", "replace")})' if ch_code < 256 else '',
              'kind': g['kind'], 'width': g['width'], 'height': g['height'], 'x': g['x'], 'y': g['y']}
        if g['width'] and g['height'] and g['kind']:
            a = np.frombuffer(planes[g['offset']:g['offset'] + g['width'] * g['height'] * 3], np.uint8).reshape(g['height'], g['width'], 3)
            X, Y = (i % 16) * cw, (i // 16) * ch
            sheet[Y:Y + g['height'], X:X + g['width']] = np.dstack([a[:, :, 0]] * 3 + [a[:, :, 1]])
            gl['sheetRect'] = [X, Y, g['width'], g['height']]
        glyphs.append(gl)
    out = ROOT / 'UI/Fonts' / slug(B.join(norm(e.path).split(B)[1:-1])) / (stem(e.path) + '__index_data.png')
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet, 'RGBA').save(out)
    write(out.with_name(stem(e.path) + '.json'), {'source': source(e.path), 'header': {'magic': hex(magic), 'version': ver, 'field08': field08, 'lineHeight': line_h},
                                                  'firstCharacter': 0x20, 'glyphs': glyphs, 'sheet': rel(out),
                                                  'representation': 'RGB = palette index (DATA), alpha = coverage; colour comes from the draw-time palette (e.g. data\\gui\\palettes\\font_white.pcx in frontend)',
                                                  'decoder': 'production decodeBobLibraryBmd on embedded record (FNT header 16 bytes per cultures_fnt.py)',
                                                  'confidence': 'SOURCE_COMPLETE; PRESENTATION_PARTIAL (palette at draw time)'})
    row.update(STATUS='DECODED', GLYPHS=len(fr), OUTPUT=rel(out))
    frows.append(row)
csvout(ROOT / 'Catalogs/fonts.csv', frows)
print('fonts', len(frows), collections.Counter(r['STATUS'] for r in frows))
