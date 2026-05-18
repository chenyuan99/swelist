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
