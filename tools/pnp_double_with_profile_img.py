#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_double_with_profile_img.py

EXPERIMENTAL image-based Print-and-Play path (PNG/JPG).

Prefer ``pnp_double_with_profile_pdf.py`` for production duplex alignment.
This tool is optional and not covered by the main characterization suite.

Optional dependencies (install after the main stack)::

    pip install -r requirements.txt
    pip install -r requirements-img.txt

The script:
    - computes a relative crop from ``--ref-original`` / ``--ref-crop``,
    - applies the same crop to all pages,
    - applies printer back-side corrections (rotation, shifts, flip mode)
      to **backs only**,
    - emits a multi-page PDF sized from the printer profile.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Sequence, Tuple


IMG_DEPS_HINT = (
    "Missing optional image-tool dependencies. "
    "Install them with: pip install -r requirements-img.txt"
)


def require_img_dependencies() -> None:
    """
    Import OpenCV / NumPy / FPDF or raise ImportError with an install hint.

    Separated for unit tests (mock ImportError) and for CLI missing-extras UX.
    """
    try:
        import cv2  # noqa: F401
        import numpy  # noqa: F401
        from fpdf import FPDF  # noqa: F401
    except ImportError as exc:
        raise ImportError(IMG_DEPS_HINT) from exc


def _fail(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def load_profile(path: str) -> Dict[str, Any]:
    """
    Load a printer profile from a JSON file and normalize its fields.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Profile not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        try:
            prof = json.load(f)
        except json.JSONDecodeError as exc:
            raise json.JSONDecodeError(
                f"Invalid JSON profile (comments are not allowed): {exc.msg}",
                exc.doc,
                exc.pos,
            ) from exc

    if not isinstance(prof, dict):
        raise ValueError("Profile root must be a JSON object.")

    paper = prof.get("paper", {})
    margins = prof.get("margins", {})
    back = prof.get("back_corrections", {})

    return {
        "paper_w": float(paper.get("width_mm", 297.0)),
        "paper_h": float(paper.get("height_mm", 210.0)),
        "orientation": paper.get("orientation", "landscape"),
        "margin_x": float(margins.get("x_mm", 0.0)),
        "margin_y": float(margins.get("y_mm", 0.0)),
        "flip_mode": prof.get("flip_mode", "long"),
        "rot_deg": float(back.get("extra_rot_deg", 0.0)),
        "shift_x": float(back.get("shift_x_mm", 0.0)),
        "shift_y": float(back.get("shift_y_mm", 0.0)),
    }


def read_bgr(path: str):
    """Read an image using OpenCV (BGR format)."""
    import cv2

    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Unreadable or missing image: {path}")
    return img


def to_pil(bgr):
    """Convert an OpenCV BGR image to a PIL RGB image."""
    import cv2
    from PIL import Image

    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))


def compute_relative_box(
    ref_original_path: str, ref_crop_path: str
) -> Tuple[float, float, float, float]:
    """
    Compute the relative crop box (left, top, right, bottom) as fractions
    of the original image size, using edge template matching.
    """
    import cv2

    orig = read_bgr(ref_original_path)
    crop = read_bgr(ref_crop_path)

    H, W = orig.shape[:2]
    h, w = crop.shape[:2]
    if h > H or w > W:
        raise ValueError(
            f"Crop patch ({w}x{h}) is larger than reference original ({W}x{H})."
        )

    scale = 0.5
    orig_s = cv2.resize(
        orig, (int(W * scale), int(H * scale)), interpolation=cv2.INTER_AREA
    )
    crop_s = cv2.resize(
        crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
    )

    edges_o = cv2.Canny(cv2.cvtColor(orig_s, cv2.COLOR_BGR2GRAY), 50, 150)
    edges_c = cv2.Canny(cv2.cvtColor(crop_s, cv2.COLOR_BGR2GRAY), 50, 150)

    res = cv2.matchTemplate(edges_o, edges_c, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    if max_val < 0.3:
        raise ValueError(
            f"Crop template match failed (score={max_val:.3f}). "
            "Check that --ref-crop is a region from --ref-original."
        )

    x0_s, y0_s = max_loc
    x0 = int(x0_s / scale)
    y0 = int(y0_s / scale)
    x1 = x0 + w
    y1 = y0 + h

    return x0 / W, y0 / H, (W - x1) / W, (H - y1) / H


def apply_relative_crop(img, rel_box):
    """Apply a relative crop box to an image."""
    H, W = img.shape[:2]
    l, t, r, b = rel_box

    x0 = int(round(W * l))
    y0 = int(round(H * t))
    x1 = int(round(W * (1 - r)))
    y1 = int(round(H * (1 - b)))

    if x1 <= x0 or y1 <= y0:
        raise ValueError("Computed crop box is empty; check reference images.")

    return img[y0:y1, x0:x1]


def add_to_pdf(
    pdf,
    pil_img,
    page_w_mm: float,
    page_h_mm: float,
    margin_x_mm: float,
    margin_y_mm: float,
    shift_x_mm: float = 0.0,
    shift_y_mm: float = 0.0,
    rotate180: bool = False,
) -> None:
    """
    Add a PIL image to the PDF, scaled and centered on the page,
    applying optional shifts and a 180-degree rotation (backs only).

    Short-edge flip is applied in PIL (fpdf2 ``image()`` has no portable
    ``rotation=`` across versions).
    """
    from PIL import Image as PILImage

    if rotate180:
        pil_img = pil_img.rotate(180, resample=PILImage.BICUBIC, expand=False)
        # Mirror placement so the content stays optically flipped for duplex.
        shift_x_mm = -shift_x_mm
        shift_y_mm = -shift_y_mm

    fd, tmp = tempfile.mkstemp(suffix=".jpg")
    os.close(fd)
    try:
        pil_img.save(tmp, "JPEG", quality=95)
        pdf.add_page()

        iw, ih = pil_img.size
        max_w = page_w_mm - 2 * margin_x_mm
        max_h = page_h_mm - 2 * margin_y_mm
        if max_w <= 0 or max_h <= 0:
            raise ValueError("Margins leave no printable area on the page.")

        ratio = min(max_w / iw, max_h / ih)
        w, h = iw * ratio, ih * ratio

        x = (page_w_mm - w) / 2 + shift_x_mm
        y = (page_h_mm - h) / 2 + shift_y_mm

        pdf.image(tmp, x=x, y=y, w=w, h=h)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pnp_double_with_profile_img.py",
        description=(
            "EXPERIMENTAL: build a duplex PDF from PNG/JPG pages using a "
            "printer profile and OpenCV crop matching. Prefer "
            "pnp_double_with_profile_pdf.py for production. Requires optional "
            "deps from requirements-img.txt."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Pairing: for each --front index, emit front then back. "
            "If a matching --back is omitted, the cropped front is duplicated "
            "as the back (documented experimental behavior).\n\n"
            "Install extras: pip install -r requirements-img.txt"
        ),
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Path to runtime JSON printer profile (no comment-bearing templates).",
    )
    parser.add_argument(
        "--ref-original",
        required=True,
        help="Reference full screenshot used to locate the crop.",
    )
    parser.add_argument(
        "--ref-crop",
        required=True,
        help="Reference crop patch that must match inside --ref-original.",
    )
    parser.add_argument(
        "--front",
        action="append",
        dest="fronts",
        default=None,
        metavar="PATH",
        help="Front image path (repeatable; at least one required).",
    )
    parser.add_argument(
        "--back",
        action="append",
        dest="backs",
        default=None,
        metavar="PATH",
        help=(
            "Back image path (repeatable; index-aligned with --front). "
            "Missing backs → duplicate cropped front."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Destination PDF path (must differ from inputs).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print progress messages to stdout.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Execute the image workflow; return process exit code."""
    try:
        require_img_dependencies()
    except ImportError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    from fpdf import FPDF
    from PIL import Image

    fronts: Sequence[str] = args.fronts or []
    backs: Sequence[str] = args.backs or []
    if not fronts:
        _fail("At least one --front image is required.")

    for label, path in (
        ("profile", args.profile),
        ("ref-original", args.ref_original),
        ("ref-crop", args.ref_crop),
        *((f"front[{i}]", p) for i, p in enumerate(fronts)),
        *((f"back[{i}]", p) for i, p in enumerate(backs)),
    ):
        if not os.path.exists(path):
            _fail(f"Missing {label} path: {path}")

    try:
        prof = load_profile(args.profile)
    except FileNotFoundError as exc:
        _fail(str(exc))
    except json.JSONDecodeError as exc:
        _fail(
            f"Invalid profile JSON: {exc.msg}. "
            "Runtime profiles must be plain JSON (no // or /* */ comments). "
            "Copy and strip comments from the template under profiles/."
        )
    except (TypeError, ValueError) as exc:
        _fail(f"Invalid profile: {exc}")

    page_w = prof["paper_w"]
    page_h = prof["paper_h"]
    if prof["orientation"].lower().startswith("land") and page_w < page_h:
        page_w, page_h = page_h, page_w

    try:
        rel_box = compute_relative_box(args.ref_original, args.ref_crop)
        if args.verbose:
            print(f"Relative crop box (L,T,R,B fractions): {rel_box}")
    except (FileNotFoundError, ValueError) as exc:
        _fail(str(exc))

    # Page size follows profile paper dimensions (custom mm format).
    pdf = FPDF(unit="mm", format=(page_w, page_h))

    try:
        for i, front_path in enumerate(fronts):
            try:
                front = apply_relative_crop(read_bgr(front_path), rel_box)
            except (FileNotFoundError, ValueError) as exc:
                _fail(str(exc))
            pil_f = to_pil(front)
            # Fronts: identity placement — no profile rot/shift/flip.
            add_to_pdf(
                pdf,
                pil_f,
                page_w,
                page_h,
                prof["margin_x"],
                prof["margin_y"],
            )

            if i < len(backs) and os.path.exists(backs[i]):
                try:
                    back = apply_relative_crop(read_bgr(backs[i]), rel_box)
                except (FileNotFoundError, ValueError) as exc:
                    _fail(str(exc))
            else:
                if args.verbose:
                    print(
                        f"No --back for index {i}; duplicating cropped front as back."
                    )
                back = front.copy()

            pil_b = to_pil(back)
            rot_deg = prof["rot_deg"]
            if abs(rot_deg) > 1e-3:
                pil_b = pil_b.rotate(rot_deg, resample=Image.BICUBIC, expand=False)

            rotate180 = prof["flip_mode"].lower() == "short"
            add_to_pdf(
                pdf,
                pil_b,
                page_w,
                page_h,
                prof["margin_x"],
                prof["margin_y"],
                shift_x_mm=prof["shift_x"],
                shift_y_mm=prof["shift_y"],
                rotate180=rotate180,
            )

        pdf.output(args.output)
    except SystemExit:
        raise
    except OSError as exc:
        _fail(f"Could not write output PDF {args.output!r}: {exc}")
    except (ValueError, TypeError) as exc:
        _fail(f"Failed while building PDF: {exc}")

    print(f"Generated: {args.output}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1


if __name__ == "__main__":
    sys.exit(main())
