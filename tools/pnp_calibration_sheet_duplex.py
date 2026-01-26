#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pnp_calibration_sheet_duplex.py

Script to generate Print-and-Play calibration sheets for duplex printing.
"""

# Front pages are printed in black; Back_long and Back_short are printed in red
# to clearly distinguish them during calibration.
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black, Color

W, H = landscape(A4)

# Red color for back pages (adjust if a stronger tone is preferred)
BACK_RED = Color(1, 0, 0)

def draw_cross(c, x, y, size=8):
    c.line(x - size, y, x + size, y)
    c.line(x, y - size, x, y + size)

def draw_labels(c, title, flip_hint):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, H - 30, title)
    c.setFont("Helvetica", 10)
    c.drawString(40, H - 45, flip_hint)

def draw_feed_guides(c, top=True):
    c.setFont("Helvetica-Bold", 12)
    if top:
        c.drawString(W / 2 - 18, H - 20, "TOP")
        c.drawString(20, H / 2, "FEED EDGE →")
        c.drawString(W - 120, H / 2, "← FEED EDGE")
    else:
        c.drawString(W / 2 - 18, 10, "TOP")
        c.drawString(20, H / 2, "FEED EDGE →")
        c.drawString(W - 120, H / 2, "← FEED EDGE")

def draw_registration(c, margin=15, stroke_color=black):
    c.setStrokeColor(stroke_color)
    c.setFillColor(stroke_color)
    c.setLineWidth(0.9)
    pts = [
        (margin, margin),
        (W - margin, margin),
        (margin, H - margin),
        (W - margin, H - margin),
        (W / 2, H / 2),
    ]
    for (x, y) in pts:
        draw_cross(c, x, y, size=8)

def make_front():
    c = canvas.Canvas("PnP_Calibration_Front.pdf", pagesize=(W, H))
    c.setStrokeColor(black)
    c.setFillColor(black)
    draw_labels(
        c,
        "PnP Calibration FRONT (double-sided print)",
        "Side A (front) printed in BLACK."
    )
    draw_feed_guides(c, top=True)
    draw_registration(c, margin=15, stroke_color=black)
    c.showPage()
    c.save()
    print("PnP_Calibration_Front.pdf generated.")

def make_back_long():
    # Back page for long-edge flipping: same orientation as the front.
    c = canvas.Canvas("PnP_Calibration_Back_long.pdf", pagesize=(W, H))
    c.setStrokeColor(BACK_RED)
    c.setFillColor(BACK_RED)
    draw_labels(
        c,
        "PnP Calibration BACK (Flip: LONG edge)",
        "Side B (back) printed in RED — flip on the long edge."
    )
    draw_feed_guides(c, top=True)
    draw_registration(c, margin=15, stroke_color=BACK_RED)
    c.showPage()
    c.save()
    print("PnP_Calibration_Back_long.pdf generated.")

def make_back_short():
    # Back page for short-edge flipping: content rotated 180 degrees
    # relative to the front.
    c = canvas.Canvas("PnP_Calibration_Back_short.pdf", pagesize=(W, H))
    c.translate(W, H)
    c.rotate(180)  # rotate the entire canvas
    c.setStrokeColor(BACK_RED)
    c.setFillColor(BACK_RED)
    draw_labels(
        c,
        "PnP Calibration BACK (Flip: SHORT edge)",
        "Side B (back) printed in RED — flip on the short edge."
    )
    draw_feed_guides(c, top=True)
    draw_registration(c, margin=15, stroke_color=BACK_RED)
    c.showPage()
    c.save()
    print("PnP_Calibration_Back_short.pdf generated.")

if __name__ == "__main__":
    make_front()
    make_back_long()
    make_back_short()
    print("\nPrint the FRONT page first, then either BACK_long or BACK_short depending on your flip mode.")
    print("If you do not have automatic duplex printing, reinsert the same sheet following the TOP and FEED EDGE markers.")
