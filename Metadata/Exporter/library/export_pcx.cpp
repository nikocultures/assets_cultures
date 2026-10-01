// Production PCX decode (cultures::graphics::decodeIndexedPcx) for asset export/validation.
// usage: export_pcx <in.pcx> <out.bin>
// out.bin: int32 status, int32 width, int32 height, width*height indices, 1024 bytes paletteBgra (uint32 LE).
#include "cultures/graphics/indexed_pcx.hpp"
#include <fstream>
#include <iterator>
#include <vector>
using namespace cultures::graphics;
int main(int argc, char** argv) {
    if (argc != 3) return 2;
    std::ifstream in(argv[1], std::ios::binary);
    std::vector<uint8_t> b((std::istreambuf_iterator<char>(in)), {});
    IndexedPcxImage img;
    auto r = decodeIndexedPcx(b, img);
    std::ofstream out(argv[2], std::ios::binary);
    int32_t head[3] = {static_cast<int32_t>(r), img.width, img.height};
    out.write((char*)head, 12);
    if (r == IndexedPcxDecodeResult::decoded) {
        out.write((char*)img.indices.data(), img.indices.size());
        out.write((char*)img.paletteBgra.data(), 1024);
    }
    return out ? 0 : 8;
}
