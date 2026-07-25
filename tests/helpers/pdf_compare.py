"""PDF comparison helpers for golden-output tests."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Union

import fitz


PathLike = Union[str, Path]


def file_bytes_equal(a: PathLike, b: PathLike) -> bool:
    """True if both files exist and have identical bytes."""
    pa, pb = Path(a), Path(b)
    if not pa.is_file() or not pb.is_file():
        return False
    return pa.read_bytes() == pb.read_bytes()


def content_stream_digest(path: PathLike) -> str:
    """
    Deterministic digest of page count + concatenated content streams.

    Ignores document metadata / timestamps that may differ across saves.
    """
    doc = fitz.open(path)
    try:
        h = hashlib.sha256()
        h.update(str(len(doc)).encode())
        for i in range(len(doc)):
            page = doc[i]
            page.clean_contents()
            h.update(page.read_contents())
            h.update(f"|{page.rect.width:.3f}x{page.rect.height:.3f}|".encode())
        return h.hexdigest()
    finally:
        doc.close()


def pdfs_equivalent(a: PathLike, b: PathLike) -> bool:
    """Prefer byte identity; fall back to content-stream digest."""
    if file_bytes_equal(a, b):
        return True
    return content_stream_digest(a) == content_stream_digest(b)
