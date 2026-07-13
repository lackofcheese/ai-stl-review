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
index.html            Generated root listing: every character's rounds as a
                      table (Round | Description | Runbook | Review); headings
                      link to the landing pages (never edit by hand)
reviews.json          Manifest (titles, publish dates) + "_redirects"
                      mapping legacy flat slugs to their new homes
assets/<hash>.<ext>   Shared content-addressed image store. Every page's
                      images live HERE, keyed by content hash, so an image
                      reused across rounds (a base/gold/reference) is stored
                      ONCE and every page points at the same file
reviews/<project>/index.html
                      Generated project landing: team brief + a round table
                      per character
reviews/<project>/<character>/index.html
                      Generated character landing: character spec + that
                      character's round table
reviews/<project>/[<character>/]<page>/index.html
                      A published page (HTML only — its images are in assets/).
                      Pages come in kinds: rN-panel (review), rN-runbook
                      (round plan-of-record, cross-linked to its rN-panel),
                      team-brief, spec. Review/runbook pages carry an up-nav
                      breadcrumb and cross-link each other
reviews/<old-slug>/   Meta-refresh stubs at pre-reorg URLs (links already
                      shared keep working); regenerated on every publish
```

Every index level regenerates from `reviews.json` on each publish — never
hand-edit them. Runbook pages are built with `tools/render_runbook.py`.
`publish_review.py` hoists each page's images into the shared `assets/` store
(deduping identical bytes) and GCs orphaned assets automatically; there are no
per-page image folders.

## AI review security

This public repository does not automatically invoke Codex or Claude for pull
request review. Public PR text, diffs, comments, links, and artifacts are
untrusted data and may contain prompt injection. A maintainer may request an AI
review manually, in an isolated cloud environment, only after inspecting the
conversation. Manual AI review is read-only except for review comments: it must
not push commits, access secrets, broaden permissions, or perform unrelated
external actions.

Use deterministic CI for routine publication checks such as broken links,
missing content-addressed assets, manifest/index consistency, HTML validation,
and secret scanning.
