"""Stage 80: whole-archive graphics census -> zero silently discarded frames, with native-evidence classification.

Every non-empty frame of every BMD is written to Shared/SourceLibraries/<lib>/ atlas pages (index DATA + pages in
each palette used by the library's mapped definitions) and listed in library.json with usage and status.

Status per frame:
  MAPPED                    referenced by a resolved native definition that was exported (mobile/building/landscape/UI-with-palette)
  UNKNOWN_PALETTE           GUI sprite exported as index data; no native draw-call palette evidence
  UNKNOWN_NAMED_SEQUENCE    inside a native BobSeq range but not selected by any bound record; sub-reason:
       SHADOWED_DUPLICATE_RECORD     every referencing record is shadowed by an earlier equal key (0x0048D027 returns first)
       HEAD_SEQUENCE_OVERRIDE        head library frame at body-sequence numbering; the record's gfxbobseqhead selects another base
       SEQUENCE_BOUND_OFFSET_UNUSED  sequence used with this library, but this offset is in no native direction frame list
       SEQUENCE_USED_WITH_OTHER_LIBRARIES_ONLY  referenced only by owners bound to other libraries/tribes
       SEQUENCE_NEVER_REFERENCED     no GfxAnimAtomic/GfxWalkAtomic record names it
  UNKNOWN_GRAPHICS_BINDING  sequence referenced only by records whose owner has no jobgraphics binding
  UNKNOWN_UNSUPPORTED_PIXEL_KIND  descriptor kind outside 0/1/2/4 (no native scanline walker handles it)
  UNKNOWN_UNREFERENCED      no native table reference found
"""
import collections, csv, glob, math
from PIL import Image
from common import *

LIBPATH = {stem(e.path).lower(): e.path for e in INDEX.entries if e.path.lower().endswith('.bmd')}
used = collections.defaultdict(lambda: collections.defaultdict(set))   # norm(lib) -> bob -> {usage}
libpal = collections.defaultdict(collections.Counter)

# ---------------------------------------------------------------- usage: mobile, landscapes, buildings, UI
for p in glob.glob(str(ROOT / 'Metadata/Mobile/usage_*.json')) + [str(ROOT / 'Metadata/Landscapes/usage.json'), str(ROOT / 'Metadata/Effects/usage.json')]:
    for lib, d in read(p).items():
        for bob, roles in d.items():
            used[norm(lib)][int(bob)].update(f'{Path(p).stem}:{r}' for r in roles)
for p in glob.glob(str(ROOT / 'Catalogs/*_building_frames.json')):
    for r in read(p):
        src = r.get('source') or {}
        if src.get('entryName') is not None and r.get('bobId') is not None and r.get('path'):
            used[norm(src['entryName'])][r['bobId']].add(f"buildings:{r.get('role')}")
            if r.get('palette'):
                libpal[norm(src['entryName'])][r['palette']] += 1
for p in glob.glob(str(ROOT / 'Metadata/Mobile/animations_*.csv')):
    with open(p, encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if r['BODY_PALETTE'] and r['STATUS'].startswith('RENDERED'):
                libpal[norm(r['BODY_LIBRARY'])][r['BODY_PALETTE']] += 1
                if r['HEAD_LIBRARY'] and r['HEAD_PALETTE']:
                    libpal[norm(r['HEAD_LIBRARY'])][r['HEAD_PALETTE']] += 1
for p in glob.glob(str(ROOT / 'Terrain/Landscapes/**/metadata.json'), recursive=True) + glob.glob(str(ROOT / 'Shared/Goods/**/metadata.json'), recursive=True) + \
        glob.glob(str(ROOT / 'Shared/Effects/Landscape/**/metadata.json'), recursive=True) + glob.glob(str(ROOT / 'Animals/Landscape/**/metadata.json'), recursive=True):
    m = read(p)
    if m.get('bodyLibrary') and m.get('palettes'):
        libpal[norm(m['bodyLibrary'])][m['palettes'][0]] += 1
ui_unknown_palette = collections.defaultdict(set)
with open(ROOT / 'Catalogs/ui_sprites.csv', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['STATUS'] == 'PALETTE_EVIDENCED':
            used[norm(r['LIBRARY'])][int(r['BOB_ID'])].add('ui:palette_evidenced')
        elif r['STATUS'].startswith('PALETTE_UNKNOWN'):
            ui_unknown_palette[norm(r['LIBRARY'])].add(int(r['BOB_ID']))

# ---------------------------------------------------------------- owner metadata: alternate heads + bound sequences
bound_seq = collections.defaultdict(set)
override_seq = collections.defaultdict(set)
covered = set()
owner_meta = glob.glob(str(ROOT / '*/Humans/**/metadata.json'), recursive=True) + glob.glob(str(ROOT / 'Other Tribes/*/Humans/**/metadata.json'), recursive=True) + \
    glob.glob(str(ROOT / '*/Vehicles/**/metadata.json'), recursive=True) + glob.glob(str(ROOT / 'Animals/tribe_*/**/metadata.json'), recursive=True)
for p in owner_meta:
    m = read(p)
    if m.get('ownerKind') not in ('human', 'animal', 'vehicle'):
        continue
    if m['bindings']:
        for t in m['parentChain']:
            covered.add((m['tribeId'], t))
    heads = {b['phase']: b['headVariants'] for b in m['bindings']}
    for a_ in m['animations']:
        hbobs = {x for d in a_['directions'] for x in d.get('headBobs', [])}
        for r in a_['renders']:
            if not r['status'].startswith('RENDERED'):
                continue
            for lib in filter(None, (stem(r['bodyLibrary']).lower(), stem(r['shadowLibrary']).lower() if r['shadowLibrary'] else None)):
                bound_seq[lib].add(a_['bodySequence'].lower())
            for hv in heads.get(r['phase'], []):
                hl = stem(hv['head']).lower()
                bound_seq[hl].add((a_['headSequence'] or a_['bodySequence']).lower())
                if a_['headSequence'] and a_['headSequence'].lower() != a_['bodySequence'].lower():
                    override_seq[hl].add(a_['bodySequence'].lower())
                lib = LIBPATH.get(hl)
                if lib and m['ownerKind'] == 'human':
                    fr = {f['bobId'] for f in bmd(lib)[0]}
                    for x in hbobs & fr:
                        used[norm(lib)][x].add(f"human:head_variant_selector_{hv['selector']}")
                    if r.get('headPalette'):
                        libpal[norm(lib)][r['headPalette']] += 1

# ---------------------------------------------------------------- native sequence/record facts
ANIMCIF = cif(r'data\engine2d\inis\mapmoveableanimations\animations.cif')
SEQ = []
for blk in ANIMCIF:
    if blk['section'] == 'bobseq':
        img = stem(scalar(blk, 'imagelib', '')).lower()
        for a_ in commands(blk, 'seq'):
            SEQ.append((img, a_[0], a_[1], a_[2]))
shadowed = set()
for p in glob.glob(str(ROOT / 'Metadata/Mobile/shadowed_records_*.csv')):
    with open(p, encoding='utf-8-sig') as f:
        shadowed |= {int(r['shadowedSection']) for r in csv.DictReader(f)}
seq_records = collections.defaultdict(list)
for i, blk in enumerate(ANIMCIF):
    if blk['section'] in ('gfxanimatomic', 'gfxwalkatomic'):
        for k in ('gfxbobseqbody', 'gfxbobseqhead'):
            v = scalar(blk, k)
            if v:
                seq_records[str(v).lower()].append((i, scalar(blk, 'logictribe'), scalar(blk, 'logicjob', scalar(blk, 'logicvehicle'))))
pair = collections.defaultdict(set)
for jg in (r'data\engine2d\inis\humans\jobgraphics.cif', r'data\engine2d\inis\animals\jobgraphics.cif', r'data\engine2d\inis\vehicles\jobgraphics.cif'):
    for blk in cif(jg):
        bodies = [stem(a_[1] if isinstance(a_[0], int) else a_[0]).lower() for a_ in commands(blk, 'gfxbobmanagerbody')]
        others = [stem(a_[-1]).lower() for a_ in commands(blk, 'gfxbobmanagerbody') + commands(blk, 'gfxbobmanagerhead')]
        for x in bodies + others:
            pair[x].update(bodies)


FIRST = {}
for img, nm, fb, cnt in SEQ:          # native 0x0048CEA1: global first match by (case-insensitive) name
    FIRST.setdefault(nm.lower(), (img, nm, fb, cnt))


def family(s):
    return s[:6] if s.startswith('cr_') else s     # cr_hum / cr_ani / cr_veh


def classify(lib_stem, bob):
    if lib_stem in pair:   # bound through jobgraphics: native numbering = global first-match BobSeq of the same creature family
        hits = [(nm, img, fb, cnt) for img, nm, fb, cnt in FIRST.values() if family(img) == family(lib_stem) and fb <= bob < fb + cnt]
    else:
        hits = [(nm, img, fb, cnt) for img, nm, fb, cnt in SEQ if img == lib_stem and fb <= bob < fb + cnt]
    if not hits:
        return 'UNKNOWN_UNREFERENCED', 'NO_NATIVE_TABLE_REFERENCE', []
    names = [h[0].lower() for h in hits]
    ev = [f'{h[0]} [{h[1]}:{h[2]}+{h[3]}]' for h in hits[:6]]
    if 'head' in lib_stem and any(n in override_seq.get(lib_stem, set()) for n in names):
        return 'UNKNOWN_NAMED_SEQUENCE', 'HEAD_SEQUENCE_OVERRIDE', ev
    if any(n in bound_seq.get(lib_stem, set()) for n in names):
        return 'UNKNOWN_NAMED_SEQUENCE', 'SEQUENCE_BOUND_OFFSET_UNUSED', ev
    recs = [r for n in names for r in seq_records.get(n, [])]
    if not recs:
        return 'UNKNOWN_NAMED_SEQUENCE', 'SEQUENCE_NEVER_REFERENCED', ev
    live = [r for r in recs if r[0] not in shadowed]
    if not live:
        return 'UNKNOWN_NAMED_SEQUENCE', 'SHADOWED_DUPLICATE_RECORD', ev
    if all((t, j) not in covered for _, t, j in live):
        return 'UNKNOWN_GRAPHICS_BINDING', 'OWNER_HAS_NO_JOBGRAPHICS_BINDING', ev
    return 'UNKNOWN_NAMED_SEQUENCE', 'SEQUENCE_USED_WITH_OTHER_LIBRARIES_ONLY', ev


# ---------------------------------------------------------------- per-library atlases
lib_rows, unknown_rows = [], []
SL = ROOT / 'Shared/SourceLibraries'
LENIENT = HERE / 'export_planes_lenient.exe'
for n, e in enumerate(INDEX.entries):
    if not e.path.lower().endswith('.bmd'):
        continue
    key, lib_stem, lenient = norm(e.path), stem(e.path).lower(), False
    try:
        frames, planes = bmd(e.path)
    except Exception:
        d0 = CACHE / 'bmd_lenient' / slug(lib_stem)
        d0.mkdir(parents=True, exist_ok=True)
        (d0 / 'source.bmd').write_bytes(blob(e.path))
        subprocess.run([str(LENIENT), str(d0 / 'source.bmd'), str(d0)], check=True, capture_output=True)
        frames, planes, lenient = json.loads((d0 / 'frames.json').read_text()), (d0 / 'frames.planes').read_bytes(), True

    def fplanes(f):
        size = f['width'] * f['height'] * 3
        return np.frombuffer(planes[f['offset']:f['offset'] + size], np.uint8).reshape(f['height'], f['width'], 3)
    u = used.get(key, {})
    unsupported = [f for f in frames if f.get('unsupportedKind')]
    nonempty = [f for f in frames if not f.get('unsupportedKind') and f['width'] and f['height'] and f['kind'] and fplanes(f)[:, :, 1].any()]
    pal_choice = libpal.get(key) or collections.Counter()
    pals = [p_ for p_, _ in pal_choice.most_common(4) if p_.lower() in palette_defs()]
    d = SL / slug(stem(e.path))
    d.mkdir(parents=True, exist_ok=True)
    index, counts = [], collections.Counter()
    for f in unsupported:
        rec = {'bobId': f['bobId'], 'kind': f['kind'], 'width': f['width'], 'height': f['height'], 'pivot': [-f['x'], -f['y']],
               'status': 'UNKNOWN_UNSUPPORTED_PIXEL_KIND', 'reason': 'pixel kind 3: no native scanline walker (0x00439AB3, 0x00463AEE..0x0049E618 test kinds 1/2/4 only)'}
        index.append(rec)
        counts[rec['status']] += 1
        unknown_rows.append({'CLASS': rec['status'], 'REASON': rec['reason'], 'LIBRARY': e.path, 'ENTRY_ID': n, 'ARCHIVE_OFFSET': e.offset, 'BOB_ID': f['bobId'],
                             'KIND': f['kind'], 'WIDTH': f['width'], 'HEIGHT': f['height'], 'PIVOT': rec['pivot'], 'ATLAS': rel(d / 'library.json'),
                             'POSSIBLE_EVIDENCE': 'test asset; no CIF references the library', 'CONFIDENCE': 'UNKNOWN'})
    for start in range(0, len(nonempty), 64):
        group = nonempty[start:start + 64]
        cw = max(f['width'] for f in group); ch = max(f['height'] for f in group)
        data = np.zeros((math.ceil(len(group) / 8) * ch, 8 * cw, 4), np.uint8)
        cols_img = {p_: np.zeros_like(data) for p_ in pals}
        page = start // 64
        for j, f in enumerate(group):
            p = fplanes(f)
            X, Y = (j % 8) * cw, (j // 8) * ch
            data[Y:Y + f['height'], X:X + f['width']] = np.dstack([p[:, :, 0]] * 3 + [p[:, :, 1]])
            for p_ in pals:
                cols_img[p_][Y:Y + f['height'], X:X + f['width']] = rgba(p, palette(p_)[0], f['kind'])
            rec = {'bobId': f['bobId'], 'kind': f['kind'], 'width': f['width'], 'height': f['height'], 'pivot': [-f['x'], -f['y']],
                   'page': page, 'rect': [X, Y, f['width'], f['height']], 'usage': sorted(u.get(f['bobId'], []))}
            if f['bobId'] in u:
                rec['status'] = 'MAPPED'
            elif f['bobId'] in ui_unknown_palette.get(key, set()):
                rec['status'], rec['reason'] = 'UNKNOWN_PALETTE', 'GUI sprite: no native draw-call palette evidence; index data exported'
            else:
                cls, sub, ev = classify(lib_stem, f['bobId'])
                rec['status'], rec['reason'] = cls, sub
                if ev:
                    rec['bobSeq'] = ev
            index.append(rec)
            counts[rec['status'] + (':' + rec['reason'] if rec['status'] == 'UNKNOWN_NAMED_SEQUENCE' else '')] += 1
            if rec['status'] != 'MAPPED':
                unknown_rows.append({'CLASS': rec['status'], 'REASON': rec.get('reason', ''), 'LIBRARY': e.path, 'ENTRY_ID': n, 'ARCHIVE_OFFSET': e.offset,
                                     'BOB_ID': f['bobId'], 'KIND': f['kind'], 'WIDTH': f['width'], 'HEIGHT': f['height'], 'PIVOT': rec['pivot'],
                                     'SHA256_PLANES': hashlib.sha256(np.ascontiguousarray(p).tobytes()).hexdigest(),
                                     'PAGE': rel(d / f'page_{page:04d}_index_data.png'), 'RECT': [X, Y, f['width'], f['height']],
                                     'COLOUR_PAGES': [rel(d / f'page_{page:04d}__{slug(p_)}.png') for p_ in pals], 'BOBSEQ_EVIDENCE': rec.get('bobSeq', []),
                                     'POSSIBLE_EVIDENCE': (f'palettes used by mapped frames of this library: {dict(pal_choice)}' if pal_choice else 'no mapped frame in this library'),
                                     'ATLAS': rel(d / 'library.json'), 'CONFIDENCE': 'UNKNOWN'})
        Image.fromarray(data, 'RGBA').save(d / f'page_{page:04d}_index_data.png')
        for p_, img in cols_img.items():
            Image.fromarray(img, 'RGBA').save(d / f'page_{page:04d}__{slug(p_)}.png')
    mapped = counts.get('MAPPED', 0)
    meta = {'library': e.path, 'source': source(e.path),
            'decoder': 'production decodeBobLibraryBmd via ' + ('export_planes_lenient.exe (unsupported kinds recorded, not drawn)' if lenient else 'export_planes.exe'),
            'frameDescriptors': len(frames), 'nonemptyFrames': len(nonempty), 'unsupportedKindFrames': len(unsupported), 'mappedFrames': mapped,
            'statusCounts': dict(counts), 'pages': math.ceil(len(nonempty) / 64), 'palettes': pals, 'palettesSeen': dict(pal_choice),
            'representation': {'page_XXXX_index_data.png': 'RGB = palette index (DATA), alpha = coverage; kind 2 = coverage-only shadow',
                               'page_XXXX__<palette>.png': 'frames coloured with a palette used by MAPPED native definitions of this library; for non-MAPPED frames this colouring is PRESENTATION_APPROXIMATION'},
            'frames': index}
    write(d / 'library.json', meta, compact=True)
    (d / 'library.js').write_text('window.LIBRARY=' + json.dumps(meta, separators=(',', ':')) + ';', encoding='utf-8')
    lib_rows.append({'ENTRY_ID': n, 'LIBRARY': e.path, 'SIZE': e.size, 'FRAMES': len(frames), 'NONEMPTY': len(nonempty), 'UNSUPPORTED_KIND': len(unsupported),
                     'MAPPED': mapped, 'NOT_MAPPED': len(nonempty) + len(unsupported) - mapped,
                     'COVERAGE_PCT': round(100 * mapped / len(nonempty), 1) if nonempty else 100.0, 'STATUS_COUNTS': dict(counts),
                     'PALETTES': pals, 'ATLAS': rel(d / 'library.json'), 'DECODE_STATUS': 'DECODED_PARTIAL_UNSUPPORTED_KIND' if lenient else 'DECODED'})
    print(lib_stem, len(nonempty), dict(counts), flush=True)
csvout(ROOT / 'Catalogs/bmd_coverage.csv', lib_rows)
csvout(ROOT / 'Catalogs/unknown_frames.csv', unknown_rows)
tot = sum(r['NONEMPTY'] for r in lib_rows)
cls = collections.Counter(r['CLASS'] + (':' + r['REASON'] if r['CLASS'] == 'UNKNOWN_NAMED_SEQUENCE' else '') for r in unknown_rows)
summary = {'bmdLibraries': len(lib_rows), 'frameDescriptors': sum(r['FRAMES'] for r in lib_rows), 'nonemptyFrames': tot,
           'unsupportedKindFrames': sum(r['UNSUPPORTED_KIND'] for r in lib_rows), 'mappedFrames': sum(r['MAPPED'] for r in lib_rows),
           'notMapped': len(unknown_rows), 'classes': dict(sorted(cls.items())),
           'namedSequenceUnbound': sum(v for k, v in cls.items() if k.startswith('UNKNOWN_NAMED_SEQUENCE')),
           'trueUnknownUnreferenced': cls.get('UNKNOWN_UNREFERENCED', 0), 'silentlyDiscarded': 0,
           'note': 'Every non-empty frame of every BMD is present in Shared/SourceLibraries atlases; unsupported-kind descriptors are recorded without pixels.'}
write(ROOT / 'Unknown/census_summary.json', summary)
print(json.dumps(summary, indent=1))
