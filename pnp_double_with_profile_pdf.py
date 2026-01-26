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

import argparse, json, os, tempfile, shutil
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO

# ---------- Utilities ----------
def mm_to_pt(mm):
    """
    Convert millimeters to PDF points.

    PDF coordinates use points, where:
    - 1 inch = 25.4 mm
    - 1 inch = 72 points

    Parameters:
        mm (float): Value in millimeters.

    Returns:
        float: Equivalent value in PDF points.
    """
    return mm * 72.0 / 25.4


def load_profile(path):
    """
    Load a printer calibration profile from a JSON file.

    A default profile is always created first. If a JSON profile file
    is provided and exists, its values are merged into the default profile.
    Nested dictionaries are merged key by key.

    Parameters:
        path (str or None): Path to the JSON profile file.

    Returns:
        dict: The resulting printer profile dictionary.
    """

    # Default profile (A4 portrait, short-edge flip, sample calibration)
    prof = {
        "paper": {"width_mm": 210.0, "height_mm": 297.0, "orientation": "portrait"},
        "margins": {"x_mm": 0.0, "y_mm": 0.0},
        "flip_mode": "short",
        "back_corrections": {
            "extra_rot_deg": 0.30,
            "shift_x_mm": 1.0,
            "shift_y_mm": 1.0
        }
    }

    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in data:
            if isinstance(data[k], dict) and k in prof:
                prof[k].update(data[k])
            else:
                prof[k] = data[k]

    return prof

def effective_total(total, order, on_odd):
    """
    Compute the effective number of pages to process.

    This function adjusts the total page count depending on the page
    order mode and the selected policy for odd-page PDFs.

    Parameters:
        total (int): Number of pages in the input PDF.
        order (str): Page order mode.
        on_odd (str): Policy for handling odd-page PDFs
                      ("warn", "add_blank", or "drop_last").

    Returns:
        int: Effective number of pages after applying the policy.
    """
    if order == "fronts_then_backs" and (total % 2 == 1):
        if on_odd == "add_blank":
            return total + 1
        if on_odd == "drop_last":
            return total - 1
    return total

def is_back_page(index0, total_eff, order):
    """
    Determine whether a given page index corresponds to a back page.

    The logic depends on the selected page order mode.

    Parameters:
        index0 (int): Zero-based page index in the effective sequence.
        total_eff (int): Effective total number of pages.
        order (str): Page order mode.

    Returns:
        bool: True if the page is a back page, False otherwise.
    """
    if order == "single_sided":
        return False
    if order == "interleaved":
        return (index0 % 2) == 1
    if order == "fronts_then_backs":
        half = total_eff // 2
        return index0 >= half
    if order == "last_back":
        return index0 == (total_eff - 1)
    return False

def _save_pdf(doc, path):
    """Save PDF with maximum compaction."""
    doc.save(path, garbage=4, deflate=True, clean=True)

def safe_save(out_doc, src_path, out_path):
    """
    Saves 'out_doc' while avoiding conflicts with the input file and OS file locks.
    - If the output path matches the input path, saves to a temporary file and then replaces it.
    - Ensures a .pdf extension and creates the destination directory if it does not exist.
    """
    out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
    os.makedirs(out_dir, exist_ok=True)

    if not out_path.lower().endswith(".pdf"):
        out_path = out_path + ".pdf"

    same_file = os.path.abspath(src_path) == os.path.abspath(out_path)
    if same_file:
        fd, tmp_path = tempfile.mkstemp(prefix=os.path.basename(out_path) + ".tmp.", suffix=".pdf", dir=out_dir)
        os.close(fd)
        _save_pdf(out_doc, tmp_path)
        out_doc.close()
        try:
            os.replace(tmp_path, out_path)
        except Exception:
            shutil.copy2(tmp_path, out_path)
            os.remove(tmp_path)
    else:
        _save_pdf(out_doc, out_path)
        out_doc.close()
    return out_path

# ---------- Vector processing ----------
def build_back_matrix(rect, extra_rot, rotate180, shift_x_pt, shift_y_pt):
    """
    Build the transformation matrix applied to back pages.

    This includes optional fine rotation, optional 180-degree flip,
    and optional X/Y translation.
    """
    M = fitz.Matrix(1, 0, 0, 1, 0, 0)

    if abs(extra_rot) > 1e-6:
        cx = rect.width / 2.0
        cy = rect.height / 2.0
        M = (
            fitz.Matrix(1, 0, 0, 1, cx, cy)
            * fitz.Matrix(rotation=extra_rot)
            * fitz.Matrix(1, 0, 0, 1, -cx, -cy)
            * M
        )

    if rotate180:
        cx = rect.width / 2.0
        cy = rect.height / 2.0
        M = (
            fitz.Matrix(1, 0, 0, 1, cx, cy)
            * fitz.Matrix(rotation=180)
            * fitz.Matrix(1, 0, 0, 1, -cx, -cy)
            * M
        )

    if abs(shift_x_pt) > 1e-6 or abs(shift_y_pt) > 1e-6:
        shift_matrix = fitz.Matrix(1, 0, 0, 1, shift_x_pt, shift_y_pt)
        M = shift_matrix * M

    return M

def copy_pdf_page(out_doc, src_doc, index, rect, matrix=None):
    """
    Copy a page from the source document into the output document,
    optionally applying a transformation matrix.
    """
    new_page = out_doc.new_page(width=rect.width, height=rect.height)
    if matrix is None:
        new_page.show_pdf_page(rect, src_doc, index)
    else:
        new_page.show_pdf_page(rect, src_doc, index, matrix=matrix)

def process_pdf_vector(in_path, out_path, profile, order, on_odd, flip_mode_override=None):
    """
    Process a Print-and-Play PDF using vector operations only.

    This function copies pages from the input PDF to a new PDF, applying
    fine-grained corrections (rotation and X/Y shifts) to back pages only,
    according to the provided printer profile.

    No rasterization is performed. If any vector operation fails, the caller
    is expected to fall back to raster processing.

    Parameters:
        in_path (str): Path to the input PDF file.
        out_path (str): Path to the output PDF file.
        profile (dict): Printer calibration profile.
        order (str): Page order mode (e.g. interleaved, fronts_then_backs).
        on_odd (str): Policy for odd-page PDFs in fronts_then_backs mode.
        flip_mode_override (str, optional): Overrides the profile flip mode.

    Returns:
        bool: True if vector processing succeeds, False otherwise.
    """

    src = fitz.open(in_path)
    out = fitz.open()

    flip_mode = (flip_mode_override or profile.get("flip_mode", "short")).lower()
    bc = profile.get("back_corrections", {})
    extra_rot = float(bc.get("extra_rot_deg", 0.0))
    shift_x_pt = mm_to_pt(float(bc.get("shift_x_mm", 0.0)))
    shift_y_pt = mm_to_pt(float(bc.get("shift_y_mm", 0.0)))
    rotate180 = (flip_mode == "short")

    total = len(src)
    total_eff = effective_total(total, order, on_odd)

    try:
        for i in range(total_eff):
            if i < total:
                rect = src[i].rect
            else:
                rect = src[-1].rect  # geometry reference for added blank page

            if i >= total:
                out.new_page(width=rect.width, height=rect.height)
                continue

            if not is_back_page(i, total_eff, order):
                copy_pdf_page(out, src, i, rect)
            else:
                matrix = build_back_matrix(
                    rect,
                    extra_rot,
                    rotate180,
                    shift_x_pt,
                    shift_y_pt
                )
                copy_pdf_page(out, src, i, rect, matrix=matrix)

        src.close()
        final_path = safe_save(out, in_path, out_path)
        print(f"Saved (vector): {final_path}")
        return True

    except (fitz.FitzError, RuntimeError, IOError):
        return False

    finally:
        try:
            src.close()
        except Exception:
            pass
        try:
            out.close()
        except Exception:
            pass

# ---------- Raster fallback (compressed JPEG) ----------
def render_page_image(src_doc, index, total, dpi):
    """
    Render a PDF page to a PIL image at the given DPI.
    If index exceeds total, return a blank image using the last page geometry.
    """
    if index < total:
        page = src_doc[index]
        rect = page.rect
        pix = page.get_pixmap(
            matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
            alpha=False
        )
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return img, rect

    last_rect = src_doc[-1].rect
    px_w = int(last_rect.width * dpi / 72.0)
    px_h = int(last_rect.height * dpi / 72.0)
    img = Image.new("RGB", (px_w, px_h), "white")
    return img, last_rect

def apply_back_transform_raster(img, extra_rot, rotate180):
    """
    Apply raster transformations to a back page image.
    """
    if abs(extra_rot) > 1e-6:
        img = img.rotate(extra_rot, resample=Image.BICUBIC, expand=False)
    if rotate180:
        img = img.rotate(180, resample=Image.BICUBIC, expand=False)
    return img

def draw_image_on_canvas(canv, img, rect, shift_x_pt=0.0, shift_y_pt=0.0, jpeg_quality=85):
    """
    Draw a PIL image onto a ReportLab canvas page using JPEG compression.
    """
    if canv.getPageNumber() == 0:
        canv.setPageCompression(1)

    buf = BytesIO()
    img.save(
        buf,
        format="JPEG",
        quality=max(1, min(95, jpeg_quality)),
        optimize=True
    )
    buf.seek(0)

    ir = ImageReader(buf)
    canv.setPageSize((rect.width, rect.height))
    canv.drawImage(
        ir,
        shift_x_pt,
        shift_y_pt,
        width=rect.width,
        height=rect.height,
        preserveAspectRatio=False,
        mask="auto"
    )
    canv.showPage()

def raster_fallback(in_path, out_path, profile, order, on_odd, flip_mode_override=None, dpi=300, jpeg_quality=85
):
    """
    Process a Print-and-Play PDF using rasterization with JPEG compression.

    This function renders each page to an image at the specified DPI and
    rebuilds the PDF using compressed JPEG images. Corrections (rotation
    and X/Y shifts) are applied to back pages only, according to the printer
    profile.

    This mode is used as a fallback when vector-based processing fails or
    is explicitly requested. It prioritizes compatibility and controlled
    file size over full vector fidelity.

    Parameters:
        in_path (str): Path to the input PDF file.
        out_path (str): Path to the output PDF file.
        profile (dict): Printer calibration profile.
        order (str): Page order mode (e.g. interleaved, fronts_then_backs).
        on_odd (str): Policy for odd-page PDFs in fronts_then_backs mode.
        flip_mode_override (str, optional): Overrides the profile flip mode.
        dpi (int): Rasterization resolution in DPI.
        jpeg_quality (int): JPEG quality (1–95).

    Returns:
        None
    """

    bc = profile.get("back_corrections", {})
    extra_rot = float(bc.get("extra_rot_deg", 0.0))
    shift_x_pt = mm_to_pt(float(bc.get("shift_x_mm", 0.0)))
    shift_y_pt = mm_to_pt(float(bc.get("shift_y_mm", 0.0)))
    flip_mode = (flip_mode_override or profile.get("flip_mode", "short")).lower()
    rotate180 = (flip_mode == "short")

    if os.path.abspath(in_path) == os.path.abspath(out_path):
        base = os.path.basename(out_path)
        out_dir = os.path.dirname(os.path.abspath(out_path)) or "."
        out_path = os.path.join(out_dir, base.replace(".pdf", "_aligned.pdf"))
        print(f"Output path adjusted to avoid overwriting input: {out_path}")

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
                canv = canvas.Canvas(out_path, pagesize=(rect.width, rect.height))

            draw_image_on_canvas(
                canv,
                img,
                rect,
                shift_x_pt=x_shift,
                shift_y_pt=y_shift,
                jpeg_quality=jpeg_quality
            )

        if canv:
            canv.save()
        print(f"Saved (raster JPEG {jpeg_quality} at {dpi} dpi): {out_path}")

    finally:
        try:
            src.close()
        except Exception:
            pass

# ---------- Main entry point ----------
def main():
    """
    Command-line entry point for the PnP Double-Side Aligner.

    This function parses command-line arguments, loads the printer profile,
    applies optional CLI overrides, and executes the alignment workflow
    using vector processing, raster processing, or automatic fallback.

    Vector processing is attempted first unless explicitly disabled.
    Raster processing is used as a fallback when vector operations fail
    or when explicitly requested.
    """

    ap = argparse.ArgumentParser(
        description=(
            "Realign a Print-and-Play PDF using a printer profile "
            "(corrections are applied to back pages only)."
        )
    )
    ap.add_argument("--input", required=True, help="Input PDF file.")
    ap.add_argument("--output", required=True, help="Output PDF file.")
    ap.add_argument("--profile", default=None, help="Path to JSON printer profile (optional).")
    ap.add_argument(
        "--order",
        default="interleaved",
        choices=["interleaved", "fronts_then_backs", "single_sided", "last_back"],
        help="Front/back page order."
    )
    ap.add_argument(
        "--on-odd",
        default="warn",
        choices=["warn", "add_blank", "drop_last"],
        help="Action to take if the PDF has an odd number of pages "
             "(applies only to fronts_then_backs)."
    )
    ap.add_argument(
        "--flip-mode",
        choices=["long", "short"],
        help="Override the duplex flip mode."
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
        )
    )
    ap.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for raster fallback (default: 300)."
    )
    ap.add_argument(
        "--jpeg-quality",
        type=int,
        default=85,
        help="JPEG quality for raster output (1–95, default: 85)."
    )
    args = ap.parse_args()

    profile = load_profile(args.profile)

    # Apply CLI overrides, if provided
    if args.rot is not None:
        profile["back_corrections"]["extra_rot_deg"] = args.rot
    if args.shiftx is not None:
        profile["back_corrections"]["shift_x_mm"] = args.shiftx
    if args.shifty is not None:
        profile["back_corrections"]["shift_y_mm"] = args.shifty

    if args.mode == "vector":
        ok = process_pdf_vector(
            args.input,
            args.output,
            profile,
            args.order,
            args.on_odd,
            args.flip_mode
        )
        if not ok:
            print("Vector mode failed. No output was generated.")
            return

    elif args.mode == "raster":
        raster_fallback(
            args.input,
            args.output,
            profile,
            args.order,
            args.on_odd,
            args.flip_mode,
            dpi=args.dpi,
            jpeg_quality=args.jpeg_quality
        )

    else:  # auto
        ok = process_pdf_vector(
            args.input,
            args.output,
            profile,
            args.order,
            args.on_odd,
            args.flip_mode
        )
        if not ok:
            print("Vector processing unavailable; using compressed raster output.")
            raster_fallback(
                args.input,
                args.output,
                profile,
                args.order,
                args.on_odd,
                args.flip_mode,
                dpi=args.dpi,
                jpeg_quality=args.jpeg_quality
            )

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
