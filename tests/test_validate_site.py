from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_site import validate  # noqa: E402


HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title></head><body>{body}</body></html>
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "assets").mkdir()
        (self.root / ".github" / "workflows").mkdir(parents=True)

        image = b"\xff\xd8\xfffixture"
        digest = hashlib.sha256(image).hexdigest()[:16]
        self.asset_name = f"{digest}.jpg"
        (self.root / "assets" / self.asset_name).write_bytes(image)

        manifest = {
            "_redirects": {"old/r1-panel": "team/character/r1-panel"},
            "team/character/r1-panel": {
                "published": "2026-01-01T00:00:00+00:00",
                "title": "Round 1",
                "updated": "2026-01-01T00:00:00+00:00",
            },
            "team/character/r1-runbook": {
                "published": "2026-01-01T00:00:00+00:00",
                "title": "Round 1 runbook",
                "updated": "2026-01-01T00:00:00+00:00",
            },
        }
        (self.root / "reviews.json").write_text(
            json.dumps(manifest, indent=1) + "\n", encoding="utf-8"
        )

        self.write_html("index.html", '<a href="reviews/team/">Team</a>')
        self.write_html("reviews/team/index.html", '<a href="character/">Character</a>')
        self.write_html(
            "reviews/team/character/index.html",
            '<a href="r1-panel/">Panel</a><a href="r1-runbook/">Runbook</a>',
        )
        self.write_html(
            "reviews/team/character/r1-panel/index.html",
            f'<a href="../r1-runbook/">Runbook</a><div id="in-1"></div>'
            f'<button data-inputs="in-1"></button><img src="../../../../assets/{self.asset_name}" '
            f'data-full="../../../../assets/{self.asset_name}" alt="fixture">',
        )
        self.write_html(
            "reviews/team/character/r1-runbook/index.html",
            '<a href="../r1-panel/">Panel</a>',
        )
        self.write_html(
            "reviews/old/r1-panel/index.html",
            '<meta http-equiv="refresh" content="0; url=../../team/character/r1-panel/">'
            '<a href="../../team/character/r1-panel/">Moved</a>',
        )
        (self.root / ".github" / "workflows" / "ci.yml").write_text(
            """name: CI
on:
  pull_request:
permissions:
  contents: read
concurrency:
  group: test
  cancel-in-progress: true
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: python scripts/validate_site.py
""",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_html(self, relative: str, body: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(HTML.format(title=relative, body=body), encoding="utf-8")

    def test_valid_fixture_passes(self) -> None:
        self.assertEqual(validate(self.root), [])

    def test_broken_link_is_reported(self) -> None:
        page = self.root / "reviews/team/character/r1-panel/index.html"
        page.write_text(page.read_text() + '<a href="missing/">broken</a>', encoding="utf-8")
        self.assertTrue(any("broken href" in error for error in validate(self.root)))

    def test_asset_hash_mismatch_is_reported(self) -> None:
        asset = self.root / "assets" / self.asset_name
        asset.write_bytes(asset.read_bytes() + b"changed")
        self.assertTrue(any("SHA-256" in error for error in validate(self.root)))

    def test_missing_manifest_page_is_reported(self) -> None:
        (self.root / "reviews/team/character/r1-runbook/index.html").unlink()
        self.assertTrue(any("canonical page is missing" in error for error in validate(self.root)))

    def test_manifest_format_drift_is_reported(self) -> None:
        manifest = self.root / "reviews.json"
        manifest.write_text(json.dumps(json.loads(manifest.read_text())), encoding="utf-8")
        self.assertTrue(any("formatting differs" in error for error in validate(self.root)))

    def test_empty_manifest_is_reported(self) -> None:
        (self.root / "reviews.json").write_text("{}\n", encoding="utf-8")
        self.assertTrue(any("at least one canonical page" in error for error in validate(self.root)))

    def test_bracketed_secret_reference_is_reported(self) -> None:
        workflow = self.root / ".github/workflows/ci.yml"
        workflow.write_text(
            workflow.read_text() + "      - run: echo ${{ secrets['NPM_TOKEN'] }}\n",
            encoding="utf-8",
        )
        self.assertTrue(any("must not access secrets" in error for error in validate(self.root)))

    def test_cross_page_fragment_is_reported(self) -> None:
        page = self.root / "reviews/team/character/r1-runbook/index.html"
        page.write_text(
            page.read_text().replace('../r1-panel/">', '../r1-panel/#missing">'),
            encoding="utf-8",
        )
        self.assertTrue(any("fragment target" in error for error in validate(self.root)))

    def test_flow_style_pull_request_requires_concurrency(self) -> None:
        workflow = self.root / ".github/workflows/ci.yml"
        workflow.write_text(
            workflow.read_text()
            .replace("on:\n  pull_request:\n", "on: [pull_request]\n")
            .replace(
                "concurrency:\n  group: test\n  cancel-in-progress: true\n",
                "",
            ),
            encoding="utf-8",
        )
        errors = validate(self.root)
        self.assertTrue(any("concurrency group" in error for error in errors))
        self.assertTrue(any("cancel superseded" in error for error in errors))

    def test_unpinned_action_and_ai_workflow_are_reported(self) -> None:
        workflow = self.root / ".github/workflows/ci.yml"
        workflow.write_text(
            workflow.read_text()
            + "      - uses: vendor/example@v1\n"
            + "      - run: codex review\n",
            encoding="utf-8",
        )
        errors = validate(self.root)
        self.assertTrue(any("not pinned" in error for error in errors))
        self.assertTrue(any("AI/LLM" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
