# Research: Direct-Read Duplex Calibration

## R1. Measurement viewpoint vs correction space

- **Decision**: Readings are taken from the front, through the paper. The aligner
  corrects in back-page coordinates. Backs in PnP files are mirrored in X
  (long-edge flip in portrait, short-edge flip in landscape), so a front-view
  offset `(tx, ty)` and clockwise rotation `φ` map to
  `shift_x_mm = tx`, `shift_y_mm = −ty`, `extra_rot_deg = φ`.
- **Rationale**: Mirroring X flips the sign of X and the sense of rotation;
  the aligner contract (+X right, +Y down, +rot clockwise in the back page)
  then needs the opposite of the back-page error: `−(−tx) = tx`, `−ty`,
  `−(−φ) = φ`.
- **Second order**: the printer also rotates the correcting shift, so the
  shift is counter-rotated: `s = −R(−φ)·t` in the front view before mirroring.
  Negligible for typical skews (<0.01 mm at 0.2°), 0.1 mm at 1° and 5 mm.
- **Verification**: Raster simulation of a duplex print (mirror + known error)
  and the geometric test in `tests/unit/test_calibration.py`.

## R2. Rotation estimate

- **Decision**: Least-squares fit of `d(P) = φ·J(P − c) + t`, with
  `J(x, y) = (−y, x)` (clockwise for Y down) and `c` the page centre.
- **Rationale**: The old formula only captured shear; a pure rotation gave 0°.
  Least squares uses every reading and yields per-point residuals to flag
  reading mistakes.

## R3. Sheet design

- Front: thick crosses (1 pt) at 25 mm from each edge and at the centre.
- Back: thin scales (0.3 pt), ±6 mm, ticks every 0.5 mm, labels every 2 mm,
  8 mm away from the cross so the two scales never overlap, labelled with the
  negated offset so the reading equals the back displacement.
- Orientation witness ("TOP") on the back: upside down through the paper means
  the wrong flip mode was chosen.
- Black only (no colour toner needed).

## R4. `flip_mode` in generated profiles

- **Decision**: Always `"long"`.
- **Rationale**: In the aligner, `flip_mode` only decides whether backs are
  rotated 180° (`short`). Both sheets (and typical PnP files) have backs
  mirrored in X, which must not be rotated. The print dialog setting
  (long edge for portrait, short edge for landscape) is documented separately.

## R5. Driver scaling (observed with KDE/Okular, generalised in the guide)

- "No scaling" offset the page by the declared 4.23 mm margin to the right and
  down, clipping ~8.5 mm on two edges and adding ~8.5 mm of relative X offset
  between faces.
- "Fit to printable area" scaled the page by ~4 %.
- "Fit to full page" printed an A4 PDF at 100 % with no offset.
- The margin test page detects all three cases.
