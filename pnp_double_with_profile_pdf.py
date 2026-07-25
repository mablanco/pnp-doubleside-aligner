#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_double_with_profile_pdf.py

Realigns a Print-and-Play PDF by applying corrections to back pages only
(fine rotation and X/Y shifts).

Features:
- JSON printer profiles with CLI overrides
- Page order modes: interleaved, fronts_then_backs, single_sided, last_back
- Safe saving to avoid OS locks and temporary chunk files
- Output modes: auto, vector, raster
- Compact raster fallback (JPEG with configurable DPI and quality)

This is the main script of the PnP Double-Side Aligner project.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from io import BytesIO
from typing import Any, Optional, Tuple

import fitz  # PyMuPDF
from PIL import Image
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from geometry import (
    build_back_matrix,
    effective_total,
    is_back_page,
    mm_to_pt,
    raster_rotation_angle,
    reportlab_shift_y,
)
from io_pdf import safe_replace_file, safe_save
from profiles import apply_cli_overrides, load_profile

# Re-export for tests that import from this module
__all__ = [
    "mm_to_pt",
    "load_profile",
    "effective_total",
    "is_back_page",
    "build_back_matrix",
    "apply_back_transform_raster",
    "draw_image_on_canvas",
    "process_pdf_vector",
    "raster_fallback",
    "main",
]


def _matrix_is_identity(matrix: fitz.Matrix) -> bool:
    return (
        abs(matrix.a - 1) < 1e-12
        and abs(matrix.b) < 1e-12
        and abs(matrix.c) < 1e-12
        and abs(matrix.d - 1) < 1e-12
        and abs(matrix.e) < 1e-12
        and abs(matrix.f) < 1e-12
    )


def copy_pdf_page(
    out_doc: fitz.Document,
    src_doc: fitz.Document,
    index: int,
    rect: fitz.Rect,
    matrix: Optional[fitz.Matrix] = None,
) -> None:
    """
    Copy a page from the source document into the output document.

    When a non-identity matrix is provided, place via show_pdf_page then wrap
    the content stream with a PDF cm transform (show_pdf_page ignores matrix=).
    """
    new_page = out_doc.new_page(width=rect.width, height=rect.height)
    new_page.show_pdf_page(rect, src_doc, index)
    if matrix is None or _matrix_is_identity(matrix):
        return
    new_page.clean_contents()
    xrefs = new_page.get_contents()
    if not xrefs:
        return
    cont = new_page.read_contents()
    prefix = (
        f"q\n{matrix.a} {matrix.b} {matrix.c} {matrix.d} {matrix.e} {matrix.f} cm\n"
    ).encode()
    suffix = b"\nQ\n"
    out_doc.update_stream(xrefs[0], prefix + cont + suffix)


def process_pdf_vector(
    in_path: str,
    out_path: str,
    profile: dict,
    order: str,
    on_odd: str,
    flip_mode_override: Optional[str] = None,
) -> bool:
    """
    Process a Print-and-Play PDF using vector operations only.

    Returns True on success. Propagates TypeError/RuntimeError/OSError/ValueError
    for recoverable auto-fallback.
    """
    src: Optional[fitz.Document] = None
    out: Optional[fitz.Document] = None
    try:
        src = fitz.open(in_path)
        out = fitz.open()

        flip_mode = (flip_mode_override or profile.get("flip_mode", "short")).lower()
        bc = profile.get("back_corrections", {})
        extra_rot = float(bc.get("extra_rot_deg", 0.0))
        shift_x_pt = mm_to_pt(float(bc.get("shift_x_mm", 0.0)))
        shift_y_pt = mm_to_pt(float(bc.get("shift_y_mm", 0.0)))
        rotate180 = flip_mode == "short"

        total = len(src)
        total_eff = effective_total(total, order, on_odd)

        for i in range(total_eff):
            if i < total:
                rect = src[i].rect
            else:
                rect = src[-1].rect

            if i >= total:
                out.new_page(width=rect.width, height=rect.height)
                continue

            if not is_back_page(i, total_eff, order):
                copy_pdf_page(out, src, i, rect)
            else:
                matrix = build_back_matrix(
                    rect, extra_rot, rotate180, shift_x_pt, shift_y_pt
                )
                copy_pdf_page(out, src, i, rect, matrix=matrix)

        src.close()
        src = None
        final_path = safe_save(out, in_path, out_path)
        out = None  # closed by safe_save
        print(f"Saved (vector): {final_path}")
        return True
    except Exception:
        if src is not None:
            try:
                src.close()
            except Exception:
                pass
        if out is not None:
            try:
                out.close()
            except Exception:
                pass
        raise


def render_page_image(
    src_doc: fitz.Document, index: int, total: int, dpi: int
) -> Tuple[Image.Image, fitz.Rect]:
    """Render a PDF page to a PIL image at the given DPI."""
    if index < total:
        page = src_doc[index]
        rect = page.rect
        pix = page.get_pixmap(
            matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
            alpha=False,
        )
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img, rect

    last_rect = src_doc[-1].rect
    px_w = int(last_rect.width * dpi / 72.0)
    px_h = int(last_rect.height * dpi / 72.0)
    img = Image.new("RGB", (px_w, px_h), "white")
    return img, last_rect


def apply_back_transform_raster(
    img: Image.Image, extra_rot: float, rotate180: bool
) -> Image.Image:
    """Apply raster transforms; positive extra_rot is clockwise."""
    if abs(extra_rot) > 1e-6:
        img = img.rotate(
            raster_rotation_angle(extra_rot),
            resample=Image.BICUBIC,
            expand=False,
        )
    if rotate180:
        img = img.rotate(180, resample=Image.BICUBIC, expand=False)
    return img


def draw_image_on_canvas(
    canv: Any,
    img: Image.Image,
    rect: Any,
    shift_x_pt: float = 0.0,
    shift_y_pt: float = 0.0,
    jpeg_quality: int = 85,
) -> None:
    """
    Draw a PIL image onto a ReportLab canvas page using JPEG compression.

    shift_y_pt uses the calibration contract (+Y downward); converted to
    ReportLab coordinates internally.
    """
    if canv.getPageNumber() == 0:
        canv.setPageCompression(1)

    buf = BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=max(1, min(95, jpeg_quality)),
        optimize=True,
    )
    buf.seek(0)

    ir = ImageReader(buf)
    canv.setPageSize((rect.width, rect.height))
    canv.drawImage(
        ir,
        shift_x_pt,
        reportlab_shift_y(shift_y_pt),
        width=rect.width,
        height=rect.height,
        preserveAspectRatio=False,
        mask="auto",
    )
    canv.showPage()


def raster_fallback(
    in_path: str,
    out_path: str,
    profile: dict,
    order: str,
    on_odd: str,
    flip_mode_override: Optional[str] = None,
    dpi: int = 300,
    jpeg_quality: int = 85,
) -> str:
    """
    Process via rasterization with JPEG compression.

    Same-path output uses temp file + replace (aligned with vector safe_save).
    Returns the final output path.
    """
    bc = profile.get("back_corrections", {})
    extra_rot = float(bc.get("extra_rot_deg", 0.0))
    shift_x_pt = mm_to_pt(float(bc.get("shift_x_mm", 0.0)))
    shift_y_pt = mm_to_pt(float(bc.get("shift_y_mm", 0.0)))
    flip_mode = (flip_mode_override or profile.get("flip_mode", "short")).lower()
    rotate180 = flip_mode == "short"

    if not out_path.lower().endswith(".pdf"):
        out_path = out_path + ".pdf"

    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(out_dir, exist_ok=True)
    same_file = os.path.abspath(in_path) == os.path.abspath(out_path)

    if same_file:
        fd, write_path = tempfile.mkstemp(
            prefix=os.path.basename(out_path) + ".tmp.",
            suffix=".pdf",
            dir=out_dir,
        )
        os.close(fd)
    else:
        write_path = out_path

    src = fitz.open(in_path)
    canv = None
    total = len(src)
    total_eff = effective_total(total, order, on_odd)

    try:
        for i in range(total_eff):
            img, rect = render_page_image(src, i, total, dpi)

            if i < total and is_back_page(i, total_eff, order):
                img = apply_back_transform_raster(img, extra_rot, rotate180)
                x_shift, y_shift = shift_x_pt, shift_y_pt
            else:
                x_shift, y_shift = 0.0, 0.0

            if canv is None:
                canv = canvas.Canvas(write_path, pagesize=(rect.width, rect.height))

            draw_image_on_canvas(
                canv,
                img,
                rect,
                shift_x_pt=x_shift,
                shift_y_pt=y_shift,
                jpeg_quality=jpeg_quality,
            )

        if canv:
            canv.save()

        if same_file:
            final_path = safe_replace_file(write_path, out_path)
        else:
            final_path = write_path

        print(f"Saved (raster JPEG {jpeg_quality} at {dpi} dpi): {final_path}")
        return final_path

    finally:
        try:
            src.close()
        except Exception:
            pass


def _emit_odd_warning(total: int, order: str, on_odd: str) -> None:
    if order == "fronts_then_backs" and total % 2 == 1 and on_odd == "warn":
        print(
            f"Warning: odd page count ({total}) with order=fronts_then_backs; "
            "continuing with documented classification (use add_blank or "
            "drop_last to change effective length).",
            file=sys.stderr,
        )


def _fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    """CLI entry point for the PnP Double-Side Aligner."""
    ap = argparse.ArgumentParser(
        description=(
            "Realign a Print-and-Play PDF using a printer profile "
            "(corrections are applied to back pages only)."
        )
    )
    ap.add_argument("--input", required=True, help="Input PDF file.")
    ap.add_argument("--output", required=True, help="Output PDF file.")
    ap.add_argument(
        "--profile",
        default=None,
        help="Path to JSON printer profile (optional).",
    )
    ap.add_argument(
        "--order",
        default="interleaved",
        choices=["interleaved", "fronts_then_backs", "single_sided", "last_back"],
        help="Front/back page order.",
    )
    ap.add_argument(
        "--on-odd",
        default="warn",
        choices=["warn", "add_blank", "drop_last"],
        help=(
            "Action to take if the PDF has an odd number of pages "
            "(applies only to fronts_then_backs)."
        ),
    )
    ap.add_argument(
        "--flip-mode",
        choices=["long", "short"],
        help="Override the duplex flip mode.",
    )
    ap.add_argument("--rot", type=float, help="Override extra_rot_deg (degrees).")
    ap.add_argument("--shiftx", type=float, help="Override shift_x_mm (millimeters).")
    ap.add_argument("--shifty", type=float, help="Override shift_y_mm (millimeters).")
    ap.add_argument(
        "--mode",
        default="auto",
        choices=["auto", "vector", "raster"],
        help=(
            "Processing mode: "
            "auto (try vector, fall back to raster), "
            "vector (vector only), "
            "raster (raster only)."
        ),
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for raster fallback (default: 300).",
    )
    ap.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="JPEG quality for raster output (1–95, default: 85).",
    )
    args = ap.parse_args()

    if not os.path.isfile(args.input):
        _fail(f"Input PDF not found or unreadable: {args.input}")

    try:
        profile = load_profile(args.profile)
    except FileNotFoundError as exc:
        _fail(f"{exc}. Provide a valid --profile path or omit --profile for identity.")
    except json.JSONDecodeError as exc:
        _fail(
            f"Invalid profile JSON: {exc.msg}. "
            "Runtime profiles must be plain JSON (no // or /* */ comments). "
            "Copy and strip comments from the template under profiles/."
        )
    except (ValueError, TypeError, OSError) as exc:
        _fail(f"Invalid profile: {exc}")

    apply_cli_overrides(
        profile, rot=args.rot, shiftx=args.shiftx, shifty=args.shifty
    )

    try:
        with fitz.open(args.input) as probe:
            total = len(probe)
    except Exception as exc:
        _fail(f"Cannot open input PDF {args.input}: {exc}")

    _emit_odd_warning(total, args.order, args.on_odd)

    try:
        if args.mode == "vector":
            try:
                ok = process_pdf_vector(
                    args.input,
                    args.output,
                    profile,
                    args.order,
                    args.on_odd,
                    args.flip_mode,
                )
            except (TypeError, RuntimeError, OSError, ValueError) as exc:
                _fail(f"Vector mode failed: {exc}")
            if not ok:
                _fail("Vector mode failed. No output was generated.")

        elif args.mode == "raster":
            raster_fallback(
                args.input,
                args.output,
                profile,
                args.order,
                args.on_odd,
                args.flip_mode,
                dpi=args.dpi,
                jpeg_quality=args.jpeg_quality,
            )

        else:  # auto
            try:
                process_pdf_vector(
                    args.input,
                    args.output,
                    profile,
                    args.order,
                    args.on_odd,
                    args.flip_mode,
                )
            except (TypeError, RuntimeError, OSError, ValueError) as exc:
                print(
                    f"Vector processing unavailable ({exc}); "
                    "falling back to compressed raster output.",
                    file=sys.stderr,
                )
                raster_fallback(
                    args.input,
                    args.output,
                    profile,
                    args.order,
                    args.on_odd,
                    args.flip_mode,
                    dpi=args.dpi,
                    jpeg_quality=args.jpeg_quality,
                )

    except SystemExit:
        raise
    except Exception as exc:
        _fail(f"Unexpected error while processing PDF: {exc}")

    bc = profile["back_corrections"]
    print(f"Finished: {args.output}")
    print(
        f"Order: {args.order}, "
        f"Flip: {args.flip_mode or profile.get('flip_mode', 'short')}, "
        f"On-odd: {args.on_odd}, "
        f"Mode: {args.mode}"
    )
    print(
        f"Corrections: "
        f"rotation={bc['extra_rot_deg']}°, "
        f"shift=({bc['shift_x_mm']} mm, {bc['shift_y_mm']} mm)"
    )


if __name__ == "__main__":
    main()
