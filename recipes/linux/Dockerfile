# Producer for every Linux tool on os=linux,arch=x86_64,libc=glibc,os_version=2.28.
# manylinux_2_28 (AlmaLinux 8, glibc 2.28, gcc-toolset-14). OBS's dependencies
# float at glibc 2.28, a documented exception to zackees/forge's 2.17 rule
# (Qt 6 and current PipeWire/GLib do not support older; obs-rust/obs-studio#926).
# Each tool is one layer, built into its own /opt/obs-deps/<tool> (the path the
# consumer installs it to); `bosn run --task linux` then packs every one.
FROM quay.io/pypa/manylinux_2_28_x86_64@sha256:4131ddd7acb9c6c966af02fe7e71edc51e078c2d41f475966697676430bfa2ae

RUN dnf install -y --setopt=install_weak_deps=False \
        nasm which file \
        libX11-devel libXext-devel libXfixes-devel libXrender-devel libXi-devel libxshmfence-devel \
        libxcb-devel xcb-util-devel xcb-util-wm-devel xcb-util-image-devel xcb-util-keysyms-devel \
        xcb-util-renderutil-devel xcb-util-cursor-devel libxkbcommon-devel libxkbcommon-x11-devel \
        wayland-devel wayland-protocols-devel mesa-libEGL-devel mesa-libgbm-devel libglvnd-devel libdrm-devel \
        libva-devel vulkan-headers vulkan-loader-devel \
        fontconfig-devel freetype-devel glib2-devel dbus-devel openssl-devel zlib-devel \
        pcre2-devel libffi-devel libmount-devel \
 && dnf clean all
# AlmaLinux 8's ninja 1.8 cannot build Qt 6.11 (multiple-output rules need >= 1.10),
# and its meson 0.58 is older than PipeWire 1.2 needs (>= 0.61).
RUN /opt/python/cp312-cp312/bin/pip install --no-cache-dir ninja==1.11.1.4 meson==1.5.2 \
 && ln -sf /opt/python/cp312-cp312/bin/ninja /usr/local/bin/ninja \
 && ln -sf /opt/python/cp312-cp312/bin/meson /usr/local/bin/meson

COPY recipes/linux/common.sh /opt/recipes/common.sh
# Cheapest and least likely to change first; Qt last.
COPY recipes/linux/headers.sh /opt/recipes/headers.sh
RUN /opt/recipes/headers.sh
COPY recipes/linux/qrcodegen.sh /opt/recipes/qrcodegen.sh
RUN /opt/recipes/qrcodegen.sh
COPY recipes/linux/fdk-aac.sh /opt/recipes/fdk-aac.sh
RUN /opt/recipes/fdk-aac.sh
COPY recipes/linux/glib.sh /opt/recipes/glib.sh
RUN /opt/recipes/glib.sh
COPY recipes/linux/pipewire.sh /opt/recipes/pipewire.sh
RUN /opt/recipes/pipewire.sh
COPY recipes/linux/ffmpeg.sh /opt/recipes/ffmpeg.sh
RUN /opt/recipes/ffmpeg.sh
COPY recipes/linux/qt6.sh /opt/recipes/qt6.sh
RUN /opt/recipes/qt6.sh
