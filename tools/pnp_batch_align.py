#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatically processes all PDFs in a directory, applying back-page alignment,
and detects the page order per PDF using visual heuristics when
--auto-detect-smart is enabled.

This script uses pnp_double_with_profile_pdf.py as a worker
(by default, located in the same directory).
"""

import os, argparse, glob, subprocess, re, math, sys
import fitz  # PyMuPDF
from PIL import Image

# Common-back cluster thresholds (research R1)
VISUAL_ABS_THRESHOLD = 0.80
VISUAL_MARGIN = 0.03
# Cap fingerprints for large PDFs (research R3)
MAX_FINGERPRINT_PAGES = 40

# ----------------- Filename hints -----------------
NAME_HINTS = [
    (re.compile(r'fronts?_then_backs?|halves', re.I), 'fronts_then_backs'),
    (re.compile(r'last[_\- ]?back', re.I), 'last_back'),
    (re.compile(r'single[_\- ]?sided|single', re.I), 'single_sided'),
    (re.compile(r'interleav', re.I), 'interleaved'),
]

def name_hint_to_order(name):
    for rx, order in NAME_HINTS:
        if rx.search(name):
            return order
    return None

# ----------------- Visual fingerprints -----------------
def page_fingerprint(doc, idx, thumb=32, dpi=72):
    """
    Compute a simple visual fingerprint (list of floats) for page `idx`.

    The page is rendered at low resolution, converted to grayscale,
    resized to thumb x thumb, and normalized using z-score
    (mean and variance normalization) for robustness.
    """
    page = doc[idx]
    # Lightweight render: factor 1.0 ≈ 72 dpi
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img = img.convert("L").resize((thumb, thumb), Image.BILINEAR)
    vec = list(img.getdata())
    # Normalization
    m = sum(vec) / len(vec)
    var = sum((x - m) ** 2 for x in vec) / len(vec)
    sd = math.sqrt(var) if var > 1e-9 else 1.0
    return [(x - m) / sd for x in vec]

def cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return dot / (na * nb)

def avg_sim_block(fps, start, end):
    """Average pairwise cosine similarity among fingerprints fps[start:end]."""
    block = fps[start:end]
    if len(block) < 2:
        return 0.0
    sims = []
    for i in range(len(block)):
        for j in range(i + 1, len(block)):
            sims.append(cosine_sim(block[i], block[j]))
    return sum(sims) / len(sims) if sims else 0.0

def avg_sim_indices(fps, indices):
    """Average pairwise cosine similarity among fps at the given indices."""
    if len(indices) < 2:
        return 0.0
    sims = []
    for i in range(len(indices)):
        for j in range(i + 1, len(indices)):
            sims.append(cosine_sim(fps[indices[i]], fps[indices[j]]))
    return sum(sims) / len(sims) if sims else 0.0

def sample_page_indices(n, max_samples=MAX_FINGERPRINT_PAGES):
    """
    Evenly spaced page indices for fingerprinting.

    When N > max_samples, sample up to max_samples indices across [0, N)
    so both odd-index and second-half candidacy can still be scored.
    """
    if n <= 0:
        return []
    if n <= max_samples:
        return list(range(n))
    # Inclusive endpoints via linspace-style rounding
    return sorted({int(round(i * (n - 1) / (max_samples - 1))) for i in range(max_samples)})

def detect_order_by_page_count(total):
    """
    Detect page order based only on page count.
    """
    if total <= 1:
        return "single_sided", "pages:1"
    if total % 2 == 1:
        return "last_back", f"pages:odd({total})"
    return None, None

def decide_by_common_back(sim_odd_cluster, sim_second_half_cluster, even_default):
    """
    Decide even-page order via common-back clusters (research R1).

    - Odd-index cluster high → interleaved (shared backs on B pages in F,B,F,B…)
    - Second-half cluster high → fronts_then_backs (shared backs in second half)
    - Else → even_default with visual:tie reason
    """
    t, m = VISUAL_ABS_THRESHOLD, VISUAL_MARGIN
    if (
        sim_odd_cluster >= t
        and sim_odd_cluster >= sim_second_half_cluster + m
    ):
        return (
            "interleaved",
            f"visual:odd-cluster({sim_odd_cluster:.2f})"
            f">second-half({sim_second_half_cluster:.2f})",
        )

    if (
        sim_second_half_cluster >= t
        and sim_second_half_cluster >= sim_odd_cluster + m
    ):
        return (
            "fronts_then_backs",
            f"visual:second-half({sim_second_half_cluster:.2f})"
            f">odd-cluster({sim_odd_cluster:.2f})",
        )

    return (
        even_default,
        f"visual:tie({sim_odd_cluster:.2f} vs {sim_second_half_cluster:.2f})"
        f"->{even_default}",
    )


def detect_order_smart(pdf_path, even_default='interleaved', verbose=False):
    """
    Smart heuristic for detecting page order:
      - filename hints
      - single page -> single_sided
      - odd page count -> last_back
      - even page count -> common-back cluster (odd-index vs second-half)
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return even_default, "open-fallback"

    try:
        total = len(doc)
        name = os.path.basename(pdf_path)

        # 1) Filename hint
        name_hint = name_hint_to_order(name)
        if name_hint:
            return name_hint, f"name-hint:{name_hint}"

        # 2) Page count rules
        order, reason = detect_order_by_page_count(total)
        if order:
            return order, reason

        # 3) Visual analysis (even number of pages); sample when N is large
        indices = sample_page_indices(total)
        fps_by_page = {}
        for idx in indices:
            fps_by_page[idx] = page_fingerprint(doc, idx)

        half = total // 2
        odd_idxs = [i for i in indices if i % 2 == 1]
        second_idxs = [i for i in indices if i >= half]

        # fps list indexed by page number for avg_sim_indices
        max_idx = max(indices) if indices else -1
        fps = [None] * (max_idx + 1)
        for i, fp in fps_by_page.items():
            fps[i] = fp

        sim_odd_cluster = avg_sim_indices(fps, odd_idxs)
        sim_second_half_cluster = avg_sim_indices(fps, second_idxs)

        if verbose:
            print(
                f"   visual: sim_odd_cluster={sim_odd_cluster:.3f}, "
                f"sim_second_half_cluster={sim_second_half_cluster:.3f}, "
                f"sampled={len(indices)}/{total}"
            )

        return decide_by_common_back(
            sim_odd_cluster,
            sim_second_half_cluster,
            even_default,
        )
    except Exception:
        return even_default, "open-fallback"
    finally:
        doc.close()

def determine_order(pdf, args):
    """
    Determine page order for a given PDF.
    """
    if args.auto_detect_smart:
        return detect_order_smart(
            pdf,
            even_default=args.even_default,
            verbose=args.verbose
        )

    with fitz.open(pdf) as d:
        total = len(d)

    if total <= 1:
        return "single_sided", "pages:1"
    if total % 2 == 1:
        return "last_back", f"pages:odd({total})"

    return args.even_default, f"pages:even({total})->{args.even_default}"

def build_worker_command(pdf, output, order, args):
    """
    Build the command line for the worker alignment script.
    """
    cmd = [
        "python3", args.script,
        "--input", pdf,
        "--output", output,
        "--order", order,
        "--on-odd", args.on_odd,
        "--dpi", str(args.dpi)
    ]

    if args.profile:
        cmd += ["--profile", args.profile]
    if args.flip_mode:
        cmd += ["--flip-mode", args.flip_mode]
    if args.rot is not None:
        cmd += ["--rot", str(args.rot)]
    if args.shiftx is not None:
        cmd += ["--shiftx", str(args.shiftx)]
    if args.shifty is not None:
        cmd += ["--shifty", str(args.shifty)]

    return cmd



def main():
    ap = argparse.ArgumentParser(
        description=(
            "Batch PnP aligner (experimental). "
            "Optional --auto-detect-smart chooses page order per PDF."
        )
    )
    ap.add_argument("--input-dir", required=True, help="Directory containing input PDFs.")
    ap.add_argument("--output-dir", required=True, help="Destination directory.")
    ap.add_argument("--profile", default=None, help="JSON printer profile (optional).")
    ap.add_argument(
        "--auto-detect-smart",
        action="store_true",
        help=(
            "Enable experimental smart page-order detection "
            "(name hint → page count → content → even-default)."
        ),
    )
    ap.add_argument(
        "--even-default",
        default="interleaved",
        choices=["interleaved", "fronts_then_backs"],
        help="Default order if the PDF is even and no clear pattern is found.",
    )
    ap.add_argument(
        "--on-odd",
        default="warn",
        choices=["warn", "add_blank", "drop_last"],
        help="Action to take if the PDF is odd in fronts_then_backs mode.",
    )
    ap.add_argument("--flip-mode", choices=["long", "short"], help="Override profile flip mode.")
    ap.add_argument("--rot", type=float, help="Override extra_rot_deg (degrees).")
    ap.add_argument("--shiftx", type=float, help="Override shift_x_mm (millimeters).")
    ap.add_argument("--shifty", type=float, help="Override shift_y_mm (millimeters).")
    ap.add_argument("--dpi", type=int, default=600, help="DPI for worker raster fallback.")
    ap.add_argument(
        "--script",
        default="pnp_double_with_profile_pdf.py",
        help="Path to the individual alignment script."
    )
    ap.add_argument("--verbose", action="store_true", help="Show visual similarity metrics.")
    args = ap.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    pdfs = sorted(glob.glob(os.path.join(args.input_dir, "*.pdf")))
    if not pdfs:
        print("No PDFs found in the input directory.")
        return

    failures = 0
    for pdf in pdfs:
        name = os.path.basename(pdf)

        order, why = determine_order(pdf, args)
        print(f"{name}: order='{order}' ({why})")

        out_name = os.path.splitext(name)[0] + f"_{order}_aligned.pdf"
        output = os.path.join(args.output_dir, out_name)
        print(f"Processing: {name} -> {out_name}")

        cmd = build_worker_command(pdf, output, order, args)
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            failures += 1
            print(f"Worker failed for {name} (exit {result.returncode})", file=sys.stderr)

    print("\nBatch processing completed. Review:", args.output_dir)
    if failures:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
