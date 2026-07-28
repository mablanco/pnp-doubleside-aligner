# Image-tool fixtures

Tiny deterministic PNGs for the experimental image PnP tool smoke tests
(`tools/pnp_double_with_profile_img.py`).

| File | Role |
|------|------|
| `ref_original.png` | Full reference screenshot (200×200) |
| `ref_crop.png` | Crop patch cut from `ref_original` (must match via OpenCV template match) |
| `front0.png` | Sample front page (same geometry as reference) |
| `back0.png` | Sample back page (same geometry; distinct corner mark) |

Regenerate only if intentional fixture change is required:

```bash
python - <<'PY'
# See repo history / implement script that wrote these assets.
PY
```

These fixtures are **optional-path** inputs: default CI does not require
OpenCV; marked `@pytest.mark.img` tests skip when extras are absent.
