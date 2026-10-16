"""Consumer side: resolve from the root manifest.json and install an asset.

Plain HTTPS from raw.githubusercontent.com and github.com release downloads
(and the CDN hosts those redirect to). The GitHub API is never used; any other
host is refused, redirects included.
"""

from __future__ import annotations

import hashlib
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .catalog import ASSETS_RAW, resolve
from .model import Asset, ManifestError, Platform, Variant, parse_index

ROOT_URL = f"{ASSETS_RAW}/manifest.json"
ALLOWED_HOSTS = frozenset(
    {"raw.githubusercontent.com", "github.com", "objects.githubusercontent.com", "release-assets.githubusercontent.com"}
)


def check_url(url: str) -> str:
    u = urllib.parse.urlsplit(url)
    if u.scheme != "https" or u.hostname not in ALLOWED_HOSTS:
        raise ManifestError(f"refusing {url}: only https from {sorted(ALLOWED_HOSTS)} (never the GitHub API)")
    return url


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


_OPENER = urllib.request.build_opener(_CheckedRedirects)


def get(url: str) -> bytes:
    with _OPENER.open(check_url(url), timeout=60) as r:
        return r.read()


@dataclass(frozen=True)
class Pin:
    """What a consumer pins: the tool version for its platform, and the bytes it expects."""

    tool: str
    version: str
    platform: Platform
    variant: Variant
    sha256: str


def install(pin: Pin, dest: Path, root_url: str = ROOT_URL) -> Asset:
    index = parse_index(get(root_url), root_url)
    asset = resolve(
        index, pin.tool, pin.version, pin.platform, pin.variant, lambda rel: get(urllib.parse.urljoin(root_url, rel))
    )
    if asset.sha256 != pin.sha256:
        raise ManifestError(f"{pin.tool} {pin.version}: the catalog's asset is {asset.sha256}, pinned {pin.sha256}")
    with tempfile.TemporaryDirectory(prefix="obs-studio-libs-") as tmp:
        archive = Path(tmp) / asset.filename
        errors = []
        for url in asset.urls:
            try:
                with _OPENER.open(check_url(url), timeout=60) as r, archive.open("wb") as f:
                    shutil.copyfileobj(r, f, 1 << 20)
                break
            except OSError as e:
                errors.append(f"{url}: {e}")
        else:
            raise ManifestError("could not download:\n  " + "\n  ".join(errors))
        h = hashlib.sha256()
        with archive.open("rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
        if archive.stat().st_size != asset.size_bytes or h.hexdigest() != asset.sha256:
            raise ManifestError(f"{asset.filename}: size or sha256 differs from the catalog")
        dest.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive, "r:zst") as tar:
            tar.extractall(dest, filter="tar")
    return asset
