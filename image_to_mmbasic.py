#!/usr/bin/env python3
"""
image_to_mmbasic.py  (fixed)
Converts an input image into MMBasic code that draws it using horizontal
run-length encoded LINE segments. Correctly skips the LW parameter:
  LINE x1,y,x2,y, , RGB(r,g,b)
"""

from PIL import Image
from pathlib import Path
import argparse
from typing import Tuple, List

def parse_rgb(csv: str):
    parts = [p.strip() for p in csv.split(",")]
    if len(parts) != 3:
        raise ValueError("RGB must be R,G,B")
    r,g,b = map(int, parts)
    for v in (r,g,b):
        if not (0 <= v <= 255):
            raise ValueError("RGB components must be 0..255")
    return r,g,b

def letterbox(img: Image.Image, target_w: int, target_h: int, bg):
    sw, sh = img.size
    scale = min(target_w / sw, target_h / sh)
    nw, nh = max(1, int(round(sw * scale))), max(1, int(round(sh * scale)))
    resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg)
    ox, oy = (target_w - nw)//2, (target_h - nh)//2
    canvas.paste(resized, (ox, oy))
    return canvas

def solid_resize(img: Image.Image, target_w: int, target_h: int):
    return img.resize((target_w, target_h), Image.LANCZOS)

def quantize_image(img: Image.Image, n_colors: int, dither: bool):
    if n_colors <= 0:
        return img
    dither_flag = Image.FLOYDSTEINBERG if dither else Image.NONE
    q = img.convert("RGB").quantize(colors=n_colors, method=Image.MEDIANCUT, dither=dither_flag)
    return q.convert("RGB")

def emit_mmbasic_header(title: str, author: str):
    lines = []
    lines.append(f"REM {title}" if title else "REM Image draw program")
    if author:
        lines.append(f"REM Author: {author}")
    lines.append("OPTION EXPLICIT")
    lines.append("CLS RGB(0,0,0)")
    lines.append("SUB DrawImage()")
    return lines

def emit_mmbasic_footer(call_sub: bool):
    lines = ["END SUB"]
    if call_sub:
        lines.append("DrawImage")
    return lines

def image_to_rle_lines(img: Image.Image, offx: int, offy: int, comment_rate: int = 20):
    w, h = img.size
    px = img.load()
    out = []
    for y in range(h):
        if comment_rate > 0 and (y % comment_rate == 0):
            out.append(f"REM Row {y}")
        x = 0
        while x < w:
            sx = x
            r,g,b = px[x, y][:3] if isinstance(px[x,y], tuple) else (0,0,0)
            x += 1
            while x < w:
                c2 = px[x, y]
                if isinstance(c2, tuple) and c2[:3] == (r,g,b):
                    x += 1
                else:
                    break
            ex = x - 1
            X1, X2, Y = sx + offx, ex + offx, y + offy
            out.append(f"  LINE {X1},{Y},{X2},{Y}, , RGB({r},{g},{b})")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_image")
    ap.add_argument("output_bas")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--keep-aspect", type=int, default=1)
    ap.add_argument("--bg", type=str, default="0,0,0")
    ap.add_argument("--quantize", type=int, default=0)
    ap.add_argument("--dither", type=int, default=0)
    ap.add_argument("--offset-x", type=int, default=0)
    ap.add_argument("--offset-y", type=int, default=0)
    ap.add_argument("--title", type=str, default="Image Draw")
    ap.add_argument("--author", type=str, default="")
    ap.add_argument("--comment-rate", type=int, default=20)
    ap.add_argument("--no-header", action="store_true")
    ap.add_argument("--call-sub", type=int, default=1)
    args = ap.parse_args()

    img = Image.open(args.input_image).convert("RGB")
    sw, sh = img.size
    tw = args.width if args.width > 0 else sw
    th = args.height if args.height > 0 else sh
    bg = parse_rgb(args.bg)

    if (tw, th) != (sw, sh):
        img = letterbox(img, tw, th, bg) if args.keep_aspect else solid_resize(img, tw, th)

    img = quantize_image(img, args.quantize, bool(args.dither))

    lines = []
    if not args.no_header:
        lines += emit_mmbasic_header(args.title, args.author)
    lines += image_to_rle_lines(img, args.offset_x, args.offset_y, args.comment_rate)
    if not args.no_header:
        lines += emit_mmbasic_footer(bool(args.call_sub))

    Path(args.output_bas).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote", args.output_bas, "size", img.size)

if __name__ == "__main__":
    main()
