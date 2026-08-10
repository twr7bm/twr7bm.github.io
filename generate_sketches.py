#!/usr/bin/env python3
"""
Generate the sketch portraits used on the hero photo toggle.

Three deliberately *distinct* looks (Count/Gaussian random sketches are the same
operation and look identical, so only Count is kept as the algorithmic nod):

  count     : randomized count-sketch, reconstructed PIXEL-WISE (whole image
              flattened per channel, not row-by-row). Each pixel hashes to one of
              m buckets with a +/-1 sign; recover per pixel; median-of-k kills the
              heavy-tailed collision noise. Keeps color -> speckled grain.
  halftone  : classic newsprint dot screen (dot area proportional to darkness),
              tinted to the site's paper/ink palette.
  pencil    : color-dodge pencil-sketch (grayscale / blurred-inverse), tinted.
  lowrank   : rank-r truncated SVD per channel -> smooth "compressed" ghost.

Deterministic. Requires numpy + pillow.

    python3 generate_sketches.py
"""
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageOps

SRC   = "img/sketch_original.png"
PAPER = np.array([244, 243, 238], np.float32)   # --paper
INK   = np.array([ 23,  24,  28], np.float32)    # --ink

C_M, C_K, C_SEED = 22000, 9, 7919               # count sketch


def count_sketch(chan, m=C_M, k=C_K, seed=C_SEED):
    N = chan.shape[0]
    rec = np.empty((k, N), np.float32)
    for t in range(k):
        rng = np.random.default_rng(seed + t * 104729)
        h = rng.integers(0, m, N)
        s = rng.integers(0, 2, N).astype(np.float32) * 2 - 1
        y = np.bincount(h, weights=s * chan, minlength=m)
        rec[t] = s * y[h]
    return np.median(rec, axis=0)


def make_count(rgb):
    H, W, _ = rgb.shape
    out = np.empty_like(rgb)
    for c in range(3):
        out[..., c] = count_sketch(rgb[..., c].reshape(-1)).reshape(H, W)
    return np.clip(out, 0, 255).astype(np.uint8)


def tint(gray):                                  # L in [0,255] -> paper..ink
    t = (gray.astype(np.float32) / 255.0)[..., None]
    return np.clip(INK + (PAPER - INK) * t, 0, 255).astype(np.uint8)


def make_halftone(src, cell=5, ss=4):
    # gentle contrast stretch so the portrait reads as dot density
    g = np.asarray(ImageOps.autocontrast(src.convert("L"), cutoff=2), np.float32)
    H, W = g.shape
    big = Image.new("L", (W * ss, H * ss), 255)
    d = ImageDraw.Draw(big)
    for y in range(0, H, cell):
        for x in range(0, W, cell):
            dark = 1 - g[y:y + cell, x:x + cell].mean() / 255
            r = (cell * ss / 2) * np.sqrt(max(dark, 0.0))   # max dot just fills the cell
            cx, cy = (x + cell / 2) * ss, (y + cell / 2) * ss
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=0)
    small = np.asarray(big.resize((W, H), Image.LANCZOS))
    return tint(small)


def make_lowrank(rgb, r=12):
    # keep only the top-r singular values per channel -> smooth, "compressed" ghost
    out = np.empty_like(rgb)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        for c in range(3):
            U, S, Vt = np.linalg.svd(rgb[..., c].astype(np.float64), full_matrices=False)
            out[..., c] = (U[:, :r] * S[:r]) @ Vt[:r]
    return np.clip(out, 0, 255).astype(np.uint8)


def make_pencil(src, sigma=6):
    g = src.convert("L")
    inv = ImageOps.invert(g).filter(ImageFilter.GaussianBlur(sigma))
    gn = np.asarray(g, np.float32)
    bn = np.asarray(inv, np.float32)
    pencil = np.where(bn >= 255, 255.0, np.minimum(255.0, gn * 255.0 / (255.0 - bn + 1e-3)))
    return tint(pencil)


def main():
    src = Image.open(SRC).convert("RGB")
    rgb = np.asarray(src, np.float32)
    print(f"source {SRC}  {src.size[0]}x{src.size[1]}")

    Image.fromarray(make_count(rgb)).save("img/sketch_count.png")
    print("  count    -> img/sketch_count.png")
    Image.fromarray(make_halftone(src)).save("img/sketch_halftone.png")
    print("  halftone -> img/sketch_halftone.png")
    Image.fromarray(make_pencil(src)).save("img/sketch_pencil.png")
    print("  pencil   -> img/sketch_pencil.png")
    Image.fromarray(make_lowrank(rgb)).save("img/sketch_lowrank.png")
    print("  lowrank  -> img/sketch_lowrank.png")


if __name__ == "__main__":
    main()
