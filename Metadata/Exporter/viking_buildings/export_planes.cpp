#include "cultures/graphics/bob_compositor.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
using namespace cultures::graphics;
int main(int argc,char**argv){
 if(argc!=3)return 2;std::ifstream in(argv[1],std::ios::binary);std::vector<uint8_t>b((std::istreambuf_iterator<char>(in)),{});BobDecodedLibrary lib;
 if(decodeBobLibraryBmd(b,lib)!=BobDecodeResult::decoded)return 3;
 std::filesystem::path out(argv[2]);std::filesystem::create_directories(out);std::ofstream meta(out/"frames.json");meta<<"[";
 for(size_t n=0;n<lib.frames.size();n++){
 auto f=lib.frames[n];if(f.right<0||f.bottom<0||f.right>8192||f.bottom>8192)return 4;
 std::vector<uint8_t> data(size_t(f.right)*f.bottom*3,0);PixelSurface s{};s.width=f.right;s.height=f.bottom;s.pitch=f.right;bool ok=true;
 auto put=[&](int x,int y,uint8_t i,uint8_t m){auto p=(size_t(y)*f.right+x)*3;data[p]=i;data[p+1]=255;data[p+2]=m;};
 if(f.pixelKind==4)ok=detail::bobWalkKind4FrameRuns(lib,f,s,-f.left,-f.top,[&](int x,int y,uint8_t i,uint8_t m){put(x,y,i,m);});
 else if(f.pixelKind==1||f.pixelKind==2)ok=detail::bobWalkFrameRuns(lib,f,s,-f.left,-f.top,f.pixelKind==1?1:0,[&](int x,int y,uint8_t i){put(x,y,f.pixelKind==1?i:0,0);});
 else if(f.pixelKind!=0) return 5;
 if(!ok)return 6;
 const auto id=lib.firstBobId+int(n);std::ofstream raw(out/(std::to_string(id)+".planes"),std::ios::binary);raw.write((char*)data.data(),data.size());if(!raw)return 7;
 if(n)meta<<",";meta<<"{\"bobId\":"<<id<<",\"frameIndex\":"<<n<<",\"kind\":"<<f.pixelKind<<",\"x\":"<<f.left<<",\"y\":"<<f.top<<",\"width\":"<<f.right<<",\"height\":"<<f.bottom<<",\"firstScanline\":"<<f.scanlineIndex<<"}";
 }meta<<"]";std::cout<<lib.frames.size();return meta?0:8;
}
