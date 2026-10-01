"""Stage 0: source-hash baseline (or verification) and full CIF evidence dump."""
import sys
from common import *

mode = sys.argv[1] if len(sys.argv) > 1 else 'before'
hashes = {str(p): sha_file(p) for p in source_files()}
ev = ROOT / 'Metadata/Evidence/library'
if mode == 'before':
    write(ev / 'source_hashes_before.json', hashes)
    out = ROOT / 'Metadata/Sources/CIF'
    rows = []
    for n, e in enumerate(INDEX.entries):
        if not e.path.lower().endswith('.cif'):
            continue
        rp = e.path.replace(B, '/')
        try:
            lines = cif_lines(e.path)
            blocks = cif(e.path)
            (out / (rp + '.txt')).parent.mkdir(parents=True, exist_ok=True)
            (out / (rp + '.txt')).write_text('\n'.join(lines), encoding='utf-8')
            write(out / (rp + '.json'), {'source': source(e.path), 'blocks': blocks}, compact=True)
            sections = {}
            for b in blocks:
                sections[b['section']] = sections.get(b['section'], 0) + 1
            rows.append({'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'SECTIONS': sections, 'STATUS': 'DECODED'})
        except Exception as x:  # keep record of undecodable CIF
            rows.append({'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'SECTIONS': {}, 'STATUS': f'FAILED {type(x).__name__}: {x}'})
    csvout(ROOT / 'Catalogs/cif_index.csv', rows)
    print('hashed', len(hashes), 'cif', len(rows), 'failed', sum(r['STATUS'] != 'DECODED' for r in rows))
else:
    before = read(ev / 'source_hashes_before.json')
    changed = [k for k in before if before[k] != hashes.get(k)]
    added = [k for k in hashes if k not in before]
    res = {'filesChecked': len(before), 'changed': changed, 'added': added, 'unchanged': not changed,
           'ORIGINAL_FILES_MODIFIED': 'NONE' if not changed else 'MODIFIED'}
    write(ev / f'source_hashes_{mode}.json', dict(res, hashes=hashes))
    print(json.dumps(res))
