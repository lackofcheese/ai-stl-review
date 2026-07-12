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
index.html            Generated root listing, grouped by project -> character,
                      pages in round order; project/character headings link to
                      their landing pages (never edit by hand)
reviews.json          Manifest (titles, publish dates) + "_redirects"
                      mapping legacy flat slugs to their new homes
reviews/<project>/index.html
                      Generated project landing: team brief + character list
reviews/<project>/<character>/index.html
                      Generated character landing: character spec + rounds
                      newest-first, each round grouping its runbook + review
reviews/<project>/[<character>/]<page>/
                      A published page + its images. Pages come in kinds:
                      rN-panel  (review), rN-runbook (round plan-of-record,
                      cross-linked to its rN-panel), team-brief, spec
reviews/<old-slug>/   Meta-refresh stubs at pre-reorg URLs (links already
                      shared keep working); regenerated on every publish
```

All three index levels regenerate from `reviews.json` on every publish — never
hand-edit them. Runbook pages are built with `tools/render_runbook.py` in the
pipeline repo and published the same way as reviews.
