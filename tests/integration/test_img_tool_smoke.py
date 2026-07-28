"""Happy-path smoke for the experimental image tool (optional OpenCV/FPDF)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("cv2")
pytest.importorskip("fpdf")


@pytest.mark.img
def test_img_tool_smoke(
    run_img_cli,
    img_fixtures_dir: Path,
    repo_root: Path,
    tmp_output: Path,
):
    out = tmp_output / "pnp_img_out.pdf"
    proc = run_img_cli(
        [
            "--profile",
            str(repo_root / "profiles" / "example_printer.json"),
            "--ref-original",
            str(img_fixtures_dir / "ref_original.png"),
            "--ref-crop",
            str(img_fixtures_dir / "ref_crop.png"),
            "--front",
            str(img_fixtures_dir / "front0.png"),
            "--back",
            str(img_fixtures_dir / "back0.png"),
            "--output",
            str(out),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    assert out.is_file()
    assert "Generated" in proc.stdout


@pytest.mark.img
def test_fronts_do_not_receive_back_corrections(
    run_img_cli,
    img_fixtures_dir: Path,
    fixtures_dir: Path,
    tmp_output: Path,
):
    """
    Behavioral: with non-zero back corrections, front page content position
    matches an identity (zero-correction) run's front page; backs differ.
    """
    import fitz

    profile = fixtures_dir / "profile_nonzero.json"
    out_corrected = tmp_output / "corrected.pdf"
    out_identity = tmp_output / "identity.pdf"

    common = [
        "--ref-original",
        str(img_fixtures_dir / "ref_original.png"),
        "--ref-crop",
        str(img_fixtures_dir / "ref_crop.png"),
        "--front",
        str(img_fixtures_dir / "front0.png"),
        "--back",
        str(img_fixtures_dir / "back0.png"),
    ]

    # Identity profile: write a temp zero-correction profile
    identity_prof = tmp_output / "identity_profile.json"
    identity_prof.write_text(
        '{"paper":{"width_mm":210,"height_mm":297,"orientation":"portrait"},'
        '"margins":{"x_mm":0,"y_mm":0},"flip_mode":"long",'
        '"back_corrections":{"extra_rot_deg":0,"shift_x_mm":0,"shift_y_mm":0}}',
        encoding="utf-8",
    )

    proc_id = run_img_cli(
        ["--profile", str(identity_prof), *common, "--output", str(out_identity)]
    )
    proc_c = run_img_cli(
        ["--profile", str(profile), *common, "--output", str(out_corrected)]
    )
    assert proc_id.returncode == 0, proc_id.stderr
    assert proc_c.returncode == 0, proc_c.stderr

    doc_id = fitz.open(out_identity)
    doc_c = fitz.open(out_corrected)
    assert doc_id.page_count == 2
    assert doc_c.page_count == 2

    # Front pages (index 0): pixmap should match (no back corrections on fronts).
    pix_id_f = doc_id.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1))
    pix_c_f = doc_c.load_page(0).get_pixmap(matrix=fitz.Matrix(1, 1))
    assert pix_id_f.tobytes() == pix_c_f.tobytes()

    # Back pages (index 1): should differ when profile has non-zero corrections.
    pix_id_b = doc_id.load_page(1).get_pixmap(matrix=fitz.Matrix(1, 1))
    pix_c_b = doc_c.load_page(1).get_pixmap(matrix=fitz.Matrix(1, 1))
    assert pix_id_b.tobytes() != pix_c_b.tobytes()
