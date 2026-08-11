#!/usr/bin/env python3
"""
Build the hero portrait + its four sketch toggles.

Step 1 crops the high-res source photo (img/selfie.jpg, 6000x4000) to a square and
saves a crisp display JPG (img/sketch_original.jpg). Step 2 makes four genuine
*project-onto-a-subspace-then-recover* sketches from it — the same compress-then-
reconstruct idea in four bases:

  count    : randomized count-sketch (hashing), recovered pixel-wise, median-of-k.
  dct      : block-DCT, keep the low-frequency cosine coeffs per block, invert.
  wavelet  : Haar transform, keep the largest coeffs by magnitude, invert.
  lowrank  : truncated SVD per channel.

Sketches render at WORK px; the display photo at DISP px (higher, so it stays sharp
on high-DPR phones). Params scale with resolution so the artifacts look consistent.

Deterministic. Requires numpy + pillow.   ->   python3 generate_sketches.py
"""
import numpy as np
from PIL import Image

SRC_HI = "img/selfie.jpg"
DISP   = "img/sketch_original.jpg"
CROP   = (1050, 0, 4650, 3600)   # square crop of selfie.jpg matching the framing
DISP_PX = 720                    # crisp display original
WORK    = 440                    # sketch working resolution (2x the old 220 baseline)
S       = WORK // 220            # param scale factor vs the original baseline


def build_original():
    im = Image.open(SRC_HI).convert("RGB").crop(CROP)
    im.resize((DISP_PX, DISP_PX), Image.LANCZOS).save(DISP, quality=88)
    return im.resize((WORK, WORK), Image.LANCZOS)


# ---------------- count sketch (random hashing) ----------------
def _count_sketch(chan, m, k=9, seed=7919):
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
    m = int(0.4545 * H * W)                     # keep the old m/N compression ratio
    out = np.empty_like(rgb)
    for c in range(3):
        out[..., c] = _count_sketch(rgb[..., c].reshape(-1), m).reshape(H, W)
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------- block DCT coding ----------------
def _dct_mat(n):
    k = np.arange(n)[:, None]; m = np.arange(n)[None, :]
    D = np.cos(np.pi * (2 * m + 1) * k / (2 * n)) * np.sqrt(2.0 / n)
    D[0] *= 1 / np.sqrt(2)
    return D

def _dct_channel(ch, keep, n):
    D = _dct_mat(n)
    Hp = -(-ch.shape[0] // n) * n; Wp = -(-ch.shape[1] // n) * n
    p = np.zeros((Hp, Wp)); p[:ch.shape[0], :ch.shape[1]] = ch
    out = np.zeros_like(p)
    with np.errstate(all="ignore"):
        for y in range(0, Hp, n):
            for x in range(0, Wp, n):
                C = D @ p[y:y+n, x:x+n] @ D.T
                M = np.zeros_like(C); M[:keep, :keep] = C[:keep, :keep]
                out[y:y+n, x:x+n] = D.T @ M @ D
    return out[:ch.shape[0], :ch.shape[1]]

def make_dct(rgb, block, keep):
    return np.clip(np.stack([_dct_channel(rgb[..., c], keep, block) for c in range(3)], -1), 0, 255).astype(np.uint8)


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
def _wave_channel(ch, keep_frac, N, L):
    p = np.zeros((N, N)); p[:ch.shape[0], :ch.shape[1]] = ch
    C = _haar2d(p, L); flat = np.abs(C).ravel()
    k = max(1, int(keep_frac * flat.size))
    thr = np.partition(flat, -k)[-k]
    C[np.abs(C) < thr] = 0
    return _ihaar2d(C, L)[:ch.shape[0], :ch.shape[1]]
def make_wavelet(rgb, keep_frac=0.025):
    N = 1 << int(np.ceil(np.log2(max(rgb.shape[:2])))); L = 6
    return np.clip(np.stack([_wave_channel(rgb[..., c], keep_frac, N, L) for c in range(3)], -1), 0, 255).astype(np.uint8)


# ---------------- truncated SVD ----------------
def make_lowrank(rgb, r):
    out = np.empty_like(rgb)
    with np.errstate(all="ignore"):
        for c in range(3):
            U, Sg, Vt = np.linalg.svd(rgb[..., c].astype(np.float64), full_matrices=False)
            out[..., c] = (U[:, :r] * Sg[:r]) @ Vt[:r]
    return np.clip(out, 0, 255).astype(np.uint8)


def main():
    work = np.asarray(build_original(), np.float64)
    print(f"original -> {DISP} ({DISP_PX}px); sketches at {WORK}px (scale {S}x)")
    for name, arr in [
        ("count",   make_count(work)),
        ("dct",     make_dct(work, block=8 * S, keep=2 * S)),
        ("wavelet", make_wavelet(work)),
        ("lowrank", make_lowrank(work, r=12 * S)),
    ]:
        Image.fromarray(arr).save(f"img/sketch_{name}.png")
        print(f"  {name:8s} -> img/sketch_{name}.png")


if __name__ == "__main__":
    main()
