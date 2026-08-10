#!/usr/bin/env python3
"""
Regenerate the Count and Gaussian sketch portraits — PIXEL-WISE.

The previous version sketched each image *row* as an independent 1-D vector
(m=80 out of 220), which produced strong horizontal banding. This version
treats the whole image as one flattened pixel vector per color channel, so the
reconstruction error is spread as uniform grain instead of streaks.

  Gaussian sketch  : y = S x,  x_hat = S^T y,  averaged over k copies.
                     S has i.i.d. +/-1 entries (Achlioptas' database-friendly
                     random projection — a sub-Gaussian JL sketch that is
                     visually identical to a true Gaussian one but ~40x faster
                     to sample). Recovery is unbiased since E[S^T S] = m*I.
  Count sketch     : each pixel hashes to one of m buckets with a +/-1 sign;
                     recover per pixel, take the MEDIAN over k copies to kill
                     the heavy-tailed collision noise.

Deterministic: fixed seeds, so results are reproducible on every run.

    python3 generate_sketches.py
"""
import numpy as np
from PIL import Image

SRC        = "img/sketch_original.png"
OUT_COUNT  = "img/sketch_count.png"
OUT_GAUSS  = "img/sketch_gaussian.png"

# --- Gaussian (Rademacher JL projection) ---
G_M   = 6000     # sketch dimension per copy
G_K   = 24       # copies to average  (total measurements m*k ~ 3x pixels)
G_SEED = 20260210

# --- Count sketch ---
C_M   = 22000    # buckets (~N/2)
C_K   = 9        # copies for the per-pixel median (odd)
C_SEED = 7919


def load(path):
    im = Image.open(path).convert("RGB")
    return np.asarray(im, dtype=np.float32), im.size  # (H,W,3)


def gaussian_sketch(chan, m, k, seed):
    """chan: 1-D float32 vector (all pixels of one channel)."""
    N = chan.shape[0]
    acc = np.zeros(N, dtype=np.float64)
    for t in range(k):
        rng = np.random.default_rng(seed + t * 104729)
        nbytes = (m * N + 7) // 8
        bits = np.unpackbits(rng.integers(0, 256, nbytes, dtype=np.uint8))[:m * N]
        S = bits.astype(np.float32).reshape(m, N)
        S *= 2.0; S -= 1.0                 # {0,1} -> {-1,+1}
        y = S @ chan                       # sketch  (m,)
        acc += S.T @ y                     # recover (N,)  ~ m * chan + noise
        del S
    return acc / (k * m)                   # unbiased mean-of-k estimate


def count_sketch(chan, m, k, seed):
    N = chan.shape[0]
    recovered = np.empty((k, N), dtype=np.float32)
    for t in range(k):
        rng = np.random.default_rng(seed + t * 104729)
        h = rng.integers(0, m, N)                      # bucket per pixel
        s = (rng.integers(0, 2, N).astype(np.float32) * 2 - 1)  # +/-1 sign
        y = np.bincount(h, weights=s * chan, minlength=m)       # sketch
        recovered[t] = s * y[h]                                 # per-pixel recover
    return np.median(recovered, axis=0)                # median-of-k


def run(fn, arr, *params):
    H, W, _ = arr.shape
    out = np.empty_like(arr)
    for c in range(3):
        out[..., c] = fn(arr[..., c].reshape(-1), *params).reshape(H, W)
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    arr, size = load(SRC)
    print(f"source {SRC}  {size[0]}x{size[1]}  N={arr.shape[0]*arr.shape[1]} pixels/channel")

    print("count sketch  (pixel-wise, median-of-%d, m=%d) ..." % (C_K, C_M))
    Image.fromarray(run(count_sketch, arr, C_M, C_K, C_SEED)).save(OUT_COUNT)

    print("gaussian sketch (pixel-wise, mean-of-%d, m=%d) ..." % (G_K, G_M))
    Image.fromarray(run(gaussian_sketch, arr, G_M, G_K, G_SEED)).save(OUT_GAUSS)

    print("wrote", OUT_COUNT, "and", OUT_GAUSS)


if __name__ == "__main__":
    main()
