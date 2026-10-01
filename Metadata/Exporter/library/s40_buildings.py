import sys,json,csv,hashlib,subprocess,re,shutil,html,os,collections
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
sys.path.insert(0,r'E:\cultures\re-data\evidence\decompilation\tools')
from catalog_game_data import read_index,archive_blob,parse_blocks,commands,scalar,PATHS
ROOT=Path(r'E:\assets cultures');HERE=ROOT/'Metadata/Exporter/viking_buildings';CACHE=Path(__file__).resolve().parent/'cache'/'buildings';CACHE.mkdir(parents=True,exist_ok=True)
TRIBE_ID=int(sys.argv[1]);TRIBE_NAME={1:'Vikings',2:'Franks',3:'Byzantines',4:'Arabs',7:'Other Tribes/Egypt'}[TRIBE_ID];TAG=TRIBE_NAME.split('/')[-1].lower()
PREFIX={1:'viking ',2:'frank ',3:'byzantine ',4:'saracen ',7:'egypt '}[TRIBE_ID]
ARCH=Path(r'E:\cultures\vanilla-data\DataX\Libs\data0001.lib');INDEX=read_index(ARCH);ENT={e.path.lower():(n,e) for n,e in enumerate(INDEX.entries)}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
inputs=sorted(p for root in [Path(r'E:\cultures\vanilla-data\DataX'),Path(r'E:\cultures\original')] for p in root.rglob('*') if p.is_file())
before={str(p):digest(p) for p in inputs}
def write(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding='utf-8')
def blob(n):return archive_blob(ARCH,INDEX,n)
def slug(n):return re.sub(r'[^\w.-]+','_',n.strip(),flags=re.UNICODE).strip('_')
def rel(p):return str(p.relative_to(ROOT)).replace('\\','/')
def source(n):
 idx,e=ENT[n.lower()];return {'archive':str(ARCH),'entryId':idx,'entryName':e.path,'offset':e.offset,'size':e.size,'sha256':hashlib.sha256(blob(n)).hexdigest()}
def parsed(n):return parse_blocks(blob(n))
HOUSES=parsed(PATHS['house_graphics']);PALS=parsed(PATHS['palettes']);LAND=parsed(r'data\engine2d\inis\landscapes\landscapes.cif')
PAL={str(scalar(b,'editname')).lower():b for b in PALS};LANDMAP={str(scalar(b,'editname')).lower():b for b in LAND};LO={scalar(b,'logictype'):b for b in parsed(PATHS['houses'])}
shared=collections.defaultdict(set)
for b in HOUSES:
 for libs in commands(b,'gfxboblibs'):
  for n in libs:shared[n.lower()].add(scalar(b,'logictribetype'))
LIB={};PALETTE={};errors=[];records=[];levels=[];buildings=[];rendered={};land_exported={};currentErrors=[]
def library(n):
 if n.lower() in LIB:return LIB[n.lower()]
 d=CACHE/slug(n);d.mkdir(exist_ok=True);raw=d/'source.bmd';raw.write_bytes(blob(n))
 subprocess.run([str(HERE/'export_planes.exe'),str(raw),str(d)],check=True,capture_output=True)
 frames={f['bobId']:f for f in json.loads((d/'frames.json').read_text())}
 LIB[n.lower()]=(d,frames,raw);return LIB[n.lower()]
def planes(n,bob):
 d,fs,raw=library(n);f=fs[bob];a=np.frombuffer((d/f'{bob}.planes').read_bytes(),dtype=np.uint8).reshape(f['height'],f['width'],3).copy();return f,a

def palette(n):
 if n.lower() not in PALETTE:
  b=PAL[n.lower()];path=scalar(b,'gfxfile');data=blob(path)
  if len(data)<769 or data[-769]!=12:raise ValueError('No PCX palette '+path)
  PALETTE[n.lower()]=(np.frombuffer(data[-768:],dtype=np.uint8).reshape(256,3),source(path),b)
 return PALETTE[n.lower()]
def save_rgba(p,a):
 a[a[:,:,3]==0]=0
 p.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(a,'RGBA').save(p)
def darken(a,mask):
 # Native 0x0049B930 integer arithmetic in BGR destination convention.
 v=a[:,:,2].astype(np.uint32)|(a[:,:,1].astype(np.uint32)<<8)|(a[:,:,0].astype(np.uint32)<<16)
 t1=((v>>15)&0x1fffe)//3;t2=((v&255)<<1)//3
 v=((((v>>7)&0x1fe)//3)|(t1<<8))<<8|(((t1+t2)>>4)+t2)
 for c,shift in [(0,16),(1,8),(2,0)]:a[:,:,c][mask]=((v>>shift)&255)[mask]
 return a

def frame_unchecked(n,bob,pal,target,role='body',force_shared=False):
 key=(n.lower(),bob,pal.lower() if pal else '',role)
 if key in rendered:return rendered[key]
 f,a=planes(n,bob)
 common={'bobId':bob,'descriptor':f,'pivot':[-f['x'],-f['y']],'source':source(n),'rawLibrary':rel(library(n)[2]),'role':role,'confidence':'AUTOMATED_CONFIRMED'}
 if role=='reveal_threshold' and f['kind']!=4:
  common.update(notApplicable=True,path=None,representation='No kind4 second-byte reveal plane in this descriptor');rendered[key]=common;return common
 if f['kind']==0 or not f['width'] or not f['height']:
  common.update(empty=True,path=None);rendered[key]=common;return common
 if force_shared or len(shared[n.lower()])>1:
  target=ROOT/'Shared/Buildings'/slug(n)/slug(pal or 'coverage')/role/f'frame_{bob:06}.png'
 target.parent.mkdir(parents=True,exist_ok=True)
 if role in ['shadow_coverage','auxiliary_threshold']:
  v=a[:,:,0] if role=='auxiliary_threshold' else np.full(a.shape[:2],255,dtype=np.uint8)
  rgba=np.dstack([v,v,v,a[:,:,1]])
  common['representation']='DATA mask: coverage and per-pixel threshold; not an alpha shadow or colored sprite'
 elif role=='reveal_threshold':
  v=a[:,:,2];rgba=np.dstack([v,v,v,a[:,:,1]]);common['representation']='DATA mask: second source byte, not display alpha'
 else:
  colors,prov,pdef=palette(pal);rgba=np.dstack([colors[a[:,:,0]],a[:,:,1]])
  common.update(palette=pal,paletteSource=prov,paletteDefinition=pdef,representation='Unlit source color frame; runtime light/selection/background composition separate')
  if role=='effect' and f['kind']==4:
   rgba[:,:,3]=(a[:,:,2].astype(np.uint16)*a[:,:,1]//255).astype(np.uint8);common['representation']='Source RGBA preview; native kind4 /256 blending and runtime effects remain separate'
 save_rgba(target,rgba);common['path']=rel(target);common['pixelSha256']=hashlib.sha256(rgba.tobytes()).hexdigest();write(target.with_suffix('.json'),common);rendered[key]=common
 return common

def frame(n,bob,pal,target,role='body',force_shared=False):
 try:
  return frame_unchecked(n,bob,pal,target,role,force_shared)
 except Exception as e:
  message=f'{role}: {n} BOB {bob}: {type(e).__name__}: {e}'
  currentErrors.append(message)
  m={'bobId':bob,'source':source(n),'path':None,'descriptor':{},'confidence':'UNKNOWN','error':message}
  unknown=ROOT/'Unknown/ByArchive/data0001'/f'entry_{source(n)["entryId"]:06}'/f'bob_{bob}_{role}.json'
  write(unknown,m)
  return m

def landscape(name):
 key=name.replace('_',' ').lower()
 if key in land_exported:return land_exported[key]
 if key not in LANDMAP:raise ValueError('Landscape definition unresolved: '+name)
 b=LANDMAP[key];libs=commands(b,'gfxboblibs')[0];pals=commands(b,'gfxpalette')[0];folder=ROOT/'Shared/Effects'/slug(key);seqs=[]
 for args in commands(b,'gfxframes'):
  seq=[]
  for bob in args[1:]:seq.append(frame(libs[0],bob,pals[0],folder/f'frame_{bob:06}.png','effect',True))
  seqs.append({'nativeValency':args[0],'frames':seq})
 m={'nativeName':scalar(b,'editname'),'definition':b,'sequences':seqs,'timing':'UNKNOWN until runtime owner/rate validated','confidence':'PARTIAL','source':source(r'data\engine2d\inis\landscapes\landscapes.cif')};write(folder/'metadata.json',m);land_exported[key]=rel(folder/'metadata.json');return land_exported[key]

def construction(lib,pal,tuples,out):
 ids={v for t in tuples for v in t[2:4] if v>=0}
 if not ids:return []
 desc=[planes(lib,b)[0] for b in ids];xmin=min(f['x'] for f in desc);ymin=min(f['y'] for f in desc);xmax=max(f['x']+f['width'] for f in desc);ymax=max(f['y']+f['height'] for f in desc);w=xmax-xmin;h=ymax-ymin
 results=[];colors,_,_=palette(pal)
 for p in [0,10,25,50,75,100]:
  rgba=np.zeros((h,w,4),dtype=np.uint8);op=np.zeros((h,w),dtype=np.uint8);contrib=[]
  eligible=[]
  for t in tuples:
   lvl,ext,bob,aux,start,end=t
   if ext or start>p:continue
   if end==start and p==end:raise ValueError('native zero denominator construction tuple '+str(t))
   threshold=256 if p>end else (((p-start)*100//(end-start))*255)//100
   eligible.append((t,threshold))
   if aux>=0:
    f,a=planes(lib,aux)
    if f['kind']==0:continue
    if f['kind']!=1:raise ValueError('unsupported auxiliary kind '+str(f))
    mask=(a[:,:,1]>0)&(a[:,:,0]<=threshold);sl=np.s_[f['y']-ymin:f['y']-ymin+f['height'],f['x']-xmin:f['x']-xmin+f['width']];op[sl]+=mask.astype(np.uint8)
  for t,threshold in eligible:
   f,a=planes(lib,t[2]);mask=a[:,:,1]>0
   if p<=t[5]:
    if f['kind']!=4:mask=np.zeros_like(mask) # native 0049DA62 only kind4
    else:mask &= a[:,:,2]<=threshold
   sl=np.s_[f['y']-ymin:f['y']-ymin+f['height'],f['x']-xmin:f['x']-xmin+f['width']];layer=rgba[sl];layer[:,:,:3][mask]=colors[a[:,:,0]][mask];layer[:,:,3][mask]=255
   contrib.append({'tuple':t,'threshold':threshold,'bodyPixels':int(mask.sum()),'drawOrder':'auxiliary pass before all body layers; body layer order follows CIF'})
  path=out/f'progress_{p:03}.png';save_rgba(path,rgba);Image.fromarray(op,'L').save(out/f'progress_{p:03}_destination_darken_counts.png')
  yy,xx=np.indices((h,w));bg=np.where(((xx//16+yy//16)%2)==0,176,208).astype(np.uint8);preview=np.dstack([bg,bg,bg,np.full_like(bg,255)])
  for count in range(int(op.max())):darken(preview,op>count)
  mask=rgba[:,:,3]>0;preview[mask]=rgba[mask];save_rgba(out/f'PREVIEW_progress_{p:03}_checkerboard.png',preview)
  m={'progressPercent':p,'path':rel(path),'pivot':[-xmin,-ymin],'dimensions':[w,h],'palette':pal,'contributingLayers':contrib,'destinationDarkeningCounts':rel(out/f'progress_{p:03}_destination_darken_counts.png'),'confidence':'PARTIAL','note':'PNG is body-only on transparent background; destination-dependent auxiliary pass is separate. Checkerboard image is PREVIEW, not original terrain. Native progress thresholds/order recovered at 0x00495B57/0x0049DA62/0x0049E618; runtime palette/shading and builder marker not baked.'};write(path.with_suffix('.json'),m);results.append(m)
 return results

write(ROOT/f'Metadata/Evidence/{TAG}_buildings_hashes_before.json',before)
priority={}
selected=[(i,b) for i,b in enumerate(HOUSES) if b['section']=='gfxhouse' and scalar(b,'logictribetype')==TRIBE_ID]
for gid,b in sorted(selected,key=lambda v:priority.get(v[0],100+v[0])):
 name=scalar(b,'editname');base=name[len(PREFIX):] if name.lower().startswith(PREFIX) else name;folder=ROOT/TRIBE_NAME/'Buildings'/(''.join(x.capitalize() for x in base.split())+f'_gfx{gid}')
 libs=commands(b,'gfxboblibs')[0];pals=commands(b,'gfxpalette')[0];logic=dict(commands(b,'logictype'));bm={'nativeName':name,'tribe':TRIBE_NAME,'nativeTribeId':TRIBE_ID,'gfxHouseId':gid,'logicDefinitions':{str(v):LO.get(v) for v in logic.values()},'definition':b,'source':source(PATHS['house_graphics']),'levels':[],'overall':'PARTIAL','nativeReferences':{'Game.exe':['0x0048E651','0x0048089E','0x00495B57','0x00496594','0x0049B3EE','0x0049B930','0x0049DA62','0x0049E618'],'Editor.exe':['0x0044543D','0x0043921A','0x0043921F']},'folder':rel(folder)}
 for level,bob in commands(b,'gfxbobid'):
  out=folder/f'level_{level}';lm={'nativeName':name,'tribe':TRIBE_NAME,'logicHouseType':logic[level],'gfxHouseId':gid,'level':level,'bodyBob':bob,'bobLibrary':libs[0],'shadowLibrary':libs[1] if len(libs)>1 else None,'shadowBob':bob if len(libs)>1 else None,'paletteAlternatives':pals,'paletteSelection':'House unique ID modulo palette count, then lighting/shading table (0x00495B57); all native palettes exported','levelsAreZeroBased':True,'confidencePerField':{'body':'AUTOMATED_CONFIRMED','sourceMapping':'AUTOMATED_CONFIRMED','pivot':'AUTOMATED_CONFIRMED','runtimePivot':'PARTIAL','shadow':'PARTIAL','construction':'PARTIAL','doors':'PARTIAL','animation':'PARTIAL','effects':'PARTIAL','overall':'PARTIAL'},'baseFrames':[],'constructionLayers':[t for t in commands(b,'gfxbobconstructionlayer') if t[0]==level],'doors':[t for t in commands(b,'gfxdoorbobid') if t[0]==level],'animations':[t for t in commands(b,'gfxoverlay') if t[0]==level],'effects':{},'errors':[],'nativeReferences':bm['nativeReferences']}
  currentErrors=lm['errors']
  if False:lm['manualValidation']={'status':'MANUAL_CONFIRMED_1TO1','scope':'finished/base visual; user confirmation 2026-10-01','noRepeatComparison':True,'pivotScope':'Decoded pivot automated; controlled world-anchor comparison not explicitly described'}
  for d in ['main','shadow','construction','states','animation','effects']:(out/d).mkdir(parents=True,exist_ok=True)
  try:
   for pi,pal in enumerate(pals):
    target=out/'main'/(f'frame_{bob:06}.png' if pi==0 else f'palette_{slug(pal)}/frame_{bob:06}.png');fr=frame(libs[0],bob,pal,target);lm['baseFrames'].append(fr)
   f=lm['baseFrames'][0]['descriptor'];lm.update(width=f.get('width'),height=f.get('height'),pivot=[-f['x'],-f['y']] if 'x' in f else None)
   if len(libs)>1:lm['shadow']=frame(libs[1],bob,None,out/'shadow'/f'coverage_{bob:06}.png','shadow_coverage')
   write(out/'shadow/metadata.json',{'asset':lm.get('shadow'),'rule':'Native destination darkening, not alpha blend','Game.exe':'0x0049B930','drawOrder':'before finished body; extension keeps existing shadow; new construction uses auxiliary threshold maps','confidence':'AUTOMATED_CONFIRMED (source coverage); PARTIAL (live composition)'})
   parts=[]
   for t in lm['constructionLayers']:
    for pi,pal in enumerate(pals):
     parts.append(frame(libs[0],t[2],pal,out/'construction'/'layers'/slug(pal)/f'body_{t[2]:06}.png'))
    parts.append(frame(libs[0],t[2],None,out/'construction'/'layers'/f'reveal_{t[2]:06}.png','reveal_threshold'))
    if t[3]>=0:parts.append(frame(libs[0],t[3],None,out/'construction'/'layers'/f'auxiliary_threshold_{t[3]:06}.png','auxiliary_threshold'))
   lm['constructionParts']=parts
   if any(t[1]==0 for t in lm['constructionLayers']):
    try:lm['constructionSnapshots']=construction(libs[0],pals[0],lm['constructionLayers'],out/'construction')
    except Exception as e:lm['errors'].append('Construction snapshot: '+str(e))
   write(out/'construction/metadata.json',{'tuples':lm['constructionLayers'],'parts':parts,'extensionTuples':[t for t in lm['constructionLayers'] if t[1]],'rule':'Auxiliary index <= reveal threshold darkens destination in pass 1; main kind4 second-byte <= threshold copies palette pixel in pass 2; source order preserved; after end use full body','confidence':'PARTIAL','paletteAlternatives':pals})
   doorframes=[]
   for t in lm['doors']:
    if t[2]>=0:
     for pal in pals:doorframes.append({'tuple':t,'asset':frame(libs[0],t[2],pal,out/'states/door'/slug(pal)/f'frame_{t[2]:06}.png')})
   lm['doorFrames']=doorframes;write(out/'states/metadata.json',{'idleBase':lm['baseFrames'],'doorFrames':doorframes,'doorPredicate':'House door scan 0x00495B57, 0x0042C214/0x0042C392, Human 0x00441AAD checks +0xB50/+0xB51. Not equivalent to any Farmer assignment or production state.','working':'See native overlay state lanes; no fabricated unique working sprite','confidence':'PARTIAL'})
   anim=[]
   for t in lm['animations']:
    seq=[]
    for pos,abob in enumerate(t[6:]):
     seq.append({'sequenceIndex':pos,'bobId':abob,'ticksPerFrame':t[5],'asset':frame(libs[0],abob,pals[0],out/'animation'/f'frame_{abob:06}.png')})
    anim.append({'nativeTuple':t,'level':t[0],'stateLane':t[1],'requiredLaneState':t[2],'offset':t[3:5],'ticksPerFrame':t[5],'sequence':seq,'rule':'index=(native tick / ticksPerFrame) modulo count; 0x004341C0 state lane gating; rate in seconds UNKNOWN','evidence':'0x00495B57'})
   write(out/'animation/animation.json',{'body':'static base plus declared overlays','sequences':anim,'confidence':'AUTOMATED_CONFIRMED (native frame order); PARTIAL (runtime triggers/timing)'})
   fx={k:[t for t in commands(b,k) if t[0]==level] for k in ['gfxfirepoint','gfxsmokepoint','gfxholyfirepoint','gfxoverlaylandscape']};fx['sharedEffects']={}
   names=[]
   if fx['gfxfirepoint']:names+=['fx fire house 0','fx fire house 1','fx fire house 2']
   if fx['gfxsmokepoint']:names+=['fx smoke']
   if fx['gfxholyfirepoint']:names+=['fx fire incense']
   names+=[t[-1] for t in fx['gfxoverlaylandscape']]
   for fxn in names:
    try:fx['sharedEffects'][fxn]=landscape(fxn)
    except Exception as e:lm['errors'].append('Effect '+fxn+': '+str(e))
   fx['confidence']='PARTIAL';fx['note']='Native spawn points/definitions/ordered frames retained. Damage, destruction, holy-fire activation and exact timing are runtime dependent.';lm['effects']=fx;write(out/'effects/metadata.json',fx)
  except Exception as e:lm['errors'].append(str(e));errors.append({'gfxId':gid,'level':level,'error':str(e)})
  if lm['errors']:errors.append({'gfxId':gid,'level':level,'errors':lm['errors']})
  if not lm['baseFrames'] or not lm['baseFrames'][0].get('path'):lm['confidencePerField']['body']='UNKNOWN'
  lm['sourceAssetExport']='COMPLETE' if not lm['errors'] else 'PARTIAL';write(out/'metadata.json',lm);bm['levels'].append(rel(out/'metadata.json'));levels.append((out,lm))
 bm['sourceAssetExport']='COMPLETE' if all(not m['errors'] for o,m in levels if m['gfxHouseId']==gid) else 'PARTIAL';write(folder/'metadata.json',bm);buildings.append(bm);print(f'Gfx {gid}: {name} exported',flush=True)
# Explicit top-level Farm confidence survives broader-layer status.
farm=None
if False:
 farm=ROOT/'Vikings/Buildings/Farm/metadata.json';fm=json.loads(farm.read_text());fm['confidencePerField']={'body':'MANUAL_CONFIRMED_1TO1','palette':'MANUAL_CONFIRMED_1TO1','pivot':'AUTOMATED_CONFIRMED','worldAnchor':'PARTIAL','shadow':'PARTIAL','construction':'PARTIAL','animation':'PARTIAL','effects':'PARTIAL','overall':'PARTIAL'};fm['manualValidation']='User confirms finished/base Farm visual = 1:1; no repeated validation';write(farm,fm)
# Preserve all old unresolved rows outside newly refreshed Viking level mappings.
def merge_csv(name,new,keyfields,columns):
 p=ROOT/'Catalogs'/name;old=[]
 if p.exists():
  with p.open(encoding='utf-8-sig',newline='') as h:old=list(csv.DictReader(h))
 keys={tuple(str(r.get(k,'')) for k in keyfields) for r in new};old=[r for r in old if tuple(str(r.get(k,'')) for k in keyfields) not in keys]
 allrows=old+new;fields=list(dict.fromkeys(columns+[k for r in allrows for k in r]))
 with p.open('w',encoding='utf-8-sig',newline='') as h:w=csv.DictWriter(h,fields);w.writeheader();w.writerows(allrows)
hrows=[];xrows=[]
for out,m in levels:
 fr=(m.get('baseFrames') or [{}])[0];d=fr.get('descriptor',{});prov=fr.get('source',{});conf='AUTOMATED_CONFIRMED' if fr.get('path') else 'UNKNOWN'
 hrows.append(dict(NAME=m['nativeName'],LOGIC_ID=m['logicHouseType'],GFX_ID=m['gfxHouseId'],TRIBE=TRIBE_ID,LEVEL=m['level'],BOB_ID=m['bodyBob'],MAIN_LIBRARY=m['bobLibrary'],SHADOW_LIBRARY=m['shadowLibrary'],SHADOW_BOB_ID=m['shadowBob'],WIDTH=d.get('width'),HEIGHT=d.get('height'),PIVOT_X=(-d['x'] if 'x' in d else None),PIVOT_Y=(-d['y'] if 'y' in d else None),PIXEL_KIND=d.get('kind'),CONSTRUCTION=json.dumps(m['constructionLayers']),CONFIDENCE=conf,OVERALL='PARTIAL',OUTPUT_PATH=fr.get('path'),METADATA=rel(out/'metadata.json'),SOURCE_EXPORT=m['sourceAssetExport'],NOTES='Base source confidence only; live presentation separate.'))
 x=dict(CATEGORY='Buildings',SUBCATEGORY=m['nativeName'],TRIBE=TRIBE_NAME,LOGIC_ID=m['logicHouseType'],GFX_ID=m['gfxHouseId'],LEVEL=m['level'],STATE='finished base frame',ARCHIVE=prov.get('archive'),ENTRY_ID=prov.get('entryId'),ENTRY_NAME=prov.get('entryName'),FORMAT='BMD',WIDTH=d.get('width'),HEIGHT=d.get('height'),FRAMES=1,PIVOT_X=(-d['x'] if 'x' in d else None),PIVOT_Y=(-d['y'] if 'y' in d else None),SHADOW_ENTRY=m['shadowLibrary'],GAME_EXE_ADDRESS='0x00495B57;0x0048E651',EDITOR_EXE_ADDRESS='0x0044543D',CPP_SYMBOL='decodeBobLibraryBmd;bobWalkFrameRuns;bobWalkKind4FrameRuns',OUTPUT_PATH=fr.get('path'),CONFIDENCE=conf,NOTES=f"BOB {m['bodyBob']}; metadata {rel(out/'metadata.json')}; overall PARTIAL")
 xrows.append(x)
merge_csv('houses.csv',hrows,['GFX_ID','LEVEL'],list(hrows[0]));merge_csv('asset_cross_reference.csv',xrows,['GFX_ID','LEVEL','STATE'],'CATEGORY SUBCATEGORY TRIBE LOGIC_ID GFX_ID JOB_ID GOOD_ID VEHICLE_ID ANIMAL_ID LANDSCAPE_ID LEVEL STATE ARCHIVE ENTRY_ID ENTRY_NAME FORMAT WIDTH HEIGHT FRAMES PIVOT_X PIVOT_Y SHADOW_ENTRY GAME_EXE_ADDRESS EDITOR_EXE_ADDRESS CPP_SYMBOL OUTPUT_PATH CONFIDENCE NOTES'.split())
write(ROOT/f'Catalogs/{TAG}_building_frames.json',list(rendered.values()));write(ROOT/f'Metadata/Evidence/{TAG}_buildings_errors.json',errors)
after={str(p):digest(p) for p in inputs};assert before==after;write(ROOT/f'Metadata/Evidence/{TAG}_buildings_integrity.json',{'filesChecked':len(inputs),'unchanged':before==after,'hashes':after})
write(ROOT/f'Metadata/Evidence/{TAG}_buildings_summary.json',{'buildings':len(buildings),'levels':len(levels),'sourceComplete':sum(b['sourceAssetExport']=='COMPLETE' for b in buildings),'sourcePartial':sum(b['sourceAssetExport']!='COMPLETE' for b in buildings),'uniqueFrameExports':len(rendered),'errors':errors,'buildingsDetail':buildings,'sourceFilesUnchanged':len(inputs)})
print('DONE',len(buildings),len(levels),len(rendered),len(errors),flush=True)
