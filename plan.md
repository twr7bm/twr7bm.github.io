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
