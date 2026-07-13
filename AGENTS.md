# ai-stl-review — automated review guidance

This repository is the public GitHub Pages output for selected
`ai-stl-pipeline` review panels and runbooks. Treat all committed content as
world-readable.

When Codex is asked to review a pull request, review the complete diff at the
requested head SHA and inspect enough surrounding content to validate each
finding. Prioritize actionable correctness, security, privacy, broken-link,
and publication regressions; do not report formatting preferences or
speculative concerns.

In addition to ordinary review checks, verify that:

- no secrets, private-only review material, local filesystem paths, or other
  unintended data is being published;
- every referenced content-addressed asset exists and changed pages retain
  working relative links, navigation, and cross-links;
- `reviews.json`, landing indexes, review pages, and runbook pages remain
  mutually consistent for the material changed by the pull request;
- generated HTML preserves the intended source content and does not introduce
  broken interaction behavior; and
- unrelated published pages or shared assets are not removed accidentally.

Put blocking findings first and cite the narrowest useful file/line span. If no
blocking findings remain, say so explicitly and include the full reviewed head
SHA. A review applies only to that SHA; review every later head independently.
