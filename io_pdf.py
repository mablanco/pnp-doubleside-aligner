"""Shared PDF I/O helpers (safe save)."""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any


def save_pdf(doc: Any, path: str) -> None:
    """Save PDF with compaction."""
    doc.save(path, garbage=4, deflate=True, clean=True)


def safe_save(out_doc: Any, src_path: str, out_path: str) -> str:
    """
    Save out_doc avoiding conflicts with the input file and OS locks.

    Same-path → temp file + os.replace (copy2 fallback). Ensures .pdf suffix
    and creates the destination directory when needed.
    """
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    if not out_path.lower().endswith(".pdf"):
        out_path = out_path + ".pdf"

    same_file = os.path.abspath(src_path) == os.path.abspath(out_path)
    if same_file:
        fd, tmp_path = tempfile.mkstemp(
            prefix=os.path.basename(out_path) + ".tmp.",
            suffix=".pdf",
            dir=out_dir,
        )
        os.close(fd)
        save_pdf(out_doc, tmp_path)
        out_doc.close()
        try:
            os.replace(tmp_path, out_path)
        except OSError:
            shutil.copy2(tmp_path, out_path)
            os.remove(tmp_path)
    else:
        save_pdf(out_doc, out_path)
        out_doc.close()
    return out_path


def safe_replace_file(src_tmp: str, dest_path: str) -> str:
    """Replace dest_path with src_tmp via os.replace (copy2 fallback)."""
    try:
        os.replace(src_tmp, dest_path)
    except OSError:
        shutil.copy2(src_tmp, dest_path)
        os.remove(src_tmp)
    return dest_path
