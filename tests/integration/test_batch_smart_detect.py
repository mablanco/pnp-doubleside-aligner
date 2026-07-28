"""Integration/CLI: batch --auto-detect-smart enablement and classification."""

from __future__ import annotations

from pathlib import Path


def _copy(src: Path, dest: Path) -> None:
    dest.write_bytes(src.read_bytes())


def test_batch_smart_detect_classifies_fixtures(
    run_batch,
    sample_interleaved: Path,
    sample_fronts_then_backs: Path,
    sample_single: Path,
    sample_odd: Path,
    tmp_path: Path,
):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()

    # Neutral names exercise content / page-count paths (not filename hints)
    _copy(sample_interleaved, in_dir / "cards_inter.pdf")
    _copy(sample_fronts_then_backs, in_dir / "cards_split.pdf")
    _copy(sample_single, in_dir / "one_page.pdf")
    _copy(sample_odd, in_dir / "three_pages.pdf")
    # Name hint should win even if content were halves
    _copy(sample_fronts_then_backs, in_dir / "demo_interleaved.pdf")

    proc = run_batch(
        [
            "--input-dir",
            str(in_dir),
            "--output-dir",
            str(out_dir),
            "--auto-detect-smart",
            "--verbose",
        ]
    )
    combined = (proc.stdout + proc.stderr).lower()
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "unavailable" not in combined
    assert "disabled" not in combined
    assert "nameerror" not in combined
    assert "avg_sim_block" not in combined

    # Per-file status: order= and reason present (T024)
    out = proc.stdout
    assert "cards_inter.pdf: order='interleaved'" in out
    assert "visual:odd-cluster" in out
    assert "cards_split.pdf: order='fronts_then_backs'" in out
    assert "visual:second-half" in out
    assert "one_page.pdf: order='single_sided'" in out
    assert "three_pages.pdf: order='last_back'" in out
    assert "demo_interleaved.pdf: order='interleaved'" in out
    assert "name-hint:interleaved" in out
    for name in (
        "cards_inter.pdf",
        "cards_split.pdf",
        "one_page.pdf",
        "three_pages.pdf",
        "demo_interleaved.pdf",
    ):
        line = next(ln for ln in out.splitlines() if ln.startswith(f"{name}:"))
        assert "order='" in line
        assert "(" in line and ")" in line  # reason in parentheses


def test_batch_smart_detect_ambiguous_even_default(
    run_batch,
    sample_ambiguous_even: Path,
    tmp_path: Path,
):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    _copy(sample_ambiguous_even, in_dir / "mixed_even.pdf")

    proc = run_batch(
        [
            "--input-dir",
            str(in_dir),
            "--output-dir",
            str(out_dir),
            "--auto-detect-smart",
            "--even-default",
            "fronts_then_backs",
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "mixed_even.pdf: order='fronts_then_backs'" in proc.stdout
    assert "visual:tie" in proc.stdout


def test_batch_smart_detect_open_fallback(run_batch, tmp_path: Path):
    in_dir = tmp_path / "in"
    out_dir = tmp_path / "out"
    in_dir.mkdir()
    out_dir.mkdir()
    (in_dir / "bad.pdf").write_bytes(b"%PDF-not-really")

    proc = run_batch(
        [
            "--input-dir",
            str(in_dir),
            "--output-dir",
            str(out_dir),
            "--auto-detect-smart",
            "--even-default",
            "fronts_then_backs",
        ]
    )
    # Detect must not NameError; worker may fail on corrupt PDF
    combined = (proc.stdout + proc.stderr).lower()
    assert "nameerror" not in combined
    assert "avg_sim_block" not in combined
    assert "open-fallback" in proc.stdout
    assert "order='fronts_then_backs'" in proc.stdout
