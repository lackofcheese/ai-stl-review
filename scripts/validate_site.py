#!/usr/bin/env python3
"""Deterministic integrity and publication-safety checks for the static site."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Iterable
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ASSET_NAME = re.compile(r"[0-9a-f]{16}\.(?:jpg|png|webp)")
CANONICAL_SLUG = re.compile(r"[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)+")
REDIRECT_SLUG = re.compile(r"[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*")
PINNED_ACTION = re.compile(r"[0-9a-f]{40}")
TEXT_SUFFIXES = {".html", ".json", ".md", ".py", ".txt", ".yaml", ".yml"}
RESOURCE_ATTRIBUTES = {"href", "src", "data-full"}
SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "GitHub token": re.compile(r"\b(?:github_pat_[0-9A-Za-z_]{20,}|gh[pousr]_[0-9A-Za-z]{36,})\b"),
    "OpenAI/Anthropic key": re.compile(r"\bsk-(?:ant-|proj-)?[0-9A-Za-z_-]{20,}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "Slack token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{20,}\b"),
}
PRIVATE_PATH = re.compile(
    r"(?:file:" + r"//|/(?:Users|home)/[^\s<>'\"]+|[A-Za-z]:\\Users\\[^\s<>'\"]+)",
    re.IGNORECASE,
)
AI_WORKFLOW = re.compile(r"\b(?:anthropic|claude|codex|llm|ollama|openai)\b", re.IGNORECASE)
ACTION_PERMISSION = re.compile(
    r"(?m)^\s{2,}(actions|attestations|checks|contents|deployments|discussions|"
    r"id-token|issues|models|packages|pages|pull-requests|security-events|statuses):\s*"
    r"([a-z-]+)\s*$"
)


class DuplicateJsonKey(ValueError):
    """Raised when JSON contains a duplicate object key."""


class SiteParser(HTMLParser):
    """Collect the small set of HTML facts that affect publication integrity."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doctype = False
        self.html_lang = False
        self.charsets = 0
        self.viewports = 0
        self.refresh = False
        self.title_depth = 0
        self.title_text: list[str] = []
        self.ids: set[str] = set()
        self.duplicate_ids: set[str] = set()
        self.resources: list[tuple[str, str]] = []
        self.fragments: list[str] = []

    def handle_decl(self, decl: str) -> None:
        if decl.strip().lower() == "doctype html":
            self.doctype = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs}
        tag = tag.lower()

        if tag == "html" and values.get("lang", "").strip():
            self.html_lang = True
        elif tag == "meta":
            if values.get("charset", "").lower() == "utf-8":
                self.charsets += 1
            if values.get("name", "").lower() == "viewport" and values.get("content"):
                self.viewports += 1
            if values.get("http-equiv", "").lower() == "refresh" and values.get("content"):
                self.refresh = True
        elif tag == "title":
            self.title_depth += 1

        element_id = values.get("id")
        if element_id:
            if element_id in self.ids:
                self.duplicate_ids.add(element_id)
            self.ids.add(element_id)

        for name, value in attrs:
            name = name.lower()
            if value and name in RESOURCE_ATTRIBUTES:
                self.resources.append((name, value))
                if name == "href" and value.startswith("#") and len(value) > 1:
                    self.fragments.append(unquote(value[1:]))
            elif value and name == "data-inputs":
                self.fragments.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title" and self.title_depth:
            self.title_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.title_depth:
            self.title_text.append(data)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey(f"duplicate key {key!r}")
        result[key] = value
    return result


def _display(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _parse_html(path: Path, root: Path, errors: list[str]) -> SiteParser:
    parser = SiteParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError) as exc:
        errors.append(f"{_display(path, root)}: cannot read as UTF-8 HTML: {exc}")
    except Exception as exc:  # HTMLParser can raise on malformed declarations.
        errors.append(f"{_display(path, root)}: HTML parse failed: {exc}")
    return parser


def _resolve_local(root: Path, document: Path, reference: str) -> Path | None:
    parsed = urlsplit(reference)
    if parsed.scheme or parsed.netloc or reference.startswith("//"):
        return None

    raw_path = unquote(parsed.path)
    if not raw_path:
        return document
    if raw_path.startswith("/"):
        prefix = "/ai-stl-review/"
        if not raw_path.startswith(prefix):
            return root.parent / "__invalid_absolute_site_path__"
        return root / raw_path.removeprefix(prefix)
    return document.parent / raw_path


def _target_file(path: Path) -> Path:
    return path / "index.html" if path.is_dir() else path


def _validate_html(root: Path, html_files: list[Path], errors: list[str]) -> dict[Path, SiteParser]:
    parsed: dict[Path, SiteParser] = {}
    for path in html_files:
        label = _display(path, root)
        document = _parse_html(path, root, errors)
        parsed[path] = document

        if not document.doctype:
            errors.append(f"{label}: missing <!doctype html>")
        if not document.html_lang:
            errors.append(f"{label}: missing non-empty <html lang>")
        if document.charsets != 1:
            errors.append(f"{label}: expected one UTF-8 charset declaration, found {document.charsets}")
        if not document.refresh and document.viewports != 1:
            errors.append(f"{label}: expected one viewport meta tag, found {document.viewports}")
        if not "".join(document.title_text).strip():
            errors.append(f"{label}: missing non-empty <title>")
        for duplicate in sorted(document.duplicate_ids):
            errors.append(f"{label}: duplicate id {duplicate!r}")
        for fragment in document.fragments:
            if fragment not in document.ids:
                errors.append(f"{label}: fragment target #{fragment} does not exist")

        for attribute, reference in document.resources:
            target = _resolve_local(root, path, reference)
            if target is None:
                continue
            try:
                resolved = target.resolve().relative_to(root.resolve())
            except ValueError:
                errors.append(f"{label}: {attribute} escapes the repository: {reference!r}")
                continue
            target_path = root / resolved
            if not target_path.exists():
                errors.append(f"{label}: broken {attribute} {reference!r}")
            elif target_path.is_dir() and not (target_path / "index.html").is_file():
                errors.append(f"{label}: linked directory has no index.html: {reference!r}")
    return parsed


def _load_manifest(root: Path, errors: list[str]) -> dict[str, object]:
    path = root / "reviews.json"
    try:
        source = path.read_text(encoding="utf-8")
        value = json.loads(source, object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJsonKey) as exc:
        errors.append(f"reviews.json: invalid JSON: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append("reviews.json: root must be an object")
        return {}
    if source != json.dumps(value, ensure_ascii=True, indent=1) + "\n":
        errors.append("reviews.json: formatting differs from json.dumps(..., indent=1)")
    return value


def _timestamp(value: object, label: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str):
        errors.append(f"{label}: must be an ISO-8601 string")
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        errors.append(f"{label}: invalid ISO-8601 timestamp {value!r}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{label}: timestamp must include a timezone")
        return None
    return parsed


def _local_targets(root: Path, document: Path, parser: SiteParser) -> set[Path]:
    targets: set[Path] = set()
    for _, reference in parser.resources:
        target = _resolve_local(root, document, reference)
        if target is None:
            continue
        try:
            targets.add(_target_file(target.resolve()).relative_to(root.resolve()))
        except ValueError:
            continue
    return targets


def _validate_manifest(
    root: Path, manifest: dict[str, object], parsed_html: dict[Path, SiteParser], errors: list[str]
) -> tuple[set[str], set[str], set[Path]]:
    redirects_value = manifest.get("_redirects", {})
    if not isinstance(redirects_value, dict):
        errors.append("reviews.json:_redirects must be an object")
        redirects: dict[str, object] = {}
    else:
        redirects = redirects_value

    canonical = {key for key in manifest if key != "_redirects"}
    redirect_slugs = set(redirects)
    landing_dirs: set[Path] = set()

    for slug in sorted(canonical):
        if not CANONICAL_SLUG.fullmatch(slug):
            errors.append(f"reviews.json:{slug}: invalid canonical slug")
            continue
        metadata = manifest[slug]
        if not isinstance(metadata, dict):
            errors.append(f"reviews.json:{slug}: metadata must be an object")
            continue
        title = metadata.get("title")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"reviews.json:{slug}: title must be a non-empty string")
        published = _timestamp(metadata.get("published"), f"reviews.json:{slug}:published", errors)
        updated = _timestamp(metadata.get("updated"), f"reviews.json:{slug}:updated", errors)
        if published and updated and updated < published:
            errors.append(f"reviews.json:{slug}: updated precedes published")

        parts = slug.split("/")
        landing_dirs.add(Path("reviews", parts[0]))
        if len(parts) >= 3:
            landing_dirs.add(Path("reviews", parts[0], parts[1]))

        page = root / "reviews" / slug / "index.html"
        if not page.is_file():
            errors.append(f"reviews.json:{slug}: canonical page is missing")

    for alias, target in sorted(redirects.items()):
        if not REDIRECT_SLUG.fullmatch(alias):
            errors.append(f"reviews.json:_redirects:{alias}: invalid redirect slug")
        if not isinstance(target, str) or target not in canonical:
            errors.append(f"reviews.json:_redirects:{alias}: target is not a canonical manifest page")
            continue
        if alias in canonical:
            errors.append(f"reviews.json:_redirects:{alias}: alias collides with a canonical page")
        stub = root / "reviews" / alias / "index.html"
        if not stub.is_file():
            errors.append(f"reviews.json:_redirects:{alias}: redirect stub is missing")
        elif stub in parsed_html:
            if not parsed_html[stub].refresh:
                errors.append(f"reviews.json:_redirects:{alias}: stub has no meta refresh")
            expected = Path("reviews") / target / "index.html"
            if expected not in _local_targets(root, stub, parsed_html[stub]):
                canonical_url = f"https://lackofcheese.github.io/ai-stl-review/reviews/{target}/"
                refs = {value for _, value in parsed_html[stub].resources}
                if canonical_url not in refs:
                    errors.append(f"reviews.json:_redirects:{alias}: stub does not link to {target}")

    expected_pages = {
        Path("reviews") / slug / "index.html" for slug in canonical | redirect_slugs
    } | {directory / "index.html" for directory in landing_dirs}
    actual_pages = {
        path.relative_to(root) for path in (root / "reviews").rglob("index.html")
    }
    for stale in sorted(actual_pages - expected_pages):
        errors.append(f"{stale.as_posix()}: page is not represented by the manifest hierarchy")
    for missing in sorted(expected_pages - actual_pages):
        errors.append(f"{missing.as_posix()}: expected manifest or landing page is missing")

    root_index = root / "index.html"
    if root_index in parsed_html:
        root_targets = _local_targets(root, root_index, parsed_html[root_index])
        for project in sorted({directory for directory in landing_dirs if len(directory.parts) == 2}):
            expected = project / "index.html"
            if expected not in root_targets:
                errors.append(f"index.html: missing project landing link to {project.as_posix()}/")

    for slug in sorted(canonical):
        parts = slug.split("/")
        landing = (
            Path("reviews", parts[0], parts[1], "index.html")
            if len(parts) >= 3
            else Path("reviews", parts[0], "index.html")
        )
        landing_path = root / landing
        expected = Path("reviews") / slug / "index.html"
        if landing_path in parsed_html and expected not in _local_targets(
            root, landing_path, parsed_html[landing_path]
        ):
            errors.append(f"{landing.as_posix()}: missing manifest page link to reviews/{slug}/")

    for directory in sorted(landing_dirs):
        if len(directory.parts) != 3:
            continue
        project_index = root / directory.parent / "index.html"
        expected = directory / "index.html"
        if project_index in parsed_html and expected not in _local_targets(
            root, project_index, parsed_html[project_index]
        ):
            errors.append(
                f"{_display(project_index, root)}: missing character landing link to {directory.as_posix()}/"
            )

    for slug in sorted(canonical):
        match = re.fullmatch(r"(.+)/r([0-9]+[a-z]?)-(panel|runbook)", slug)
        if not match:
            continue
        other_kind = "runbook" if match.group(3) == "panel" else "panel"
        counterpart = f"{match.group(1)}/r{match.group(2)}-{other_kind}"
        if counterpart not in canonical:
            continue
        page = root / "reviews" / slug / "index.html"
        expected = Path("reviews") / counterpart / "index.html"
        if page in parsed_html and expected not in _local_targets(root, page, parsed_html[page]):
            errors.append(f"reviews/{slug}/index.html: missing cross-link to {counterpart}")

    return canonical, redirect_slugs, landing_dirs


def _validate_assets(root: Path, parsed_html: dict[Path, SiteParser], errors: list[str]) -> None:
    assets_dir = root / "assets"
    files = {path for path in assets_dir.iterdir() if path.is_file()} if assets_dir.is_dir() else set()
    referenced: set[Path] = set()

    for document, parser in parsed_html.items():
        for attribute, reference in parser.resources:
            target = _resolve_local(root, document, reference)
            if target is None:
                continue
            try:
                relative = target.resolve().relative_to(root.resolve())
            except ValueError:
                continue
            if relative.parts and relative.parts[0] == "assets":
                referenced.add(root / relative)
                if attribute not in {"src", "data-full"}:
                    errors.append(
                        f"{_display(document, root)}: asset should use src or data-full, not {attribute}"
                    )

    for path in sorted(files):
        label = _display(path, root)
        if not ASSET_NAME.fullmatch(path.name):
            errors.append(f"{label}: asset name must be a 16-hex SHA-256 prefix plus jpg/png/webp")
            continue
        contents = path.read_bytes()
        digest = hashlib.sha256(contents).hexdigest()
        if not digest.startswith(path.stem):
            errors.append(f"{label}: filename does not match the file's SHA-256 digest")
        header = contents[:12]
        if path.suffix == ".jpg" and not header.startswith(b"\xff\xd8\xff"):
            errors.append(f"{label}: .jpg extension does not match file signature")
        elif path.suffix == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
            errors.append(f"{label}: .png extension does not match file signature")
        elif path.suffix == ".webp" and not (header.startswith(b"RIFF") and header[8:12] == b"WEBP"):
            errors.append(f"{label}: .webp extension does not match file signature")

    for missing in sorted(referenced - files):
        errors.append(f"{_display(missing, root)}: referenced asset is missing")
    for orphan in sorted(files - referenced):
        errors.append(f"{_display(orphan, root)}: orphaned content-addressed asset")


def _tracked_text_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in {".git", "assets"}:
            continue
        yield path


def _validate_publication_safety(root: Path, errors: list[str]) -> None:
    for path in _tracked_text_files(root):
        label = _display(path, root)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{label}: cannot scan as UTF-8 text: {exc}")
            continue
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"{label}: possible {name} in public content")
        if PRIVATE_PATH.search(text):
            errors.append(f"{label}: possible private local filesystem path in public content")


def _validate_workflows(root: Path, errors: list[str]) -> None:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.exists():
        errors.append(".github/workflows: deterministic CI workflow is missing")
        return

    workflows = sorted((*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")))
    if not workflows:
        errors.append(".github/workflows: deterministic CI workflow is missing")
        return

    for path in workflows:
        label = _display(path, root)
        text = path.read_text(encoding="utf-8")
        if "pull_request_target:" in text:
            errors.append(f"{label}: pull_request_target is forbidden for public PR validation")
        if re.search(r"\$\{\{\s*secrets\.", text, re.IGNORECASE):
            errors.append(f"{label}: pull-request workflows must not access secrets")
        if AI_WORKFLOW.search(text):
            errors.append(f"{label}: automatic AI/LLM invocation is forbidden in this public repository")
        if not re.search(r"(?m)^permissions:\s*\n\s{2}contents:\s*read\s*$", text):
            errors.append(f"{label}: top-level permissions must be exactly least-privilege contents: read")
        if len(re.findall(r"(?m)^\s*permissions:\s*$", text)) != 1:
            errors.append(f"{label}: job-level or duplicate permissions blocks are forbidden")
        for permission in ACTION_PERMISSION.finditer(text):
            if permission.groups() != ("contents", "read"):
                errors.append(
                    f"{label}: unnecessary Actions permission: "
                    f"{permission.group(1)}: {permission.group(2)}"
                )
        for match in re.finditer(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)", text):
            action = match.group(1)
            if action.startswith("./"):
                continue
            if "@" not in action or not PINNED_ACTION.fullmatch(action.rsplit("@", 1)[1]):
                errors.append(f"{label}: action is not pinned to an immutable commit SHA: {action}")
        if re.search(r"(?m)^\s{2}pull_request:\s*$", text):
            if not re.search(r"(?m)^concurrency:\s*$", text):
                errors.append(f"{label}: pull-request workflow needs a concurrency group")
            if not re.search(r"(?m)^\s{2}cancel-in-progress:\s*true\s*$", text):
                errors.append(f"{label}: pull-request workflow must cancel superseded commits")


def validate(root: Path) -> list[str]:
    """Return every deterministic validation error below *root*."""
    root = root.resolve()
    errors: list[str] = []
    html_files = sorted(path for path in root.rglob("*.html") if ".git" not in path.parts)
    if not html_files:
        errors.append("no HTML files found")
        return errors

    parsed_html = _validate_html(root, html_files, errors)
    manifest = _load_manifest(root, errors)
    if manifest:
        _validate_manifest(root, manifest, parsed_html, errors)
    _validate_assets(root, parsed_html, errors)
    _validate_publication_safety(root, errors)
    _validate_workflows(root, errors)
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    errors = validate(args.root)
    if errors:
        print(f"site validation failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("site validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
