"""Stage 1: decode every BMD in the archive with the production decoder and record per-frame facts."""
import collections
from common import *

rows = []
for n, e in enumerate(INDEX.entries):
    if not e.path.lower().endswith('.bmd'):
        continue
    try:
        frames, planes = bmd(e.path)
        kinds = collections.Counter(f['kind'] for f in frames)
        nonempty = 0
        out = []
        for f in frames:
            size = f['width'] * f['height'] * 3
            chunk = planes[f['offset']:f['offset'] + size]
            ne = bool(size and any(chunk[1::3]))
            nonempty += ne
            out.append({k: f[k] for k in ('bobId', 'frameIndex', 'kind', 'x', 'y', 'width', 'height')} |
                       {'pivot': [-f['x'], -f['y']], 'nonempty': ne, 'planesSha256': hashlib.sha256(chunk).hexdigest()})
        write(ROOT / 'Metadata/Sources/BMD' / (slug(stem(e.path)) + '.json'),
              {'source': source(e.path), 'decoder': 'cultures::graphics::decodeBobLibraryBmd (production, via export_planes.exe)',
               'firstBobId': frames[0]['bobId'] if frames else None, 'frames': out}, compact=True)
        rows.append({'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'SIZE': e.size, 'SHA256': source(e.path)['sha256'],
                     'FRAMES': len(frames), 'NONEMPTY': nonempty, 'FIRST_BOB': frames[0]['bobId'] if frames else '',
                     'KINDS': dict(sorted(kinds.items())), 'STATUS': 'DECODED'})
    except Exception as x:
        rows.append({'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'SIZE': e.size, 'STATUS': f'FAILED {x}'})
    print(rows[-1]['ENTRY_NAME'], rows[-1].get('FRAMES'), rows[-1]['STATUS'], flush=True)
csvout(ROOT / 'Catalogs/bmd_libraries.csv', rows)
print('BMD', len(rows), 'decoded', sum(r['STATUS'] == 'DECODED' for r in rows), 'frames', sum(r.get('FRAMES', 0) for r in rows),
      'nonempty', sum(r.get('NONEMPTY', 0) for r in rows))
