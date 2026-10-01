import sys,json,csv,hashlib,subprocess,struct
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,r'E:\cultures\re-data\evidence\decompilation\tools')
from cultures_lib import read_index
from catalog_game_data import parse_blocks,commands,scalar,PATHS,archive_blob
from cultures_bmd import parse,write_png
import cultures_cif
ROOT=Path(r'E:\assets cultures'); DATA=Path(r'E:\cultures\vanilla-data\DataX'); WORK=Path(__file__).resolve().parent
for d in ['Catalogs','Metadata/Houses','Metadata/Evidence']: (ROOT/d).mkdir(parents=True,exist_ok=True)
def csvout(name,rows,fields=None):
 with (ROOT/'Catalogs'/name).open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields or list(rows[0]));w.writeheader();w.writerows(rows)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
files=sorted([p for p in DATA.rglob('*') if p.is_file()]+list(Path(r'E:\cultures\original').glob('*.exe')))
before={str(p):sha(p) for p in files};(ROOT/'Metadata/Evidence/source_hashes_before.json').write_text(json.dumps(before,indent=2))
inv=[];rows=[];lookup={}
for p in files:
 with p.open('rb') as f:magic=f.read(16).hex()
 item=dict(PATH=str(p),SIZE=p.stat().st_size,MAGIC_HEX=magic,FORMAT=p.suffix,ENTRIES='',NAMES='',COMPRESSION='UNKNOWN',SHA256=before[str(p)])
 if p.suffix.lower()=='.lib':
  idx=read_index(p);item.update(FORMAT='Cultures LIB header word 1',ENTRIES=len(idx.entries),NAMES='full logical paths',COMPRESSION='none at container level')
  for n,e in enumerate(idx.entries):
   lookup.setdefault(e.path.lower(),[]).append((p,idx,n,e))
   rows.append(dict(ARCHIVE=str(p),ENTRY_ID=n,ENTRY_NAME=e.path,OFFSET=e.offset,SIZE=e.size,FORMAT=Path(e.path).suffix.lstrip('.').upper(),COMPRESSED='NO (container)',KNOWN_CATEGORY='Houses' if 'houses' in e.path.lower() else 'UNKNOWN',CONFIDENCE='CONFIRMED',NOTES='ENTRY_ID is zero-based table ordinal, not a native numeric resource ID.'))
 inv.append(item)
csvout('file_inventory.csv',inv);csvout('archive_index.csv',rows)
def resource(name):
 matches=lookup[name.lower()]
 if len(matches)!=1:raise ValueError('ambiguous resource '+name)
 p,idx,n,e=matches[0];return archive_blob(p,idx,name)
def provenance(name):
 p,idx,n,e=lookup[name.lower()][0];return dict(archive=str(p),entryId=n,entryName=e.path,offset=e.offset,size=e.size,sha256=hashlib.sha256(resource(name)).hexdigest())
blocks={k:parse_blocks(resource(PATHS[k])) for k in ['house_graphics','palettes','houses','house_strings','tribes']}
for k in blocks:
 (ROOT/'Metadata/Evidence'/f'{k}.txt').write_text('\n'.join(cultures_cif.decode(resource(PATHS[k]))),encoding='utf-8')
pals={scalar(b,'editname'):scalar(b,'gfxfile') for b in blocks['palettes']}
selected=[];houseRows=[];cross=[]
fields='CATEGORY SUBCATEGORY TRIBE LOGIC_ID GFX_ID JOB_ID GOOD_ID VEHICLE_ID ANIMAL_ID LANDSCAPE_ID LEVEL STATE ARCHIVE ENTRY_ID ENTRY_NAME FORMAT WIDTH HEIGHT FRAMES PIVOT_X PIVOT_Y SHADOW_ENTRY GAME_EXE_ADDRESS EDITOR_EXE_ADDRESS CPP_SYMBOL OUTPUT_PATH CONFIDENCE NOTES'.split()
for gid,b in enumerate([b for b in blocks['house_graphics'] if b['section']=='gfxhouse']):
 name=scalar(b,'editname','')
 if name not in ['viking farm','viking mill','viking bakery','viking home','viking headquarters','viking headquarters house']:continue
 libs=commands(b,'gfxboblibs')[0];logic=dict(commands(b,'logictype'));rec=parse(resource(libs[0]))[0];shadow=parse(resource(libs[1]))[0]
 metadata=dict(nativeName=name,gfxHouseId=gid,tribe=scalar(b,'logictribetype'),libraries=[provenance(x) for x in libs],definition=b,confidence='PARTIAL',mappingEvidence='Native CIF fields; Game registry order; original in-game comparison pending',levels=[])
 for level,bob in commands(b,'gfxbobid'):
  f=rec.frames[bob-rec.header_words[2]];sf=shadow.frames[bob-shadow.header_words[2]]
  row=dict(NAME=name,LOGIC_ID=logic[level],GFX_ID=gid,TRIBE=1,LEVEL=level,BOB_ID=bob,MAIN_LIBRARY=libs[0],SHADOW_LIBRARY=libs[1],SHADOW_BOB_ID=bob,WIDTH=f.width,HEIGHT=f.height,PIVOT_X=-f.dx,PIVOT_Y=-f.dy,PIXEL_KIND=f.kind,SHADOW_KIND=sf.kind,CONSTRUCTION=json.dumps([x for x in commands(b,'gfxbobconstructionlayer') if x[0]==level]),CONFIDENCE='PARTIAL')
  houseRows.append(row);metadata['levels'].append(row)
  cr={k:'' for k in fields};cr.update(CATEGORY='Buildings',SUBCATEGORY=name,TRIBE='Vikings',LOGIC_ID=logic[level],GFX_ID=gid,LEVEL=level,STATE='finished base frame',ARCHIVE=provenance(libs[0])['archive'],ENTRY_ID=provenance(libs[0])['entryId'],ENTRY_NAME=libs[0],FORMAT='BMD',WIDTH=f.width,HEIGHT=f.height,FRAMES=1,PIVOT_X=-f.dx,PIVOT_Y=-f.dy,SHADOW_ENTRY=libs[1],GAME_EXE_ADDRESS='0x0048E651;0x0048089E;0x00430FCE;0x00495B57',EDITOR_EXE_ADDRESS='0x0044543D (registry loader)',CPP_SYMBOL='PublishedGfxHouseDefinition;ProductionWorldCompositor',CONFIDENCE='PARTIAL',NOTES=f'BOB_ID={bob}; base frame only; original-game visual validation pending')
  cross.append(cr)
 (ROOT/'Metadata/Houses'/f'gfx_{gid}.json').write_text(json.dumps(metadata,indent=2))
 selected.append(metadata)
# Export only Farm base frame, using production C++ parser and drawing function.
farm=next(m for m in selected if m['nativeName']=='viking farm');b=farm['definition'];lib=commands(b,'gfxboblibs')[0][0];palname=commands(b,'gfxpalette')[0][0];palpath=pals[palname];pcx=resource(palpath)
assert pcx[-769]==12
(WORK/'farm.bmd').write_bytes(resource(lib));(WORK/'palette.rgb').write_bytes(pcx[-768:])
info=json.loads(subprocess.check_output([str(WORK/'export_frame.exe'),str(WORK/'farm.bmd'),'60',str(WORK/'palette.rgb'),str(WORK/'farm.rgba')],text=True))
out=ROOT/'Vikings/Buildings/Farm/level_0/main/frame_000060.png';write_png(out,info['width'],info['height'],(WORK/'farm.rgba').read_bytes())
meta=dict(category='building',tribe='Vikings',tribeId=1,logicHouseType=12,gfxHouseId=4,level=0,state='finished base frame',bobId=60,frameIndex=60-info['firstBobId'],frames=1,width=info['width'],height=info['height'],pivot=[-info['left'],-info['top']],source=provenance(lib),palette=dict(name=palname,source=provenance(palpath)),shadowAsset=commands(b,'gfxboblibs')[0][1],shadowBobId=60,confidence='PARTIAL',nativeMapping='CIF-evidenced',visualValidation='PENDING comparison with original Game.exe',rendering='Original PCX palette; kind4 second byte ignored for finished body per production drawing code; dynamic lighting/effects not baked; shadow not baked',decoder=info)
(out.parent.parent/'metadata.json').write_text(json.dumps(meta,indent=2))
for r in cross:
 if r['GFX_ID']==4:r['OUTPUT_PATH']=str(out)
csvout('houses.csv',houseRows);csvout('asset_cross_reference.csv',cross,fields)
after={str(p):sha(p) for p in files};assert before==after
(ROOT/'Metadata/Evidence/source_hash_verification.json').write_text(json.dumps(dict(filesChecked=len(files),unchanged=before==after,hashes=after),indent=2))
print(json.dumps(dict(files=len(files),entries=len(rows),mappings=houseRows,export=str(out),decoder=info),indent=2))
