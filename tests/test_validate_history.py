"""validate_history.py: published timestamps are append-only."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/validate_history.py'

ENTRY = {'published': '2026-07-10T00:00:00+00:00',
         'title': 'Example', 'updated': '2026-07-10T00:00:00+00:00'}


def git(root, *args):
    subprocess.run(['git', '-C', str(root), *args], check=True,
                   capture_output=True)


def make_repo(tmp, manifest):
    root = pathlib.Path(tmp)
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 'test@example.com')
    git(root, 'config', 'user.name', 'test')
    (root / 'reviews.json').write_text(json.dumps(manifest, indent=1))
    git(root, 'add', '-A')
    git(root, 'commit', '-q', '-m', 'base')
    return root


def run_check(root):
    return subprocess.run([sys.executable, str(SCRIPT), '--base', 'HEAD',
                           '--root', str(root)],
                          capture_output=True, text=True)


class ValidateHistoryTests(unittest.TestCase):
    def test_unchanged_and_updated_metadata_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, {'team/char/r1-panel': dict(ENTRY)})
            changed = {'team/char/r1-panel': dict(
                ENTRY, title='New title', updated='2026-07-18T00:00:00+00:00')}
            (root / 'reviews.json').write_text(json.dumps(changed, indent=1))
            result = run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_changed_published_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, {'team/char/r1-panel': dict(ENTRY)})
            changed = {'team/char/r1-panel': dict(
                ENTRY, published='2026-07-18T00:00:00+00:00')}
            (root / 'reviews.json').write_text(json.dumps(changed, indent=1))
            result = run_check(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn('append-only', result.stdout)

    def test_withdrawal_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, {'team/char/r1-panel': dict(ENTRY),
                                   '_redirects': {}})
            (root / 'reviews.json').write_text(json.dumps({'_redirects': {}},
                                                          indent=1))
            result = run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn('withdrawn', result.stdout)

    def test_new_slug_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(tmp, {'team/char/r1-panel': dict(ENTRY)})
            grown = {'team/char/r1-panel': dict(ENTRY),
                     'team/char/r2-panel': dict(ENTRY)}
            (root / 'reviews.json').write_text(json.dumps(grown, indent=1))
            result = run_check(root)
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == '__main__':
    unittest.main()
