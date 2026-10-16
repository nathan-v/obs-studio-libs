#!/usr/bin/env bash
# glib 2.80.5 for os=linux,arch=x86_64,libc=glibc,os_version=2.28 (obs-studio-libs).
# GLib/GIO (AlmaLinux 8 has 2.56; OBS's linux-pipewire needs >= 2.76). The
# release tarball carries the subprojects (gvdb) that a git checkout lacks.
# AlmaLinux 8's PCRE2 10.32 is too old (GLib needs 10.34's PCRE2_MATCH_INVALID_UTF),
# so GLib's own pinned PCRE2 wrap is built and linked in statically.
PREFIX=/opt/obs-deps/glib
VERSION=2.80.5
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

glib() {
    tar_src glib https://download.gnome.org/sources/glib/2.80/glib-2.80.5.tar.xz \
        9f23a9de803c695bbfde7e37d6626b18b9a83869689dd79019bf3ae66c3e6771
    meson setup build --prefix="$PREFIX" --libdir=lib --buildtype=release \
        -Dintrospection=disabled -Dtests=false -Dman-pages=disabled -Ddocumentation=false \
        -Dsysprof=disabled -Dselinux=disabled -Dxattr=true -Dlibmount=enabled -Dnls=disabled \
        --force-fallback-for=pcre2 -Dpcre2:default_library=static
    ninja -C build && ninja -C build install
}
run_steps glib
