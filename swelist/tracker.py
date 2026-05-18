import csv
import io
import json
import os
import sqlite3
from typing import Optional

import typer
from rich import print
from rich.table import Table

tracker_app = typer.Typer(help="Local SQLite job application tracker")

DEFAULT_DB = os.path.expanduser("~/.offerplus/applications.db")

INIT_SQL = """
CREATE TABLE IF NOT EXISTS applications (
    name        TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    job_id      TEXT,
    applied_on  TEXT,
    notes       TEXT,
    updated_at  TEXT DEFAULT (datetime('now'))
);
"""

STATUS_VALUES = {"Not started", "In progress", "Rejected", "Done"}


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@tracker_app.command("init")
def tracker_init(
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """Initialize the tracker database (safe to re-run)."""
    conn = _connect(db)
    conn.execute(INIT_SQL)
    conn.commit()
    conn.close()
    print(f"[green]Tracker initialized at {db}[/green]")


@tracker_app.command("list")
def tracker_list(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    company: Optional[str] = typer.Option(None, help="Filter by company name (partial match)"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """List tracked job applications."""
    conn = _connect(db)

    query = "SELECT name, status, job_id, applied_on, updated_at FROM applications WHERE 1=1"
    params: list = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if company:
        query += " AND name LIKE ?"
        params.append(f"%{company}%")

    query += " ORDER BY updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("[yellow]No applications found.[/yellow]")
        raise typer.Exit()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Application", min_width=40)
    table.add_column("Status", min_width=12)
    table.add_column("Job ID", min_width=10)
    table.add_column("Applied", min_width=12)
    table.add_column("Updated", min_width=20)

    status_colors = {
        "Done": "green",
        "In progress": "yellow",
        "Rejected": "red",
        "Not started": "dim",
    }

    for row in rows:
        color = status_colors.get(row["status"], "white")
        table.add_row(
            row["name"],
            f"[{color}]{row['status']}[/{color}]",
            row["job_id"] or "—",
            row["applied_on"] or "—",
            row["updated_at"] or "—",
        )

    print(table)
    print(f"\n[dim]{len(rows)} application(s)[/dim]")


@tracker_app.command("export")
def tracker_export(
    format: str = typer.Option("csv", help="Export format: csv or json"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """Export all applications to CSV or JSON (stdout)."""
    conn = _connect(db)
    rows = conn.execute(
        "SELECT name, status, job_id, applied_on, notes, updated_at FROM applications ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    if format == "json":
        print(json.dumps([dict(r) for r in rows], indent=2, ensure_ascii=False))
    else:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["name", "status", "job_id", "applied_on", "notes", "updated_at"])
        writer.writeheader()
        writer.writerows([dict(r) for r in rows])
        print(buf.getvalue(), end="")
