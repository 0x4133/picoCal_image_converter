#!/usr/bin/env python3
"""
image_to_mmbasic_pairle.py
Compact "pair-RLE" encoder for MMBasic with no files on disk.

Format emitted into DATA:
- First: palette size P, then P triples of r,g,b
- Then for each row y = 0..H-1:
    DATA nPairs, len1, col1, len2, col2, ..., lenN, colN
- After last row, a terminator DATA of just -1

Decoder emitted in BASIC:
- Builds pal%(i) = RGB(r,g,b)
- For y from 0..H-1:
    READ n : IF n=-1 THEN EXIT DO
    x=0
    FOR k=1 TO n
       READ l,c : LINE x,y,x+l-1,y, , pal%(c) : x=x+l
    NEXT
This avoids storing xStart and y for every run, cutting DATA roughly in half.
"""

from PIL import Image
import argparse

def quantize_image(img, n_colors, dither):
    if n_colors <= 0: return img.convert("RGB")
    dither_flag = Image.FLOYDSTEINBERG if dither else Image.NONE
    q = img.convert("RGB").quantize(colors=n_colors, method=Image.MEDIANCUT, dither=dither_flag)
    return q.convert("RGB")

def letterbox(img, tw, th, bg=(0,0,0)):
    sw, sh = img.size
    scale = min(tw/sw, th/sh)
    nw, nh = max(1, int(round(sw*scale))), max(1, int(round(sh*scale)))
    c = Image.new("RGB", (tw, th), bg)
    c.paste(img.resize((nw, nh), Image.LANCZOS), ((tw-nw)//2, (th-nh)//2))
    return c

def solid_resize(img, tw, th):
    return img.resize((tw, th), Image.LANCZOS)

def build_palette(img):
    pal = []
    idx = {}
    px = img.load()
    w,h = img.size
    for y in range(h):
        for x in range(w):
            c = px[x,y][:3]
            if c not in idx:
                idx[c] = len(pal); pal.append(c)
    return pal, idx

def row_pairs(img, idxmap):
    """Return list of rows; each row is [(len, colorIdx), ...] starting at x=0."""
    rows = []
    px = img.load()
    w,h = img.size
    for y in range(h):
        x = 0
        pairs = []
        while x < w:
            c = px[x,y][:3]
            ci = idxmap[c]
            x0 = x; x += 1
            while x < w and px[x,y][:3] == c: x += 1
            pairs.append((x - x0, ci))
        rows.append(pairs)
    return rows

def chunked(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i+n]

def emit_bas(img, pal, rows, title, author):
    w,h = img.size
    L = []
    L.append(f"REM {title}" if title else "REM Image via Pair-RLE")
    if author: L.append(f"REM Author: {author}")
    L += ["OPTION EXPLICIT","CLS RGB(0,0,0)","SUB DrawImage()",
          f"  CONST W={w}, H={h}",
          "  DIM pal%(255)",
          "  LOCAL i, r, g, b, y, x, n, k, l, c",
          "  READ i : IF i <> " + str(len(pal)) + " THEN PRINT \"Bad palette\" : END",
          "  FOR i=0 TO " + str(len(pal)-1),
          "    READ r,g,b : pal%(i)=RGB(r,g,b)",
          "  NEXT",
          "  FOR y=0 TO H-1",
          "    READ n : IF n=-1 THEN EXIT FOR",
          "    x=0",
          "    FOR k=1 TO n",
          "      READ l,c",
          "      LINE x,y,x+l-1,y, , pal%(c)",
          "      x=x+l",
          "    NEXT k",
          "  NEXT y",
          "END SUB",
          "DrawImage"]
    # Palette
    L.append(f"DATA {len(pal)}")
    pvals = []
    for r,g,b in pal: pvals += [r,g,b]
    for ch in chunked(pvals, 24): L.append("DATA " + ",".join(map(str, ch)))
    # Rows
    for pairs in rows:
        flat = [len(pairs)]
        for l,c in pairs: flat += [l,c]
        for ch in chunked(flat, 32):
            L.append("DATA " + ",".join(map(str, ch)))
    # Terminator
    L.append("DATA -1")
    return "\n".join(L) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_image")
    ap.add_argument("output_bas")
    ap.add_argument("--width", type=int, default=0)
    ap.add_argument("--height", type=int, default=0)
    ap.add_argument("--keep-aspect", type=int, default=1)
    ap.add_argument("--bg", type=str, default="0,0,0")
    ap.add_argument("--quantize", type=int, default=48)  # slightly lower default to save more space
    ap.add_argument("--dither", type=int, default=1)
    ap.add_argument("--title", type=str, default="Image Pair-RLE")
    ap.add_argument("--author", type=str, default="")
    args = ap.parse_args()

    img = Image.open(args.input_image).convert("RGB")
    sw,sh = img.size
    tw = args.width if args.width>0 else sw
    th = args.height if args.height>0 else sh
    bg = tuple(map(int, args.bg.split(",")))
    if (tw,th)!=(sw,sh): img = letterbox(img, tw, th, bg) if args.keep_aspect else solid_resize(img, tw, th)
    img = quantize_image(img, args.quantize, bool(args.dither))
    pal, idx = build_palette(img)
    rows = row_pairs(img, idx)
    out = emit_bas(img, pal, rows, args.title, args.author)
    from pathlib import Path
    Path(args.output_bas).write_text(out, encoding="utf-8")
    print("Wrote", args.output_bas, "size", img.size, "palette", len(pal))

if __name__ == "__main__":
    main()
