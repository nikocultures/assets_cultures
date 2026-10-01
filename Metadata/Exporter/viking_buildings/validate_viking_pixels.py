import json,subprocess,sys,hashlib
from pathlib import Path
from PIL import Image
sys.path.insert(0,r'E:\cultures\re-data\evidence\decompilation\tools')
from cultures_lib import read_index
from catalog_game_data import archive_blob
r=Path(r'E:\assets cultures');a=Path(r'E:\cultures\vanilla-data\DataX\Libs\data0001.lib');idx=read_index(a);dest=r/'Metadata/Exporter/viking_buildings/validation';dest.mkdir(exist_ok=True);rows=[]
for p in (r/'Vikings/Buildings').glob('**/level_*/metadata.json'):
 m=json.loads(p.read_text())
 for f in m.get('baseFrames',[]):
  if not f.get('path'):continue
  pal=archive_blob(a,idx,f['paletteSource']['entryName']);(dest/'palette.rgb').write_bytes(pal[-768:]);q=subprocess.run([str(Path(__file__).resolve().parent/'export_frame.exe'),str(r/f['rawLibrary']),str(f['bobId']),str(dest/'palette.rgb'),str(dest/'reference.rgba')],check=True,capture_output=True,text=True)
  expected=(dest/'reference.rgba').read_bytes();image=Image.open(r/f['path']).convert('RGBA');same=expected==image.tobytes();assert same,f['path'];rows.append({'gfxHouseId':m['gfxHouseId'],'level':m['level'],'palette':f['palette'],'bobId':f['bobId'],'pixelEqualToProductionDraw':same,'path':f['path']})
(r/'Metadata/Evidence/viking_buildings_pixel_validation.json').write_text(json.dumps({'comparison':'Independent production drawBobClippedBorrowed32 vs exported source PNG; not an original game screenshot','framesChecked':len(rows),'allEqual':all(x['pixelEqualToProductionDraw'] for x in rows),'records':rows},indent=2))
print('Production body draw comparison:',len(rows),'PASS')
