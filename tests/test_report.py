import sqlite3

import pytest

from swelist.report import build_report, compute_stats, fetch_rows, render_html
from swelist.tracker import INIT_SQL


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "applications.db")
    conn = sqlite3.connect(path)
    conn.execute(INIT_SQL)
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def populated_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO applications (name, status, job_id, applied_on, notes) VALUES (?, ?, ?, ?, ?)",
        [
            ("Amazon — SDE, AWS", "In progress", "10414382", "2026-05-17", "great team"),
            ("Google — Software Engineer", "Rejected", "G123", "2026-04-01", None),
            ("Meta — SWE, Infra", "Done", "M456", "2026-03-15", None),
            ("Stripe — Backend Engineer", "Not started", None, None, None),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def full_schema_db(tmp_path):
    """A DB using the richer v0.5.0 schema (company, tags, next_action, etc.)."""
    path = str(tmp_path / "full.db")
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE applications (
            name TEXT PRIMARY KEY, status TEXT NOT NULL, job_id TEXT, company TEXT,
            applied_on TEXT, last_touch TEXT, interview_date TEXT, next_action TEXT,
            link TEXT, tags TEXT, notes TEXT, updated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute(
        "INSERT INTO applications (name, status, company, applied_on, interview_date, "
        "next_action, link, tags, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "Anthropic — SWE",
            "Interviewing",
            "Anthropic",
            "2026-06-01",
            "2026-06-09",
            "Prep",
            "https://boards.greenhouse.io/anthropic/jobs/1",
            "Referral,Remote",
            "Recruiter call went well",
        ),
    )
    conn.commit()
    conn.close()
    return path


class TestFetchRows:
    def test_fetch_rows_count_and_bucket_mapping(self, populated_db):
        rows = fetch_rows(populated_db)
        assert len(rows) == 4
        buckets = {r["name"]: r["bucket"] for r in rows}
        assert buckets["Amazon — SDE, AWS"] == "Interview"  # In progress
        assert buckets["Google — Software Engineer"] == "Rejected/Closed"
        assert buckets["Meta — SWE, Infra"] == "Hired"  # Done
        assert buckets["Stripe — Backend Engineer"] == "Active"  # Not started

    def test_fetch_rows_splits_company_and_role(self, populated_db):
        rows = fetch_rows(populated_db)
        amazon = next(r for r in rows if r["name"] == "Amazon — SDE, AWS")
        assert amazon["company_display"] == "Amazon"
        assert amazon["role_display"] == "SDE, AWS"

    def test_fetch_rows_falls_back_on_base_schema(self, populated_db):
        rows = fetch_rows(populated_db)
        # v0.2.x schema has no tags/company/etc columns — should not error
        assert all(r["tag_list"] == [] for r in rows)
        assert all(r.get("link") is None for r in rows)

    def test_fetch_rows_uses_full_schema_columns(self, full_schema_db):
        rows = fetch_rows(full_schema_db)
        row = rows[0]
        assert row["company_display"] == "Anthropic"
        assert row["tag_list"] == ["Referral", "Remote"]
        assert row["link"] == "https://boards.greenhouse.io/anthropic/jobs/1"
        assert row["bucket"] == "Interview"


class TestComputeStats:
    def test_totals_and_buckets(self, populated_db):
        stats = compute_stats(fetch_rows(populated_db))
        assert stats["total"] == 4
        assert stats["by_bucket"]["Interview"] == 1
        assert stats["by_bucket"]["Hired"] == 1
        assert stats["by_bucket"]["Rejected/Closed"] == 1
        assert stats["by_bucket"]["Active"] == 1

    def test_funnel_and_rejection_rate(self, populated_db):
        stats = compute_stats(fetch_rows(populated_db))
        # Interview + Hired = 2 of 4 total progressed past screen
        assert stats["funnel_pct"] == 50
        # 3 resolved (non-Active): 1 rejected / 3 resolved = 33%
        assert stats["rejection_pct"] == 33

    def test_empty_rows(self):
        stats = compute_stats([])
        assert stats["total"] == 0
        assert stats["funnel_pct"] == 0
        assert stats["rejection_pct"] == 0

    def test_by_tag_from_full_schema(self, full_schema_db):
        stats = compute_stats(fetch_rows(full_schema_db))
        assert stats["by_tag"]["Referral"] == 1
        assert stats["by_tag"]["Remote"] == 1

    def test_unmapped_status_is_flagged(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "INSERT INTO applications (name, status) VALUES (?, ?)",
            ("Weird — Co", "Some Unknown Status"),
        )
        conn.commit()
        conn.close()
        stats = compute_stats(fetch_rows(db_path))
        assert "Some Unknown Status" in stats["unmapped_statuses"]
        # unmapped statuses still fall back to Active rather than being dropped
        assert stats["by_bucket"]["Active"] == 1


class TestRenderHtml:
    def test_render_html_basic_structure(self, populated_db):
        rows = fetch_rows(populated_db)
        stats = compute_stats(rows)
        html = render_html(rows, stats)
        assert html.startswith("<!doctype html>")
        assert "cdn.jsdelivr.net/npm/chart.js" in html
        assert html.count('<tr data-status') == 4
        assert "Amazon" in html
        assert "—" in html  # em dash preserved, not mangled

    def test_render_html_empty_state(self):
        html = render_html([], compute_stats([]))
        assert "No applications tracked yet" in html
        assert '<tr data-status' not in html

    def test_render_html_link_only_rendered_when_http(self, full_schema_db):
        rows = fetch_rows(full_schema_db)
        html = render_html(rows, compute_stats(rows))
        assert '<a href="https://boards.greenhouse.io/anthropic/jobs/1"' in html


class TestBuildReport:
    def test_writes_file_and_returns_stats(self, populated_db, tmp_path):
        output = str(tmp_path / "out" / "dashboard.html")
        stats = build_report(populated_db, output)
        assert stats["total"] == 4
        with open(output, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("<!doctype html>")

    def test_creates_parent_directory(self, populated_db, tmp_path):
        output = str(tmp_path / "nested" / "dir" / "dashboard.html")
        build_report(populated_db, output)
        assert (tmp_path / "nested" / "dir" / "dashboard.html").exists()
