# obs-studio-libs

Prebuilt build dependencies for [OBS-Studio-Rust](https://github.com/obs-rust/obs-studio),
compiled once per version and per platform, then downloaded by every build
instead of being compiled again (obs-rust/obs-studio#525, #926).

## Layout

| Path | What |
|---|---|
| `manifest.json` | The [manifest.json](https://github.com/zackees/manifest.json) **Index**: one entry per tool, pointing at its Catalog with sha256 and size. |
| `assets/<tool>/manifest.json` | The tool's **Catalog**: channels (`latest-stable`, `stable`), and per version a Release with one Asset per platform. |
| Release `<tool>-<version>` | The assets: `<tool>-<version>-<platform>[-<variant>].tar.zst`, zstd level 9. |
| `scripts/libs.py` | `pack` (directory to `.tar.zst` plus its Asset record), `add` (record into the Catalog and refresh the Index), `slice` (an EmbeddedSlice for a consumer to pin). |

## Plain HTTPS, no GitHub API

Consumers fetch everything as static files:

- catalogs: `https://raw.githubusercontent.com/obs-rust/obs-studio-libs/main/...`
- assets: `https://github.com/obs-rust/obs-studio-libs/releases/download/<tool>-<version>/<file>`

Neither is `api.github.com`, so a build needs no token and is not
rate-limited. Every asset is pinned by sha256, and the Index pins each Catalog
by sha256, so the chain is verifiable end to end. A consumer normally commits an
EmbeddedSlice (`scripts/libs.py slice`) and needs no network lookup to know
what to download.

## Platforms

| Platform tuple | Built by |
|---|---|
| `os=linux,arch=x86_64,libc=glibc,os_version=2.28` | obs-studio's `build-aux/appimage/manylinux/` image (manylinux_2_28, AlmaLinux 8), packed with `scripts/libs.py pack` |
| `os=windows,arch=x86_64,libc=msvc` | `.github/workflows/qt6.yml` on `windows-2022`, with obs-deps' recipe |
| `os=windows,arch=aarch64,libc=msvc` | `.github/workflows/qt6.yml` on `windows-11-arm` |
| `os=darwin,arch=universal2,os_version=11.0` | `.github/workflows/qt6.yml` on `macos-15` |

For Linux, `os_version` is the glibc floor: the oldest glibc the libraries run on.

## Tools

- **qt6**: Qt 6. Linux has qtbase, qtsvg and qtwayland; Windows and macOS have
  obs-deps' Qt set. Each archive's contents are a Qt install prefix (`lib/`,
  `include/`, `plugins/`, `lib/cmake/Qt6*`). Qt's CMake packages are
  relocatable, so the prefix can be extracted anywhere.
