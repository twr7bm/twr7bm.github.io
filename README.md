# twr7bm.github.io

Personal academic site for **Tahseen Rabbani** — AI/ML Postdoctoral Scholar,
University of Chicago. Live at https://twr7bm.github.io

## Stack
A single self-contained `index.html` (inline CSS + vanilla JS, no framework, no
build step). Fonts: Instrument Serif / Instrument Sans / IBM Plex Mono via
Google Fonts. Deploys via GitHub Pages on push to `master`.

## Sketch portraits
The hero photo can be swapped for a **count** or **Gaussian** sketch of the
image. Both are reconstructed *pixel-wise* (the whole image as one flattened
vector per channel — not row-by-row) by `generate_sketches.py`:

    python3 generate_sketches.py     # requires numpy + pillow

Outputs `img/sketch_count.png` and `img/sketch_gaussian.png`.
