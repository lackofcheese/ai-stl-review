#!/usr/bin/env python3
"""Publication-history guard: `published` timestamps never change.

Compares reviews.json in the working tree against a base git ref (the PR
merge-base in CI). For every canonical page slug present at the base and
still present now, the recorded `published` timestamp must be unchanged —
republishing legitimately updates `title` and `updated`, but the original
publication instant is append-only history (the Discord allowlist pins its
`approvedAt` to it). Removing a slug is allowed: withdrawal of a
publication is a legitimate, deliberate act.

  python3 scripts/validate_history.py --base <git-ref> [--root .]

Dependency-free by design, like scripts/validate_site.py.
"""
import argparse
import json
import pathlib
import subprocess
import sys


def manifest_at(root, base):
    result = subprocess.run(['git', '-C', str(root), 'show',
                             f'{base}:reviews.json'],
                            capture_output=True, text=True)
    if result.returncode:
        sys.exit(f'cannot read reviews.json at {base}: '
                 f'{result.stderr.strip()}')
    return json.loads(result.stdout)


def canonical_slugs(manifest):
    return {slug: entry for slug, entry in manifest.items()
            if not slug.startswith('_')}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--base', required=True,
                    help='git ref to compare against (PR merge-base)')
    ap.add_argument('--root', default='.', help='repository root')
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    try:
        head = json.loads((root / 'reviews.json').read_text())
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f'cannot read working-tree reviews.json: {exc}')
    base = canonical_slugs(manifest_at(root, a.base))
    head = canonical_slugs(head)

    problems = []
    for slug, entry in sorted(base.items()):
        if slug not in head:
            print(f'NOTE: {slug} was withdrawn (allowed)')
            continue
        before = entry.get('published')
        after = head[slug].get('published')
        if before != after:
            problems.append(f'{slug}: published changed '
                            f'{before!r} -> {after!r} — the publication '
                            f'instant is append-only history')
    if problems:
        for problem in problems:
            print(f'FAIL: {problem}')
        sys.exit(1)
    print(f'history: OK ({len(base)} base slug(s) checked)')


if __name__ == '__main__':
    main()
