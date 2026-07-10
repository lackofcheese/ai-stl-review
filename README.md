# ai-stl-review

Public review pages for the miniature pipeline (ai-stl-pipeline is the
private working repo). Served via GitHub Pages at:

https://lackofcheese.github.io/ai-stl-review/

**Everything in this repo is world-readable** — pages land here only when
Dimitri explicitly opts a review in. Publishing is done by
`tools/publish_review.py` in the pipeline repo: it copies a review
directory into `reviews/<slug>/`, regenerates the index, commits, and
pushes. Don't edit `index.html` by hand; it's generated.

Layout:

```
index.html            Generated listing of all published reviews
reviews/<slug>/       One published review page + its images
```
