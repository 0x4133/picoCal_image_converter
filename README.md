Here’s a clean, drop-in **README.md** for your script. It’s practical, future-proofed, and won’t make your repo look like a cry for help.

---

# image_to_mmbasic.py

Converts an input image into **MMBasic** code that recreates the image using horizontal run-length encoded `LINE` segments.
The generator intentionally skips the optional **line width** parameter, emitting the correct MMBasic form:

```
LINE x1,y, x2,y, , RGB(r,g,b)
```

This avoids the common “invalid parameter” errors caused by accidentally passing color where MMBasic expects a width.

## Features

* **RLE by row:** Packs consecutive same-color pixels into one horizontal `LINE`.
* **Aspect-aware resizing:** Letterbox to fit a target size without distortion, or force a solid resize.
* **Palette reduction:** Optional color quantization with optional dithering to drastically shrink output size.
* **Offsets:** Draw anywhere on screen with `--offset-x` and `--offset-y`.
* **Header/subroutine:** Emits a minimal program wrapper with `SUB DrawImage()` and an optional call.
* **Readable output:** Periodic `REM Row N` comments for debugging and chunking.

---

## Requirements

* Python 3.8+
* [Pillow](https://python-pillow.org/) (PIL fork)

Install:

```bash
python -m pip install pillow
```

---

## Usage

```bash
./image_to_mmbasic.py INPUT_IMAGE OUTPUT.bas [options]
```

### Options

| Option                |      Default | Description                                                  |
| --------------------- | -----------: | ------------------------------------------------------------ |
| `--width INT`         |          `0` | Target width. `0` keeps source width.                        |
| `--height INT`        |          `0` | Target height. `0` keeps source height.                      |
| `--keep-aspect {0,1}` |          `1` | `1` letterboxes to preserve aspect; `0` does a solid resize. |
| `--bg "R,G,B"`        |      `0,0,0` | Letterbox background color.                                  |
| `--quantize INT`      |          `0` | Limit palette to N colors; `0` disables quantization.        |
| `--dither {0,1}`      |          `0` | Floyd–Steinberg dithering when quantizing.                   |
| `--offset-x INT`      |          `0` | X offset for all segments.                                   |
| `--offset-y INT`      |          `0` | Y offset for all segments.                                   |
| `--title STR`         | `Image Draw` | REM title in header.                                         |
| `--author STR`        |         `""` | REM author in header.                                        |
| `--comment-rate INT`  |         `20` | Insert `REM Row N` every N rows; `0` disables.               |
| `--no-header`         |          off | Don’t emit `OPTION EXPLICIT`, `CLS`, and `SUB` wrappers.     |
| `--call-sub {0,1}`    |          `1` | Append `DrawImage` call after the `SUB` definition.          |

---

## Examples

### 1) Quick start, no scaling

```bash
./image_to_mmbasic.py input.png output.bas
```

### 2) Fit into 320×240 with letterbox and reduced palette

```bash
./image_to_mmbasic.py input.jpg out.bas \
  --width 320 --height 240 --keep-aspect 1 --bg "0,0,0" \
  --quantize 32 --dither 1
```

### 3) Force resize, draw at (10,20), no header

```bash
./image_to_mmbasic.py input.bmp out.bas \
  --width 480 --height 272 --keep-aspect 0 \
  --offset-x 10 --offset-y 20 \
  --no-header
```

---

## What the output looks like

Header (unless `--no-header`):

```basic
REM Image Draw
OPTION EXPLICIT
CLS RGB(0,0,0)
SUB DrawImage()
```

Body (excerpt):

```basic
REM Row 0
  LINE 0,0, 23,0, , RGB(34,177,76)
  LINE 24,0, 31,0, , RGB(0,0,0)
REM Row 1
  LINE 0,1, 31,1, , RGB(34,177,76)
' ...
```

Footer:

```basic
END SUB
DrawImage
```

> Note the intentional blank argument before `RGB(...)` to skip line width.

---

## Device/display notes

* **Coordinate limits:** Make sure your image size plus offsets stays inside your device’s drawable range. If your firmware complains about values outside a valid range, **reduce `--width/--height`** or adjust offsets.
* **Performance vs quality:** More colors produce more segments and larger `.bas` files. Use `--quantize` (and optionally `--dither 0`) to shrink output and speed up drawing.
* **Integer math:** All coordinates are emitted as integers. Colors are in `RGB(0..255, 0..255, 0..255)`.

---

## Tips for smaller, faster programs

* Try `--quantize 16` or `--quantize 32` with `--dither 0` to reduce the number of distinct runs.
* Keep `--comment-rate` higher (or `0` to disable) to shave a few kilobytes.
* Prefer letterboxing (`--keep-aspect 1`) to avoid resampling noise that creates extra color runs.

---

## Troubleshooting

* **“Invalid parameter range” or coordinates out of bounds:**
  Your target display or MMBasic environment has tighter limits. Lower `--width/--height`, adjust offsets, or pre-scale the source.

* **Program too large or slow to render:**
  Increase `--quantize`, disable `--dither`, reduce dimensions, or crop the source image.

* **Color banding after quantization:**
  Re-enable dithering with `--dither 1`, or increase `--quantize`.

---

## Internals (for contributors)

* **RLE pass:** Adjacent same-color pixels per row are merged into one `LINE`.
* **Resizing:**

  * `letterbox(...)` preserves aspect with background fill.
  * `solid_resize(...)` forces exact W×H.
* **Quantization:** Uses Pillow’s `MEDIANCUT` with optional Floyd–Steinberg dithering.

Key functions:

* `image_to_rle_lines(img, offx, offy, comment_rate)`
* `quantize_image(img, n_colors, dither)`
* `letterbox(...)` / `solid_resize(...)`
* `emit_mmbasic_header(...)` / `emit_mmbasic_footer(...)`

---

## Roadmap

* Optional palette extraction + color remap table for deterministic outputs.
* Vertical or block RLE to further reduce statements on some images.
* Binary packer that emits compressed data + MMBasic decompressor.
* Region tiling with dedupe for repeated textures/icons.

---

## License

MIT. Do whatever, don’t blame the author when you turn a 4K photo into a 9-MB BASIC file and your device cries.
