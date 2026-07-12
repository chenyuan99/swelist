"""Structural tests for the html-report skill (skills/html-report/SKILL.md).

Mirrors the pattern used for other reference-driven skills in this repo:
plain assertions against the real files, catching the kind of drift CI
would otherwise miss (missing required sections, stale references to the
old CSV-based design, a generated-report path that isn't gitignored).
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_FILE = REPO_ROOT / "skills" / "html-report" / "SKILL.md"
GITIGNORE = REPO_ROOT / ".gitignore"
PROFILE = REPO_ROOT / "skills" / "profile.md"

# CLAUDE.md's "Writing a new skill" section requires these sections, in order.
REQUIRED_SECTIONS = [
    "## When to Use This Skill",
    "## Setup",
    "## Config:",
    "## Workflow",
    "## Report Format",
    "## Edge Cases",
]


def _skill_text():
    return SKILL_FILE.read_text(encoding="utf-8")


def test_skill_file_exists():
    assert SKILL_FILE.exists(), f"{SKILL_FILE} not found"


def test_skill_frontmatter_has_name_and_description():
    text = _skill_text()
    assert text.startswith("---\n"), "SKILL.md must start with a YAML frontmatter block"
    frontmatter = text.split("---", 2)[1]
    assert "name:" in frontmatter
    assert "description:" in frontmatter


def test_skill_file_is_non_trivial():
    text = _skill_text().strip()
    assert len(text) > 2000, "SKILL.md appears suspiciously short"


def test_skill_contains_required_sections():
    text = _skill_text()
    for section in REQUIRED_SECTIONS:
        assert section in text, f"Missing required section: {section!r}"


def test_skill_reads_the_shared_sqlite_tracker():
    text = _skill_text()
    assert "~/.offerplus/applications.db" in text
    assert "job-application-manager" in text
    assert "sqlite" in text.lower()


def test_skill_no_longer_references_the_old_csv_design():
    text = _skill_text()
    assert "job_search_tracker.csv" not in text
    assert "documents/applications" not in text


def test_skill_is_documented_as_read_only():
    text = _skill_text()
    assert "read-only" in text.lower()


def test_reports_folder_is_gitignored():
    rules = {line.strip() for line in GITIGNORE.read_text(encoding="utf-8").splitlines()}
    assert "reports/" in rules, "reports/ must be gitignored — generated dashboards are personal output"


def test_profile_lists_html_report_skill():
    text = PROFILE.read_text(encoding="utf-8")
    assert "`html-report`" in text
