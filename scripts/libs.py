#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# ///
"""Pack and catalog obs-studio-libs artifacts (zackees/manifest.json format).

    uv run scripts/libs.py pack <dir> --tool qt6 --version 6.11.1 --platform os=linux,arch=x86_64,libc=glibc,os_version=2.28 --out dist
    uv run scripts/libs.py add  dist/<asset>.json --assets <assets checkout>   # <tool>/manifest.json + the root manifest.json
    uv run scripts/libs.py slice --tool qt6 --version 6.11.1 --platform os=linux,arch=x86_64 --assets <dir> -o slice.json

pack   archives <dir>'s contents as <tool>-<version>-<platform>[-<variant>].tar.zst
       (zstd level 9; Python's own tarfile + compression.zstd, so the same
       script runs on Linux, macOS and Windows runners) and writes the
       manifest.json Asset for it next to it (<asset>.json).
add    records an Asset in the tool's Catalog (<tool>/manifest.json; creating
       the Release, newest first), points the tool's channels at it, and
       rewrites the root manifest.json, the Index every consumer starts from,
       whose descriptors point at each Catalog by relative URL, sha256 and size.

The catalogs live on the orphan `assets` branch (the layout soldr-toolchain
uses): manifest.json at its root, one <tool>/manifest.json per tool.
slice  projects one platform's entry into an EmbeddedSlice for a consumer to
       pin (obs-studio commits it as e.g. build-aux/appimage/manylinux/qt6.json).

Everything is served as plain HTTPS: assets from the release download URL
(github.com/<repo>/releases/download/<tag>/<file>), catalogs from
raw.githubusercontent.com (.../assets/manifest.json). Neither is the GitHub API, so consumers need no
token and are not rate-limited.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "obs-rust/obs-studio-libs"
RAW = f"https://raw.githubusercontent.com/{REPO}/assets"  # the orphan assets branch, as in soldr-toolchain
SCHEMA = "https://zackees.github.io/manifest.json/v1/manifest.schema.json"
ZSTD_LEVEL = 9
PLATFORM_KEYS = ("os", "arch", "os_version", "libc", "abi")
VARIANT_KEYS = ("optimization", "edition", "flavor")


def parse_tuple(text: str, keys: tuple[str, ...]) -> dict[str, str]:
    out = {}
    for part in filter(None, (text or "").split(",")):
        k, _, v = part.partition("=")
        if k not in keys or not v:
            raise SystemExit(f"bad tuple field {part!r}; expected key=value with key in {keys}")
        out[k] = v
    return out


def flat(platform: dict, variant: dict) -> str:
    """os=linux,arch=x86_64,libc=glibc,os_version=2.28 -> linux-x86_64-glibc2.28"""
    parts = [platform["os"], platform["arch"]]
    if platform.get("libc") and platform["libc"] != "msvc":
        parts.append(platform["libc"] + platform.get("os_version", ""))
    elif platform.get("os_version"):
        parts.append(platform["os_version"])
    parts += [variant[k] for k in VARIANT_KEYS if variant.get(k)]
    return "-".join(parts)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def release_tag(tool: str, version: str) -> str:
    return f"{tool}-{version}"


def pack(args: argparse.Namespace) -> int:
    platform = parse_tuple(args.platform, PLATFORM_KEYS)
    variant = parse_tuple(args.variant, VARIANT_KEYS)
    src = args.dir.resolve()
    args.out.mkdir(parents=True, exist_ok=True)
    name = f"{args.tool}-{args.version}-{flat(platform, variant)}.tar.zst"
    archive = args.out / name
    entries = sorted(src.iterdir())
    if not entries:
        raise SystemExit(f"{src} is empty")
    with tarfile.open(archive, "w:zst", level=ZSTD_LEVEL) as tar:
        for entry in entries:
            tar.add(entry, arcname=entry.name)  # the directory's contents, at the archive root
    asset = {
        "filename": name,
        "media_type": "application/zstd",
        "size_bytes": archive.stat().st_size,
        "sha256": sha256(archive),
        "urls": [f"https://github.com/{REPO}/releases/download/{release_tag(args.tool, args.version)}/{name}"],
    }
    record = {"tool": args.tool, "version": args.version, "platform": platform, "variant": variant, "asset": asset}
    (args.out / f"{name}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"{archive}: {asset['size_bytes']} bytes, sha256 {asset['sha256']}")
    return 0


def descriptor(path: Path, url: str) -> dict:
    return {"url": url, "sha256": sha256(path), "size_bytes": path.stat().st_size,
            "media_type": "application/vnd.manifest.v1+json"}


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n")


def add(args: argparse.Namespace) -> int:
    for rec_path in args.records:
        rec = json.loads(rec_path.read_text())
        tool, version = rec["tool"], rec["version"]
        cat_path = args.assets / tool / "manifest.json"
        cat = json.loads(cat_path.read_text()) if cat_path.exists() else {
            "$schema": SCHEMA, "kind": "Catalog", "schema_version": 1, "tool": tool,
            "online_url": f"{RAW}/{tool}/manifest.json", "channels": {}, "releases": [],
        }
        rel = next((r for r in cat["releases"] if r["version"] == version), None)
        if rel is None:
            rel = {"version": version, "published_at": "", "platforms": []}
            cat["releases"].append(rel)
        rel["published_at"] = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        key = (json.dumps(rec["platform"], sort_keys=True), json.dumps(rec["variant"], sort_keys=True))
        rel["platforms"] = [p for p in rel["platforms"]
                            if (json.dumps(p["platform"], sort_keys=True), json.dumps(p["variant"], sort_keys=True)) != key]
        rel["platforms"].append({"platform": rec["platform"], "variant": rec["variant"], "asset": rec["asset"]})
        rel["platforms"].sort(key=lambda p: flat(p["platform"], p["variant"]))
        cat["releases"].sort(key=lambda r: [int(x) if x.isdigit() else x for x in r["version"].replace("-", ".").split(".")],
                             reverse=True)
        cat["channels"]["latest-stable"] = cat["releases"][0]["version"]
        cat["channels"].setdefault("stable", cat["releases"][0]["version"])
        write_json(cat_path, cat)
        print(f"{cat_path.relative_to(args.assets)}: {tool} {version} {flat(rec['platform'], rec['variant'])}")
    write_index(args.assets)
    return 0


def write_index(assets: Path) -> None:
    """The root manifest.json: the Index, with relative descriptors (as soldr-toolchain)."""
    index = {"$schema": SCHEMA, "kind": "Index", "schema_version": 1, "tools": {}}
    summaries = json.loads((ROOT / "summaries.json").read_text())
    for cat_path in sorted(assets.glob("*/manifest.json")):
        tool = cat_path.parent.name
        index["tools"][tool] = {
            "descriptor": descriptor(cat_path, f"{tool}/manifest.json"),
            "summary": summaries.get(tool, ""),
            "kind_hint": "library",
        }
    write_json(assets / "manifest.json", index)


def make_slice(args: argparse.Namespace) -> int:
    cat_path = args.assets / args.tool / "manifest.json"
    cat = json.loads(cat_path.read_text())
    want = parse_tuple(args.platform, PLATFORM_KEYS)
    want_v = parse_tuple(args.variant, VARIANT_KEYS)
    version = cat["channels"].get(args.version, args.version)
    rel = next(r for r in cat["releases"] if r["version"] == version)
    # A missing field is a wildcard (the manifest.json resolution rule).
    hits = [p for p in rel["platforms"]
            if all(p["platform"].get(k) == v for k, v in want.items())
            and all(p["variant"].get(k) == v for k, v in want_v.items())]
    if len(hits) != 1:
        raise SystemExit(f"{len(hits)} matches for {want} {want_v} in {args.tool} {version}")
    hit = hits[0]
    doc = {
        "$schema": SCHEMA, "kind": "EmbeddedSlice", "schema_version": 1, "tool": args.tool,
        "compiled_for": {"platform": hit["platform"], "variant": hit["variant"], "channel": version},
        "compiled_version": version, "asset": hit["asset"],
        "online_url": cat["online_url"], "online_sha256": sha256(cat_path),
    }
    write_json(args.output, doc)
    print(f"{args.output}: {args.tool} {version} {hit['asset']['filename']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    pk = sub.add_parser("pack")
    pk.add_argument("dir", type=Path)
    pk.add_argument("--tool", required=True)
    pk.add_argument("--version", required=True)
    pk.add_argument("--platform", required=True, help="os=..,arch=..[,libc=..][,os_version=..][,abi=..]")
    pk.add_argument("--variant", default="", help="optimization=..[,edition=..][,flavor=..]")
    pk.add_argument("--out", type=Path, default=Path("dist"))
    ad = sub.add_parser("add")
    ad.add_argument("records", type=Path, nargs="+")
    ad.add_argument("--assets", type=Path, required=True, help="a checkout of the assets branch")
    sl = sub.add_parser("slice")
    sl.add_argument("--tool", required=True)
    sl.add_argument("--version", required=True, help="a version or a channel")
    sl.add_argument("--platform", required=True)
    sl.add_argument("--variant", default="")
    sl.add_argument("--assets", type=Path, required=True, help="a checkout of the assets branch")
    sl.add_argument("-o", "--output", type=Path, required=True)
    args = p.parse_args(argv)
    return {"pack": pack, "add": add, "slice": make_slice}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
