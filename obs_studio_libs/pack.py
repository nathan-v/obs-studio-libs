"""Archives: pack a directory as <tool>-<version>-<platform>[-<variant>][-<label>].tar.zst.

For a Linux glibc platform the floor is *measured* before anything is written
(as soldr-toolchain requires: asserting a floor is not measuring it): every ELF
file's required GLIBC_ versions must be at or below platform.os_version.
"""

from __future__ import annotations

import hashlib
import tarfile
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path

from elftools.common.exceptions import ELFError
from elftools.elf.elffile import ELFFile
from elftools.elf.gnuversions import GNUVerNeedSection

from .catalog import asset_url
from .model import Asset, ManifestError, PackRecord, Platform, ReleasePlatform, Variant, dumps

ZSTD_LEVEL = 9


@dataclass(frozen=True)
class FloorViolation:
    path: str
    needs: str


def _version_tuple(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def glibc_needs(path: Path) -> str | None:
    """The newest GLIBC_x.y the ELF file requires, or None (not ELF / requires none)."""
    try:
        with path.open("rb") as f:
            if f.read(4) != b"\x7fELF":
                return None
            f.seek(0)
            elf = ELFFile(f)
            newest: tuple[int, ...] | None = None
            for section in elf.iter_sections():
                if not isinstance(section, GNUVerNeedSection):
                    continue
                for _, auxiliaries in section.iter_versions():
                    for aux in auxiliaries:
                        name = aux.name
                        if name.startswith("GLIBC_2.") and name[6:].replace(".", "").isdigit():
                            v = _version_tuple(name[6:])
                            newest = v if newest is None or v > newest else newest
            return None if newest is None else ".".join(map(str, newest))
    except (ELFError, OSError):
        return None


def measure_floor(root: Path, floor: str) -> list[FloorViolation]:
    limit = _version_tuple(floor)
    out = []
    for f in sorted(p for p in root.rglob("*") if p.is_file() and not p.is_symlink()):
        needs = glibc_needs(f)
        if needs is not None and _version_tuple(needs) > limit:
            out.append(FloorViolation(str(f.relative_to(root)), needs))
    return out


def archive_name(tool: str, version: str, platform: Platform, variant: Variant, label: str) -> str:
    parts = [tool, version, platform.flat()]
    if variant.flat():
        parts.append(variant.flat())
    if label:
        parts.append(label)
    return "-".join(parts) + ".tar.zst"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pack(
    src: Path, tool: str, version: str, platform: Platform, variant: Variant, out: Path, label: str = ""
) -> PackRecord:
    src = src.resolve()
    entries = sorted(src.iterdir())
    if not entries:
        raise ManifestError(f"{src} is empty")
    if platform.os == "linux" and platform.libc == "glibc":
        if not platform.os_version:
            raise ManifestError("a linux glibc platform needs os_version: the glibc floor")
        bad = measure_floor(src, platform.os_version)
        if bad:
            lines = "\n".join(f"  {b.path}: GLIBC_{b.needs}" for b in bad[:40])
            raise ManifestError(f"{len(bad)} files need a glibc newer than {platform.os_version}:\n{lines}")
    out.mkdir(parents=True, exist_ok=True)
    # A build label (a rebuild of a published version) is the variant's flavor, so the
    # rebuild is a separate entry beside the original in the same Release: both stay
    # resolvable, and a consumer picks one by the sha256 it pins (as soldr-toolchain does).
    if label:
        variant = replace(variant, flavor=label)
    name = archive_name(tool, version, platform, variant, "")
    archive = out / name
    with tarfile.open(archive, "w:zst", level=ZSTD_LEVEL) as tar:
        for entry in entries:
            tar.add(entry, arcname=entry.name)  # the directory's contents at the archive root
    asset = Asset(name, "application/zstd", archive.stat().st_size, _sha256(archive), (asset_url(tool, version, name),))
    record = PackRecord(tool, version, ReleasePlatform(platform, variant, asset))
    (out / f"{name}.json").write_text(dumps(record))
    return record


def ingest(
    artifact: Path, tool: str, version: str, platform: Platform, variant: Variant, out: Path, label: str = ""
) -> PackRecord:
    """A forge artifact (forge-<name>-<version>-<platform>.tar.gz of a Conan package folder) -> pack()."""
    with tempfile.TemporaryDirectory(prefix="ingest-") as tmp:
        with tarfile.open(artifact) as tar:
            tar.extractall(tmp, filter="tar")
        return pack(Path(tmp), tool, version, platform, variant, out, label)
