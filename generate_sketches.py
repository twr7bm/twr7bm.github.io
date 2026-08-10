#!/usr/bin/env python3
"""
Generate the sketch portraits used on the hero photo toggle.

Every option is a genuine *project-onto-a-subspace-then-recover* map — the same
idea (compress by keeping few coefficients, then reconstruct) in four different
bases, so the toggle reads as an honest little tour of linear sketching:

  count    : randomized count-sketch. y = Sx via hashing (each pixel -> one of m
             buckets with a +/-1 sign); recover x_hat = s * y[h]; median-of-k
             kills the heavy-tailed collision noise. Reconstructed PIXEL-WISE
             (whole image flattened per channel). -> colored speckle grain.
  dct      : block DCT coding. Each 8x8 block is projected onto its top keep*keep
             low-frequency cosine coefficients, then inverse-DCT'd. -> JPEG-style
             blockiness.
  wavelet  : Haar wavelet transform, keep the largest `keep_frac` coefficients by
             magnitude (a sparse projection), then invert. -> multi-scale mosaic.
  lowrank  : truncated SVD per channel — project onto the top-r singular subspace
             and reconstruct. -> smooth "compressed" ghost.

Deterministic. Requires numpy + pillow.

    python3 generate_sketches.py
"""
import numpy as np
from PIL import Image

SRC = "img/sketch_original.png"


# ---------------- count sketch (random hashing) ----------------
C_M, C_K, C_SEED = 22000, 9, 7919

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


# ---------------- block DCT coding ----------------
def _dct_mat(n=8):
    k = np.arange(n)[:, None]; m = np.arange(n)[None, :]
    D = np.cos(np.pi * (2 * m + 1) * k / (2 * n)) * np.sqrt(2.0 / n)
    D[0] *= 1 / np.sqrt(2)
    return D

def _dct_channel(ch, keep, n=8):
    D = _dct_mat(n)
    Hp = -(-ch.shape[0] // n) * n; Wp = -(-ch.shape[1] // n) * n
    p = np.zeros((Hp, Wp)); p[:ch.shape[0], :ch.shape[1]] = ch
    out = np.zeros_like(p)
    with np.errstate(all="ignore"):
        for y in range(0, Hp, n):
            for x in range(0, Wp, n):
                C = D @ p[y:y+n, x:x+n] @ D.T
                M = np.zeros_like(C); M[:keep, :keep] = C[:keep, :keep]   # projection
                out[y:y+n, x:x+n] = D.T @ M @ D
    return out[:ch.shape[0], :ch.shape[1]]

def make_dct(rgb, keep=2):
    return np.clip(np.stack([_dct_channel(rgb[..., c], keep) for c in range(3)], -1), 0, 255).astype(np.uint8)


# ---------------- Haar wavelet coding ----------------
_R2 = np.sqrt(2.0)

def _haar2d(a, L):
    cur = a.copy(); h, w = a.shape
    for l in range(L):
        ch, cw = h >> l, w >> l; b = cur[:ch, :cw]
        e = (b[:, 0::2] + b[:, 1::2]) / _R2; o = (b[:, 0::2] - b[:, 1::2]) / _R2; b = np.concatenate([e, o], 1)
        e = (b[0::2, :] + b[1::2, :]) / _R2; o = (b[0::2, :] - b[1::2, :]) / _R2; b = np.concatenate([e, o], 0)
        cur[:ch, :cw] = b
    return cur

def _ihaar2d(c, L):
    cur = c.copy(); h, w = c.shape
    for l in reversed(range(L)):
        ch, cw = h >> l, w >> l; b = cur[:ch, :cw]
        top = b[:ch // 2, :]; bot = b[ch // 2:, :]
        col = np.empty_like(b); col[0::2, :] = (top + bot) / _R2; col[1::2, :] = (top - bot) / _R2
        le = col[:, :cw // 2]; ro = col[:, cw // 2:]
        row = np.empty_like(b); row[:, 0::2] = (le + ro) / _R2; row[:, 1::2] = (le - ro) / _R2
        cur[:ch, :cw] = row
    return cur

def _wave_channel(ch, keep_frac, L=6, N=256):
    p = np.zeros((N, N)); p[:ch.shape[0], :ch.shape[1]] = ch
    C = _haar2d(p, L); flat = np.abs(C).ravel()
    k = max(1, int(keep_frac * flat.size))
    thr = np.partition(flat, -k)[-k]
    C[np.abs(C) < thr] = 0
    return _ihaar2d(C, L)[:ch.shape[0], :ch.shape[1]]

def make_wavelet(rgb, keep_frac=0.025):
    return np.clip(np.stack([_wave_channel(rgb[..., c], keep_frac) for c in range(3)], -1), 0, 255).astype(np.uint8)


# ---------------- truncated SVD ----------------
def make_lowrank(rgb, r=12):
    out = np.empty_like(rgb)
    with np.errstate(all="ignore"):
        for c in range(3):
            U, S, Vt = np.linalg.svd(rgb[..., c].astype(np.float64), full_matrices=False)
            out[..., c] = (U[:, :r] * S[:r]) @ Vt[:r]
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    src = Image.open(SRC).convert("RGB")
    rgb = np.asarray(src, np.float64)
    print(f"source {SRC}  {src.size[0]}x{src.size[1]}")
    for name, arr in [
        ("count",   make_count(rgb)),
        ("dct",     make_dct(rgb)),
        ("wavelet", make_wavelet(rgb)),
        ("lowrank", make_lowrank(rgb)),
    ]:
        Image.fromarray(arr).save(f"img/sketch_{name}.png")
        print(f"  {name:8s} -> img/sketch_{name}.png")


if __name__ == "__main__":
    main()
