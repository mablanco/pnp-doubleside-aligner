#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_double_with_profile_img.py

Script to crop, align and assemble Print-and-Play card sheet images
(fronts and backs) using a printer calibration profile.

The script:
- computes a relative crop based on a reference image and a reference crop,
- applies the same crop to all pages,
- applies printer back-side corrections (rotation, shifts, flip mode),
- generates an A4 PDF according to the profile.
"""

import os
import json
import cv2
import numpy as np
from PIL import Image
from fpdf import FPDF

# ======== QUICK CONFIGURATION ========
PROFILE_PATH = "profiles/my_calibrated_printer.json"

REF_ORIGINAL = "ref_original.png"   # base screenshot of the current PnP
REF_CROP     = "ref_crop.png"       # correct cropped area from that screenshot

FRONTS = [
    # add your front images here
]

BACKS = [
    # add your back images here (leave empty to duplicate fronts)
]
# ====================================

def load_profile(path):
    """
    Load a printer profile from a JSON file and normalize its fields.
    """
    with open(path, "r", encoding="utf-8") as f:
        prof = json.load(f)

    paper = prof.get("paper", {})
    margins = prof.get("margins", {})
    back = prof.get("back_corrections", {})

    return {
        "paper_w": paper.get("width_mm", 297.0),
        "paper_h": paper.get("height_mm", 210.0),
        "orientation": paper.get("orientation", "landscape"),
        "margin_x": margins.get("x_mm", 0.0),
        "margin_y": margins.get("y_mm", 0.0),
        "flip_mode": prof.get("flip_mode", "long"),
        "rot_deg": back.get("extra_rot_deg", 0.0),
        "shift_x": back.get("shift_x_mm", 0.0),
        "shift_y": back.get("shift_y_mm", 0.0),
    }

def read_bgr(path):
    """
    Read an image using OpenCV (BGR format).
    """
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(path)
    return img

def to_pil(bgr):
    """
    Convert an OpenCV BGR image to a PIL RGB image.
    """
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

def compute_relative_box(ref_original_path, ref_crop_path):
    """
    Compute the relative crop box (left, top, right, bottom) as fractions
    of the original image size, using template matching.
    """
    orig = read_bgr(ref_original_path)
    crop = read_bgr(ref_crop_path)

    H, W = orig.shape[:2]
    h, w = crop.shape[:2]

    scale = 0.5
    orig_s = cv2.resize(orig, (int(W * scale), int(H * scale)), interpolation=cv2.INTER_AREA)
    crop_s = cv2.resize(crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    edges_o = cv2.Canny(cv2.cvtColor(orig_s, cv2.COLOR_BGR2GRAY), 50, 150)
    edges_c = cv2.Canny(cv2.cvtColor(crop_s, cv2.COLOR_BGR2GRAY), 50, 150)

    res = cv2.matchTemplate(edges_o, edges_c, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(res)

    x0_s, y0_s = max_loc
    x0 = int(x0_s / scale)
    y0 = int(y0_s / scale)
    x1 = x0 + w
    y1 = y0 + h

    return x0 / W, y0 / H, (W - x1) / W, (H - y1) / H

def apply_relative_crop(img, rel_box):
    """
    Apply a relative crop box to an image.
    """
    H, W = img.shape[:2]
    l, t, r, b = rel_box

    x0 = int(round(W * l))
    y0 = int(round(H * t))
    x1 = int(round(W * (1 - r)))
    y1 = int(round(H * (1 - b)))

    return img[y0:y1, x0:x1]

def add_to_pdf(pdf, pil_img, page_w_mm, page_h_mm, margin_x_mm, margin_y_mm, shift_x_mm=0.0, shift_y_mm=0.0, rotate180=False):
    """
    Add a PIL image to the PDF, scaled and centered on the page,
    applying optional shifts and a 180-degree rotation.
    """
    _rng = np.random.default_rng(seed=int.from_bytes(os.urandom(8), "little"))
    tmp = f"_tmp_{_rng.integers(1_000_000_000)}.jpg"
    pil_img.save(tmp, "JPEG", quality=95)

    pdf.add_page()

    iw, ih = pil_img.size
    max_w = page_w_mm - 2 * margin_x_mm
    max_h = page_h_mm - 2 * margin_y_mm

    ratio = min(max_w / iw, max_h / ih)
    w, h = iw * ratio, ih * ratio

    x = (page_w_mm - w) / 2 + shift_x_mm
    y = (page_h_mm - h) / 2 + shift_y_mm

    if rotate180:
        pdf.image(
            tmp,
            x=page_w_mm - x - w,
            y=page_h_mm - y - h,
            w=w,
            h=h,
            rotation=180
        )
    else:
        pdf.image(tmp, x=x, y=y, w=w, h=h)

    os.remove(tmp)

def main():
    prof = load_profile(PROFILE_PATH)
    page_w = prof["paper_w"]
    page_h = prof["paper_h"]

    # Enforce landscape if specified by the profile
    if prof["orientation"].lower().startswith("land") and page_w < page_h:
        page_w, page_h = page_h, page_w

    rel_box = compute_relative_box(REF_ORIGINAL, REF_CROP)

    pdf = FPDF(unit="mm", format="A4", orientation="L" if page_w > page_h else "P")
    total = len(FRONTS)

    for i in range(total):
        # Front page
        front = apply_relative_crop(read_bgr(FRONTS[i]), rel_box)
        pil_f = to_pil(front)
        add_to_pdf(pdf, pil_f, page_w, page_h, prof["margin_x"], prof["margin_y"])

        # Back page
        if i < len(BACKS) and os.path.exists(BACKS[i]):
            back = apply_relative_crop(read_bgr(BACKS[i]), rel_box)
        else:
            back = front.copy()

        pil_b = to_pil(back)

        # Fine rotation from printer profile
        rot_deg = prof["rot_deg"]
        if abs(rot_deg) > 1e-3:
            pil_b = pil_b.rotate(rot_deg, resample=Image.BICUBIC, expand=False)

        rotate180 = (prof["flip_mode"].lower() == "short")
        add_to_pdf(
            pdf,
            pil_b,
            page_w,
            page_h,
            prof["margin_x"],
            prof["margin_y"],
            shift_x_mm=prof["shift_x"],
            shift_y_mm=prof["shift_y"],
            rotate180=rotate180
        )

    pdf.output("PnP_FrontBack_Profiled.pdf")
    print("Generated: PnP_FrontBack_Profiled.pdf")

if __name__ == "__main__":
    main()
