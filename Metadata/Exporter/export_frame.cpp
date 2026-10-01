#include "cultures/graphics/bob_compositor.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
using namespace cultures::graphics;
int main(int argc,char**argv){
 if(argc!=5)return 2;
 std::ifstream in(argv[1],std::ios::binary); std::vector<uint8_t>b((std::istreambuf_iterator<char>(in)),{});
 BobDecodedLibrary lib; if(decodeBobLibraryBmd(b,lib)!=BobDecodeResult::decoded)return 3;
 int id=std::stoi(argv[2]);int n=id-lib.firstBobId;if(n<0||n>=lib.frames.size())return 4;
 auto f=lib.frames[n]; if(f.right<=0||f.bottom<=0||f.right>4096||f.bottom>4096)return 5;
 std::ifstream p(argv[3],std::ios::binary);std::vector<uint8_t>pal((std::istreambuf_iterator<char>(p)),{});if(pal.size()!=768)return 6;
 std::array<uint32_t,256> colors; for(int i=0;i<256;i++)colors[i]=0xff000000u|(pal[i*3+2]<<16)|(pal[i*3+1]<<8)|pal[i*3];
 std::vector<uint32_t>pixels(f.right*f.bottom,0);size_t written=0;
 if(drawBobClippedBorrowed32(lib,id,pixels,f.right,f.right,f.bottom,-f.left,-f.top,colors,&written)!=BobDrawResult::drawn)return 7;
 std::ofstream out(argv[4],std::ios::binary);out.write((char*)pixels.data(),pixels.size()*4);
 std::cout<<"{\"width\":"<<f.right<<",\"height\":"<<f.bottom<<",\"left\":"<<f.left<<",\"top\":"<<f.top<<",\"pixelKind\":"<<f.pixelKind<<",\"firstBobId\":"<<lib.firstBobId<<",\"libraryFrames\":"<<lib.frames.size()<<",\"writtenPixels\":"<<written<<"}";return out?0:8;
}
