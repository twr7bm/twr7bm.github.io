## Website Redesign Plan

### Completed
- **Full redesign** (v1): Dropped old Bootstrap 3 / Freelancer theme. Built modern dark academic theme with:
  - Dark palette (#0c0c14 base, muted blue #7ba4cc + warm gold #c9a96e accents)
  - Typography: DM Serif Display (headings) + Inter (body) via Google Fonts
  - Frosted-glass navbar with backdrop-filter blur
  - Hero section: side-by-side circular photo + bio (responsive → stacked on mobile)
  - Card-based publications with colored venue tags and hover lift effects
  - Artwork section: 2x2 grid with lightbox viewer
  - Scroll-triggered fade-in animations
  - Fully self-contained (no Bootstrap/jQuery/Font Awesome dependencies)
  - Mobile responsive with hamburger menu
- **Photo centering fix**: Added `object-position: 35% 25%` to hero-photo so face is centered in circular crop
- **Dead link fix**: Updated NeurIPS 2023 "Private On-Device LSH" paper link to correct proceedings URL

### Notes
- Must push to master for GitHub Pages to render (no branch deploys)
- Old CSS files (css/freelancer.css, css/bootstrap.min.css) still in repo but no longer referenced

### Session: 2026-08-10 — polsia-style rebuild
- **Full redesign (v2)** into an editorial "polsia" idiom, matching the Next Puzzle
  site: light cool-paper palette + near-black ink + burnt-rust accent, sharp 2px
  corners, hairline rules, registration/crop-mark corners on the portrait, and a
  mono "instrument" treatment for the sketch toggle. Typography swapped to
  **Instrument Serif** (display) + **Instrument Sans** (body) + **IBM Plex Mono**
  (labels). Kept dark/light toggle (light is now default; dark via [data-theme]).
- Dropped the wireframe canvas background. All content preserved (news, 12 works,
  hidden workshop section, artwork + lightbox, socials, CV link).
- **Fixed the sketches** — regenerated Count and Gaussian portraits *pixel-wise*
  (whole image flattened per channel) instead of the old 1-D row sketching that
  caused horizontal banding. See generate_sketches.py.
- **Cleanup**: removed unreferenced Bootstrap/Freelancer/jQuery/Font-Awesome/less
  and glyphicon font dirs; resolved a committed merge conflict in README.md.

### Session: 2026-08-10 — v3 redesign + honest sketches
- **Redesign (v3)** away from the editorial-serif "millennial intellectual" look:
  single warm sans (Hanken Grotesk, no serif/mono), a sticky **left-rail** layout
  (photo + sketch toggle + bio + nav + socials) with a wide content column so the
  page fills the width instead of a narrow centered column with big blank borders.
  Soft rounded corners, subtle dividers — minimal, not brutalist. Kept dark/light.
- **Sketches are now all genuine projection+recovery** (dropped the halftone/riso
  filters): count (random hashing), DCT (block cosine), wavelet (Haar), low-rank
  (SVD) — four bases for the same compress-then-recover idea.
