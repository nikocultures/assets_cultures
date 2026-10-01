import sys,json,csv,hashlib,subprocess,math,collections,html,shutil
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,r'E:\cultures\re-data\evidence\decompilation\tools')
from catalog_game_data import read_index,archive_blob,commands,scalar
R=Path(r'E:\assets cultures'); W=Path('work'); H=R/'Vikings/Humans'; M=R/'Metadata/Humans'; X=R/'Metadata/Exporter/viking_humans'
for p in [H,M,R/'Unknown/Humans',H/'Equipment']:p.mkdir(parents=True,exist_ok=True)
A=Path(r'E:\cultures\vanilla-data\DataX\Libs\data0001.lib'); IX=read_index(A)
def load(n):return json.loads((W/('human_'+n+'.json')).read_text(encoding='utf-8'))
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def csvout(p,rows,fields=None):
 if fields is None:fields=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in row.items()} for row in rows)
def key(p):return p.replace('/','\\').lower()
def stem(p):return p.replace('\\','/').split('/')[-1].rsplit('.',1)[0]
G=load('human');J={scalar(b,'type'):b for b in load('jobs') if 1<=scalar(b,'type')<=47}; AN=load('animations');AT=load('atomic'); T=next(b for b in load('tribes') if scalar(b,'type')==1)
allow={x[0] for x in commands(T,'allowjob') if x[0] in J}
vg=[dict(b,sourceSectionOrdinal=i) for i,b in enumerate(G) if scalar(b,'logictribe')==1]
for b in vg:save(M/'Graphics'/f"section_{b['sourceSectionOrdinal']}.json",b)
for n in ['human','jobs','atomic','animations','random','goods','tribes']:
 shutil.copy2(W/('human_'+n+'.json'),M/('native_'+n+'.json'))
P=json.loads((W/'palettes.json').read_text(encoding='utf-8'));pdef=next(b for b in P if str(scalar(b,'editname','')).lower()=='test_human_00'); pp=scalar(pdef,'gfxfile');pcx=archive_blob(A,IX,pp);assert pcx[-769]==12
pal=np.frombuffer(pcx[-768:],np.uint8).reshape(256,3);(M/'test_human_00.rgb').write_bytes(pcx[-768:]);(M/'test_human_00.pcx').write_bytes(pcx);save(M/'palette.json',{'name':'test_human_00','source':pp,'definition':pdef,'previewStatus':'SOURCE_BASE_PALETTE; runtime random patches NOT applied','randomPatchDefinitions':'native_random.json'})
# Preserve declared palette sources for future exact runtime selections.
pr=[]
for b in P:
 name=scalar(b,'editname','');file=scalar(b,'gfxfile','')
 if not file:continue
 if 'human' not in str(file).lower() and 'creature' not in str(file).lower():continue
 try:
  raw=archive_blob(A,IX,file);out=M/'PaletteSources'/Path(file.replace('\\','/')).name;out.parent.mkdir(exist_ok=True);out.write_bytes(raw);pr.append({'name':name,'source':file,'path':out.relative_to(R).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'definition':b})
 except (KeyError,FileNotFoundError):pass
save(M/'palette_sources.json',pr)
libs=sorted({key(s):s for b in vg for c in b['commands'] if c['name'] in ['gfxbobmanagerbody','gfxbobmanagerhead'] for s in c['arguments'][1:]}.values(),key=str.lower)
libdata={};librows=[]
for lib in libs:
 ident=stem(lib);d=H/'Shared/SourceLibraries'/ident;d.mkdir(parents=True,exist_ok=True);cache=W/'human_planes'/ident;cache.mkdir(parents=True,exist_ok=True)
 raw=archive_blob(A,IX,lib);(d/(ident+'.bmd')).write_bytes(raw)
 subprocess.run([str(X/'export_planes.exe'),str(d/(ident+'.bmd')),str(cache)],check=True,capture_output=True)
 frames=json.loads((cache/'frames.json').read_text());planes=(cache/'frames.planes').read_bytes(); nonempty=[]
 for f in frames:
  size=f['width']*f['height']*3;chunk=planes[f['offset']:f['offset']+size];f['sha256Planes']=hashlib.sha256(chunk).hexdigest();f['pivot']=[-f['x'],-f['y']];f['nonempty']=bool(size and any(chunk[1::3]));f['previewStatus']='DESTINATION_SHADOW_MASK' if f['kind']==2 else 'SOURCE_BASE_PALETTE';f.pop('offset');
  if f['nonempty']:nonempty.append((f,chunk))
 for start in range(0,len(nonempty),64):
  group=nonempty[start:start+64];cw=max(f['width'] for f,_ in group);ch=max(f['height'] for f,_ in group);sheet=Image.new('RGBA',(cw*8,ch*math.ceil(len(group)/8)));indices=Image.new('L',sheet.size);coverage=Image.new('L',sheet.size);secondary=Image.new('L',sheet.size)
  page=start//64;fn=f'page_{page:04d}.png'
  for j,(f,chunk) in enumerate(group):
   a=np.frombuffer(chunk,np.uint8).reshape(f['height'],f['width'],3);rgba=np.zeros((f['height'],f['width'],4),np.uint8);rgba[:,:,:3]=pal[a[:,:,0]] if f['kind']!=2 else 0;rgba[:,:,3]=a[:,:,1];rgba[a[:,:,1]==0]=0
   x=(j%8)*cw;y=(j//8)*ch;sheet.paste(Image.fromarray(rgba),(x,y));indices.paste(Image.fromarray(a[:,:,0]),(x,y));coverage.paste(Image.fromarray(a[:,:,1]),(x,y));secondary.paste(Image.fromarray(a[:,:,2]),(x,y));f['atlas']=fn;f['rect']=[x,y,f['width'],f['height']]
  sheet.save(d/fn);indices.save(d/f'page_{page:04d}_indices.png');coverage.save(d/f'page_{page:04d}_coverage.png');secondary.save(d/f'page_{page:04d}_secondary.png')
 entry=next((i,e) for i,e in enumerate(IX.entries) if key(e.path)==key(lib))
 meta={'library':lib,'sourceArchive':str(A),'archiveEntryOrdinal':entry[0],'archiveOffset':entry[1].offset,'archiveSize':entry[1].size,'sourceSha256':hashlib.sha256(raw).hexdigest(),'palette':pp,'frameCount':len(frames),'nonemptyCount':len(nonempty),'frames':frames,'semantics':'Source palette preview; kind 2 is coverage-only destination-dependent shadow, black preview not final composition; original indices, coverage and kind4 secondary byte preserved in companion PNGs. No scaling.'}
 save(d/'metadata.json',meta);(d/'data.js').write_text('window.LIBS=window.LIBS||{};window.LIBS['+json.dumps(ident)+']='+json.dumps(meta,separators=(',',':'))+';',encoding='utf-8');libdata[key(lib)]={'id':ident,'dir':d,'meta':meta,'frames':{f['bobId']:f for f in frames}}
 librows.append({k:v for k,v in meta.items() if k!='frames'});print(ident,len(frames),len(nonempty),flush=True)
save(M/'libraries.json',librows)
# Sequence names are globally looked up in source order, independent of selected body library.
seqs=[];seqmap={}
for i,b in enumerate(AN):
 if b['section']!='bobseq':continue
 image=shadow=''
 for c in b['commands']:
  a=c['arguments']
  if c['name']=='imagelib':image=a[0]
  elif c['name']=='shadowlib':shadow=a[0]
  elif c['name']=='seq':
   s={'name':a[0],'firstBob':a[1],'count':a[2],'declaredImageLibrary':image,'declaredShadowLibrary':shadow,'sectionOrdinal':i};seqs.append(s);seqmap.setdefault(a[0].lower(),s)
save(M/'bob_sequences.json',seqs)
atomicmap={}
for i,b in enumerate(AT):atomicmap.setdefault(str(scalar(b,'name','')).lower(),dict(b,sourceSectionOrdinal=i))
def chain(j):
 out=[]
 while j in J and j not in out:out.append(j);j=scalar(J[j],'baseatomics',0)
 return out
def gfx(j,section):return next((b for p in chain(j) for b in vg if b['section']==section and scalar(b,'logicjob')==p),None)
def dirs(b,head=False):
 out=[[] for _ in range(8)]
 for c in b['commands']:
  n=c['name'];a=c['arguments'];target=['gfxanimframelistheaddir','gfxwalkframelisthead'] if head else ['gfxanimframelistdir','gfxwalkframelist']
  if n in target:out[a[0]].extend(a[1:])
  if n==('gfxanimframelisthead' if head else 'gfxanimframelist'):out=[list(a) for _ in range(8)]
 return out
records=[]
for i,b in enumerate(AN):
 if scalar(b,'logictribe')!=1 or scalar(b,'logicjob',0) not in J:continue
 atomic=b['section']=='gfxanimatomic';body=dirs(b);head=dirs(b,True);sn=scalar(b,'gfxbobseqbody','');hn=scalar(b,'gfxbobseqhead',sn);s=seqmap.get(sn.lower());hs=seqmap.get(hn.lower());steps=[c for c in b['commands'] if c['name'].startswith('gfxinhouse')]
 valid=bool(sn or any(body) or (scalar(b,'gfxanimmode',0)==2 and steps))
 r={'id':i,'job':scalar(b,'logicjob'),'kind':'atomic' if atomic else 'walk','selector':scalar(b,'logicatomicaction' if atomic else 'logicgoodtype',0),'subId':scalar(b,'logicinhouseatomicsubid',0),'mode':scalar(b,'gfxanimmode',0),'bodySequence':s,'headSequence':hs,'bodySequenceName':sn,'headSequenceName':hn,'directions':[],'inHouseSteps':steps,'runtimeCandidate':valid,'raw':b}
 for d in range(8):
  bf=[(s['firstBob'] if s else 0)+v for v in body[d]] if s or not sn else [];hf=[hs['firstBob']+v for v in (head[d] or body[d])] if hs else list(bf)
  r['directions'].append({'direction':d,'bodyOffsets':body[d],'headOffsets':head[d],'bodyBobs':bf,'headBobs':hf,'shadowBobs':list(bf)})
 records.append(r);save(M/'Animations'/f'section_{i}.json',r)
save(M/'animations.json',records)
setatomic={}
for a in commands(T,'setatomic'):setatomic.setdefault((a[0],a[1]),a[2])
used=set();xref=[];humans=[];missing=[];jobmeta=[]
for j,b in J.items():
 parents=chain(j);base=gfx(j,'jobbasegraphics');change=gfx(j,'jobchangegraphics');name=scalar(b,'name'); bindings=[]
 for phase,g in [('initial',base),('jobChange',change)]:
  if g:bindings.append({'phase':phase,'sourceSectionOrdinal':g['sourceSectionOrdinal'],'bodies':commands(g,'gfxbobmanagerbody'),'heads':commands(g,'gfxbobmanagerhead'),'paletteRemaps':commands(g,'gfxpaletterandom')})
 effective={}
 for p in parents:
  for r in records:
   if r['job']==p and r['runtimeCandidate']:effective.setdefault((r['kind'],r['selector'],r['subId']),r)
 rows=[];errors=[]
 for k,r in effective.items():
  aname=next((setatomic[(p,r['selector'])] for p in parents if (p,r['selector']) in setatomic),'') if r['kind']=='atomic' else ''
  atom=atomicmap.get(aname.lower());duration=scalar(atom,'length','UNKNOWN') if atom else 'NOT_APPLICABLE' if r['kind']=='walk' else 'UNKNOWN'
  row={'tribe':1,'jobId':j,'nativeName':name,'nativeAllowJob':j in allow,'animationSourceJob':r['job'],'graphicsAnimationSectionOrdinal':r['id'],'kind':r['kind'],'atomicActionSelector':r['selector'] if r['kind']=='atomic' else '', 'carriedGoodSelector':r['selector'] if r['kind']=='walk' else '', 'actionOpcode':'UNKNOWN','behaviorMode':'UNKNOWN','atomicName':aname or 'UNKNOWN' if r['kind']=='atomic' else 'walk','atomicDefinitionSectionOrdinal':atom.get('sourceSectionOrdinal','') if atom else '', 'subId':r['subId'],'graphicsMode':r['mode'],'nativeLength':duration,'events':commands(atom,'event') if atom else [],'interruptable':scalar(atom,'interruptable','UNSPECIFIED') if atom else '', 'bodySequence':r['bodySequenceName'],'headSequence':r['headSequenceName'],'directions':r['directions'],'bindings':bindings,'timingRule':'frameTick % count' if r['kind']=='walk' else 'progress % count' if r['mode']==1 else 'timeline percentages; recursive subanimation; see steps' if r['mode']==2 else 'min(count-1, floor(count*progress/duration)); duration0=>0','loop':'caller-controlled; UNKNOWN final repeat policy','inHouseSteps':r['inHouseSteps'],'confidence':'NATIVE_DATA_AND_CPP_PARITY; RUNTIME_PALETTE_PARTIAL'}
  for bind in bindings:
   for v in bind['bodies']:
    for lib,channel in [(v[1],'bodyBobs')]+([(v[2],'shadowBobs')] if len(v)>2 else []):
     for dr in r['directions']:
      for bob in dr[channel]:
       used.add((key(lib),bob))
       if bob not in libdata[key(lib)]['frames']:errors.append({'animation':r['id'],'phase':bind['phase'],'library':lib,'bobId':bob,'direction':dr['direction'],'layer':channel})
   for v in bind['heads']:
    for dr in r['directions']:
     for bob in dr['headBobs']:
      used.add((key(v[1]),bob))
      if bob not in libdata[key(v[1])]['frames'] and libdata[key(v[1])]['meta']['frameCount']!=0:errors.append({'animation':r['id'],'phase':bind['phase'],'library':v[1],'bobId':bob,'direction':dr['direction'],'layer':'headBobs'})
  xref.append(row);rows.append(row)
 # Preserve setatomic selectors even where no render candidate is present.
 amap={}
 for p in parents:
  for (owner,selector),n in setatomic.items():
   if owner==p:amap.setdefault(selector,n)
 unresolved=[{'selector':sel,'atomicName':n,'definition':atomicmap.get(n.lower()),'status':'NO_TOP_LEVEL_GRAPHICS_CANDIDATE'} for sel,n in amap.items() if ('atomic',sel,0) not in effective]
 sex='female' if j in [1,3,5,47] else 'male' if j in [2,4] or 6 in parents else 'UNKNOWN';age='baby' if j<=2 else 'child' if j<=4 else 'adult'
 summary={'tribe':1,'jobId':j,'nativeName':name,'nativeAllowJob':j in allow,'sex':sex,'ageClass':age,'parentChain':parents,'baseGraphicsSection':base['sourceSectionOrdinal'] if base else None,'changeGraphicsSection':change['sourceSectionOrdinal'] if change else None,'bindings':bindings,'animationCount':len(rows),'missingReferenceCount':len(errors),'sourceMappingStatus':'PARTIAL_MISSING_REFERENCES' if errors else 'SOURCE_MAPPED','appearanceStatus':'PARTIAL_RUNTIME_PALETTE; NO_ORIGINAL_VISUAL_CONFIRMATION','GameExeAddresses':['0x004803D5','0x00480576','0x0049445E','0x00494AE6'],'EditorExeReference':'UNKNOWN; shared data evidence only','cppSymbol':'MobileSpriteRegistry; MobileSpriteRuntimeOwner; HumanRandomPaletteRegistry','definition':b,'unresolvedAtomics':unresolved}
 meta=dict(summary,animations=rows,missingReferences=errors);save(M/'Jobs'/f'job_{j:02d}.json',meta);(H/f'job_{j:02d}.js').write_text('window.JOB='+json.dumps(meta,separators=(',',':'))+';',encoding='utf-8');jobmeta.append(meta);humans.append(summary);missing.extend(dict(x,jobId=j) for x in errors)
save(M/'missing_references.json',missing);csvout(R/'Catalogs/humans.csv',humans);csvout(R/'Catalogs/human_job_atomic_animation.csv',xref)
unknown=[]
for lib,l in libdata.items():
 for f in l['meta']['frames']:
  if f['nonempty'] and (lib,f['bobId']) not in used:unknown.append(dict(f,library=l['meta']['library'],sourceArchive=str(A),archiveEntryOrdinal=l['meta']['archiveEntryOrdinal'],sourceSha256=l['meta']['sourceSha256'],previewDirectory=l['dir'].relative_to(R).as_posix(),confidence='UNKNOWN_UNUSED_BY_RESOLVED_VIKING_TABLES'))
save(R/'Unknown/Humans/frames.json',unknown);csvout(R/'Unknown/Humans/frames.csv',unknown)
goods=[{'goodId':scalar(b,'logicgood'),'humanRandomPalettes':commands(b,'graphicshumanrandompalette'),'nativeGraphicsDefinition':b,'classification':'HUMAN_PALETTE_PATCH; separate Good sprite not established','source':'data\\engine2d\\inis\\goods\\goodgraphics.cif'} for b in load('goods')]
csvout(R/'Catalogs/goods.csv',goods);save(H/'Equipment/carried_goods.json',goods);save(H/'Equipment/native_equipment.json',{'allowEquip':commands(T,'allowequip'),'jobDefinitions':list(J.values()),'status':'Palette patch links and raw equipment requirements preserved. Separate attachment classification UNKNOWN unless native animation proves baked silhouette. No fabricated tool sprites.'})
save(M/'summary.json',{'allowedHumanJobs':len(allow),'allHumanJobsExamined':len(J),'graphicsDefinitions':len(vg),'baseGraphicsDefinitions':sum(b['section']=='jobbasegraphics' for b in vg),'changeGraphicsDefinitions':sum(b['section']=='jobchangegraphics' for b in vg),'sourceLibraries':len(libs),'frameDescriptors':sum(x['frameCount'] for x in librows),'nonemptyFrames':sum(x['nonemptyCount'] for x in librows),'animationDefinitions':len(records),'effectiveJobAnimationRows':len(xref),'unknownNonemptyFrames':len(unknown),'missingReferenceOccurrences':len(missing),'allowedJobIds':sorted(allow)})
save(M/'browser_jobs.json',humans)
shutil.copy2(Path(__file__),X/'export_humans.py')
print('DONE',json.loads((M/'summary.json').read_text()),flush=True)
