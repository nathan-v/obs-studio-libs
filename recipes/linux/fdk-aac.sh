#!/usr/bin/env bash
# fdk-aac 2.0.3 for os=linux,arch=x86_64,libc=glibc,os_version=2.28 (obs-studio-libs).
# The AAC encoder obs-libfdk uses.
PREFIX=/opt/obs-deps/fdk-aac
VERSION=2.0.3
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

fdkaac() {
    # v2.0.3
    git_src fdkaac https://github.com/mstorsjo/fdk-aac.git 716f4394641d53f0d79c9ddac3fa93b03a49f278
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
        -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=ON -DBUILD_PROGRAMS=OFF
    cmake --build build && cmake --install build
}

run_steps fdkaac
