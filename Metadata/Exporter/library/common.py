"""Shared helpers for the whole-library exporter.

Reuses the existing production readers:
  * LIB index / CIF de-obfuscation: re-data/evidence/decompilation/tools (cultures_lib, cultures_cif, catalog_game_data)
  * BMD decoding: cultures::graphics::decodeBobLibraryBmd + bobWalkFrameRuns/bobWalkKind4FrameRuns
    through export_planes.exe (source: ../viking_humans/export_planes.cpp)
Original files are opened read-only.
"""
import sys, json, csv, hashlib, subprocess, re, functools
from pathlib import Path
import numpy as np
sys.dont_write_bytecode = True
sys.path.insert(0, r'E:\cultures\re-data\evidence\decompilation\tools')
from catalog_game_data import read_index, archive_blob, parse_blocks, commands, scalar, localization  # noqa: E402
import cultures_cif  # noqa: E402

ROOT = Path(r'E:\assets cultures')
HERE = Path(__file__).resolve().parent
CACHE = HERE / 'cache'
DATAX = Path(r'E:\cultures\vanilla-data\DataX')
ORIGINAL = Path(r'E:\cultures\original')
ARCH = DATAX / 'Libs' / 'data0001.lib'
INDEX = read_index(ARCH)
ENT = {e.path.lower().replace('/', '\\'): (n, e) for n, e in enumerate(INDEX.entries)}
PLANES_EXE = ROOT / 'Metadata/Exporter/viking_humans/export_planes.exe'
B = chr(92)


def norm(p):
    return str(p).replace('/', B).lower()


def blob(name):
    n, e = ENT[norm(name)]
    with ARCH.open('rb') as f:
        f.seek(e.offset)
        data = f.read(e.size)
    assert len(data) == e.size
    return data


def has(name):
    return norm(name) in ENT


@functools.lru_cache(maxsize=None)
def source(name):
    n, e = ENT[norm(name)]
    return {'archive': str(ARCH), 'entryId': n, 'entryName': e.path, 'offset': e.offset, 'size': e.size,
            'sha256': hashlib.sha256(blob(name)).hexdigest()}


@functools.lru_cache(maxsize=None)
def cif(name):
    return parse_blocks(blob(name))


def cif_lines(name):
    return cultures_cif.decode(blob(name))


def slug(n):
    return re.sub(r'[^\w.-]+', '_', str(n).strip(), flags=re.UNICODE).strip('_')


def stem(p):
    return str(p).replace('/', B).split(B)[-1].rsplit('.', 1)[0]


def rel(p):
    return str(Path(p).relative_to(ROOT)).replace(B, '/')


def write(p, obj, compact=False):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, separators=(',', ':')) if compact
                 else json.dumps(obj, indent=1, ensure_ascii=False), encoding='utf-8')


def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))


def csvout(p, rows, fields=None):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        for r in rows:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in r.items()})


def sha_file(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def source_files():
    return sorted([p for p in DATAX.rglob('*') if p.is_file()] + [p for p in ORIGINAL.iterdir() if p.is_file()])


# ---------------------------------------------------------------- BMD decoding (production C++)
@functools.lru_cache(maxsize=None)
def bmd(name):
    """Decode a BMD through the production decoder. Returns (frames:list, planes:bytes).

    Each frame: bobId, frameIndex, kind, x, y, width, height, firstScanline, offset.
    Planes per pixel: [palette index, coverage(255 where a pixel run exists), kind4 secondary byte].
    """
    d = CACHE / 'bmd' / slug(stem(name))
    fj, fp = d / 'frames.json', d / 'frames.planes'
    src = d / 'source.bmd'
    if not (fj.exists() and fp.exists() and (d / 'ok').exists()):
        d.mkdir(parents=True, exist_ok=True)
        src.write_bytes(blob(name))
        r = subprocess.run([str(PLANES_EXE), str(src), str(d)], capture_output=True)
        if r.returncode != 0:
            raise RuntimeError(f'production BMD decoder failed for {name}: exit {r.returncode}')
        (d / 'ok').write_text('1')
    return json.loads(fj.read_text()), fp.read_bytes()


def frame_planes(name, frame):
    frames, planes = bmd(name)
    size = frame['width'] * frame['height'] * 3
    return np.frombuffer(planes[frame['offset']:frame['offset'] + size], np.uint8).reshape(frame['height'], frame['width'], 3)


# ---------------------------------------------------------------- palettes
@functools.lru_cache(maxsize=None)
def palette_defs():
    return {str(scalar(b, 'editname', '')).lower(): b for b in cif(r'data\engine2d\inis\palettes\palettes.cif')}


@functools.lru_cache(maxsize=None)
def pcx_palette(path):
    data = blob(path)
    if len(data) < 769 or data[-769] != 12:
        raise ValueError('no PCX 256 palette: ' + path)
    return np.frombuffer(data[-768:], np.uint8).reshape(256, 3)


@functools.lru_cache(maxsize=None)
def palette(name):
    """Named GfxPalette256 -> (256x3 array, source path)."""
    b = palette_defs()[str(name).lower()]
    path = scalar(b, 'gfxfile')
    return pcx_palette(path), path


def rgba(planes, pal, kind):
    out = np.zeros(planes.shape[:2] + (4,), np.uint8)
    if kind != 2 and pal is not None:
        out[:, :, :3] = pal[planes[:, :, 0]]
    out[:, :, 3] = planes[:, :, 1]
    out[planes[:, :, 1] == 0] = 0
    return out


# ---------------------------------------------------------------- pixel validation against production drawer
RENDER_BATCH = HERE / 'render_batch.exe'


def validate(name, pal, bob_ids, tag):
    """Render bob_ids of library `name` with 256x3 `pal` through production drawBobClippedBorrowed32
    and compare byte-for-byte with rgba() of the decoded planes. Returns {bobId: 'PIXEL_CONFIRMED'|reason}."""
    frames, _ = bmd(name)
    by = {f['bobId']: f for f in frames}
    ids = sorted({i for i in bob_ids if i in by and by[i]['kind'] in (1, 4) and by[i]['width'] and by[i]['height']})
    if not ids:
        return {}
    d = CACHE / 'validate'
    d.mkdir(parents=True, exist_ok=True)
    key = slug(stem(name)) + '_' + slug(tag)
    (d / (key + '.ids')).write_text('\n'.join(map(str, ids)))
    (d / (key + '.rgb')).write_bytes(np.ascontiguousarray(pal, np.uint8).tobytes())
    src = CACHE / 'bmd' / slug(stem(name)) / 'source.bmd'
    r = subprocess.run([str(RENDER_BATCH), str(src), str(d / (key + '.rgb')), str(d / (key + '.ids')), str(d / (key + '.bin'))], capture_output=True)
    if r.returncode:
        raise RuntimeError(f'render_batch failed {r.returncode} for {name}')
    data = (d / (key + '.bin')).read_bytes()
    out, pos = {}, 0
    while pos < len(data):
        i, w, h, st = np.frombuffer(data[pos:pos + 16], '<i4')
        pos += 16
        if st:
            out[int(i)] = f'REFERENCE_STATUS_{st}'
            continue
        ref = np.frombuffer(data[pos:pos + w * h * 4], np.uint8).reshape(h, w, 4)
        pos += w * h * 4
        f = by[int(i)]
        mine = rgba(frame_planes(name, f), pal, f['kind'])
        out[int(i)] = 'PIXEL_CONFIRMED' if mine.shape == ref.shape and np.array_equal(mine, ref) else 'PIXEL_MISMATCH'
    (d / (key + '.bin')).unlink()
    return out


# ---------------------------------------------------------------- human random palette patches (0x0048B258 semantics)
@functools.lru_cache(maxsize=None)
def palette16(name):
    """GfxPalette16 -> 16x3 colours (gfxcolorrange <palette256> <range>)."""
    for b in cif(r'data\engine2d\inis\palettes\palettes.cif'):
        if b['section'] == 'gfxpalette16' and str(scalar(b, 'editname', '')).lower() == str(name).lower():
            src, rng = commands(b, 'gfxcolorrange')[0]
            return palette(src)[0][rng * 16:(rng + 1) * 16]
    return None


@functools.lru_cache(maxsize=None)
def random_palette_defs():
    return {str(scalar(b, 'name', '')).lower(): b for b in cif(r'data\engine2d\inis\humans\randompalette.cif')}


def apply_random_palette(name, body, head):
    """Deterministic application choosing, per target range, the highest-weight alternative (first on ties) --
    one outcome the native weighted draw can produce. Returns list of applied choices."""
    d = random_palette_defs().get(str(name).lower())
    if d is None:
        return [{'definition': name, 'status': 'NOT_FOUND'}]
    patches = commands(d, 'patch')
    order = list(dict.fromkeys(p[0] for p in patches))
    log = []
    for t in order:
        alts = [p for p in patches if p[0] == t]
        sel = max(alts, key=lambda p: p[-1])  # max() keeps first among equal weights
        dst = body if t <= 15 else head
        if len(sel) == 4:
            log.append({'target': t, 'status': 'NESTED_RANDOMPALETTE_SKIPPED (as production)', 'patch': sel})
            continue
        src = sel[1]
        if isinstance(src, int):
            s = body if src <= 15 else head
            colors = s[(src & 15) * 16:(src & 15) * 16 + 16].copy()
        else:
            colors = palette16(src)
            if colors is None:
                log.append({'target': t, 'status': 'PALETTE16_NOT_FOUND', 'patch': sel})
                continue
        dst[(t & 15) * 16:(t & 15) * 16 + 16] = colors
        log.append({'target': t, 'source': src, 'weight': sel[-1], 'alternatives': len(alts)})
    return log


# ---------------------------------------------------------------- PCX (production decodeIndexedPcx + independent PIL check)
PCX_EXE = HERE / 'export_pcx.exe'


def pcx_decode(data, tag):
    """Returns (indices HxW uint8, palette 256x3 uint8, status, validation)."""
    d = CACHE / 'pcx'
    d.mkdir(parents=True, exist_ok=True)
    src, out = d / (slug(tag) + '.pcx'), d / (slug(tag) + '.bin')
    src.write_bytes(data)
    r = subprocess.run([str(PCX_EXE), str(src), str(out)], capture_output=True)
    raw = out.read_bytes()
    st, w, h = np.frombuffer(raw[:12], '<i4')
    if r.returncode or st != 0:
        return None, None, f'PRODUCTION_DECODE_STATUS_{st}', 'NOT_COMPARED'
    idx = np.frombuffer(raw[12:12 + w * h], np.uint8).reshape(h, w)
    bgra = np.frombuffer(raw[12 + w * h:12 + w * h + 1024], np.uint8).reshape(256, 4)
    pal = bgra[:, [2, 1, 0]].copy()
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(data))
        if im.mode == 'L':  # PIL folds greyscale palettes to L; compare against palette[index]
            ok = bool((pal[:, 0] == pal[:, 1]).all() and (pal[:, 1] == pal[:, 2]).all()) and np.array_equal(np.array(im), pal[idx][:, :, 0])
        else:
            ok = im.mode == 'P' and np.array_equal(np.array(im), idx) and np.array_equal(
                np.frombuffer(bytes(im.getpalette()[:768]), np.uint8).reshape(256, 3), pal)
        v = 'PIXEL_CONFIRMED (production decodeIndexedPcx == independent PIL decode)' if ok else 'PIXEL_MISMATCH vs PIL'
    except Exception as x:
        v = f'PIL_UNAVAILABLE {type(x).__name__}'
    src.unlink(); out.unlink()
    return idx, pal, 'DECODED', v


def reference_render(name, pal, bob_ids, tag):
    """Production drawBobClippedBorrowed32 renders (RGBA arrays) for bob_ids of library `name` with 256x3 `pal`."""
    frames, _ = bmd(name)
    by = {f['bobId']: f for f in frames}
    ids = sorted({i for i in bob_ids if i in by and by[i]['kind'] in (1, 4) and by[i]['width'] and by[i]['height']})
    out = {}
    if not ids:
        return out
    d = CACHE / 'validate'
    d.mkdir(parents=True, exist_ok=True)
    key = slug(stem(name)) + '_ref_' + slug(tag)
    (d / (key + '.ids')).write_text('\n'.join(map(str, ids)))
    (d / (key + '.rgb')).write_bytes(np.ascontiguousarray(pal, np.uint8).tobytes())
    src = CACHE / 'bmd' / slug(stem(name)) / 'source.bmd'
    r = subprocess.run([str(RENDER_BATCH), str(src), str(d / (key + '.rgb')), str(d / (key + '.ids')), str(d / (key + '.bin'))], capture_output=True)
    if r.returncode:
        raise RuntimeError(f'render_batch failed {r.returncode} for {name}')
    data = (d / (key + '.bin')).read_bytes()
    pos = 0
    while pos < len(data):
        i, w, h, st = np.frombuffer(data[pos:pos + 16], '<i4')
        pos += 16
        if st:
            continue
        out[int(i)] = np.frombuffer(data[pos:pos + w * h * 4], np.uint8).reshape(h, w, 4).copy()
        pos += w * h * 4
    (d / (key + '.bin')).unlink()
    return out
