"""Self-contained HTML dashboard generator for the SQLite application tracker.

Reads the same `applications` table the `tracker` subcommands write to and
renders a single offline-friendly `.html` file: stat cards, Chart.js charts,
and a filterable table. Chart.js itself loads from a CDN on first open;
everything else (CSS, JS, data) is inlined.
"""

import json
import os
import sqlite3
from collections import Counter
from datetime import date
from html import escape
from typing import Optional

BASE_COLUMNS = ["name", "status", "job_id", "applied_on", "notes", "updated_at"]
EXTRA_COLUMNS = ["company", "last_touch", "interview_date", "next_action", "link", "tags"]

BUCKET_ORDER = ["Active", "Interview", "Offer", "Hired", "Rejected/Closed"]

BUCKET_COLORS = {
    "Active": "#3b82f6",
    "Interview": "#f59e0b",
    "Offer": "#8b5cf6",
    "Hired": "#22c55e",
    "Rejected/Closed": "#ef4444",
}

# Covers both the current pipeline statuses and the older Not started/In
# progress/Rejected/Done schema, so the report works against either.
STATUS_BUCKETS = {
    "applied / received": "Active",
    "oa": "Active",
    "recruiter screen": "Active",
    "not started": "Active",
    "interviewing": "Interview",
    "in progress": "Interview",
    "offer": "Offer",
    "hired": "Hired",
    "done": "Hired",
    "rejected": "Rejected/Closed",
    "withdrawn": "Rejected/Closed",
}


def _normalise_status(status: Optional[str]) -> str:
    return STATUS_BUCKETS.get((status or "").strip().lower(), "Active")


def _split_name(name: str) -> "tuple[str, str]":
    if " — " in name:
        company, role = name.split(" — ", 1)
        return company, role
    return name, ""


def _available_columns(conn: sqlite3.Connection) -> "list[str]":
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(applications)")}
    return BASE_COLUMNS + [c for c in EXTRA_COLUMNS if c in existing]


def fetch_rows(db_path: str) -> "list[dict]":
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    columns = _available_columns(conn)
    query = f"SELECT {', '.join(columns)} FROM applications ORDER BY applied_on DESC, name ASC"
    rows = [dict(r) for r in conn.execute(query)]
    conn.close()

    for row in rows:
        company, role = _split_name(row["name"])
        row["company_display"] = row.get("company") or company
        row["role_display"] = role
        row["bucket"] = _normalise_status(row.get("status"))
        tags = row.get("tags") or ""
        row["tag_list"] = [t.strip() for t in tags.split(",") if t.strip()]
    return rows


def compute_stats(rows: "list[dict]") -> dict:
    total = len(rows)
    by_bucket = Counter(r["bucket"] for r in rows)
    by_tag = Counter(t for r in rows for t in r["tag_list"])
    by_month: Counter = Counter()
    for r in rows:
        applied = (r.get("applied_on") or "").strip()
        month = applied[:7] if len(applied) >= 7 else "Unknown"
        by_month[month] += 1

    resolved = [r for r in rows if r["bucket"] != "Active"]
    past_screen = [r for r in rows if r["bucket"] in ("Interview", "Offer", "Hired")]
    rejected = by_bucket.get("Rejected/Closed", 0)

    funnel_stages = {
        "Applied": total,
        "Interview": sum(by_bucket.get(b, 0) for b in ("Interview", "Offer", "Hired")),
        "Offer": sum(by_bucket.get(b, 0) for b in ("Offer", "Hired")),
        "Hired": by_bucket.get("Hired", 0),
    }

    return {
        "total": total,
        "by_bucket": by_bucket,
        "by_tag": by_tag,
        "by_month": dict(sorted(by_month.items())),
        "funnel_stages": funnel_stages,
        "funnel_pct": round(100 * len(past_screen) / total) if total else 0,
        "rejection_pct": round(100 * rejected / len(resolved)) if resolved else 0,
        "unmapped_statuses": sorted(
            {r["status"] for r in rows if (r.get("status") or "").strip().lower() not in STATUS_BUCKETS}
        ),
    }


def _e(value) -> str:
    return escape(str(value)) if value not in (None, "") else "—"


def _table_rows_html(rows: "list[dict]") -> str:
    out = []
    for r in rows:
        link = r.get("link") or ""
        if link.startswith("http"):
            link_html = f'<a href="{escape(link)}" target="_blank" rel="noopener">{escape(link)}</a>'
        else:
            link_html = _e(link)

        notes = r.get("notes") or ""
        notes_short = notes if len(notes) <= 80 else notes[:77] + "..."
        notes_html = f'<span title="{escape(notes)}">{_e(notes_short)}</span>' if notes else "—"

        out.append(
            "<tr data-status=\"{bucket}\" data-company=\"{company}\">"
            "<td>{applied_on}</td><td>{company_disp}</td><td>{role}</td>"
            "<td><span class=\"pill\" style=\"background:{color}\">{bucket}</span></td>"
            "<td>{next_action}</td><td>{tags}</td><td>{interview_date}</td>"
            "<td>{notes}</td><td>{link}</td></tr>".format(
                bucket=escape(r["bucket"]),
                company=escape(r["company_display"]),
                applied_on=_e(r.get("applied_on")),
                company_disp=_e(r["company_display"]),
                role=_e(r["role_display"]),
                color=BUCKET_COLORS[r["bucket"]],
                next_action=_e(r.get("next_action")),
                tags=_e(", ".join(r["tag_list"])),
                interview_date=_e(r.get("interview_date")),
                notes=notes_html,
                link=link_html,
            )
        )
    return "\n".join(out)


def render_html(rows: "list[dict]", stats: dict) -> str:
    generated = date.today().isoformat()

    stat_cards = "".join(
        f'<div class="card" style="border-left-color:{BUCKET_COLORS[b]}">'
        f'<div class="num">{stats["by_bucket"].get(b, 0)}</div><div class="label">{b}</div></div>'
        for b in BUCKET_ORDER
    )

    chart_data = {
        "status": {
            "labels": BUCKET_ORDER,
            "data": [stats["by_bucket"].get(b, 0) for b in BUCKET_ORDER],
            "colors": [BUCKET_COLORS[b] for b in BUCKET_ORDER],
        },
        "tags": {
            "labels": [t for t, _ in stats["by_tag"].most_common()],
            "data": [n for _, n in stats["by_tag"].most_common()],
        },
        "month": {
            "labels": list(stats["by_month"].keys()),
            "data": list(stats["by_month"].values()),
        },
        "funnel": {
            "labels": list(stats["funnel_stages"].keys()),
            "data": list(stats["funnel_stages"].values()),
        },
    }

    if stats["total"] == 0:
        body_main = "<p class=\"empty\">No applications tracked yet. Run <code>swelist tracker add</code> to get started.</p>"
    else:
        body_main = f"""
<section class="cards">{stat_cards}</section>
<section class="charts-grid">
  <div class="chart-card"><h3>Status breakdown</h3><canvas id="statusChart" aria-label="Status breakdown"></canvas></div>
  <div class="chart-card"><h3>By tag</h3><canvas id="tagChart" aria-label="Applications by tag"></canvas></div>
</section>
<section class="charts-grid">
  <div class="chart-card"><h3>By month</h3><canvas id="monthChart" aria-label="Applications by month"></canvas></div>
  <div class="chart-card"><h3>Funnel</h3><canvas id="funnelChart" aria-label="Application funnel"></canvas></div>
</section>
<section class="table-card">
  <div class="filters">
    <input id="search" type="text" placeholder="Search company or role...">
    <select id="statusFilter"><option value="">All statuses</option>
      {"".join(f'<option value="{b}">{b}</option>' for b in BUCKET_ORDER)}
    </select>
    <select id="companyFilter"><option value="">All companies</option>
      {"".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in sorted({r["company_display"] for r in rows}))}
    </select>
  </div>
  <table>
    <thead><tr><th>Date</th><th>Company</th><th>Role</th><th>Status</th>
    <th>Next action</th><th>Tags</th><th>Interview date</th><th>Notes</th><th>Link</th></tr></thead>
    <tbody id="rows">{_table_rows_html(rows)}</tbody>
  </table>
</section>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Search Dashboard</title>
<style>
  :root {{
    --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; --border: #e2e8f0;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); margin: 0; padding: 24px; min-width: 900px;
  }}
  header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 20px; }}
  header h1 {{ font-size: 1.5rem; margin: 0; }}
  .cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 24px; }}
  .card {{ background: var(--card); border-radius: 10px; padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08); border-left: 4px solid; }}
  .card .num {{ font-size: 1.8rem; font-weight: 700; }}
  .card .label {{ color: var(--muted); font-size: .85rem; }}
  .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }}
  .chart-card {{ background: var(--card); border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .chart-card h3 {{ margin: 0 0 12px; font-size: 1rem; }}
  .table-card {{ background: var(--card); border-radius: 10px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .filters {{ display: flex; gap: 8px; margin-bottom: 12px; }}
  .filters input, .filters select {{ padding: 6px 10px; border: 1px solid var(--border); border-radius: 6px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--border); font-size: .875rem; }}
  tbody tr:nth-child(even) {{ background: #f8fafc; }}
  .pill {{ color: #fff; padding: 2px 8px; border-radius: 999px; font-size: .75rem; }}
  .empty {{ color: var(--muted); padding: 40px; text-align: center; }}
  footer {{ margin-top: 24px; color: var(--muted); font-size: .8rem; text-align: center; }}
  @media (max-width: 1100px) {{ .cards {{ grid-template-columns: repeat(3, 1fr); }} }}
</style>
</head>
<body>
<header><h1>🔍 Job Search Dashboard</h1><span>Generated: {generated}</span></header>
{body_main}
<footer>Generated by swelist &middot; {generated}</footer>
<script>
const CHART_DATA = {json.dumps(chart_data)};
try {{
  const s = document.createElement('script');
  s.src = 'https://cdn.jsdelivr.net/npm/chart.js';
  s.onload = renderCharts;
  document.head.appendChild(s);
}} catch (e) {{ /* charts degrade to stat cards */ }}

function renderCharts() {{
  try {{
    if (document.getElementById('statusChart')) {{
      new Chart(document.getElementById('statusChart'), {{
        type: 'doughnut',
        data: {{ labels: CHART_DATA.status.labels,
          datasets: [{{ data: CHART_DATA.status.data, backgroundColor: CHART_DATA.status.colors }}] }}
      }});
    }}
    if (document.getElementById('tagChart') && CHART_DATA.tags.labels.length) {{
      new Chart(document.getElementById('tagChart'), {{
        type: 'bar',
        data: {{ labels: CHART_DATA.tags.labels, datasets: [{{ data: CHART_DATA.tags.data, backgroundColor: '#3b82f6' }}] }},
        options: {{ indexAxis: 'y' }}
      }});
    }}
    if (document.getElementById('monthChart')) {{
      new Chart(document.getElementById('monthChart'), {{
        type: 'bar',
        data: {{ labels: CHART_DATA.month.labels, datasets: [{{ data: CHART_DATA.month.data, backgroundColor: '#8b5cf6' }}] }}
      }});
    }}
    if (document.getElementById('funnelChart')) {{
      new Chart(document.getElementById('funnelChart'), {{
        type: 'bar',
        data: {{ labels: CHART_DATA.funnel.labels,
          datasets: [{{ data: CHART_DATA.funnel.data, backgroundColor: '#22c55e' }}] }},
        options: {{ indexAxis: 'y' }}
      }});
    }}
  }} catch (e) {{ /* charts degrade to stat cards on any Chart.js failure */ }}
}}

(function filters() {{
  const search = document.getElementById('search');
  const statusFilter = document.getElementById('statusFilter');
  const companyFilter = document.getElementById('companyFilter');
  if (!search) return;
  function apply() {{
    const q = search.value.toLowerCase();
    const status = statusFilter.value;
    const company = companyFilter.value;
    document.querySelectorAll('#rows tr').forEach(function(row) {{
      const text = row.textContent.toLowerCase();
      const matchesText = !q || text.includes(q);
      const matchesStatus = !status || row.dataset.status === status;
      const matchesCompany = !company || row.dataset.company === company;
      row.style.display = (matchesText && matchesStatus && matchesCompany) ? '' : 'none';
    }});
  }}
  search.addEventListener('input', apply);
  statusFilter.addEventListener('change', apply);
  companyFilter.addEventListener('change', apply);
}})();
</script>
</body>
</html>
"""


def build_report(db_path: str, output_path: str) -> dict:
    """Generate the dashboard HTML and write it to output_path. Returns stats."""
    rows = fetch_rows(db_path)
    stats = compute_stats(rows)
    html = render_html(rows, stats)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return stats
