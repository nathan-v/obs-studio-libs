#!/usr/bin/env bash
# Pack the Linux tools built by recipes/linux/Dockerfile into dist/ (bosn task
# `linux`): obs-studio-libs pack measures each one's glibc floor (2.28) first.
#   recipes/linux/pack.sh [tool...]   (default: every /opt/obs-deps/<tool>)
set -euo pipefail
cd "$(dirname "$0")/../.."

UV_VERSION=0.12.13
UV_SHA256=745765a3b6e360ad76743599ae5c42e9278c7edf8bbff9fc76d05bf2623a04dd
if ! command -v uv >/dev/null; then
    curl -fsSLo /tmp/uv.tgz "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-x86_64-unknown-linux-gnu.tar.gz"
    echo "${UV_SHA256}  /tmp/uv.tgz" | sha256sum -c -
    tar -xzf /tmp/uv.tgz -C /usr/local/bin --strip-components=1
fi

tools=("$@")
[ "${#tools[@]}" -gt 0 ] || mapfile -t tools < <(ls /opt/obs-deps)
for tool in "${tools[@]}"; do
    version="$(sed -n 's/^VERSION=\([0-9][^ ]*\).*/\1/p' "recipes/linux/$tool.sh" | head -1)"
    [ -n "$version" ] || version="$(sed -n 's/^QT_VERSION=\(.*\)/\1/p' "recipes/linux/$tool.sh")"
    [ -n "$version" ] || { echo "no VERSION in recipes/linux/$tool.sh" >&2; exit 1; }
    uv run obs-studio-libs pack "/opt/obs-deps/$tool" --tool "$tool" --version "$version" \
        --platform os=linux,arch=x86_64,libc=glibc,os_version=2.28 --variant optimization=release --out dist
done
