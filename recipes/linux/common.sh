#!/usr/bin/env bash
# Shared by the Linux recipes (recipes/linux/<tool>.sh). Each recipe sets
# PREFIX=/opt/obs-deps/<tool> -- the same directory the consumer installs the
# artifact into, so pkg-config and CMake files need no relocation -- sources
# this file, and runs its steps.
set -euo pipefail

# CMake 4 refuses projects (svt-av1's bundled cpuinfo, ...) that still declare
# cmake_minimum_required < 3.5; let them configure with 3.5 policies.
export CMAKE_POLICY_VERSION_MINIMUM=3.5
JOBS="$(nproc)"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig:$PREFIX/lib64/pkgconfig:$PREFIX/share/pkgconfig"
export CMAKE_PREFIX_PATH="$PREFIX"

# git_src <dir> <url> <commit>: a shallow checkout of exactly that commit (and its submodules).
git_src() {
    git init -q "$work/$1"
    git -C "$work/$1" fetch -q --depth 1 "$2" "$3"
    git -C "$work/$1" checkout -q FETCH_HEAD
    git -C "$work/$1" submodule update -q --init --recursive --depth 1
    cd "$work/$1"
}
# tar_src <dir> <url> <sha256>
tar_src() {
    curl -fsSLo "$work/$1.tar" "$2"
    echo "$3  $work/$1.tar" | sha256sum -c -
    mkdir -p "$work/$1"
    tar -xf "$work/$1.tar" -C "$work/$1" --strip-components=1
    cd "$work/$1"
}
autotools() { ./configure --prefix="$PREFIX" --enable-shared --disable-static "$@" && make -j"$JOBS" && make install; }
cmake_build() {
    cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
        -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=ON "$@"
    cmake --build build && cmake --install build
}
# run_steps <step>...: each in a subshell from $work, announced.
run_steps() {
    for step in "$@"; do
        echo "==> $step"
        (cd "$work" && "$step")
    done
}
