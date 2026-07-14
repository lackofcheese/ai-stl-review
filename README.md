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
assets/<hash>.<ext>   Small displayed thumbnails/reference images, keyed by
                      content hash and deduplicated across pages. Full-size
                      lightbox images and explicitly approved STL downloads
                      live in the public Cloudflare R2 cache; Google Drive
                      remains canonical for pipeline binaries
reviews/<project>/index.html
                      Generated project landing: team brief + a round table
                      per character
reviews/<project>/<character>/index.html
                      Generated character landing: character spec + that
                      character's round table
reviews/<project>/[<character>/]<page>/index.html
                      A published page (HTML only — displayed previews are in
                      assets/ and full/model payloads are on R2).
                      Pages come in kinds: rN-panel (review), rN-runbook
                      (round plan-of-record, cross-linked to its rN-panel),
                      team-brief, spec. Review/runbook pages carry an up-nav
                      breadcrumb and cross-link each other
reviews/<old-slug>/   Meta-refresh stubs at pre-reorg URLs (links already
                      shared keep working); regenerated on every publish
```

Every index level regenerates from `reviews.json` on each publish — never
hand-edit them. Runbook pages are built with `tools/render_runbook.py`.
`publish_review.py` uploads full-size lightbox images and approved STLs to R2
before committing HTML, then hoists displayed thumbnails/references into the
shared `assets/` store and GCs orphaned local assets automatically. There are
no per-page image folders and no full-size/model payloads in Git history after
the 2026-07-14 cleanup.

## AI review security

This public repository does not automatically invoke Codex or Claude for pull
request review. Public PR text, diffs, comments, links, and artifacts are
untrusted data and may contain prompt injection. A maintainer may request an AI
review manually, in an isolated cloud environment, only after inspecting the
conversation. Manual AI review is read-only except for review comments: it must
not push commits, access secrets, broaden permissions, or perform unrelated
external actions.

Every manual AI review must name the exact runtime model or variant when the
product exposes it. If it does not, the review must say `model not exposed`;
never infer a model from quality, latency, product tier, or another session's
label.

Use deterministic CI for routine publication checks such as broken links,
missing content-addressed assets, manifest/index consistency, HTML validation,
and secret scanning.

## Deterministic CI

Every pull request and push to `main` runs a dependency-free Python validator
and its unit tests. CI checks:

- `reviews.json` has canonical formatting and parses without duplicate keys;
  slugs, metadata, timestamps, redirects, canonical pages, and generated
  landing indexes agree;
- every local HTML link, image, lightbox source, fragment target, round
  panel/runbook cross-link, and legacy redirect resolves;
- content pages include the required doctype, language, UTF-8 charset,
  viewport metadata, non-empty title, and unique element IDs; legacy redirect
  stubs must carry a refresh target;
- every file in `assets/` is referenced, has a supported image signature, and
  is named with the first 16 hex characters of its SHA-256 digest;
- public text has no private workstation paths or high-confidence secret/key
  formats; and
- Actions workflows keep read-only permissions, immutable action pins, no PR
  secrets, superseded-commit cancellation, and no automatic AI/LLM invocation.

Run the same checks locally with Python 3.13 (the validator uses only the
standard library):

```sh
python3 -B -m unittest discover -s tests -v
python3 -B scripts/validate_site.py .
```

CI intentionally does not run an external-link crawler because network state
is nondeterministic and can make unrelated pull requests flaky. It also does
not reformat or regenerate published HTML: those files are generated by the
private pipeline repository, and changing them here would hide source/output
drift. Browser screenshots and accessibility audits are omitted for now because
the repository has no pinned browser toolchain or source-level fixtures; local
structural, navigation, and asset checks provide a stable first gate without
adding a large dependency surface. A separate formatter and static type checker
were also considered but not added: the published HTML must retain generator
formatting, and the only handwritten executable code is this small, typed,
standard-library validator. Adding a package manager and third-party dependency
set solely for it would make CI less deterministic than unit-test and full-site
validation coverage.
