"""Stage 45: pixel audit of exported building PNG files (all tribes) against production drawBobClippedBorrowed32.

Compares the *saved PNG files* (role 'body', palette-coloured) byte-for-byte with the production renderer output.
Viking Farm base keeps MANUAL_CONFIRMED_1TO1 regardless (not re-audited as a manual claim).
"""
import collections, glob
from PIL import Image
from common import *

rows = []
for cat in sorted(glob.glob(str(ROOT / 'Catalogs/*_building_frames.json'))):
    tribe = Path(cat).stem.replace('_building_frames', '')
    recs = [r for r in read(cat) if r.get('role') == 'body' and r.get('path') and r.get('palette')]
    groups = collections.defaultdict(list)
    for r in recs:
        groups[(r['source']['entryName'], r['palette'])].append(r)
    for (lib, pal), rs in groups.items():
        ref = reference_render(lib, palette(pal)[0], [r['bobId'] for r in rs], f'bld_{tribe}_{pal}')
        for r in rs:
            p = ROOT / r['path']
            st = 'MISSING_FILE'
            if p.exists():
                mine = np.array(Image.open(p).convert('RGBA'))
                ref_ = ref.get(r['bobId'])
                st = 'NO_REFERENCE' if ref_ is None else ('PIXEL_CONFIRMED' if mine.shape == ref_.shape and np.array_equal(mine, ref_) else 'PIXEL_MISMATCH')
            rows.append({'TRIBE_SET': tribe, 'LIBRARY': lib, 'PALETTE': pal, 'BOB_ID': r['bobId'], 'PNG': r['path'], 'STATUS': st,
                         'REFERENCE': 'production drawBobClippedBorrowed32 (render_batch.exe)'})
csvout(ROOT / 'Catalogs/building_pixel_audit.csv', rows)
c = collections.Counter((r['TRIBE_SET'], r['STATUS']) for r in rows)
for k, v in sorted(c.items()):
    print(k, v)
