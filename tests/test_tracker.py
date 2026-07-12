import json
import os
import sqlite3
import tempfile

import pytest
from typer.testing import CliRunner

from swelist.tracker import DEFAULT_DB, INIT_SQL, tracker_app

runner = CliRunner()


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_applications.db")
    conn = sqlite3.connect(path)
    conn.execute(INIT_SQL)
    conn.commit()
    conn.close()
    return path


@pytest.fixture
def populated_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO applications (name, status, job_id, applied_on) VALUES (?, ?, ?, ?)",
        [
            ("Amazon — SDE, AWS", "In progress", "10414382", "2026-05-17"),
            ("Google — Software Engineer", "Rejected", "G123", "2026-04-01"),
            ("Meta — SWE, Infra", "Done", "M456", "2026-03-15"),
            ("Stripe — Backend Engineer", "Not started", None, None),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


class TestTrackerInit:
    def test_creates_db_and_table(self, tmp_path):
        path = str(tmp_path / "new.db")
        result = runner.invoke(tracker_app, ["init", "--db", path])
        assert result.exit_code == 0
        assert os.path.exists(path)
        conn = sqlite3.connect(path)
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        assert ("applications",) in tables
        conn.close()

    def test_idempotent(self, db_path):
        result = runner.invoke(tracker_app, ["init", "--db", db_path])
        assert result.exit_code == 0

    def test_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "apps.db")
        result = runner.invoke(tracker_app, ["init", "--db", path])
        assert result.exit_code == 0
        assert os.path.exists(path)


class TestTrackerList:
    def test_lists_all(self, populated_db):
        result = runner.invoke(tracker_app, ["list", "--db", populated_db])
        assert result.exit_code == 0
        assert "Amazon" in result.output
        assert "Google" in result.output
        assert "Meta" in result.output
        assert "Stripe" in result.output

    def test_filter_by_status(self, populated_db):
        result = runner.invoke(tracker_app, ["list", "--status", "Rejected", "--db", populated_db])
        assert result.exit_code == 0
        assert "Google" in result.output
        assert "Amazon" not in result.output

    def test_filter_by_company(self, populated_db):
        result = runner.invoke(tracker_app, ["list", "--company", "amazon", "--db", populated_db])
        assert result.exit_code == 0
        assert "Amazon" in result.output
        assert "Google" not in result.output

    def test_empty_db(self, db_path):
        result = runner.invoke(tracker_app, ["list", "--db", db_path])
        assert result.exit_code == 0
        assert "No applications found" in result.output


class TestTrackerAdd:
    def test_add_new(self, db_path):
        result = runner.invoke(tracker_app, [
            "add", "Stripe — Backend Engineer",
            "--status", "In progress",
            "--job-id", "S789",
            "--applied-on", "2026-05-01",
            "--db", db_path,
        ])
        assert result.exit_code == 0
        assert "Added" in result.output
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT * FROM applications WHERE name='Stripe — Backend Engineer'").fetchone()
        conn.close()
        assert row is not None
        assert row[1] == "In progress"
        assert row[2] == "S789"

    def test_add_duplicate_skips(self, populated_db):
        result = runner.invoke(tracker_app, [
            "add", "Amazon — SDE, AWS",
            "--status", "Rejected",
            "--db", populated_db,
        ])
        assert result.exit_code == 0
        assert "Skipped" in result.output
        conn = sqlite3.connect(populated_db)
        row = conn.execute("SELECT status FROM applications WHERE name='Amazon — SDE, AWS'").fetchone()
        conn.close()
        assert row[0] == "In progress"  # unchanged

    def test_add_invalid_status(self, db_path):
        result = runner.invoke(tracker_app, [
            "add", "Acme — Engineer",
            "--status", "Pending",
            "--db", db_path,
        ])
        assert result.exit_code == 1
        assert "Invalid status" in result.output

    def test_add_defaults(self, db_path):
        result = runner.invoke(tracker_app, ["add", "Acme — Engineer", "--db", db_path])
        assert result.exit_code == 0
        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT status FROM applications WHERE name='Acme — Engineer'").fetchone()
        conn.close()
        assert row[0] == "Not started"


class TestTrackerUpdate:
    def test_update_status(self, populated_db):
        result = runner.invoke(tracker_app, [
            "update", "Amazon — SDE, AWS",
            "--status", "Rejected",
            "--db", populated_db,
        ])
        assert result.exit_code == 0
        assert "Updated" in result.output
        conn = sqlite3.connect(populated_db)
        row = conn.execute("SELECT status FROM applications WHERE name='Amazon — SDE, AWS'").fetchone()
        conn.close()
        assert row[0] == "Rejected"

    def test_update_with_notes(self, populated_db):
        result = runner.invoke(tracker_app, [
            "update", "Google — Software Engineer",
            "--status", "In progress",
            "--notes", "Recruiter reached out",
            "--db", populated_db,
        ])
        assert result.exit_code == 0
        conn = sqlite3.connect(populated_db)
        row = conn.execute("SELECT status, notes FROM applications WHERE name='Google — Software Engineer'").fetchone()
        conn.close()
        assert row[0] == "In progress"
        assert row[1] == "Recruiter reached out"

    def test_update_not_found(self, db_path):
        result = runner.invoke(tracker_app, [
            "update", "Nonexistent — Role",
            "--status", "Rejected",
            "--db", db_path,
        ])
        assert result.exit_code == 1
        assert "Not found" in result.output

    def test_update_invalid_status(self, populated_db):
        result = runner.invoke(tracker_app, [
            "update", "Amazon — SDE, AWS",
            "--status", "Pending",
            "--db", populated_db,
        ])
        assert result.exit_code == 1
        assert "Invalid status" in result.output


class TestTrackerGet:
    def test_get_existing(self, populated_db):
        result = runner.invoke(tracker_app, ["get", "Amazon — SDE, AWS", "--db", populated_db])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Amazon — SDE, AWS"
        assert data["status"] == "In progress"
        assert data["job_id"] == "10414382"

    def test_get_not_found(self, db_path):
        result = runner.invoke(tracker_app, ["get", "Nonexistent — Role", "--db", db_path])
        assert result.exit_code == 1
        assert json.loads(result.output) is None

    def test_get_unicode(self, populated_db):
        result = runner.invoke(tracker_app, ["get", "Amazon — SDE, AWS", "--db", populated_db])
        assert "—" in result.output  # em dash not escaped


class TestTrackerExport:
    def test_export_csv(self, populated_db):
        result = runner.invoke(tracker_app, ["export", "--format", "csv", "--db", populated_db])
        assert result.exit_code == 0
        assert "name,status" in result.output
        assert "Amazon — SDE, AWS" in result.output
        assert "In progress" in result.output

    def test_export_json(self, populated_db):
        result = runner.invoke(tracker_app, ["export", "--format", "json", "--db", populated_db])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 4
        names = {r["name"] for r in data}
        assert "Amazon — SDE, AWS" in names
        assert "Google — Software Engineer" in names

    def test_export_json_fields(self, populated_db):
        result = runner.invoke(tracker_app, ["export", "--format", "json", "--db", populated_db])
        data = json.loads(result.output)
        row = next(r for r in data if r["name"] == "Amazon — SDE, AWS")
        assert row["status"] == "In progress"
        assert row["job_id"] == "10414382"
        assert row["applied_on"] == "2026-05-17"


class TestTrackerReport:
    def test_report_writes_html_file(self, populated_db, tmp_path):
        output = str(tmp_path / "dashboard.html")
        result = runner.invoke(tracker_app, ["report", output, "--db", populated_db])
        assert result.exit_code == 0
        assert "Dashboard generated" in result.output
        assert os.path.exists(output)
        with open(output, encoding="utf-8") as f:
            assert f.read().startswith("<!doctype html>")

    def test_report_prints_bucket_summary(self, populated_db, tmp_path):
        output = str(tmp_path / "dashboard.html")
        result = runner.invoke(tracker_app, ["report", output, "--db", populated_db])
        assert "Total: 4" in result.output
        assert "Funnel:" in result.output

    def test_report_default_output_path(self, populated_db, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(tracker_app, ["report", "--db", populated_db])
        assert result.exit_code == 0
        assert os.path.exists(tmp_path / "reports" / "application-dashboard.html")

    def test_report_empty_db(self, db_path, tmp_path):
        output = str(tmp_path / "dashboard.html")
        result = runner.invoke(tracker_app, ["report", output, "--db", db_path])
        assert result.exit_code == 0
        assert "No applications tracked yet" in result.output

    def test_report_missing_db(self, tmp_path):
        missing = str(tmp_path / "does-not-exist.db")
        output = str(tmp_path / "dashboard.html")
        result = runner.invoke(tracker_app, ["report", output, "--db", missing])
        assert result.exit_code == 1
        assert "No tracker database found" in result.output
        assert not os.path.exists(output)

    def test_report_open_flag_launches_browser(self, populated_db, tmp_path, mocker):
        output = str(tmp_path / "dashboard.html")
        mock_open = mocker.patch("swelist.tracker.webbrowser.open")
        result = runner.invoke(tracker_app, ["report", output, "--db", populated_db, "--open"])
        assert result.exit_code == 0
        mock_open.assert_called_once()
        assert output in mock_open.call_args[0][0]

    def test_report_without_open_flag_does_not_launch_browser(self, populated_db, tmp_path, mocker):
        output = str(tmp_path / "dashboard.html")
        mock_open = mocker.patch("swelist.tracker.webbrowser.open")
        runner.invoke(tracker_app, ["report", output, "--db", populated_db])
        mock_open.assert_not_called()
