"""Unit tests for raster sign helpers (PIL negate; ReportLab +Y-down)."""

from unittest.mock import MagicMock

from PIL import Image

from pnp_double_with_profile_pdf import (
    apply_back_transform_raster,
    draw_image_on_canvas,
    mm_to_pt,
)


def test_raster_positive_rot_negates_for_pil_clockwise(monkeypatch):
    """PIL rotate is CCW; contract +rot clockwise → pass -angle to Image.rotate."""
    img = Image.new("RGB", (10, 10), "white")
    seen = {}

    def fake_rotate(self, angle, resample=None, expand=False):
        seen["angle"] = angle
        return self

    monkeypatch.setattr(Image.Image, "rotate", fake_rotate)
    apply_back_transform_raster(img, 3.5, False)
    assert seen["angle"] == -3.5


def test_raster_y_down_uses_negative_reportlab_y(monkeypatch):
    """ReportLab origin is bottom-left; +Y down → draw at -shift_y_pt."""
    img = Image.new("RGB", (20, 20), "white")
    rect = MagicMock()
    rect.width = 100.0
    rect.height = 200.0

    canv = MagicMock()
    canv.getPageNumber.return_value = 0
    captured = {}

    def fake_drawImage(ir, x, y, width=None, height=None, preserveAspectRatio=False, mask=None):
        captured["x"] = x
        captured["y"] = y

    canv.drawImage = fake_drawImage
    shift_y = mm_to_pt(4.0)
    # Caller may pass already-converted canvas Y; helper must convert +Y-down.
    draw_image_on_canvas(
        canv,
        img,
        rect,
        shift_x_pt=1.0,
        shift_y_pt=shift_y,
        jpeg_quality=85,
    )
    assert captured["x"] == 1.0
    assert abs(captured["y"] - (-shift_y)) < 1e-9
