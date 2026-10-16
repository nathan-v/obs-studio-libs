# Producer for qt6 on os=linux,arch=x86_64,libc=glibc,os_version=2.28.
# manylinux_2_28 (AlmaLinux 8, glibc 2.28, gcc-toolset-14). The glibc floor of
# OBS's dependencies is 2.28, a documented exception to zackees/forge's 2.17
# rule: Qt 6 does not support older (obs-rust/obs-studio#926).
#   bosn run --task qt6-linux     (bosn.toml), then `obs-studio-libs pack` and `add`
FROM quay.io/pypa/manylinux_2_28_x86_64@sha256:4131ddd7acb9c6c966af02fe7e71edc51e078c2d41f475966697676430bfa2ae

# What qtbase, qtsvg and qtwayland build against (system libraries the host has
# at runtime; Qt's own copies of harfbuzz, png, jpeg and pcre2 are used).
RUN dnf install -y --setopt=install_weak_deps=False \
        libX11-devel libXext-devel libXfixes-devel libXrender-devel libXi-devel libxshmfence-devel \
        libxcb-devel xcb-util-devel xcb-util-wm-devel xcb-util-image-devel xcb-util-keysyms-devel \
        xcb-util-renderutil-devel xcb-util-cursor-devel libxkbcommon-devel libxkbcommon-x11-devel \
        wayland-devel wayland-protocols-devel mesa-libEGL-devel mesa-libgbm-devel libglvnd-devel libdrm-devel \
        fontconfig-devel freetype-devel glib2-devel dbus-devel openssl-devel zlib-devel \
 && dnf clean all
# AlmaLinux 8's ninja 1.8 cannot build Qt 6.11 (multiple-output rules need >= 1.10).
RUN /opt/python/cp312-cp312/bin/pip install --no-cache-dir ninja==1.11.1.4 \
 && ln -sf /opt/python/cp312-cp312/bin/ninja /usr/local/bin/ninja
COPY recipes/qt6/linux/build.sh /opt/recipe/build.sh
RUN QT_PREFIX=/opt/qt6 /opt/recipe/build.sh
