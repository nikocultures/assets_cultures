"""Stage 85: non-graphical archive documents (HLT hypertext, map DAT, TXT) -> raw bit-exact copies + reference metadata.

HLT parsed with the existing cultures_hlt reader (bytes unchanged) to list picture/icon/font/colour references;
map DAT chunk structure listed with the existing cultures_map_dat reader.
"""
import collections
from common import *
import cultures_hlt, cultures_map_dat

rows = []
for n, e in enumerate(INDEX.entries):
    ext = e.path.lower().rsplit('.', 1)[-1]
    if ext not in ('hlt', 'dat', 'txt') or B + 'sounds' + B in norm(e.path):
        continue
    data = blob(e.path)
    out = ROOT / 'Metadata/Sources/Raw' / e.path.replace(B, '/')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    row = {'ENTRY_ID': n, 'ENTRY_NAME': e.path, 'FORMAT': ext.upper(), 'SIZE': e.size, 'SHA256': source(e.path)['sha256'], 'OUTPUT': rel(out),
           'PRESERVATION': 'bit-exact copy', 'REFERENCES': [], 'STRUCTURE': ''}
    try:
        if ext == 'hlt':
            doc = cultures_hlt.parse(data)
            refs = []
            for t in getattr(doc, 'tags', []) or []:
                nm = getattr(t, 'name', '')
                if nm in ('picture', 'icon', 'font', 'color', 'globaljump', 'include'):
                    refs.append(f"{nm}:{' '.join(map(str, getattr(t, 'arguments', [])))}")
            row.update(REFERENCES=sorted(set(refs)), STATUS='SOURCE_COMPLETE (parsed by cultures_hlt)')
        elif ext == 'dat':
            ch = cultures_map_dat.parse_chunks(data)
            row.update(STRUCTURE=f'{len(ch)} chunks', STATUS='SOURCE_COMPLETE (chunk structure via cultures_map_dat)')
        else:
            row.update(STATUS='SOURCE_COMPLETE (plain text)')
    except Exception as x:
        row.update(STATUS=f'PRESERVED_RAW (parser: {type(x).__name__}: {str(x)[:80]})')
    row['CATEGORY'] = 'Map data' if B + 'maps' + B in norm(e.path) else 'Hypertext'
    rows.append(row)
csvout(ROOT / 'Catalogs/documents.csv', rows)
print('documents', len(rows), collections.Counter((r['FORMAT'], r['STATUS'][:16]) for r in rows))
