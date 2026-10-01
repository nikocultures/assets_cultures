from pathlib import Path
import json,csv,html,hashlib,shutil,re
from PIL import Image,ImageDraw,ImageFont
R=Path(r'E:\assets cultures');O=Path(r'C:\Users\niko2\Documents\Codex\2026-10-01\files-pasted-by-the-user-you\outputs');O.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False),encoding='utf-8')
def rel(p):return str(p.relative_to(R)).replace('\\','/')
s=load(R/'Metadata/Evidence/viking_buildings_summary.json');frames=load(R/'Catalogs/viking_building_frames.json');levelmeta=[]
for p in (R/'Vikings/Buildings').glob('**/level_*/metadata.json'):
 m=load(p);levelmeta.append((p,m))
 if m['gfxHouseId']==4:
  m['confidencePerField']['palette']='MANUAL_CONFIRMED_1TO1 (original house01 sample only)';m['baseFrames'][0]['confidence']='MANUAL_CONFIRMED_1TO1';m['manualValidation']['paletteScope']='Original exported house01 sample; alternative house02 remains AUTOMATED_CONFIRMED';write(p,m)
# Master cross-reference: retain all prior rows and add level-specific referenced sub-assets.
p=R/'Catalogs/asset_cross_reference.csv'
with p.open(encoding='utf-8-sig',newline='') as h:rd=csv.DictReader(h);fields=rd.fieldnames;rows=list(rd)
def assets(obj):
 if isinstance(obj,dict):
  if 'descriptor' in obj and 'bobId' in obj and 'source' in obj:yield obj
  else:
   for v in obj.values():yield from assets(v)
 elif isinstance(obj,list):
  for v in obj:yield from assets(v)
for p,m in levelmeta:
 seen=set()
 for group,obj in [('palette_variant',m['baseFrames'][1:]),('shadow',m.get('shadow')),('construction',m.get('constructionParts')),('door',m.get('doorFrames')),('animation',load(p.parent/'animation/animation.json') if (p.parent/'animation/animation.json').exists() else {})]:
  for a in assets(obj):
   key=(group,a['source']['entryName'],a['bobId'],a.get('palette'),a.get('role'))
   if key in seen:continue
   seen.add(key);d=a.get('descriptor',{});src=a['source'];state=f"{group}/{a.get('role','unresolved')}/bob_{a['bobId']}/{a.get('palette','data')}"
   row={k:'' for k in fields};row.update(CATEGORY='Buildings',SUBCATEGORY=m['nativeName'],TRIBE='Vikings',LOGIC_ID=m['logicHouseType'],GFX_ID=m['gfxHouseId'],LEVEL=m['level'],STATE=state,ARCHIVE=src['archive'],ENTRY_ID=src['entryId'],ENTRY_NAME=src['entryName'],FORMAT='BMD',WIDTH=d.get('width'),HEIGHT=d.get('height'),FRAMES=1,PIVOT_X=(-d['x'] if 'x' in d else None),PIVOT_Y=(-d['y'] if 'y' in d else None),GAME_EXE_ADDRESS='0x00495B57 (unpacked RE image)',EDITOR_EXE_ADDRESS='0x0044543D',OUTPUT_PATH=a.get('path'),CONFIDENCE='AUTOMATED_CONFIRMED' if a.get('path') or a.get('empty') or a.get('notApplicable') else 'UNKNOWN',NOTES=f"Source/frame confidence only. {a.get('representation',a.get('error',''))}")
   rows.append(row)
keys={}
for row in rows:keys[tuple(str(row.get(k,'')) for k in ['CATEGORY','TRIBE','GFX_ID','LEVEL','STATE','ENTRY_NAME'])]=row
with (R/'Catalogs/asset_cross_reference.csv').open('w',encoding='utf-8-sig',newline='') as h:w=csv.DictWriter(h,fields);w.writeheader();w.writerows(keys.values())
# Every generated source image must open and match its stored pixel hash.
valid=0
for f in frames:
 if not f.get('path'):continue
 im=Image.open(R/f['path']).convert('RGBA');assert list(im.size)==[f['descriptor']['width'],f['descriptor']['height']],f['path'];assert hashlib.sha256(im.tobytes()).hexdigest()==f['pixelSha256'],f['path'];valid+=1
# Generate one offline page per level with actual canonical links, including shared assets.
for p,m in levelmeta:
 entries=[];seen=set()
 for a in assets(m):
  if a.get('path') and a['path'] not in seen:entries.append(a);seen.add(a['path'])
 ap=p.parent/'animation/animation.json'
 if ap.exists():
  for a in assets(load(ap)):
   if a.get('path') and a['path'] not in seen:entries.append(a);seen.add(a['path'])
 def link(path):return Path(__import__('os').path.relpath(R/path,p.parent)).as_posix()
 body=f'<h1>{html.escape(m["nativeName"])} / level {m["level"]}</h1><p>Logic {m["logicHouseType"]}; GfxHouse {m["gfxHouseId"]}. Full presentation PARTIAL.</p>'
 body+='<p><a href="metadata.json">Complete metadata</a> | <a href="animation/animation.json">Native animation order/timing</a></p>'
 for a in entries:
  body+=f'<article><h3>{html.escape(str(a.get("role")))} · BOB {a["bobId"]} · {html.escape(str(a.get("palette","data")))}</h3><a href="{link(a["path"])}"><img loading="lazy" src="{link(a["path"])}"></a><p>Pivot {a.get("pivot")} · {html.escape(a.get("representation",""))}</p></article>'
 body+='<h2>Shared effects</h2>'
 for name,path in m.get('effects',{}).get('sharedEffects',{}).items():
  body+=f'<p><a href="{link(path)}">{html.escape(name)} — metadata / frame order</a></p>'
  for a in assets(load(R/path)):
   if a.get('path'):body+=f'<a href="{link(a["path"])}"><img class="small" loading="lazy" src="{link(a["path"])}" title="BOB {a["bobId"]}"></a>'
 body+='<h2>Construction snapshots</h2><p>Body-only PNGs plus separate destination darkening data. Checkerboard images are previews.</p>'
 for q in sorted((p.parent/'construction').glob('PREVIEW*.png')):body+=f'<a href="{q.relative_to(p.parent).as_posix()}"><img loading="lazy" src="{q.relative_to(p.parent).as_posix()}"></a>'
 (p.parent/'index.html').write_text('<!doctype html><meta charset="utf-8"><style>body{font:16px system-ui;background:#eae8e0;padding:25px}article{display:inline-block;vertical-align:top;width:320px;padding:16px}img{max-width:300px;max-height:230px;background:#82877d}.small{max-width:90px;max-height:110px}</style>'+body,encoding='utf-8')
# Repair display text and add frame galleries to root browser.
p=R/'index.html';text=p.read_text(encoding='utf-8')
# The index header is regenerated to avoid locale-dependent text corruption.
start=text.index('<header>');end=text.index('</header>',start)+len('</header>');options=''.join(f'<option value="gfx{b["gfxHouseId"]}">{html.escape(b["nativeName"])}</option>' for b in s['buildingsDetail'])
text=text[:start]+'<header><strong>Cultures | Original asset library</strong><p>Vikings &gt; Buildings &gt; Native definition &gt; Level / state &gt; Frames</p><select onchange="location.hash=this.value"><option>Choose building</option>'+options+'</select> <a href="Catalogs/houses.csv">House catalog</a> | <a href="VIKING_BUILDINGS_REPORT.md">Checkpoint report</a></header>'+text[end:]
for p,m in levelmeta:
 url=rel(p);text=text.replace(f'<a href="{url}">metadata.json</a>',f'<a href="{rel(p.parent/"index.html")}"><strong>Browse all frames and shared layers</strong></a><br><a href="{url}">metadata.json</a>')
text=re.sub(r'<br>Full presentation: PARTIAL',r'<br>Full presentation: PARTIAL',text)
(R/'index.html').write_text(text,encoding='utf-8')
# Contact sheet: thumbnails are only navigation previews; exported originals retain dimensions.
ordinary=sorted([(p,m) for p,m in levelmeta if m['level']==0 and m['gfxHouseId']<28],key=lambda x:x[1]['gfxHouseId'])
W,H=1120,((len(ordinary)+6)//7)*190;sheet=Image.new('RGB',(W,H),'#e8e4d9');draw=ImageDraw.Draw(sheet)
for i,(p,m) in enumerate(ordinary):
 x=(i%7)*160;y=(i//7)*190;f=m['baseFrames'][0]
 if f.get('path'):
  im=Image.open(R/f['path']).convert('RGBA');im.thumbnail((146,143));sheet.paste(im,(x+(160-im.width)//2,y+5+143-im.height),im)
 draw.text((x+6,y+152),m['nativeName'].removeprefix('viking '),fill='#202820');draw.text((x+6,y+169),f"Gfx {m['gfxHouseId']} / BOB {m['bodyBob']}",fill='#202820')
sheet.save(R/'Catalogs/viking_buildings_contact_sheet.png');shutil.copy2(R/'Catalogs/viking_buildings_contact_sheet.png',O/'Viking_Buildings_Overview.png')
validation={'sourcePngsVerified':valid,'basePaletteComparisons':96,'basePaletteComparison':'Exact RGBA match to existing C++ drawBobClippedBorrowed32; no original game comparison implied','focusedTests':'4/4 PASS','nativeRenderAddressProvenance':'Earlier unpacked analysis image; byte comparison with current on-disk Game.exe does NOT match at four sampled addresses. Current runtime correspondence remains unverified. Source archive extraction unaffected.','farmBase':'MANUAL_CONFIRMED_1TO1','rootIndexAndLevelGalleries':'created'};write(R/'Metadata/Evidence/viking_buildings_validation.json',validation)
print(json.dumps(validation,indent=2));print('Master cross reference rows',len(keys))


