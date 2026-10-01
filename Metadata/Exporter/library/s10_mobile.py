"""Stage 10: Humans (all tribes), Animals and Vehicles through the shared native mobile-sprite tables.

Lookup semantics mirror cultures::graphics::MobileSpriteRegistry (Game 0x0048BD66 loader, 0x0048CEA1
global BobSeq lookup, 0x00494AE6 frame selection, 0x004803D5 creation binding, 0x00480576 job change):
  * jobgraphics.cif  JobBaseGraphics / JobChangeGraphics / JobGraphics -> body (+_s shadow) / head libraries, palettes
  * animations.cif   BobSeq (global first-match by name), GfxAnimAtomic / GfxWalkAtomic per tribe+job
  * parent chain     jobtypes.cif baseatomics
  * vehicles         animation job = vehicle type + 49 (job types 50..55 'vehicle_*'; Vehicle+0x1EC 0x32..0x37)
Draw order (production compositor): shadow (same BOB id in _s library, destination darkening) -> body -> head.
"""
import collections, shutil, sys
from PIL import Image
from common import *

ONLY = set(sys.argv[1:])  # optional filter: human animal vehicle
TRIBE_FOLDER = {1: 'Vikings', 2: 'Franks', 3: 'Byzantines', 4: 'Arabs', 5: 'Other Tribes/Weresnakes',
                6: 'Other Tribes/Werewolves', 7: 'Other Tribes/Egypt'}
HUM, ANI, VEH = 'human', 'animal', 'vehicle'
JG = {HUM: r'data\engine2d\inis\humans\jobgraphics.cif', ANI: r'data\engine2d\inis\animals\jobgraphics.cif',
      VEH: r'data\engine2d\inis\vehicles\jobgraphics.cif'}
ANIM = r'data\engine2d\inis\mapmoveableanimations\animations.cif'
JOBS = {scalar(b, 'type'): b for b in cif(r'data\logic\jobtypes.cif')}
JOBTXT = localization(cif(r'data\text\eng\strings\gameobjects\jobs.cif'))
TRIBES = {scalar(b, 'type'): b for b in cif(r'data\logic\tribetypes\tribetypes.cif')}
TRIBETXT = localization(cif(r'data\text\eng\strings\gameobjects\tribes.cif'))
VEHTYPES = {scalar(b, 'type'): b for b in cif(r'data\logic\vehicletypes.cif')}
GOODS = {scalar(b, 'type'): b for b in cif(r'data\logic\goodtypes.cif')}
GOODTXT = localization(cif(r'data\text\eng\strings\gameobjects\goods.cif'))
ATOMICS = {}
for i, b in enumerate(cif(r'data\logic\atomicanimations\atomicanimations.cif')):
    ATOMICS.setdefault(str(scalar(b, 'name', '')).lower(), dict(b, sourceSectionOrdinal=i))
LIBPATH = {stem(e.path).lower(): e.path for e in INDEX.entries if e.path.lower().endswith('.bmd')}


def parent(j):
    return scalar(JOBS[j], 'baseatomics', 0) if j in JOBS else 0


def chain(j):
    out = []
    while j and j not in out:
        out.append(j)
        j = parent(j)
    return out


def libname(p):
    return LIBPATH.get(stem(p).lower())


# ---------------------------------------------------------------- jobgraphics (production loadJobGraphics)
def load_bindings(kind):
    base, change = [], []
    for i, b in enumerate(cif(JG[kind])):
        sec = b['section']
        if sec in ('jobbasegraphics', 'jobgraphics'):
            dest = base
        elif sec == 'jobchangegraphics' and kind == HUM:
            dest = change
        else:
            continue
        r = {'kind': kind, 'section': sec, 'sectionOrdinal': i, 'tribe': scalar(b, 'logictribe'),
             'type': scalar(b, 'logicjob', scalar(b, 'logicvehicle')), 'bodyVariants': [], 'headVariants': [],
             'bodyPalettes': [], 'headPalettes': [], 'paletteRemaps': [], 'raw': b}
        for c in b['commands']:
            a = c['arguments']
            if c['name'] == 'gfxbobmanagerbody':
                if kind == HUM:
                    r['bodyVariants'].append({'selector': a[0], 'body': a[1], 'shadow': a[2] if len(a) > 2 else ''})
                else:
                    r['bodyVariants'].append({'selector': 0, 'body': a[0], 'shadow': a[1] if len(a) > 1 else ''})
            elif c['name'] == 'gfxbobmanagerhead':
                r['headVariants'].append({'selector': a[0], 'head': a[1]} if kind == HUM else {'selector': 0, 'head': a[0]})
            elif c['name'] in ('gfxpalettebasebody', 'gfxpalettebody'):
                r['bodyPalettes'].append(a[0])
            elif c['name'] == 'gfxpalettebasehead':
                r['headPalettes'].append(a[0])
            elif c['name'] == 'gfxpaletterandom':
                r['paletteRemaps'].append(a[0])
        dest.append(r)
    return base, change


BIND = {k: load_bindings(k) for k in JG}


def find(rows, tribe, typ, parents=True):
    for t in (chain(typ) if parents else [typ]):
        for r in rows:
            if r['tribe'] == tribe and r['type'] == t:
                return r
    return None


# ---------------------------------------------------------------- animations.cif (production parseAnimationDocument)
SEQS, ANIMS = [], []
for i, b in enumerate(cif(ANIM)):
    if b['section'] == 'bobseq':
        img = shd = ''
        for c in b['commands']:
            a = c['arguments']
            if c['name'] == 'imagelib':
                img = a[0]
            elif c['name'] == 'shadowlib':
                shd = a[0]
            elif c['name'] == 'seq':
                SEQS.append({'name': a[0], 'firstBob': a[1], 'count': a[2], 'imageLibrary': img, 'shadowLibrary': shd, 'sectionOrdinal': i})
        continue
    if b['section'] not in ('gfxanimatomic', 'gfxwalkatomic'):
        continue
    atomic = b['section'] == 'gfxanimatomic'
    r = {'id': i, 'atomic': atomic, 'tribe': scalar(b, 'logictribe', 0), 'type': scalar(b, 'logicjob', scalar(b, 'logicvehicle', 0)),
         'selector': scalar(b, 'logicatomicaction' if atomic else 'logicgoodtype', 0), 'mode': scalar(b, 'gfxanimmode', 0),
         'subId': scalar(b, 'logicinhouseatomicsubid', 0) if atomic else scalar(b, 'logicwalkspeed', 100000), 'bodySeq': scalar(b, 'gfxbobseqbody', ''), 'headSeq': scalar(b, 'gfxbobseqhead', ''),
         'body': [[] for _ in range(8)], 'head': [[] for _ in range(8)], 'inHouse': [], 'raw': b}
    for c in b['commands']:
        n, a = c['name'], c['arguments']
        if n in ('gfxanimframelistdir', 'gfxwalkframelist'):
            r['body'][a[0]].extend(a[1:])
        elif n == 'gfxanimframelist':
            r['body'] = [list(a) for _ in range(8)]
        elif n in ('gfxanimframelistheaddir', 'gfxwalkframelisthead'):
            r['head'][a[0]].extend(a[1:])
        elif n == 'gfxanimframelisthead':
            r['head'] = [list(a) for _ in range(8)]
        elif n.startswith('gfxinhouse'):
            r['inHouse'].append({'command': n, 'arguments': a})
    # production erase_if: drop records without tribe/type or without any body publication
    r['bodyCandidate'] = bool(r['tribe'] > 0 and r['type'] > 0 and (r['bodySeq'] or any(r['body']) or (r['mode'] == 2 and r['inHouse'])))
    ANIMS.append(r)
SEQMAP = {}
for s in SEQS:
    SEQMAP.setdefault(s['name'].lower(), s)


SHADOWED = []


def effective_animations(tribe, typ, fallback):
    """All (atomic, selector, subId) keys resolvable for this owner, first match along the parent chain."""
    out = {}
    for t in chain(typ):
        for a in ANIMS:
            if a['bodyCandidate'] and a['tribe'] == tribe and a['type'] == t:
                k = (a['atomic'], a['selector'], a['subId'])
                if k in out and out[k]['type'] == t:
                    SHADOWED.append({'tribe': tribe, 'job': t, 'kind': 'atomic' if a['atomic'] else 'walk', 'selector': a['selector'],
                                     'subIdOrWalkSpeed': a['subId'], 'shadowedSection': a['id'], 'winningSection': out[k]['id'],
                                     'bodySequence': a['bodySeq'], 'reason': 'same (tribe, job, selector, subId/walkSpeed) key authored earlier; native 0x0048D027 returns the first match (loader 0x0048BD66 keeps authored order for equal keys)'})
                    continue
                out.setdefault(k, a)
    return out


def setatomic_name(tribe, job, selector):
    for t in chain(job):
        for a in commands(TRIBES[tribe], 'setatomic') if tribe in TRIBES else []:
            if a[0] == t and a[1] == selector:
                return a[2]
    return ''


# ---------------------------------------------------------------- frame resolution (0x00494AE6)
def resolve(a, direction):
    seq = SEQMAP.get(a['bodySeq'].lower()) if a['bodySeq'] else None
    body = a['body'][direction]
    if a['bodySeq'] and not seq:
        return None, 'BODY_SEQUENCE_UNRESOLVED'
    bb = [(seq['firstBob'] if seq else 0) + v for v in body]
    hname = a['headSeq'] or a['bodySeq']
    hseq = SEQMAP.get(hname.lower()) if hname else None
    hf = a['head'][direction] or body
    hb = [hseq['firstBob'] + v for v in hf] if hseq else list(bb)
    return {'bodyOffsets': body, 'headOffsets': a['head'][direction], 'bodyBobs': bb, 'headBobs': hb,
            'bodySequence': seq, 'headSequence': hseq}, ''


def timing(a):
    if not a['atomic']:
        return 'frame = frameTick % count (walk; caller frame tick)'
    if a['mode'] == 1:
        return 'frame = progress % count (mode 1)'
    if a['mode'] == 2:
        return 'mode 2 in-house timeline: progress*10000/duration over gfxinhouse* steps (recursive walk/anim selection)'
    return 'frame = min(count-1, floor(count*progress/duration)); duration from atomic length'


# ---------------------------------------------------------------- rendering
FRAMEIDX = {}


def frames_of(lib):
    if lib not in FRAMEIDX:
        fr, _ = bmd(lib)
        FRAMEIDX[lib] = {f['bobId']: f for f in fr}
    return FRAMEIDX[lib]


VALID = collections.defaultdict(dict)   # (lib, palette) -> {bob: status}
USED = collections.defaultdict(lambda: collections.defaultdict(list))  # lib -> bob -> [usage]


VPAL, VPALNOTE = {}, {}


def pal_of(name):
    if not name:
        return None
    return VPAL[name] if name in VPAL else palette(name)[0]


def choose_palettes(kind, tribe, typ, phase, bind):
    """Returns (bodyPaletteName, headPaletteName, provenance)."""
    if bind['bodyPalettes']:
        return bind['bodyPalettes'][0], (bind['headPalettes'][0] if bind['headPalettes'] else None), 'declared base palette (ordinal 0 of RNG list)'
    if phase == 'jobChange':
        base = find(BIND[kind][0], tribe, typ)
        if base and base['bodyPalettes']:
            return base['bodyPalettes'][0], (base['headPalettes'][0] if base['headPalettes'] else None), \
                'inherited from creation binding: 0x00480576 rebinds libraries but keeps the individual palettes'
    remaps = bind['paletteRemaps'] or (find(BIND[kind][0], tribe, typ) or {}).get('paletteRemaps', [])
    if kind == HUM and remaps:
        name = f'{remaps[0]}@player_00'
        if name not in VPAL:
            body, head = np.zeros((256, 3), np.uint8), np.zeros((256, 3), np.uint8)
            log = apply_random_palette('player_00', body, head) + apply_random_palette(remaps[0], body, head)
            VPAL[name] = body
            VPAL[name + '#head'] = head
            VPALNOTE[name] = {'construction': '0x004803D5: palettes zeroed (no base record), player colour remap then job remap', 'playerColourAssumed': 0,
                              'randomChoice': 'highest-weight alternative per range (one native-possible outcome)', 'applied': log,
                              'status': 'PRESENTATION_APPROXIMATION'}
        return name, None, 'synthesized from native random patches; see Metadata/Mobile/virtual_palettes.json'
    return None, None, 'no palette source'


def render_sheet(anim_dirs, body_lib, head_lib, shadow_lib, body_pal, head_pal, out_png):
    """anim_dirs: list of (direction, bodyBobs, headBobs). Returns sheet metadata."""
    fb = frames_of(body_lib)
    fh = frames_of(head_lib) if head_lib else {}
    fs = frames_of(shadow_lib) if shadow_lib else {}
    boxes = []
    for d, bb, hb in anim_dirs:
        for i, b in enumerate(bb):
            for lib_frames, bob in ((fb, b), (fh, hb[i] if i < len(hb) else None), (fs, b)):
                f = lib_frames.get(bob) if bob is not None else None
                if f and f['width'] and f['height'] and f['kind']:
                    boxes.append((f['x'], f['y'], f['x'] + f['width'], f['y'] + f['height']))
    if not boxes:
        return None
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    cw = max(b[2] for b in boxes) - x0; ch = max(b[3] for b in boxes) - y0
    cols = max(len(bb) for _, bb, _ in anim_dirs)
    rows = len(anim_dirs)
    sheet = np.zeros((rows * ch, cols * cw, 4), np.uint8)
    shadow = np.zeros((rows * ch, cols * cw, 4), np.uint8)
    pb, ph = pal_of(body_pal), pal_of(head_pal) if head_pal else None
    cells = []
    for r, (d, bb, hb) in enumerate(anim_dirs):
        row = []
        for c, b in enumerate(bb):
            h = hb[c] if c < len(hb) else None
            cell = {'direction': d, 'column': c, 'bodyBob': b, 'headBob': h if head_lib else None, 'shadowBob': b if shadow_lib else None,
                    'status': []}
            for lib, frames, bob, pal, layer, target in ((shadow_lib, fs, b, None, 'shadow', shadow), (body_lib, fb, b, pb, 'body', sheet),
                                                         (head_lib, fh, h, ph, 'head', sheet)):
                if not lib or bob is None:
                    continue
                f = frames.get(bob)
                if f is None:
                    cell['status'].append(f'{layer.upper()}_BOB_ABSENT_IN_LIBRARY')
                    continue
                if not (f['width'] and f['height'] and f['kind']):
                    cell['status'].append(f'{layer.upper()}_FRAME_EMPTY')
                    continue
                USED[lib][bob].append(layer)
                p = frame_planes(lib, f)
                img = rgba(p, pal if layer != 'shadow' else None, f['kind'])
                if layer == 'shadow':
                    img[:, :, 3] = p[:, :, 1]  # coverage mask; black RGB, data not final darkening
                X = c * cw + f['x'] - x0; Y = r * ch + f['y'] - y0
                m = img[:, :, 3] > 0
                region = target[Y:Y + f['height'], X:X + f['width']]
                region[m] = img[m]
                if layer != 'shadow':
                    VALID[(lib, body_pal if layer == 'body' else head_pal)].setdefault(bob, None)
            row.append(cell)
        cells.append(row)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(sheet, 'RGBA').save(out_png)
    sp = None
    if shadow_lib and shadow[:, :, 3].any():
        sp = out_png.with_name(out_png.stem + '__shadow_mask.png')
        Image.fromarray(shadow, 'RGBA').save(sp)
    return {'sheet': rel(out_png), 'shadowMask': rel(sp) if sp else None, 'cellWidth': cw, 'cellHeight': ch,
            'anchorInCell': [-x0, -y0], 'rows': [r[0]['direction'] if r else None for r in cells], 'cells': cells,
            'layout': 'row = native direction (0..7, only directions with frames), column = native frame-list order; '
                      'every cell shares one anchor (entity world position) at anchorInCell'}


# ---------------------------------------------------------------- owners
def owners():
    out = []
    if not ONLY or HUM in ONLY:
        for tribe in range(1, 8):
            for j in sorted(JOBS):
                if j > 47:
                    continue
                out.append((HUM, tribe, j, j))
    if not ONLY or ANI in ONLY:
        for tribe in range(8, 42):
            for j in (48, 49):
                out.append((ANI, tribe, j, j))
    if not ONLY or VEH in ONLY:
        for tribe in range(1, 8):
            for vt in sorted(VEHTYPES):
                out.append((VEH, tribe, vt, vt + 49))
    return out


def human_group(j):
    if j in (1, 2):
        return 'Children/Babies'
    if j in (3, 4):
        return 'Children'
    if j == 5:
        return 'Female'
    if j == 6:
        return 'Male'
    if 31 <= j <= 41:
        return 'Soldiers'
    if 42 <= j <= 47:
        return 'Heroes'
    return 'Professions'


def folder_for(kind, tribe, typ):
    if kind == HUM:
        return ROOT / TRIBE_FOLDER[tribe] / 'Humans' / human_group(typ) / f"job_{typ:02d}_{slug(scalar(JOBS[typ], 'name'))}"
    if kind == ANI:
        return ROOT / 'Animals' / f"tribe_{tribe:02d}_{slug(scalar(TRIBES[tribe], 'name'))}" / ('young_job48' if typ == 48 else 'adult_job49')
    return ROOT / TRIBE_FOLDER[tribe] / 'Vehicles' / f"type_{typ}_{slug(scalar(VEHTYPES[typ], 'name'))}"


def sheet_root(kind, tribe):
    if kind == ANI:
        return ROOT / 'Animals' / f"tribe_{tribe:02d}_{slug(scalar(TRIBES[tribe], 'name'))}" / 'Sheets'
    return ROOT / TRIBE_FOLDER[tribe] / ('Humans' if kind == HUM else 'Vehicles') / 'Sheets'


rendered = {}
records, xrows, owner_rows, unresolved_rows = [], [], [], []
for kind, tribe, typ, animtype in owners():
    base_rows, change_rows = BIND[kind]
    allow = tribe in TRIBES and any(a[0] == (typ if kind != VEH else typ) for a in commands(TRIBES[tribe], 'allowjob' if kind != VEH else 'allowvehicle'))
    phases = []
    b = find(base_rows, tribe, typ, parents=(kind != VEH))
    if b:
        phases.append(('initial', b))
    if kind == HUM:
        c = find(change_rows, tribe, typ)
        if c:
            phases.append(('jobChange', c))
    anims = effective_animations(tribe, animtype, kind != HUM)
    if not phases and not anims:
        if allow or (kind == VEH and tribe in (1, 4)):
            unresolved_rows.append({'CATEGORY': kind, 'TRIBE_ID': tribe, 'TYPE_ID': typ, 'SELECTOR': '', 'ATOMIC_NAME': '',
                                    'STATUS': 'NO_GRAPHICS_BINDING_AND_NO_ANIMATION_RECORD (native allows/declares type; no jobgraphics/animations entry)'})
        continue
    native = scalar(JOBS[typ], 'name') if kind != VEH else scalar(VEHTYPES[typ], 'name')
    english = JOBTXT.get(typ if kind != VEH else animtype, {}).get('singular', '')
    folder = folder_for(kind, tribe, typ)
    meta = {'ownerKind': kind, 'tribeId': tribe, 'nativeTribe': scalar(TRIBES[tribe], 'name') if tribe in TRIBES else None,
            'tribeEnglish': TRIBETXT.get(tribe, {}).get('plural'), 'typeId': typ, 'animationJobId': animtype, 'nativeName': native,
            'englishName': english, 'nativeAllowed': allow, 'parentChain': chain(animtype),
            'sexAge': {1: 'female baby', 2: 'male baby', 3: 'female child', 4: 'male child', 5: 'adult female', 6: 'adult male'}.get(typ, 'adult (see job/parent chain)') if kind == HUM else ('young' if typ == 48 else 'adult' if typ == 49 else None),
            'bindings': [], 'animations': [], 'sources': {'jobgraphics': source(JG[kind]), 'animations': source(ANIM)},
            'nativeReferences': {'Game.exe': ['0x0048BD66 GraphicsAnimationRegistry_LoadFromCif', '0x0048CEA1 BobSeq global lookup',
                                              '0x00494AE6 frame selection', '0x004803D5 creation binding/palette', '0x00480576 job-change rebinding',
                                              '0x0048B258 random palette patches', '0x0049B930 shadow destination darkening'],
                                 'cpp': 'MobileSpriteRegistry / MobileSpriteRuntimeOwner / ProductionWorldCompositor'},
            'folder': rel(folder)}
    if kind == VEH:
        meta['vehicleDefinition'] = VEHTYPES[typ]
        meta['animationJobEvidence'] = ('animation job = vehicle type + 49; job types 50..55 are vehicle_* with English names '
                                        'Handcart/Ox Cart/Ship/Ship/Catapult/Ox Cart Framework; Vehicle+0x1EC holds 0x32..0x37')
    for phase, bind in phases:
        meta['bindings'].append({'phase': phase, 'sectionOrdinal': bind['sectionOrdinal'], 'section': bind['section'],
                                 'definedForType': bind['type'], 'inheritedFrom': bind['type'] if bind['type'] != typ else None,
                                 'bodyVariants': bind['bodyVariants'], 'headVariants': bind['headVariants'],
                                 'bodyPalettes': bind['bodyPalettes'], 'headPalettes': bind['headPalettes'], 'paletteRemaps': bind['paletteRemaps'],
                                 'variantSelection': 'body = RNG % bodyVariants, head = RNG % headVariants, palette ordinal = RNG % palettes (0x004803D5)' if kind == HUM else 'single binding'})
    for key, a in sorted(anims.items(), key=lambda kv: (not kv[0][0], kv[0][1], kv[0][2])):
        atomic, selector, sub = key
        aname = setatomic_name(tribe, animtype, selector) if atomic else ''
        adef = ATOMICS.get(aname.lower()) if aname else None
        entry = {'animationSection': a['id'], 'definedForJob': a['type'], 'inherited': a['type'] != animtype, 'kind': 'atomic' if atomic else 'walk',
                 'atomicActionSelector': selector if atomic else None, 'carriedGoodType': selector if not atomic else None,
                 'carriedGoodName': (scalar(GOODS.get(selector, {'commands': []}), 'name', '') if not atomic and selector else ''),
                 'carriedGoodEnglish': GOODTXT.get(selector, {}).get('singular', '') if not atomic and selector else '',
                 'inHouseSubId': sub if atomic else None, 'walkSpeedThreshold': None if atomic else sub, 'mode': a['mode'], 'atomicName': aname or (None if not atomic else 'UNKNOWN (no tribe setatomic)'),
                 'atomicLength': scalar(adef, 'length') if adef else None, 'atomicEvents': (commands(adef, 'event') + commands(adef, 'eventx')) if adef else [],
                 'interruptable': scalar(adef, 'interruptable') if adef else None, 'bodySequence': a['bodySeq'], 'headSequence': a['headSeq'],
                 'timing': timing(a), 'inHouseSteps': a['inHouse'], 'directions': [], 'renders': []}
        if a['mode'] == 2:
            entry['note'] = ('Timeline record: frames come from referenced walk/anim selectors at step progress; production parser recognises '
                             'gfxinhousewalk/gfxinhouseanim; overlaybob/overlaylandscape commands are retained raw here.')
        dirs = []
        for d in range(8):
            res, err = resolve(a, d)
            if res is None:
                entry['directions'].append({'direction': d, 'status': err})
                continue
            if res['bodyBobs']:
                dirs.append((d, res['bodyBobs'], res['headBobs']))
            entry['directions'].append({'direction': d, 'bodyOffsets': res['bodyOffsets'], 'headOffsets': res['headOffsets'],
                                        'bodyBobs': res['bodyBobs'], 'headBobs': res['headBobs'],
                                        'bodySequence': res['bodySequence'], 'headSequence': res['headSequence'] if res['headSequence'] is not res['bodySequence'] else 'same as body'})
        for phase, bind in phases:
            hv = bind['headVariants'][0]['head'] if bind['headVariants'] else ''
            for bv in bind['bodyVariants']:
                body_lib, shadow_lib, head_lib = libname(bv['body']), libname(bv['shadow']) if bv['shadow'] else None, libname(hv) if hv else None
                bpal, hpal, pal_note = choose_palettes(kind, tribe, typ, phase, bind)
                r = {'phase': phase, 'bodySelector': bv['selector'], 'bodyLibrary': bv['body'], 'shadowLibrary': bv['shadow'], 'headLibrary': hv,
                     'headSelectorRendered': bind['headVariants'][0]['selector'] if bind['headVariants'] else None, 'bodyPalette': bpal, 'headPalette': hpal,
                     'paletteProvenance': pal_note}
                if not dirs:
                    r['status'] = 'NO_DIRECT_FRAMES (timeline or empty record)'
                elif not body_lib:
                    r['status'] = 'BODY_LIBRARY_NOT_IN_ARCHIVE'
                elif not bpal:
                    r['status'] = 'NO_BODY_PALETTE_DECLARED'
                else:
                    fb = frames_of(body_lib)
                    allb = [x for _, bb, _ in dirs for x in bb]
                    present = sum(1 for x in allb if x in fb)
                    r['bodyFramesPresent'] = f'{present}/{len(allb)}'
                    if present == 0:
                        r['status'] = 'VARIANT_INCOMPATIBLE: no referenced BOB exists in this body library'
                    else:
                        rk = (body_lib, head_lib, shadow_lib, bpal, hpal, a['id'])
                        if rk not in rendered:
                            lab = ('A' if atomic else 'W') + f'{selector:03d}' + ((f'_sub{sub}' if sub else '') if atomic else (f'_speed{sub}' if sub != 100000 else ''))
                            name = f"j{a['type']:02d}_{lab}_{slug(a['bodySeq'] or 'absolute')}_s{a['id']}.png"
                            sub_dir = slug(stem(body_lib)) + ('+' + slug(stem(head_lib)) if head_lib else '') + '__' + slug(bpal) + (('+' + slug(hpal)) if hpal and hpal != bpal else '')
                            rendered[rk] = render_sheet(dirs, body_lib, head_lib, shadow_lib, bpal, hpal, sheet_root(kind, tribe) / sub_dir / name)
                        sh = rendered[rk]
                        r['status'] = 'RENDERED' if present == len(allb) else 'RENDERED_PARTIAL_MISSING_BOBS'
                        if sh:
                            r.update(sheet=sh['sheet'], shadowMask=sh['shadowMask'], cellWidth=sh['cellWidth'], cellHeight=sh['cellHeight'],
                                     anchorInCell=sh['anchorInCell'], sheetRows=sh['rows'])
                            missing = sorted({s for row in sh['cells'] for cell in row for s in cell['status']})
                            if missing:
                                r['cellIssues'] = missing
                entry['renders'].append(r)
                xrows.append({'CATEGORY': {'human': 'Humans', 'animal': 'Animals', 'vehicle': 'Vehicles'}[kind], 'TRIBE_ID': tribe,
                              'TRIBE': meta['nativeTribe'], 'TYPE_ID': typ, 'ANIMATION_JOB_ID': animtype, 'NATIVE_NAME': native, 'ENGLISH': english,
                              'PHASE': phase, 'BODY_SELECTOR': bv['selector'], 'KIND': entry['kind'], 'ATOMIC_SELECTOR': entry['atomicActionSelector'],
                              'ATOMIC_NAME': entry['atomicName'], 'CARRIED_GOOD': entry['carriedGoodType'], 'CARRIED_GOOD_NAME': entry['carriedGoodName'],
                              'SUB_ID': sub if atomic else '', 'WALK_SPEED_THRESHOLD': '' if atomic else sub, 'MODE': a['mode'], 'ANIMATION_SECTION': a['id'], 'DEFINED_FOR_JOB': a['type'], 'BODY_SEQUENCE': a['bodySeq'],
                              'BODY_LIBRARY': bv['body'], 'SHADOW_LIBRARY': bv['shadow'], 'HEAD_LIBRARY': hv, 'BODY_PALETTE': r['bodyPalette'],
                              'HEAD_PALETTE': r['headPalette'], 'DIRECTIONS': len(dirs), 'FRAMES': sum(len(bb) for _, bb, _ in dirs),
                              'BOB_RANGE': f"{min(x for _, bb, _ in dirs for x in bb)}-{max(x for _, bb, _ in dirs for x in bb)}" if dirs else '',
                              'LENGTH': entry['atomicLength'], 'TIMING': entry['timing'], 'STATUS': r['status'], 'SHEET': r.get('sheet', ''),
                              'SHADOW_MASK': r.get('shadowMask', ''), 'METADATA': rel(folder / 'metadata.json')})
        meta['animations'].append(entry)
    # atomic selectors declared by the tribe with no graphics record
    declared = {}
    for t in chain(animtype):
        for s in commands(TRIBES.get(tribe, {'commands': []}), 'setatomic'):
            if s[0] == t:
                declared.setdefault(s[1], s[2])
    meta['atomicsWithoutGraphicsRecord'] = [{'selector': k, 'atomicName': v} for k, v in sorted(declared.items()) if not any(kk[0] and kk[1] == k for kk in anims)]
    for u in meta['atomicsWithoutGraphicsRecord']:
        unresolved_rows.append({'CATEGORY': kind, 'TRIBE_ID': tribe, 'TYPE_ID': typ, 'SELECTOR': u['selector'], 'ATOMIC_NAME': u['atomicName'],
                                'STATUS': 'NO_GFXANIMATOMIC_RECORD (0x00494AE6: lookup fails along the parent chain, then retries selector 0 at the chain root)'})
    statuses = collections.Counter(r['status'].split(':')[0] for e in meta['animations'] for r in e['renders'])
    meta['summary'] = {'animations': len(meta['animations']), 'renderStatus': dict(statuses), 'bindings': len(phases)}
    meta['confidence'] = {'sourceMapping': 'SOURCE_COMPLETE' if phases and anims else 'PARTIAL',
                          'framePixels': 'PIXEL_CONFIRMED (per frame; see Catalogs/pixel_validation.csv)',
                          'palette': 'SOURCE_BASE_PALETTE; runtime RNG palette ordinal/player colour/job random patches NOT applied -> PRESENTATION_APPROXIMATION' if kind == HUM else 'SOURCE_BODY_PALETTE',
                          'shadow': 'Coverage mask only; native destination darkening -> PRESENTATION_APPROXIMATION',
                          'timing': 'Native frame order and selection rules recorded; tick-to-seconds rate UNKNOWN'}
    write(folder / 'metadata.json', meta)
    records.append(meta)
    owner_rows.append({'CATEGORY': kind, 'TRIBE_ID': tribe, 'TRIBE': meta['nativeTribe'], 'TYPE_ID': typ, 'ANIMATION_JOB_ID': animtype, 'NATIVE_NAME': native,
                       'ENGLISH': english, 'SEX_AGE': meta['sexAge'], 'NATIVE_ALLOWED': allow, 'PARENT_CHAIN': chain(animtype),
                       'INITIAL_BINDING_SECTION': next((x['sectionOrdinal'] for x in meta['bindings'] if x['phase'] == 'initial'), ''),
                       'JOBCHANGE_BINDING_SECTION': next((x['sectionOrdinal'] for x in meta['bindings'] if x['phase'] == 'jobChange'), ''),
                       'BODY_LIBRARIES': sorted({v['body'] for x in meta['bindings'] for v in x['bodyVariants']}),
                       'HEAD_LIBRARIES': sorted({v['head'] for x in meta['bindings'] for v in x['headVariants']}),
                       'PALETTES': sorted({p for x in meta['bindings'] for p in x['bodyPalettes'] + x['headPalettes']}),
                       'RANDOM_PALETTES': sorted({p for x in meta['bindings'] for p in x['paletteRemaps']}),
                       'ANIMATIONS': len(meta['animations']), 'RENDER_STATUS': dict(statuses), 'MAPPING': meta['confidence']['sourceMapping'],
                       'METADATA': rel(folder / 'metadata.json')})
    print(kind, tribe, typ, native, len(meta['animations']), dict(statuses), flush=True)

# ---------------------------------------------------------------- pixel validation of every drawn frame
vrows = []
for (lib, pal), bobs in VALID.items():
    res = validate(lib, pal_of(pal), list(bobs), pal)
    c = collections.Counter(res.values())
    vrows.append({'LIBRARY': lib, 'PALETTE': pal, 'FRAMES_DRAWN': len(bobs), 'PIXEL_CONFIRMED': c.get('PIXEL_CONFIRMED', 0),
                  'MISMATCH': c.get('PIXEL_MISMATCH', 0), 'OTHER': sum(v for k, v in c.items() if k not in ('PIXEL_CONFIRMED', 'PIXEL_MISMATCH')),
                  'REFERENCE': 'production drawBobClippedBorrowed32 via render_batch.exe', 'SCOPE': 'mobile:' + ','.join(sorted(ONLY) or ['all'])})
    print('validate', stem(lib), pal, dict(c), flush=True)
tag = '_'.join(sorted(ONLY)) or 'all'
write(ROOT / f'Metadata/Mobile/virtual_palettes_{tag}.json', VPALNOTE)
csvout(ROOT / f'Metadata/Mobile/shadowed_records_{tag}.csv', list({(d['tribe'], d['shadowedSection']): d for d in SHADOWED}.values()))
write(ROOT / f'Metadata/Mobile/validation_{tag}.json', vrows)
write(ROOT / f'Metadata/Mobile/usage_{tag}.json', {lib: {str(b): sorted(set(v)) for b, v in d.items()} for lib, d in USED.items()}, compact=True)
write(ROOT / f'Metadata/Mobile/owners_{tag}.json', owner_rows)
csvout(ROOT / f'Metadata/Mobile/animations_{tag}.csv', xrows)
csvout(ROOT / f'Metadata/Mobile/owners_{tag}.csv', owner_rows)
csvout(ROOT / f'Metadata/Mobile/atomics_without_graphics_{tag}.csv', unresolved_rows)
print('DONE owners', len(records), 'rows', len(xrows), 'sheets', len(rendered), 'validated libs', len(vrows))
