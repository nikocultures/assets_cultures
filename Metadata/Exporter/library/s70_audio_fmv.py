"""Stage 70: audio (archive WAV, DataX DM2 DirectMusic) and FMV (DataX FMV MPEG) inventory.

WAVs are extracted bit-exact from data0001.lib (no transcoding). DM2 and FMV files stay where they are (originals,
referenced by path). Native references: soundfx.cif (+ _nomissioncd), humans/sounds.cif, animals/sounds.cif,
map.cif misc_music.
"""
import collections, struct, glob
from common import *

SFX = [r'data\engine2d\inis\soundfx\soundfx.cif', r'data\engine2d\inis\soundfx\soundfx_nomissioncd.cif']
refs = collections.defaultdict(list)
byname = collections.defaultdict(list)
for p in SFX:
    for i, b in enumerate(cif(p)):
        name = str(scalar(b, 'name', ''))
        for a in commands(b, 'sfx'):
            refs[norm(a[0])].append({'table': p.split(B)[-1], 'section': b['section'], 'sectionOrdinal': i, 'name': name, 'parameters': a[1:],
                                     'logicSoundType': scalar(b, 'logicsoundtype'), 'landscapeGroup': scalar(b, 'landscapegroup'),
                                     'patternGroup': scalar(b, 'patterngroup'), 'musicType': scalar(b, 'musictype')})
        byname[name.lower()].append(p)
human_use = collections.defaultdict(list)
for b in cif(r'data\engine2d\inis\humans\sounds.cif'):
    t = scalar(b, 'logictribe')
    for c in b['commands']:
        if c['name'] in ('scream', 'generic', 'respond'):
            human_use[str(c['arguments'][-1]).lower()].append({'tribe': t, 'use': c['name'], 'arguments': c['arguments'][:-1]})
animal_use = collections.defaultdict(list)
for b in cif(r'data\engine2d\inis\animals\sounds.cif'):
    animal_use[str(scalar(b, 'enginesoundgroup', '')).lower()].append({'tribe': scalar(b, 'logictribetype'), 'probability': scalar(b, 'probability'), 'minCount': scalar(b, 'mincount')})


def wav_info(data):
    if data[:4] != b'RIFF' or data[8:12] != b'WAVE':
        return {'format': 'NOT_RIFF_WAVE'}
    pos, info = 12, {}
    while pos + 8 <= len(data):
        cid, size = data[pos:pos + 4], struct.unpack_from('<I', data, pos + 4)[0]
        if cid == b'fmt ':
            fmt, ch, rate, byterate, align, bits = struct.unpack_from('<HHIIHH', data, pos + 8)
            info.update(formatTag=fmt, channels=ch, sampleRate=rate, byteRate=byterate, blockAlign=align, bitsPerSample=bits)
        elif cid == b'data':
            info['dataBytes'] = size
        pos += 8 + size + (size & 1)
    if info.get('byteRate') and 'dataBytes' in info:
        info['durationSeconds'] = round(info['dataBytes'] / info['byteRate'], 3)
    info['format'] = {1: 'PCM', 2: 'MS-ADPCM', 0x11: 'IMA-ADPCM'}.get(info.get('formatTag'), f"tag {info.get('formatTag')}")
    return info


def category(path, r, hu):
    folder = norm(path).split(B)[-2]
    if hu:
        return 'Human voices'
    if folder == 'ambient':
        return 'Ambient'
    if folder == 'jingles':
        return 'Music jingles'
    if folder == 'gui':
        return 'UI'
    n = ' '.join(x['name'].lower() for x in r) + ' ' + path.lower()
    for key, cat in (('animal', 'Animals'), ('ship', 'Ships'), ('vehicle', 'Vehicles'), ('cart', 'Vehicles'), ('fight', 'Combat'), ('hit', 'Combat'),
                     ('sword', 'Combat'), ('arrow', 'Combat'), ('build', 'Construction'), ('construct', 'Construction'), ('fire', 'Environment'),
                     ('water', 'Environment'), ('rain', 'Environment'), ('wind', 'Environment')):
        if key in n:
            return cat + ' (name-derived)'
    if folder == 'humantalk':
        return 'Human voices'
    if folder in ('static', 'generic'):
        return 'Production/actions (folder ' + folder + ')'
    return 'Unknown'


rows = []
for n, e in enumerate(INDEX.entries):
    if not e.path.lower().endswith(('.wav', '.txt')) or B + 'sounds' + B not in norm(e.path):
        continue
    data = blob(e.path)
    r = refs.get(norm(e.path), [])
    names = {x['name'].lower() for x in r}
    hu = [u for nm in names for u in human_use.get(nm, [])]
    au = [u for nm in names for u in animal_use.get(nm, [])]
    out = ROOT / 'Audio' / slug(norm(e.path).split(B)[-2]) / e.path.replace('/', B).split(B)[-1]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    info = wav_info(data) if e.path.lower().endswith('.wav') else {'format': 'TEXT'}
    cat = category(e.path, r, hu) if not au else 'Animals'
    meta = {'source': source(e.path), 'output': rel(out), 'header': info, 'nativeReferences': r, 'humanSoundUse': hu, 'animalSoundUse': au, 'category': cat,
            'categoryConfidence': 'NATIVE_TABLE' if (hu or au or info.get('format') == 'TEXT' or norm(e.path).split(B)[-2] in ('ambient', 'jingles', 'gui')) else
            ('NAME_DERIVED' if 'name-derived' in cat else 'FOLDER_ONLY'), 'preservation': 'bit-exact copy of archive entry (sha256 identical)'}
    write(out.with_suffix(out.suffix + '.json'), meta)
    rows.append({'ARCHIVE': str(ARCH), 'ENTRY_ID': n, 'ENTRY': e.path, 'FORMAT': info.get('format'), 'CHANNELS': info.get('channels'), 'SAMPLE_RATE': info.get('sampleRate'),
                 'BITS': info.get('bitsPerSample'), 'DURATION_S': info.get('durationSeconds'), 'NATIVE_NAMES': sorted(names),
                 'NATIVE_SECTIONS': sorted({x['section'] for x in r}), 'HUMAN_USE': sorted({f"tribe{u['tribe']}:{u['use']}" for u in hu}),
                 'ANIMAL_USE': sorted({f"tribe{u['tribe']}" for u in au}), 'CATEGORY': cat, 'CONFIDENCE': meta['categoryConfidence'] if r or info.get('format') == 'TEXT' else 'UNKNOWN (no native reference)',
                 'OUTPUT': rel(out), 'SHA256': meta['source']['sha256']})
# DirectMusic (loose DataX\DM2): RIFF form type only; originals referenced in place
music_use = collections.defaultdict(list)
for e in INDEX.entries:
    if e.path.lower().endswith('map.cif'):
        for b in cif(e.path):
            if b['section'] == 'misc_music':
                for c in b['commands']:
                    for a in c['arguments']:
                        if isinstance(a, str):
                            music_use[a.lower()].append(e.path)
for p in sorted((DATAX / 'DM2').glob('*')):
    head = p.open('rb').read(12)
    form = head[8:12].decode('latin-1') if head[:4] == b'RIFF' else 'NOT_RIFF'
    users = sorted({m for k, v in music_use.items() if k in p.stem.lower() or p.stem.lower() in k for m in v})
    rows.append({'ARCHIVE': 'loose DataX file', 'ENTRY_ID': '', 'ENTRY': str(p), 'FORMAT': f'DirectMusic {p.suffix[1:].upper()} RIFF:{form}', 'DURATION_S': 'UNKNOWN (DirectMusic segment; no decoder)',
                 'NATIVE_NAMES': [], 'NATIVE_SECTIONS': ['map.cif misc_music'] if users else [], 'HUMAN_USE': [], 'ANIMAL_USE': [],
                 'CATEGORY': 'Music (DirectMusic ' + ('segment' if p.suffix.lower() == '.sgt' else 'DLS instrument collection') + ')',
                 'CONFIDENCE': 'SOURCE_COMPLETE (format); usage ' + ('NATIVE (map.cif)' if users else 'UNKNOWN'), 'MAP_USES': users, 'OUTPUT': str(p), 'SHA256': sha_file(p)})
csvout(ROOT / 'Catalogs/audio.csv', rows)
write(ROOT / 'Catalogs/audio.json', rows)
print('audio', len(rows), collections.Counter(r['CATEGORY'].split(' (')[0] for r in rows), collections.Counter(str(r['CONFIDENCE'])[:20] for r in rows))
write(ROOT / 'Metadata/Audio/music_references.json', music_use)


# ---------------------------------------------------------------- FMV (MPEG program/system stream header facts)
def mpeg_info(p):
    data = p.read_bytes()
    i = data.find(b'\x00\x00\x01\xb3')
    info = {'size': len(data)}
    if i >= 0:
        w = (data[i + 4] << 4) | (data[i + 5] >> 4)
        h = ((data[i + 5] & 15) << 8) | data[i + 6]
        fr = data[i + 7] & 15
        br = ((data[i + 8] << 10) | (data[i + 9] << 2) | (data[i + 10] >> 6)) * 400
        info.update(videoStandard='MPEG-1/2 video sequence header', width=w, height=h,
                    frameRate={1: 23.976, 2: 24, 3: 25, 4: 29.97, 5: 30, 6: 50, 7: 59.94, 8: 60}.get(fr), declaredBitrate=br)
    gops = [j for j in range(0, len(data) - 8) if data[j:j + 4] == b'\x00\x00\x01\xb8'] if len(data) < 64_000_000 else []
    if gops:
        last = gops[-1] + 4
        tc = int.from_bytes(data[last:last + 4], 'big')
        hh, mm, ss, ff = (tc >> 26) & 31, (tc >> 20) & 63, (tc >> 13) & 63, (tc >> 7) & 63
        info.update(gopCount=len(gops), lastGopTimecode=f'{hh:02d}:{mm:02d}:{ss:02d}.{ff:02d}',
                    approxDurationSeconds=round(hh * 3600 + mm * 60 + ss + (ff / info['frameRate'] if info.get('frameRate') else 0), 2))
    info['audioStreams'] = sorted({hex(data[j + 3]) for j in range(0, min(len(data), 4_000_000) - 4) if data[j:j + 3] == b'\x00\x00\x01' and 0xC0 <= data[j + 3] <= 0xDF})
    return info


fm = []
for p in sorted((DATAX / 'FMV').rglob('*')):
    if p.is_file():
        info = mpeg_info(p)
        fm.append({'FILE': str(p), 'LANGUAGE_FOLDER': p.parent.name, 'NAME': p.stem, 'ROLE': 'intro (name)' if 'intro' in p.stem.lower() else ('scripted FMV slot %d: Game.exe/GameMp.exe format datax\FMV\%%s\%%s.mpg with seq_%%4.4d via mission commands start_fmv/start_pre_ingame_fmv; no map.cif in data0001.lib invokes them' % int(p.stem.split('_')[-1]) if p.stem.lower().startswith('seq_') else 'UNKNOWN'),
                   **{k.upper(): v for k, v in info.items()}, 'SHA256': sha_file(p), 'PRESERVATION': 'original left in place; no transcoding',
                   'THUMBNAIL': 'NOT_GENERATED (no MPEG decoder available in this environment)'})
csvout(ROOT / 'Catalogs/fmv.csv', fm)
write(ROOT / 'FMV/index.json', fm)
print('fmv', fm)
