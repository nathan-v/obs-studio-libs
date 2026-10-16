#!/usr/bin/env bash
# qrcodegen 1.8.0 for os=linux,arch=x86_64,libc=glibc,os_version=2.28 (obs-studio-libs).
# nayuki's QR-Code-generator (C++), built like Debian's libqrcodegencpp (obs-websocket).
PREFIX=/opt/obs-deps/qrcodegen
VERSION=1.8.0
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

qrcodegen() {
    # nayuki QR-Code-generator v1.8.0, built the way Debian's libqrcodegencpp is
    git_src qrcodegen https://github.com/nayuki/QR-Code-generator.git 720f62bddb7226106071d4728c292cb1df519ceb
    cd cpp
    g++ -O2 -fPIC -shared -Wl,-soname,libqrcodegencpp.so.1 -o libqrcodegencpp.so.1 qrcodegen.cpp
    install -Dm755 libqrcodegencpp.so.1 "$PREFIX/lib/libqrcodegencpp.so.1"
    ln -sf libqrcodegencpp.so.1 "$PREFIX/lib/libqrcodegencpp.so"
    install -Dm644 qrcodegen.hpp "$PREFIX/include/qrcodegen/qrcodegen.hpp"
    mkdir -p "$PREFIX/lib/pkgconfig"
    cat >"$PREFIX/lib/pkgconfig/qrcodegencpp.pc" <<EOF
prefix=$PREFIX
libdir=\${prefix}/lib
includedir=\${prefix}/include/qrcodegen
Name: qrcodegencpp
Description: QR Code generator library (C++)
Version: 1.8.0
Libs: -L\${libdir} -lqrcodegencpp
Cflags: -I\${includedir}
EOF
}

run_steps qrcodegen
