"""
Missing optional image-tool extras → install hint + non-zero exit.

Maps to FR-001/FR-002/FR-005: main ``requirements.txt`` must not pull
OpenCV/FPDF; ``requirements-img.txt`` is the documented install path;
running the tool without extras yields an actionable stderr hint.
"""

from __future__ import annotations

import builtins
import importlib.util
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT


def _load_img_module(name: str = "pnp_img_tool"):
    script = REPO_ROOT / "tools" / "pnp_double_with_profile_img.py"
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_main_requirements_exclude_img_extras():
    """Static check: main/dev requirements do not declare image-tool-only pkgs."""
    for name in ("requirements.txt", "requirements-dev.txt"):
        text = (REPO_ROOT / name).read_text(encoding="utf-8").lower()
        for needle in ("opencv", "cv2", "fpdf", "numpy"):
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                assert needle not in stripped, (
                    f"{name} must not require {needle!r}; use requirements-img.txt"
                )


def test_requirements_img_exists_and_pins_extras():
    path = REPO_ROOT / "requirements-img.txt"
    assert path.is_file()
    text = path.read_text(encoding="utf-8").lower()
    assert "opencv-python-headless" in text
    assert "numpy" in text
    assert "fpdf2" in text


def test_require_img_dependencies_hint(monkeypatch):
    """Unit-style: ImportError path always mentions requirements-img.txt."""
    mod = _load_img_module("pnp_img_tool_guard")
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name in ("cv2", "numpy", "fpdf") or name.startswith("fpdf."):
            raise ImportError(f"No module named {name!r}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError) as excinfo:
        mod.require_img_dependencies()
    assert "requirements-img.txt" in str(excinfo.value)


def test_cli_missing_deps_message(monkeypatch, tmp_path: Path, capsys):
    """When the guard raises, CLI stderr mentions requirements-img.txt."""
    mod = _load_img_module("pnp_img_tool_cli")

    def boom():
        raise ImportError(mod.IMG_DEPS_HINT)

    monkeypatch.setattr(mod, "require_img_dependencies", boom)

    code = mod.main(
        [
            "--profile",
            str(REPO_ROOT / "profiles" / "example_printer.json"),
            "--ref-original",
            str(tmp_path / "a.png"),
            "--ref-crop",
            str(tmp_path / "b.png"),
            "--front",
            str(tmp_path / "c.png"),
            "--output",
            str(tmp_path / "out.pdf"),
        ]
    )
    assert code != 0
    err = capsys.readouterr().err
    assert "requirements-img.txt" in err
