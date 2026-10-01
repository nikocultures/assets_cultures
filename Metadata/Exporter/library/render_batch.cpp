// Batch reference renderer for pixel validation of exported frames.
// Uses only the production decoder/drawer: decodeBobLibraryBmd + drawBobClippedBorrowed32.
// usage: render_batch <lib.bmd> <palette.rgb (768 bytes)> <ids.txt> <out.bin>
// out.bin: for each id: int32 id, int32 width, int32 height, int32 status, then width*height uint32 BGRA.
#include "cultures/graphics/bob_compositor.hpp"
#include <array>
#include <fstream>
#include <iterator>
#include <vector>
using namespace cultures::graphics;
int main(int argc, char** argv) {
    if (argc != 5) return 2;
    std::ifstream in(argv[1], std::ios::binary);
    std::vector<uint8_t> b((std::istreambuf_iterator<char>(in)), {});
    BobDecodedLibrary lib;
    if (decodeBobLibraryBmd(b, lib) != BobDecodeResult::decoded) return 3;
    std::ifstream p(argv[2], std::ios::binary);
    std::vector<uint8_t> pal((std::istreambuf_iterator<char>(p)), {});
    if (pal.size() != 768) return 6;
    std::array<uint32_t, 256> colors;
    // Same packing as the validated export_frame.cpp: little-endian memory order R,G,B,A.
    for (int i = 0; i < 256; i++) colors[i] = 0xff000000u | (pal[i * 3 + 2] << 16) | (pal[i * 3 + 1] << 8) | pal[i * 3];
    std::ifstream ids(argv[3]);
    std::ofstream out(argv[4], std::ios::binary);
    int id;
    while (ids >> id) {
        int n = id - lib.firstBobId;
        int32_t head[4] = {id, 0, 0, 1};
        if (n < 0 || n >= (int)lib.frames.size()) { out.write((char*)head, 16); continue; }
        auto f = lib.frames[n];
        if (f.right <= 0 || f.bottom <= 0 || f.right > 8192 || f.bottom > 8192) { head[3] = 2; out.write((char*)head, 16); continue; }
        std::vector<uint32_t> pixels(size_t(f.right) * f.bottom, 0);
        size_t written = 0;
        auto r = drawBobClippedBorrowed32(lib, id, pixels, f.right, f.right, f.bottom, -f.left, -f.top, colors, &written);
        head[1] = f.right; head[2] = f.bottom; head[3] = r == BobDrawResult::drawn ? 0 : 3;
        out.write((char*)head, 16);
        out.write((char*)pixels.data(), pixels.size() * 4);
    }
    return out ? 0 : 8;
}
