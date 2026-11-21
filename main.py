"""Entrypoint that copies entry.png to MAKEFUN_OUTPUT_DIR (or /output)."""

import hashlib
import os
import shutil
import sys
from pathlib import Path


def _sha256_file(path: Path) -> str:
    """Return the hex SHA-256 digest of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    """Copy entry.png to MAKEFUN_OUTPUT_DIR (default /output) and verify SHA-256."""
    src = Path(__file__).resolve().parent / "entry.png"
    if not src.is_file():
        print(f"Error: source image not found at {src}", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "entry.png"

    src_hash = _sha256_file(src)
    shutil.copy2(src, dst)
    dst_hash = _sha256_file(dst)

    if src_hash != dst_hash:
        print(
            f"Error: SHA-256 mismatch after copying {src} ({src_hash}) to {dst} ({dst_hash})",
            file=sys.stderr,
        )
        return 1

    size_bytes = dst.stat().st_size
    print(f"Copied {dst} ({size_bytes} bytes, sha256={dst_hash})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
