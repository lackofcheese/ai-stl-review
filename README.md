# ai-stl-review

Public review pages for the miniature pipeline (ai-stl-pipeline is the
private working repo). Served via GitHub Pages at:

https://lackofcheese.github.io/ai-stl-review/

**Everything in this repo is world-readable** — pages land here only when
Dimitri explicitly opts a review in. Publishing is done by
`tools/publish_review.py` in the pipeline repo: it copies a review
directory into `reviews/<slug>/`, regenerates the index, commits, and
pushes. Don't edit `index.html` by hand; it's generated.

Layout (hierarchical since 2026-07-11 — Dimitri's reorg):

```
index.html            Generated listing, grouped by project -> sub-project,
                      pages in round order (never edit by hand)
reviews.json          Manifest (titles, publish dates) + "_redirects"
                      mapping legacy flat slugs to their new homes
reviews/<project>/[<sub-project>/]<page>/
                      One published review page + its images, e.g.
                      reviews/cyber-amazons/gorgon/r3x-panel/
reviews/<old-slug>/   Meta-refresh stubs at pre-reorg URLs (links already
                      shared keep working); regenerated on every publish
```
