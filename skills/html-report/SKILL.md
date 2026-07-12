---
name: HTML Report — Application Tracker Dashboard
description: Generates a self-contained HTML dashboard (stat cards, Chart.js charts, filterable table) from the same SQLite tracker database used by application-manager — opens directly in a browser, no server required
summary: >
  Use this skill to turn the `applications` table in the shared SQLite
  tracker (`~/.offerplus/applications.db`, same database and schema the
  `job-application-manager` skill writes to) into a single self-contained
  HTML dashboard. The report shows Active/Interview/Offer/Rejected stat
  cards, a status-breakdown doughnut chart, a tags bar chart, an
  applications-by-month bar chart, and a pipeline funnel chart, plus a
  filterable, sortable table of every tracked application. Everything —
  CSS, JS, and data — is inlined into one `.html` file except the Chart.js
  library, which loads from a CDN on first open and degrades gracefully to
  the stat cards if offline. The skill only reads the tracker database; it
  never writes back, so re-running it after a Gmail sync or a manual
  `swelist tracker update` is always safe.
version: 0.2.0
author: Yuan Chen
repository: https://github.com/chenyuan99/swelist
keywords:
  - html-report
  - dashboard
  - job-search
  - application-tracker
  - chart.js
  - reporting
  - sqlite
  - data-visualization
tags:
  - career
  - productivity
  - reporting
  - job-search
category: career
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["sqlite3"]
      env: []
      mcp: []
    config:
      - key: sqlite_db_path
        description: Path to the shared SQLite tracker database (same value application-manager uses)
        default: ~/.offerplus/applications.db
      - key: report_output_path
        description: Default output path for the generated dashboard
        default: reports/application-dashboard.html
---

# HTML Report — Application Tracker Dashboard

## When to Use This Skill

Trigger when the user asks to:

- Generate, build, or refresh a job search dashboard ("build me a dashboard", "generate the html report", "/html-report")
- Visualize their application pipeline ("show me a chart of my applications", "visualize my job search")
- Export a shareable, offline view of their tracker ("give me something I can open in a browser", "make a report I can send")
- Re-run the dashboard after syncing new applications ("refresh the dashboard", "update the report with my latest applications")

Keywords: `html report`, `dashboard`, `visualize applications`, `application chart`, `job search report`, `funnel chart`, `/html-report`

This skill is **read-only**: it never modifies the tracker database. Use
the `job-application-manager` skill (or `swelist tracker add/update`) to
change application status — this skill only renders what's already there.

**Requires the `sqlite` tracker backend.** If `profile.md` has
`Tracker backend: notion`, this skill has nothing to read — see Edge Cases.

---

## Setup

**Always read `skills/profile.md` first.** It's the same file
`job-application-manager` reads, so both skills stay pointed at the same
database.

Resolve before continuing:

1. **Tracker backend** — `Integrations > Tracker Backend`
   - Must be `sqlite`. If `notion`, tell the user this report needs the
     SQLite backend and stop (see Edge Cases) rather than fabricating data.
2. **SQLite DB path** — `Integrations > Tracker Backend > SQLite DB path`
   - Default: `~/.offerplus/applications.db`
   - If the file doesn't exist: tell the user to run `swelist tracker init`
     (or sync via `job-application-manager` first) — do not generate an
     empty report silently.
3. **Output path** — argument if given, else `reports/application-dashboard.html`.
   Create the `reports/` directory if it doesn't exist.

---

## Config: Argument Parsing

| Input | Behavior |
|---|---|
| No argument | Output to `reports/application-dashboard.html` |
| A path argument (e.g. `/html-report ~/Desktop/report.html`) | Use that path instead |
| `--open` flag | After writing, tell the user to open the file — the skill cannot launch a browser itself |

---

## Config: SQLite Schema (read-only)

Same table `job-application-manager` writes to. See that skill's
"Config: SQLite Schema" section for the authoritative DDL and migration
history. This skill never runs `ALTER TABLE` — it just adapts to whichever
columns exist.

**Full (v0.5.0) schema:**

```sql
CREATE TABLE applications (
  name           TEXT PRIMARY KEY,   -- "Company — Role Title"
  status         TEXT NOT NULL,
  job_id         TEXT,
  company        TEXT,
  applied_on     TEXT,               -- ISO date YYYY-MM-DD
  last_touch     TEXT,               -- ISO date of most recent email
  interview_date TEXT,               -- ISO date of next scheduled interview
  next_action    TEXT,               -- Waiting | Prep | Follow up | Send availability
  link           TEXT,               -- job posting or portal URL
  tags           TEXT,               -- comma-separated e.g. "Referral,Remote"
  notes          TEXT,
  updated_at     TEXT DEFAULT (datetime('now'))
);
```

**Older (v0.2.x) schema** only has `name, status, job_id, applied_on, notes,
updated_at` — that's also exactly what `swelist tracker export` returns
today. Check which columns are present before building the SELECT:

```bash
sqlite3 <DB_PATH> "PRAGMA table_info(applications);"
```

If `company`, `last_touch`, `interview_date`, `next_action`, `link`, or
`tags` are missing, treat them as empty for every row and omit any
chart/table section that depends entirely on them (see Layout, Edge Cases).

---

## Config: Status Normalisation

Map every row's `status` value to one of five canonical buckets before
computing stats. Comparisons are case-insensitive. Covers both the current
pipeline statuses and the older v0.2.x values, so the report works
regardless of which schema generation wrote the row.

| Status value | Canonical bucket | Colour |
|---|---|---|
| `Applied / Received`, `OA`, `Recruiter screen`, `Not started` | Active | `#3b82f6` |
| `Interviewing`, `In progress` | Interview | `#f59e0b` |
| `Offer` | Offer | `#8b5cf6` |
| `Hired`, `Done` | Hired | `#22c55e` |
| `Rejected`, `Withdrawn` | Rejected/Closed | `#ef4444` |
| any other/unrecognised value | Active (fallback) — note in the report footer as "N rows had an unmapped status" | `#3b82f6` |

`In progress` (v0.2.x) can't be distinguished from a true "Interviewing"
stage — bucket it as Interview and note in the footer that granular
staging requires the v0.5.0 schema.

---

## Workflow

```
INPUT: output_path (optional, default "reports/application-dashboard.html")
       open_flag (optional)

STEP 0  Load profile + resolve DB
  Read skills/profile.md → tracker_backend, DB_PATH
  IF tracker_backend != "sqlite": stop, explain (see Edge Cases)
  IF DB_PATH file does not exist: stop, tell user to run `swelist tracker init`

STEP 1  Parse arguments
  IF path argument given: output_path = that path
  ELSE: output_path = "reports/application-dashboard.html"
  mkdir -p dirname(output_path)

STEP 2  Collect data
  columns = sqlite3 DB_PATH "PRAGMA table_info(applications);"
  select_cols = ["name","status","job_id","applied_on","notes","updated_at"]
                + any of ["company","last_touch","interview_date","next_action","link","tags"]
                  that exist in columns
  rows = sqlite3 -json DB_PATH
    "SELECT {', '.join(select_cols)} FROM applications ORDER BY applied_on DESC, name ASC"
  FOR each row:
    row.company_display = row.company OR extract_company_from_name(row.name)  # part before " — "
    row.role_display    = extract_role_from_name(row.name)                    # part after " — "
    row.bucket           = normalise_status(row.status)   # Config: Status Normalisation
    row.tag_list          = split(row.tags, ",") if present else []

STEP 3  Compute summary stats
  total              = len(rows)
  by_bucket           = count rows grouped by row.bucket
  by_tag              = count occurrences of each tag across row.tag_list (flatten)
  by_month            = count rows grouped by YYYY-MM of row.applied_on (blank → "Unknown")
  resolved            = rows where bucket != "Active"
  past_screen         = rows where bucket IN ("Interview", "Offer", "Hired")
  funnel_rate_pct     = round(100 * len(past_screen) / total) if total else 0
  rejection_rate_pct  = round(100 * count(bucket == "Rejected/Closed") / len(resolved)) if resolved else 0
  funnel_stages       = { Applied: total,
                          Interview: count(bucket IN (Interview, Offer, Hired)),
                          Offer: count(bucket IN (Offer, Hired)),
                          Hired: count(bucket == Hired) }

STEP 4  Generate HTML (see Layout, Design spec, and Charts below)
  Build one self-contained HTML string:
    - inline <style> block (palette, cards, charts grid, table)
    - stat cards row
    - two 2-column chart rows (doughnut, tags bar / by-month bar, funnel bar)
    - filterable table (search input + status/company dropdowns, client-side JS)
    - footer: "Generated by Claude Code · swelist · {ISO date}"
  Charts render via Chart.js loaded from https://cdn.jsdelivr.net/npm/chart.js
    (only external dependency; wrap chart init in try/catch so a failed CDN
    fetch degrades to the stat cards instead of breaking the page)

STEP 5  Write and confirm
  Write the complete HTML to output_path (Write tool — overwrite if it exists)
  IF open_flag: tell the user to open the file themselves (cannot launch a browser)
  Print the Report Format summary below
```

---

## Layout

```
┌─────────────────────────────────────────────┐
│  🔍 Job Search Dashboard    Generated: DATE  │
├──────┬──────┬──────┬──────┬──────────────────┤
│Active│Inter-│Offer │Hired │Rejected/Closed   │  ← stat cards
│  N   │view N│  N   │  N   │       N          │
├──────┴──────┴──────┴──────┴──────────────────┤
│  Status breakdown (doughnut) │ By tag (bar)   │  ← charts row
├─────────────────────────────────────────────  ┤
│  By month (bar)    │  Funnel (horizontal bar) │  ← charts row
├──────────────────────────────────────────────  ┤
│  Applications  [Status ▾] [Company ▾] [🔍 ...]│  ← table with filters
│  date │ company │ role │ status │ next action │ ...│
│  ...                                          │
└───────────────────────────────────────────────┘
```

## Design Spec

- **Colour palette:** CSS custom properties, using the status colours in
  Config: Status Normalisation above.
- **Font:** system-ui stack, no web fonts.
- **Stat cards:** white background, subtle shadow, large bold number, label
  below, left border in the status colour.
- **Charts:** 2-column grid on wide screens, stacked on narrow (`<768px`).
- **Table:**
  - Alternating row shading.
  - Status column uses a coloured pill/badge (Config: Status Normalisation colours).
  - `link` column renders as a hyperlink (`target="_blank" rel="noopener"`)
    if present; otherwise `—`.
  - Empty cells render as `—`.
  - Client-side filter: a text input filters rows across company + role;
    status and company dropdowns filter independently; all three combine
    with AND.
  - Rows sort newest-first by default (`applied_on` descending, then company A→Z).
- **Responsive:** usable at 900px+; not required to be fully responsive below that.
- **Footer:** `Generated by Claude Code · swelist · {ISO date}`.

## Charts (Chart.js)

1. **Status doughnut** — one slice per status bucket, palette colours above.
2. **By tag bar** (horizontal) — count per inferred tag (`Referral`, `Remote`,
   `Urgent`, `Visa` — see `job-application-manager`'s Tag Inference config),
   sorted descending. Omit entirely if no row has a `tags` value.
3. **By month bar** — application count per `YYYY-MM` of `applied_on`, oldest
   to newest.
4. **Application funnel** (horizontal bar) — Applied → Interview → Offer →
   Hired, each bar = count of rows reaching at least that stage.

All chart `<canvas>` elements get an `aria-label`. Wrap each chart in
`<div class="chart-card"><h3>Title</h3><canvas ...></canvas></div>`.

## Table Columns

`Date` (`applied_on`) · `Company` · `Role` · `Status` · `Next action` ·
`Tags` · `Interview date` · `Notes` (truncate to 80 chars, full text in a
`title` tooltip) · `Link` (hyperlink or `—`)

Omit any column whose value is empty across every row, and omit
`next_action` / `interview_date` / `tags` / `link` entirely if the column
doesn't exist in the DB (v0.2.x schema).

---

## File I/O Reference

### Checking available columns
```bash
sqlite3 ~/.offerplus/applications.db "PRAGMA table_info(applications);"
```

### Reading tracker rows (full v0.5.0 schema)
```bash
sqlite3 -json ~/.offerplus/applications.db \
  "SELECT name, status, job_id, company, applied_on, last_touch, interview_date,
          next_action, link, tags, notes, updated_at
   FROM applications ORDER BY applied_on DESC, name ASC;"
```

### Reading tracker rows (older v0.2.x schema fallback)
```bash
sqlite3 -json ~/.offerplus/applications.db \
  "SELECT name, status, job_id, applied_on, notes, updated_at
   FROM applications ORDER BY applied_on DESC, name ASC;"
```

### Writing the report
```
Write(file_path=output_path, content=full_html_string)
```

---

## Report Format

```
Dashboard generated: <output path>

Open it in any browser — no server needed.

Summary:
- Total applications: N
- Active: N · Interview: N · Offer: N · Hired: N · Rejected/Closed: N
- Funnel: N% progressed past resume screen

Re-run /html-report any time after syncing via application-manager
(or `swelist tracker add/update`) to refresh the dashboard.
```

(Omit the funnel line if `total == 0`; print "No applications tracked yet" instead of the stat breakdown.)

---

## Design Principles

- **Self-contained.** One file, opens offline (Chart.js needs a CDN fetch once; everything else is local).
- **Data-only.** This skill reads and renders; it never writes to the tracker database.
- **Idempotent.** Re-running overwrites the previous report at the same path — no accumulation.
- **Single source of truth.** Reads the exact same SQLite database `job-application-manager` writes to — no separate export/CSV step, so the dashboard is never stale relative to a sync that already happened.
- **Graceful on sparse data.** With only a few rows, charts still render correctly for small N; the table remains the primary value. Never suppress charts just because N is small.
- **No fabrication.** Every number in the report comes directly from the tracker database. Never infer or estimate missing fields.

---

## Edge Cases

| Situation | Handling |
|---|---|
| `Tracker backend` in `profile.md` is `notion`, not `sqlite` | Stop and tell the user this skill currently only reads the SQLite tracker; offer to switch `tracker_backend` to `sqlite` in `profile.md`, or point at an explicit `--db` path if they maintain a separate local copy |
| SQLite DB file does not exist at the resolved path | Tell the user to run `swelist tracker init` (or do an initial sync via `job-application-manager`); do not generate an empty report |
| DB exists but `applications` table has zero rows | Still generate the HTML shell; show "No applications tracked yet" instead of stat cards/charts |
| DB uses the older v0.2.x schema (no `company`/`tags`/etc.) | Build the SELECT from only the columns that exist (Step 2); omit dependent chart/table columns entirely rather than erroring |
| A row's `status` value isn't in the normalisation table | Fall back to `Active`; count it in an "N rows had an unmapped status" footer note |
| `applied_on` is null or blank | Group under "Unknown" in the by-month chart; sort such rows last in the table |
| No row has a `tags` value | Omit the "By tag" chart entirely rather than rendering an empty one |
| `link` value doesn't start with `http` | Render as plain text, not a hyperlink |
| A table column (e.g. `next_action`) is empty for every row | Omit that column from the rendered table entirely |
| Output path's parent directory doesn't exist | Create it (`mkdir -p`) before writing |
| Re-running with the same output path | Overwrite; never append or version the filename |
| User is offline when the report is later opened | Chart.js CDN fetch fails; charts area shows nothing but stat cards and table still render — never let a failed script tag blank the whole page |
| `--open` flag passed | Tell the user the file is ready and where it is; the skill cannot launch a browser itself |
