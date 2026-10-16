#!/usr/bin/env bash
# pipewire 1.2.7 for os=linux,arch=x86_64,libc=glibc,os_version=2.28 (obs-studio-libs).
# The PipeWire client library, its modules, SPA plugins and client.conf (AlmaLinux 8 has 0.3.6).
PREFIX=/opt/obs-deps/pipewire
VERSION=1.2.7
# shellcheck source=common.sh
. "$(dirname "$0")/common.sh"

pipewire() {
    # 1.2.7
    git_src pipewire https://gitlab.freedesktop.org/pipewire/pipewire.git cc7439187f61dd73b81ca69f5dbccbb52ce970b2
    meson setup build --prefix="$PREFIX" --libdir=lib --buildtype=release \
        -Dsession-managers=[] -Dexamples=disabled -Dtests=disabled -Dman=disabled -Ddocs=disabled \
        -Dsystemd=disabled -Dsystemd-user-service=disabled -Dpipewire-alsa=disabled -Dpipewire-jack=disabled \
        -Dpipewire-v4l2=disabled -Djack=disabled -Djack-devel=false -Dbluez5=disabled -Dlibcamera=disabled \
        -Dgstreamer=disabled -Dgstreamer-device-provider=disabled -Dvulkan=disabled -Dlibpulse=disabled \
        -Droc=disabled -Davahi=disabled -Decho-cancel-webrtc=disabled -Dlibusb=disabled -Dlibmysofa=disabled \
        -Dsdl2=disabled -Dsndfile=disabled -Dlibffado=disabled -Dflatpak=disabled -Dselinux=disabled \
        -Dlv2=disabled -Draop=disabled -Dx11=disabled -Dx11-xfixes=disabled -Dlibcanberra=disabled \
        -Dreadline=disabled -Dopus=disabled -Dcompress-offload=disabled -Dsnap=disabled \
        -Dudev=disabled -Dalsa=disabled -Dpw-cat=disabled -Dvideotestsrc=disabled -Daudiotestsrc=disabled \
        -Ddbus=enabled
    ninja -C build && ninja -C build install
}

run_steps pipewire
