# Printer Calibration Guide

This guide explains how to calibrate your printer so that front and back pages
align correctly when printing Print-and-Play (PnP) PDFs double-sided.

Real duplex printers introduce small but consistent errors: rotation (skew)
and a horizontal / vertical shift of the back. They are mechanical and
repeatable, so you measure them once per printer configuration, store them in
a profile and reuse it for every compatible PnP.

You need three prints in total:

1. **Margin test** – find print settings that print at 100 % with no offset.
2. **Calibration sheet** – read the back offsets and generate the profile.
3. **Verification** – the same sheet run through the aligner; refine if needed.

All commands run from the repository root. Generated PDFs
(`calibration_*.pdf`) and personal profiles (`profiles/*`) are gitignored.

## Step 1: Check the print settings (margin test)

The aligner can only correct the printer. If the print dialog scales the page
or shifts it, every calibration is wrong. Generate the margin test page:

```bash
python tools/pnp_margin_test_page.py --paper a4      # or --paper letter
```

Print it **double-sided** with the settings you plan to use for PnPs (printer,
tray, paper type and weight). Each edge has three rulers that start exactly at
the paper edge: the first visible tick is how many millimetres that edge does
not print. Then check:

- **Reference lines**: they must measure exactly 150 mm and 200 mm. Otherwise
  the dialog is scaling the page.
- **Opposite edges**: they should lose about the same (a few mm, the printer's
  non-printable margin). If one edge prints from 0 and the opposite loses
  twice the usual margin, the dialog is **shifting** the page.

Try the scaling options of your print dialog until both checks pass, and use
that option for every PnP from then on. Example (KDE / Okular, A4 laser):

| Option | Result |
|---|---|
| Fit to printable area | page scaled by ~4 % (cards come out smaller) |
| None / original size | page shifted 4.23 mm right and down (the declared margin): ~8.5 mm clipped on two edges and ~8.5 mm of extra front/back offset |
| Fit to full page | 100 %, no shift ✔ |

Other viewers and drivers name these options differently ("Actual size",
"100 %", "Fit"…): the margin test tells you which one is right.

Also note the real non-printable margin: important PnP content (cut lines,
card edges) must stay inside it.

## Step 2: Calibrate

### 2.1 Generate the sheet

```bash
python tools/pnp_calibration_sheet_duplex.py --orientation portrait --paper a4
python tools/pnp_calibration_sheet_duplex.py --orientation landscape --paper a4
```

Calibrate each orientation you print in: one profile per printer
configuration, and portrait and landscape are different configurations.

### 2.2 Print it

- Double-sided with the settings from step 1, **without** running the aligner.
- **Portrait: flip on the long edge. Landscape: flip on the short edge.** The
  sheet's backs are mirrored left-to-right, like the backs of typical PnP files.

### 2.3 Read it

Hold the sheet against a window or a lamp and look **from the front side**
(the one with the thick crosses `TL`, `TR`, `BL`, `BR`, `C`). Next to each
cross you see two thin scales printed on the back:

- **dx**: the number on the horizontal scale crossed by the thick vertical line.
- **dy**: the number on the vertical scale crossed by the thick horizontal line.

Those numbers are directly the offset of the back in millimetres
(dx > 0: back to the right, dy > 0: back lower). Halves are fine (0.5, -1.5).
If the word **TOP** printed on the back reads upside down, the duplex flip mode
is wrong: change it and print again.

### 2.4 Generate the profile

```bash
python tools/pnp_calibration_solver.py \
  --orientation portrait --paper a4 \
  --top-left 0.5 0.5 --top-right 1 0 \
  --bottom-left 1 0.5 --bottom-right 1.5 0 \
  --center 1 0 \
  --output profiles/my_printer_A4_portrait.json
```

The solver fits a rotation and a shift to all readings (least squares) and
prints the fit residual of each point. A warning means one reading does not fit
the others: check it on the sheet. It never overwrites an existing file unless
you pass `--force`; `--output -` prints the JSON instead.

How the readings become corrections: you read from the front, but the aligner
corrects the back page, which is mirrored left-to-right. The rotation and the X
shift keep their sign as corrections and the Y shift is negated (the shift is
also counter-rotated, which only matters for large skews). You never have to
apply these sign rules by hand.

## Step 3: Verify and refine

Run the aligner on the calibration sheet with the new profile and print the
result exactly as in step 2:

```bash
python pnp_double_with_profile_pdf.py \
  --input calibration_sheet_portrait_a4.pdf \
  --output calibration_sheet_portrait_a4_verify.pdf \
  --profile profiles/my_printer_A4_portrait.json --order interleaved
```

Read it the same way. Readings of 0 or ±0.5 mm are as good as it gets (sheet
to sheet variation and reading precision). If there is a consistent residual
(for example every dx is +0.5), add it to the profile:

```bash
python tools/pnp_calibration_solver.py \
  --orientation portrait --paper a4 \
  --top-left 0.5 0 --top-right 0.5 0 \
  --bottom-left 0.5 0 --bottom-right 0.5 0 \
  --refine profiles/my_printer_A4_portrait.json \
  --output profiles/my_printer_A4_portrait.json --force
```

`--refine` keeps every field of the profile and adds the residual correction
to `back_corrections`. Do not chase isolated ±0.5 mm readings: they are noise.

## Step 4 (optional): Scale differences between front and back

With manual duplex on a laser printer, the sheet goes through the fuser for the
front, loses moisture and shrinks slightly, mostly across the grain. The back
is then printed at nominal size on a smaller sheet, so it comes out slightly
larger than the front (typically 0.2–0.5 %). Rotation and shift cannot fix
it: on a card grid the outermost column on one side matches and the error
grows towards the other side (about 0.8 mm across A4 for 0.4 %).

To check, print a page with outlines only (for example card cut lines on both
sides) through the aligner and compare the edges against the light: a constant
offset is a shift, an offset that grows across the page is a scale.

To correct it, add `--fit-scale` to the solver (on the calibration readings or,
with `--refine`, on the verification readings):

```bash
python tools/pnp_calibration_solver.py --fit-scale \
  --top-left -0.4 0 --top-right 0.4 0 \
  --bottom-left -0.4 0 --bottom-right 0.4 0 \
  --refine profiles/my_printer_A4_portrait.json \
  --output profiles/my_printer_A4_portrait.json --force
```

The profile gets `scale_x` / `scale_y` factors (0.996 shrinks the back by
0.4 %) applied about the page centre, after the rotation and before the shift.
You can also try a value directly with `--scalex 0.996` on the aligner. The
calibration sheet reads in 0.5 mm steps over 160 mm, so only trust scales above
~0.3 %; smaller ones are within reading noise. Letting the sheets rest a few
minutes before feeding them back usually reduces the effect.

## Printing PnPs with the profile

```bash
python pnp_double_with_profile_pdf.py \
  --input game.pdf --output game_aligned.pdf \
  --profile profiles/my_printer_A4_portrait.json
```

Print the aligned PDF with the same settings as the calibration (scaling
option from step 1, same flip edge for the orientation).

## About `flip_mode`

In the profile, `flip_mode` does not describe the print dialog option. It only
tells the aligner whether to rotate the backs 180° (`short`) or not (`long`).
PnP files whose backs are mirrored left-to-right (the usual layout, and the
calibration sheet's) need `long` in both orientations, which is what the
solver writes. Use `short` only for files whose backs are mirrored
top-to-bottom instead: rotating them 180° turns that layout into the
left-to-right one the calibration assumes.

## Recalibrate when you change

- printer, tray, paper type or weight
- print-dialog scaling option or duplex settings
- orientation (keep one profile per orientation)

## Without automatic duplex

Print the front, put the sheet back in the tray so that the back prints on the
other side flipped as described above, and print the back. The calibration
then captures your manual feeding; keep the same procedure for your PnPs.
