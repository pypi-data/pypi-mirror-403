from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(url: str, dst: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "tokmor-pos/ear-installer"})
    with urllib.request.urlopen(req) as r, dst.open("wb") as f:  # noqa: S310
        shutil.copyfileobj(r, f)


def install_wikiparson_mini(
    *,
    src: str,
    sha256: Optional[str] = None,
    dest_dir: Optional[str] = None,
) -> Path:
    """
    Install WikiParSon mini profiles (.parson tarballs) into:
      ~/parson_final/wikiparson_mini/

    `src` can be:
      - local path to .tar.gz or .tar.zst
      - https URL to .tar.gz or .tar.zst

    Returns the destination directory path.
    """
    dest = Path(dest_dir).expanduser().resolve() if dest_dir else (Path.home() / "parson_final" / "wikiparson_mini")
    dest.mkdir(parents=True, exist_ok=True)

    # Acquire archive into a temp file
    src_s = (src or "").strip()
    if not src_s:
        raise ValueError("src is required")

    with tempfile.TemporaryDirectory(prefix="tokmor_pos_parson_") as td:
        td_path = Path(td)
        if src_s.startswith("http://") or src_s.startswith("https://"):
            # Keep extension for later logic
            name = src_s.split("?")[0].split("/")[-1] or "wikiparson_mini.tar.gz"
            arc = td_path / name
            _download(src_s, arc)
        else:
            arc = Path(src_s).expanduser().resolve()
            if not arc.exists():
                raise FileNotFoundError(str(arc))

        if sha256:
            got = _sha256_file(arc)
            exp = sha256.strip().lower()
            if got.lower() != exp:
                raise ValueError(f"SHA256 mismatch: expected {exp} got {got}")

        # Extract
        if arc.name.endswith(".tar.gz") or arc.name.endswith(".tgz"):
            with tarfile.open(arc, "r:gz") as tf:
                tf.extractall(dest)  # noqa: S202 (trusted local archive)
        elif arc.name.endswith(".tar.zst"):
            # tarfile doesn't support zstd natively in stdlib; use system tar+zstd.
            subprocess.check_call(["tar", "--use-compress-program=zstd", "-xf", str(arc), "-C", str(dest)])  # noqa: S603,S607
        else:
            raise ValueError("Unsupported archive type. Use .tar.gz or .tar.zst")

    return dest

