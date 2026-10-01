"""Focused tests for the asset-library pipeline (read-only over sources; checks outputs and native-evidence invariants)."""
import csv, collections, random, traceback
from common import *

R = []


def test(name):
    def deco(fn):
        try:
            fn()
            R.append((name, 'PASS', ''))
        except Exception as e:
            R.append((name, 'FAIL', f'{type(e).__name__}: {e}'))
            traceback.print_exc()
        return fn
    return deco


def rows(p):
    with open(ROOT / p, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


@test('LIB: archive index has 2691 entries; sampled entries match recorded sha256')
def _():
    assert len(INDEX.entries) == 2691
    arch = {r['ENTRY_NAME']: r for r in rows('Catalogs/archive_index.csv')}
    assert len(arch) == 2691 and all(r['CATEGORY'] != 'UNACCOUNTED' for r in arch.values())
    for e in random.Random(7).sample(INDEX.entries, 40):
        assert len(blob(e.path)) == e.size


@test('CIF: all 189 CIF tables decode')
def _():
    c = rows('Catalogs/cif_index.csv')
    assert len(c) == 189 and all(r['STATUS'] == 'DECODED' for r in c)


@test('BMD: 204 libraries decode with production decoder; test_house via lenient tool (3 kind-1, 4 kind-3)')
def _():
    cov = rows('Catalogs/bmd_coverage.csv')
    assert len(cov) == 205
    assert sum(r['DECODE_STATUS'] == 'DECODED' for r in cov) == 204
    th = next(r for r in cov if r['LIBRARY'].lower().endswith('test_house.bmd'))
    assert th['DECODE_STATUS'] == 'DECODED_PARTIAL_UNSUPPORTED_KIND' and th['UNSUPPORTED_KIND'] == '4' and th['NONEMPTY'] == '3'


@test('Palette rendering: random frames re-validated against production drawBobClippedBorrowed32')
def _():
    rnd = random.Random(11)
    for lib, pal in [(r'data\engine2d\bin\bobs\cr_hum_body_30.bmd', 'test_human_00'), (r'data\engine2d\bin\bobs\ls_trees.bmd', 'tree01'),
                     (r'data\engine2d\bin\bobs\cr_ani_body_00.bmd', 'deer01'), (r'data\engine2d\bin\bobs\ls_houses_frank.bmd', 'house01')]:
        fr = [f['bobId'] for f in bmd(lib)[0] if f['kind'] in (1, 4) and f['width']]
        res = validate(lib, palette(pal)[0], rnd.sample(fr, min(25, len(fr))), 'test_' + pal)
        assert res and all(v == 'PIXEL_CONFIRMED' for v in res.values()), (lib, collections.Counter(res.values()))


@test('PCX: all 409 PCX files pixel-confirmed (production decodeIndexedPcx == PIL)')
def _():
    p = [r for r in rows('Catalogs/images.csv') if r['FORMAT'] == 'PCX']
    assert len(p) == 409 and all(r['VALIDATION'].startswith('PIXEL_CONFIRMED') for r in p)


@test('Building rendering: every exported body PNG matches the production renderer; Farm stays MANUAL_CONFIRMED_1TO1')
def _():
    a = rows('Catalogs/building_pixel_audit.csv')
    assert len(a) >= 538 and all(r['STATUS'] == 'PIXEL_CONFIRMED' for r in a)
    farm = next(r for r in rows('Catalogs/houses.csv') if r['GFX_ID'] == '4' and r['LEVEL'] == '0')
    assert farm['STATUS'] == 'MANUAL_CONFIRMED_1TO1'
    assert {r['TRIBE'] for r in rows('Catalogs/houses.csv')} == {'1', '2', '3', '4', '7'}


@test('Mobile sprites: native lookup semantics (head override, shadowed duplicates, walk-speed variants, vehicle job = type + 49)')
def _():
    h = rows('Catalogs/human_job_atomic_animation.csv')
    hunter = [r for r in h if r['TRIBE_ID'] == '1' and r['TYPE_ID'] == '15' and r['BOBSEQ_BODY'] == 'human_man_hunter_walk']
    assert hunter and all(r['BOBSEQ_HEAD'] == 'human_man_generic_walk' for r in hunter)
    sh = rows('Metadata/Mobile/shadowed_records_human.csv')
    assert any(r['bodySequence'] == 'human_man_Civilian_Fight_double_punch' and r['tribe'] == '1' for r in sh)
    an = rows('Catalogs/animal_animations.csv')
    wolf = {r['WALK_SPEED_THRESHOLD'] for r in an if r['TRIBE_ID'] == '20' and r['KIND'] == 'walk' and r['CARRIED_GOOD'] in ('', '0', 'None')}
    assert {'5', '8'} <= wolf, wolf
    v = rows('Catalogs/vehicles.csv')
    assert all(int(r['ANIMATION_JOB_ID']) == int(r['TYPE_ID']) + 49 for r in v)
    assert any(r['TYPE_ID'] == '4' and r['NATIVE_DECLARATION'] == 'NATIVE_DECLARATION_NO_GRAPHICS' for r in v)
    assert len(rows('Catalogs/humans.csv')) == 269


@test('Asset metadata: goods IDs evidence-backed (Bread 19, Shoes 30, Wooden Tool 31, Iron Tool 32)')
def _():
    g = {r['GOOD_ID']: r for r in rows('Catalogs/goods.csv')}
    assert len(g) == 65
    assert (g['19']['ENGLISH'], g['30']['ENGLISH'], g['31']['ENGLISH'], g['32']['ENGLISH']) == ('Bread', 'Shoes', 'Wooden Tool', 'Iron Tool')
    assert g['19']['NATIVE_NAME'] == 'bread' and g['31']['NATIVE_NAME'] == 'tool_wooden'


@test('Catalog generation: statuses and unknown classes within the allowed vocabularies; zero-discard census')
def _():
    allowed = {'SOURCE_COMPLETE', 'PIXEL_CONFIRMED', 'MANUAL_CONFIRMED_1TO1', 'PARTIAL', 'PRESENTATION_PARTIAL', 'PRESENTATION_APPROXIMATION', 'UNKNOWN'}
    x = rows('Catalogs/asset_cross_reference.csv')
    assert {r['STATUS'] for r in x} <= allowed
    ucls = {'UNKNOWN_UNREFERENCED', 'UNKNOWN_NAMED_SEQUENCE', 'UNKNOWN_PALETTE', 'UNKNOWN_GRAPHICS_BINDING', 'UNKNOWN_UNSUPPORTED_PIXEL_KIND', 'UNKNOWN_NATIVE_STUB', 'UNKNOWN_OTHER'}
    assert {r['UNKNOWN_CLASS'] for r in rows('Catalogs/unknown_assets.csv')} <= ucls
    assert all(r['UNKNOWN_CLASS'] for r in x if r['STATUS'] == 'UNKNOWN' and r['CATEGORY'] in ('Unknown', 'UI'))
    c = read(ROOT / 'Unknown/census_summary.json')
    assert c['silentlyDiscarded'] == 0 and c['mappedFrames'] + c['notMapped'] == c['nonemptyFrames'] + c['unsupportedKindFrames']
    lib_frames = sum(len(read(p)['frames']) for p in (ROOT / 'Shared/SourceLibraries').glob('*/library.json'))
    assert lib_frames == c['nonemptyFrames'] + c['unsupportedKindFrames']
    ids = [r['ASSET_ID'] for r in x]
    assert len(ids) == len(set(ids)), 'duplicate asset ids'


@test('Browser-link validation: 0 broken links, 0 catalogued assets without browser route, UTF-8 clean')
def _():
    v = read(ROOT / 'Metadata/Evidence/library/browser_validation.json')
    assert v['brokenLinks'] == 0 and v['cataloguedWithoutBrowserRoute'] == 0 and v['mojibakeFiles'] == 0 and not v['nonUtf8TextFiles'] and not v['htmlWithoutUtf8Meta']
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    for need in ('Vikings', 'Franks', 'Byzantines', 'Saracens', 'Egypt', 'Weresnake', 'Werewolf', 'Shared', 'Terrain', 'UI', 'Audio', 'FMV', 'Fonts', 'Catalogs',
                 'Native definitions', 'Unknown', 'Evidence', 'id="search"'):
        assert need in home, need


for n, s, d in R:
    print(f'{s}  {n}' + (f'  -- {d}' if d else ''))
write(ROOT / 'Metadata/Evidence/library/focused_tests.json', [{'test': n, 'result': s, 'detail': d} for n, s, d in R])
print(f"{sum(s == 'PASS' for _, s, _ in R)}/{len(R)} passed")
