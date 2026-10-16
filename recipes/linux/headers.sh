#!/usr/bin/env bash
# headers 2026.10.16 for os=linux,arch=x86_64,libc=glibc,os_version=2.28 (obs-studio-libs).
# Header-only libraries: nlohmann/json 3.11.3, asio 1.30.2, SIMDe 0.8.2.
PREFIX=/opt/obs-deps/headers
VERSION=2026.10.16
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

json() {
    # nlohmann/json v3.11.3
    git_src json https://github.com/nlohmann/json.git 9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03
    cmake -S . -B build -G Ninja -DCMAKE_INSTALL_PREFIX="$PREFIX" -DJSON_BuildTests=OFF -DJSON_Install=ON
    cmake --install build
}
asio() {
    # asio-1-30-2
    git_src asio https://github.com/chriskohlhoff/asio.git 12e0ce9e0500bf0f247dbd1ae894272656456079
    cp -r asio/include/asio asio/include/asio.hpp "$PREFIX/include/"
}
simde() {
    # v0.8.2
    git_src simde https://github.com/simd-everywhere/simde.git 71fd833d9666141edcd1d3c109a80e228303d8d7
    mkdir -p "$PREFIX/include" && cp -r simde "$PREFIX/include/"
    mkdir -p "$PREFIX/lib/pkgconfig"
    printf 'prefix=%s\nincludedir=${prefix}/include\nName: simde\nDescription: SIMD Everywhere\nVersion: 0.8.2\nCflags: -I${includedir}\n' \
        "$PREFIX" >"$PREFIX/lib/pkgconfig/simde.pc"
}

run_steps json asio simde
