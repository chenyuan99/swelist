import csv
import io
import json
import os
import sqlite3
import webbrowser
from typing import Optional

import typer
from rich import print
from rich.table import Table

from swelist.report import build_report

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


@tracker_app.command("add")
def tracker_add(
    name: str = typer.Argument(help='Application name e.g. "Amazon — SDE, AWS"'),
    status: str = typer.Option("Not started", help="Status: Not started | In progress | Rejected | Done"),
    job_id: Optional[str] = typer.Option(None, help="Job ID from the posting"),
    applied_on: Optional[str] = typer.Option(None, help="Date applied (YYYY-MM-DD)"),
    notes: Optional[str] = typer.Option(None, help="Free-text notes"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """Add a new application (skips silently if name already exists)."""
    if status not in STATUS_VALUES:
        print(f"[red]Invalid status '{status}'. Choose from: {', '.join(sorted(STATUS_VALUES))}[/red]")
        raise typer.Exit(1)
    conn = _connect(db)
    cursor = conn.execute(
        "INSERT OR IGNORE INTO applications (name, status, job_id, applied_on, notes) VALUES (?, ?, ?, ?, ?)",
        (name, status, job_id, applied_on, notes),
    )
    conn.commit()
    conn.close()
    if cursor.rowcount:
        print(f"[green]Added:[/green] {name} → {status}")
    else:
        print(f"[yellow]Skipped (already exists):[/yellow] {name}")


@tracker_app.command("update")
def tracker_update(
    name: str = typer.Argument(help='Application name to update'),
    status: str = typer.Option(..., help="New status: Not started | In progress | Rejected | Done"),
    notes: Optional[str] = typer.Option(None, help="Replace notes (omit to leave unchanged)"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """Update the status (and optionally notes) of an existing application."""
    if status not in STATUS_VALUES:
        print(f"[red]Invalid status '{status}'. Choose from: {', '.join(sorted(STATUS_VALUES))}[/red]")
        raise typer.Exit(1)
    conn = _connect(db)
    if notes is not None:
        cursor = conn.execute(
            "UPDATE applications SET status=?, notes=?, updated_at=datetime('now') WHERE name=?",
            (status, notes, name),
        )
    else:
        cursor = conn.execute(
            "UPDATE applications SET status=?, updated_at=datetime('now') WHERE name=?",
            (status, name),
        )
    conn.commit()
    conn.close()
    if cursor.rowcount:
        print(f"[green]Updated:[/green] {name} → {status}")
    else:
        print(f"[red]Not found:[/red] {name}")
        raise typer.Exit(1)


@tracker_app.command("get")
def tracker_get(
    name: str = typer.Argument(help="Exact application name to look up"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
):
    """Get a single application by exact name (JSON output for agent use)."""
    conn = _connect(db)
    row = conn.execute(
        "SELECT name, status, job_id, applied_on, notes, updated_at FROM applications WHERE name=?",
        (name,),
    ).fetchone()
    conn.close()
    if row:
        print(json.dumps(dict(row), ensure_ascii=False))
    else:
        print(json.dumps(None))
        raise typer.Exit(1)


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


@tracker_app.command("report")
def tracker_report(
    output: str = typer.Argument("reports/application-dashboard.html", help="Output path for the HTML dashboard"),
    db: str = typer.Option(DEFAULT_DB, help="Path to SQLite database"),
    open_browser: bool = typer.Option(False, "--open", help="Open the dashboard in your default browser"),
):
    """Generate a self-contained HTML dashboard from the tracker database."""
    if not os.path.exists(db):
        print(f"[red]No tracker database found at {db}. Run 'swelist tracker init' first.[/red]")
        raise typer.Exit(1)

    stats = build_report(db, output)

    print(f"[green]Dashboard generated:[/green] {output}")
    if stats["total"] == 0:
        print("[yellow]No applications tracked yet.[/yellow]")
    else:
        buckets = stats["by_bucket"]
        print(
            f"Total: {stats['total']} · Active: {buckets.get('Active', 0)} · "
            f"Interview: {buckets.get('Interview', 0)} · Offer: {buckets.get('Offer', 0)} · "
            f"Hired: {buckets.get('Hired', 0)} · Rejected/Closed: {buckets.get('Rejected/Closed', 0)}"
        )
        print(f"Funnel: {stats['funnel_pct']}% progressed past resume screen")

    if open_browser:
        webbrowser.open(f"file://{os.path.abspath(output)}")
