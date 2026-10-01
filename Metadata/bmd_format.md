# BMD format — checkpoint evidence

Observed object header: u32 type 0x3F4 (1012), u32 version 0, i32 firstBobId, u32 frame count, five further u32 fields. Total 36 bytes. The production decoder retains those five fields without assigning all semantics. Older Python validation correlates two with compressed byte and scanline counts. Empty library handling exists in C++; the older Python parser expects arrays.

For a nonempty library, three raw-array objects follow, each u32 type 0x3E9 (1001), u32 version 0, u32 byte length, payload: descriptors, run bytes, packed scanline offsets.

Descriptors are 24 bytes: i32 pixelKind, i32 x offset, i32 y offset, i32 width, i32 height, u32 first scanline index. Production member names right/bottom represent width/height in the run walker. Cropped-image pivot is (-x offset,-y offset). Native BOB ID = firstBobId + descriptor ordinal; it is distinct from LIB entry ordinal.

Scanline 0xFFFFFFFF is empty; low 22 bits index compressed run bytes, high 10 bits give initial x. Run command 0 ends row; high-bit commands skip low-seven pixels; other commands emit low-seven pixels. Kind 1 consumes one palette index per pixel. Kind 4 consumes index plus a second byte: caller-dependent opacity/reveal metadata, NOT universally alpha. Finished house body drawing skips the second byte; construction uses it as a progress threshold. Kind 2 consumes no pixel payload and darkens the existing destination through native arithmetic (Game 0x0049B930); fixed-alpha black is only a preview approximation.

Palettes are external: GfxPalette names resolve through palettes.cif -> GfxFile PCX. PCX trailing 0x0C + 768 RGB bytes supplies the sample palette. Runtime lighting, preshading and player/context selection are separate from BMD geometry. No palette was modified.

Frame count is a library descriptor count, not a building animation duration. House GfxOverlay, GfxDoorBobId and construction/effect records select frames and timing outside the BMD. Full animation semantics remain partial.

Existing implementations: include/cultures/graphics/bob_compositor.hpp, pixel_surface_blit.hpp, production_world_compositor.hpp; RE tools cultures_bmd.py, cultures_lib.py, cultures_cif.py. C++ production parser/draw reused for the Farm PNG; older Python parser reused to inspect frame descriptors, and its PNG writer reused for serialization only.

Unsupported/unknown: complete meanings of retained header words; native 16-bit shadow lookup parity; every non-house pixel caller's second-byte semantics; all possible versions or malformed variants. This is a documented working subset, not a claim of complete format RE.
