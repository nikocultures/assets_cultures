# Viking Buildings checkpoint

OUTPUT ROOT: `E:\assets cultures`  
VIKING BUILDINGS FOUND: **37 native tribe-1 GfxHouse definitions, 70 levels**.  
FULLY EXPORTED: **32 definitions at the directly referenced source-asset level**.  
PARTIAL: **5 definitions with missing native frame references**.  
UNKNOWN: **0 wholly unidentified definitions; 2 level-0 main frame references unresolved**.  
FARM: **MANUAL_CONFIRMED_1TO1**, finished/base house01 sample, accepted from the user on 2026-10-01. No repeated original-game comparison was performed.

“Fully exported” means the available directly referenced body/palette, shadow coverage, construction, door and animation/effect source assets have been decoded and linked. It does **not** mean all gameplay-triggered composition and animation timing are proven 1:1. Overall presentation remains PARTIAL for all definitions until those runtime details are independently established. The Farm base's manual confidence is preserved separately and is not downgraded.

The 37 entries include 28 native `viking ...` definitions (including four vehicle construction-site definitions) and nine wonder definitions with native tribe ID 1. None was silently discarded or assigned a fabricated Viking name.

## Priority results

| Requested building | Native mapping / result |
|---|---|
| Farm | Gfx 4, logic 12, level 0, BOB 60. Original base sample MANUAL_CONFIRMED_1TO1. Construction, shadow and state data exported separately. Alternative palette house02 is AUTOMATED_CONFIRMED source export, not covered by the original sample confirmation. |
| Mill | Gfx 5, logic 13, BOB 70; base, door 90, inactive frame 76 and active sequence 85,84,83,82,81,80,79,78,77,76,88,87,86 exported. Source AUTOMATED_CONFIRMED; runtime presentation PARTIAL. |
| Bakery | Gfx 6, levels 0–1, logic 14/15, BOB 101/105. Source exports complete. |
| Home | Gfx 3, levels 0–4, logic 2–6, BOB 1/11/21/31/41. All five native levels exported. |
| HQ variants | Gfx 21 BOB 34 and Gfx 27 BOB 44, both logic 1, retained separately under Headquarters/gfx_21 and gfx_27. Scenario-specific selection unresolved. |
| Well | Gfx 0, logic 10, BOB 131; source exports complete. |
| Mason | Native mason hut, Gfx 17, two levels, BOB 10/20; source exports complete. |
| Potter | Native pottery, Gfx 12, three levels, BOB 0/10/20; source exports complete. |
| Joiner | Native joinery, Gfx 8, four levels, BOB 180/190/200/210; source exports complete. |
| Tailor | Native sewery, Gfx 11, two levels, BOB 0/30; source exports complete. English native localization identifies logic 18/19 as Tailor's Workshop. |
| Warehouse | Native stock, Gfx 2, three levels, BOB 53/111/121. |
| Breeder-related | Native animal farm, Gfx 10, logic 17 (Cattle Farm), BOB 30. |
| Hunter-related | No separately named hunter House definition in this tribe-1 registry. No house invented. |
| Military | Armory Gfx 9 (2 levels), barracks Gfx 19, tower Gfx 20 (2 levels), catapult construction site Gfx 25; exported with native distinctions. |
| Religious | Temple Gfx 22 and other native druid/herb definitions exported without substituting display names. |
| Docks | No separately named dock House definition found. Native ship-small construction site Gfx 26 / logic 44 / BOB 4 is exported. This is not a complete moving ship export. |

## All native definitions

| Gfx ID | Native name | Levels | Source coverage |
|---:|---|---|---|
| 0 | viking well | 0 | COMPLETE |
| 1 | viking hive | 0 | COMPLETE |
| 2 | viking stock | 0, 1, 2 | COMPLETE |
| 3 | viking home | 0, 1, 2, 3, 4 | COMPLETE |
| 4 | viking farm | 0 | COMPLETE |
| 5 | viking mill | 0 | COMPLETE |
| 6 | viking bakery | 0, 1 | COMPLETE |
| 7 | viking brewery | 0 | COMPLETE |
| 8 | viking joinery | 0, 1, 2, 3 | COMPLETE |
| 9 | viking armory | 0, 1 | COMPLETE |
| 10 | viking animal farm | 0 | COMPLETE |
| 11 | viking sewery | 0, 1 | COMPLETE |
| 12 | viking pottery | 0, 1, 2 | COMPLETE |
| 13 | viking herb hut | 0 | COMPLETE |
| 14 | viking druid hut | 0, 1 | COMPLETE |
| 15 | viking smithy | 0, 1 | COMPLETE |
| 16 | viking coin mint | 0 | COMPLETE |
| 17 | viking mason hut | 0, 1 | COMPLETE |
| 18 | viking school | 0 | COMPLETE |
| 19 | viking barracks | 0 | COMPLETE |
| 20 | viking tower | 0, 1 | COMPLETE |
| 21 | viking headquarters | 0 | COMPLETE |
| 22 | viking temple | 0 | COMPLETE |
| 23 | viking handcart | 0 | COMPLETE |
| 24 | viking oxcart | 0 | COMPLETE |
| 25 | viking catapult | 0 | COMPLETE |
| 26 | viking ship small | 0 | COMPLETE |
| 27 | viking headquarters house | 0 | COMPLETE |
| 28 | wonder pyramid | 0, 1 | PARTIAL |
| 29 | wonder leuchtturm | 0, 1, 2 | PARTIAL |
| 30 | wonder semiramis | 0, 1, 2 | PARTIAL |
| 31 | wonder semiramis front | 0, 1, 2 | PARTIAL |
| 32 | wonder artemis | 0, 1, 2 | PARTIAL |
| 33 | wonder koloss | 0, 1, 2, 3 | COMPLETE |
| 34 | wonder mausoleum | 0, 1 | COMPLETE |
| 35 | wonder zeus | 0, 1, 2 | COMPLETE |
| 36 | wonder 8th | 0 | COMPLETE |

## Exported content and limitations

- Finished body pixels for every available level, including all declared native palette alternatives. The native render chain selects palette by House unique ID modulo palette count, then applies lighting; the browser's default preview uses the first declared palette. This is not an invented recolor.
- Shadow descriptors, original BMD references and coverage data. The coverage PNG is a data mask, not a black alpha sprite. Native 32-bit destination darkening is documented; matching live 16-bit rendering and terrain/light state is not asserted.
- Construction tuples, body frames, kind-4 reveal planes, auxiliary index-threshold planes, and 0/10/25/50/75/100% body snapshots wherever valid source references allow. Auxiliary operations are stored separately as destination-darkening count maps. Checkerboard composites are explicitly PREVIEW. Native extension tuples are retained and their referenced frames exported; full upgraded-state compositions remain PARTIAL.
- Door frames and raw door predicates; ordinary occupied-door selection is not equated with Farmer assignment or a generic working-state timer.
- Declared ordered animation frames, offsets, state lanes and ticks-per-frame in animation.json. Native tick-to-seconds rate and all gameplay activation transitions remain PARTIAL. No new frames were created.
- Fire/smoke/holy-fire points plus linked shared effect definitions and source frames. Shared source images are stored once under Shared and referenced from building metadata. Landscape overlays for wonders are included where resolvable. Live effect activation, dynamic shading and precise blending remain PARTIAL.
- Frame dimensions and pivots are decoded source facts (AUTOMATED_CONFIRMED). World-cell/camera anchoring is a separate PARTIAL claim. The user's Farm statement confirms the base visual; it did not explicitly describe a controlled world-anchor measurement.

The Farm auxiliary BOB 65 is now identified more precisely from the unpacked native render code: its source bytes are progress thresholds for destination darkening through 0x0049E618, not normal palette colors. The auxiliary pass precedes all body reveal layers. At a layer's exact end, threshold 255 is used; above its end, threshold 256 / full draw is used. Reveal is governed by per-pixel source values rather than an invented top-to-bottom wipe.

## Missing native references

Five definitions remain source-PARTIAL: wonder pyramid (28), wonder leuchtturm (29), wonder semiramis (30), wonder semiramis front (31), wonder artemis (32).

The Semiramis level-0 definitions both request BOB 6 from ls_wonders.bmd, whose available IDs are 0–5. Several wonder shadow IDs are absent from their declared shadow library. Pyramid also declares door BOB 66 outside its body library's range. Each unresolved reference is retained with archive ordinal/name and requested BOB under Unknown/ByArchive/data0001 and in metadata/catalogs. Valid levels and independent sub-assets were still exported. Empty native descriptors are recorded as empty rather than turned into synthetic sprites.

## Evidence and validation

- **96 base palette renders matched the existing C++ production drawing function byte-for-byte**, including alpha and transparent RGB storage.
- **684 generated source PNGs** opened successfully, had the expected dimensions, and matched their recorded raw-pixel SHA-256 values. This count excludes construction compositions and navigation thumbnails.
- Four focused existing tests passed: bob_compositor, gfxhouse_registry_layout, gfxhouse_door_offset_initialization, mounted_library_file. No gameplay/AI/renderer source was changed; no full-game-suite result is claimed for this export pass.
- Native logic/graphic mapping is taken from the installed archive's CIF definitions, with original commands preserved. `archive_index.csv` retains all 2,691 entries.
- Editor loader/name/tribe lookup evidence remains 0x0044543D, 0x0043921A and 0x0043921F from the hash-matched Editor corpus. Editor and Game runtime presentation are not assumed identical.
- **Evidence qualification:** the render-address decompilation (0x00495B57, 0x0049B3EE, 0x0049B930, 0x0049DA62) belongs to the older unpacked analysis image, SHA-256 057C…6854. A new read-only comparison found different on-disk bytes at those addresses in current original/Game.exe (C522…B85F). Their current runtime correspondence is not proven by this session. Earlier reports that treated matching-address metadata as sufficient should be read with this correction. Source extraction and the user's independent Farm manual validation are unaffected.

## Browser and catalogs

INDEX.HTML: **updated YES**. Offline navigation: Vikings → Buildings → native definition → level → source frames, construction, doors, animation and shared effects. Each level has a frame gallery and metadata links. The overview sheet is a navigation thumbnail sheet only; source PNGs retain their original dimensions.

CATALOGS: **updated YES**. houses.csv has all 70 levels; asset_cross_reference.csv includes base and referenced sub-assets; viking_building_frames.json tracks canonical source exports. archive_index.csv is preserved. Humans/vehicles/goods catalogs are not falsely populated with unperformed category work.

Per-level metadata preserves source archive/entry, native logic type, GfxHouse, level, libraries, BOB IDs, palette sources, bounds, pivots, original tuples, animation order, effect points and separate confidence fields. A root Farm metadata file explicitly preserves MANUAL_CONFIRMED_1TO1 for the original base sample while overall remains PARTIAL.

ORIGINAL FILES MODIFIED: **NONE**. Before/after SHA-256 verification covers all files under DataX and original; see Metadata/Evidence/viking_buildings_integrity.json. All deliverables are under E:\assets cultures. Source binaries and asset archives were read-only.

## Next checkpoint

Stopping at checkpoint A as requested: all Viking House definitions have been indexed and exported as far as current native evidence permits. No expansion to another tribe occurred.

NEXT CATEGORY: **Viking Humans**. The earlier instruction to continue automatically to Humans is superseded for this turn by the explicit final checkpoint to stop after all Viking Buildings. No additional single-building approval was requested.
