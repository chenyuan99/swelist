---
name: HTML Report — Application Tracker Dashboard
description: Generates a self-contained HTML dashboard (stat cards, Chart.js charts, filterable table) from a job search tracker CSV and application archives — opens directly in a browser, no server required
summary: >
  Use this skill to turn a `job_search_tracker.csv` file (and any
  `documents/applications/*/outcome.md` archives) into a single self-contained
  HTML dashboard. The report shows total/active/interview/offer/rejected stat
  cards, a status-breakdown doughnut chart, sector and channel bar charts, an
  application funnel chart, and a filterable, sortable table of every tracked
  application. Everything — CSS, JS, and data — is inlined into one `.html`
  file except the Chart.js library, which loads from a CDN on first open and
  degrades gracefully to the stat cards if offline. The skill only reads
  existing tracker data; it never writes back to the CSV or archives, so
  re-running it after `/outcome` or manual edits is always safe.
version: 0.1.0
author: Yuan Chen
repository: https://github.com/chenyuan99/swelist
keywords:
  - html-report
  - dashboard
  - job-search
  - application-tracker
  - chart.js
  - reporting
  - csv
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
      bins: []
      env: []
      mcp: []
    config:
      - key: tracker_csv_path
        description: Path to the job search tracker CSV
        default: job_search_tracker.csv
      - key: applications_archive_dir
        description: Directory of per-application outcome archives (optional)
        default: documents/applications/
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
- Re-run the dashboard after logging new outcomes ("refresh the dashboard", "update the report with my latest applications")

Keywords: `html report`, `dashboard`, `visualize applications`, `application chart`, `job search report`, `funnel chart`, `/html-report`

This skill is **read-only**: it never modifies `job_search_tracker.csv` or the
`documents/applications/` archive. Use the `job-application-manager` skill to
update application status instead.

---

## Setup

No MCP tools or credentials are required — this skill only reads local files
and writes one HTML file.

1. **Locate the tracker CSV** — default `job_search_tracker.csv` in the repo
   root. If the user has configured a different path (e.g. in `profile.md`
   under a future `Reporting` section), use that instead.
2. **Locate the archive directory** — default `documents/applications/`.
   Optional; if it doesn't exist, skip archive enrichment entirely (see
   Edge Cases) and proceed with CSV data alone.
3. **Resolve the output path** — default `reports/application-dashboard.html`.
   Create the `reports/` directory if it doesn't exist.

---

## Config: Argument Parsing

| Input | Behavior |
|---|---|
| No argument | Output to `reports/application-dashboard.html` |
| A path argument (e.g. `/html-report ~/Desktop/report.html`) | Use that path instead |
| `--open` flag | After writing, tell the user to open the file — the skill cannot launch a browser itself |

---

## Config: Status Normalisation

Map every tracker `status` value to one of five canonical buckets before
computing stats. Comparisons are case-insensitive.

| Tracker value | Canonical bucket | Colour |
|---|---|---|
| `applied` | Active | `#3b82f6` |
| `interview` | Interview | `#f59e0b` |
| `offer` | Offer | `#8b5cf6` |
| `hired` | Hired | `#22c55e` |
| `rejected`, `no_response`, `no response`, `offer_declined`, `interview_only`, `withdrawn` | Rejected/Closed | `#ef4444` |
| any other/unrecognised value | Active (fallback) — note in the report footer as "N rows had an unmapped status" | `#3b82f6` |

---

## Config: CSV Columns

Expected columns in `job_search_tracker.csv`:

`date`, `company`, `sector`, `role`, `role_type`, `channel`, `status`,
`contact_person`, `fit_rating`, `notes`, `cv_file`, `cover_letter_file`,
`source`

Columns with only empty values across all rows may be omitted from the
rendered table (see Layout below). Missing columns entirely (older CSV
versions) are treated as all-empty and omitted the same way — do not error.

---

## Workflow

```
INPUT: output_path (optional, default "reports/application-dashboard.html")
       open_flag (optional)

STEP 0  Parse arguments
  IF path argument given: output_path = that path
  ELSE: output_path = "reports/application-dashboard.html"
  mkdir -p dirname(output_path)

STEP 1  Collect data (read in parallel)
  rows = parse_csv("job_search_tracker.csv")
    # one record per row with the columns listed in Config: CSV Columns
  IF documents/applications/ exists:
    FOR each */outcome.md under documents/applications/:
      outcome = parse_outcome_md(file)
        # extract checked interview-stage checkboxes + free-text notes
      match = fuzzy_match(outcome.company + outcome.role, rows,
                           by = lowercase(strip_punctuation(company + role)))
      IF match found: merge outcome into match.notes / match.stages
      ELSE: attach outcome as unmatched extra context (still shown in report footer)
  ELSE:
    skip archive enrichment entirely (CSV-only mode)

  FOR each row: row.bucket = normalise_status(row.status)   # Config: Status Normalisation

STEP 2  Compute summary stats
  total              = len(rows)
  by_bucket           = count rows grouped by row.bucket
  by_sector           = count rows grouped by row.sector (blank → "Unspecified")
  by_channel          = count rows grouped by row.channel into online / referral / other
  by_period           = count rows grouped by row.date (year, or year extracted from full date)
  resolved            = rows where bucket != "Active"
  past_screen         = rows where bucket IN ("Interview", "Offer", "Hired")
  funnel_rate_pct     = round(100 * len(past_screen) / total) if total else 0
  rejection_rate_pct  = round(100 * count(bucket == "Rejected/Closed") / len(resolved)) if resolved else 0
  funnel_stages       = { Applied: total,
                          Interview: count(bucket IN (Interview, Offer, Hired)),
                          Offer: count(bucket IN (Offer, Hired)),
                          Hired: count(bucket == Hired) }

STEP 3  Generate HTML (see Layout, Design spec, and Charts below)
  Build one self-contained HTML string:
    - inline <style> block (palette, cards, charts grid, table)
    - stat cards row
    - two 2-column chart rows (doughnut, sector bar / channel bar, funnel bar)
    - filterable table (search input + status/sector dropdowns, client-side JS)
    - footer: "Generated by Claude Code · ai-job-search · {ISO date}"
  Charts render via Chart.js loaded from https://cdn.jsdelivr.net/npm/chart.js
    (only external dependency; wrap chart init in try/catch so a failed CDN
    fetch degrades to the stat cards instead of breaking the page)

STEP 4  Write and confirm
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
│Total │Active│Inter-│Offer │Rejected/Closed   │  ← stat cards
│  N   │  N   │view N│  N   │       N          │
├──────┴──────┴──────┴──────┴──────────────────┤
│  Status breakdown (doughnut) │ By sector (bar)│  ← charts row
├─────────────────────────────────────────────  ┤
│  By channel (bar)  │  Funnel (horizontal bar) │  ← charts row
├──────────────────────────────────────────────  ┤
│  Applications  [Status ▾] [Sector ▾] [🔍 ...]│  ← table with filters
│  date │ company │ sector │ role │ status │ ... │
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
  - `source` column renders as a hyperlink (`target="_blank" rel="noopener"`)
    if the value starts with `http`; otherwise render as plain text or `—`.
  - Empty cells render as `—`.
  - Client-side filter: a text input filters rows across company + role +
    sector; status and sector dropdowns filter independently; all three
    combine with AND.
  - Rows sort newest-first by default (`date` descending, then company A→Z).
- **Responsive:** usable at 900px+; not required to be fully responsive below that.
- **Footer:** `Generated by Claude Code · ai-job-search · {ISO date}`.

## Charts (Chart.js)

1. **Status doughnut** — one slice per status bucket, palette colours above.
2. **By sector bar** (horizontal) — application count per sector, sorted descending.
3. **By channel bar** — online / referral / other.
4. **Application funnel** (horizontal bar) — Applied → Interview → Offer → Hired,
   each bar = count of rows reaching at least that stage.

All chart `<canvas>` elements get an `aria-label`. Wrap each chart in
`<div class="chart-card"><h3>Title</h3><canvas ...></canvas></div>`.

## Table Columns

`Date` · `Company` · `Role` · `Sector` · `Channel` · `Status` · `Notes`
(truncate to 80 chars, full text in a `title` tooltip) · `Source` (link or `—`)

Omit any column whose value is empty across every row.

---

## File I/O Reference

### Reading the tracker CSV
```
rows = read_csv("job_search_tracker.csv")
# each row → dict keyed by: date, company, sector, role, role_type, channel,
# status, contact_person, fit_rating, notes, cv_file, cover_letter_file, source
```

### Reading an outcome archive
```
outcome = read_file("documents/applications/<company-role-slug>/outcome.md")
# extract: checked "- [x] Stage name" checkboxes → stages reached
#          any free-text notes below the checklist
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
- Active: N · Interview: N · Hired: N · Rejected/Closed: N
- Funnel: N% progressed past resume screen

Re-run /html-report any time after adding new entries via /outcome to refresh the dashboard.
```

(Omit the funnel line if `total == 0`; print "No applications tracked yet" instead of the stat breakdown.)

---

## Design Principles

- **Self-contained.** One file, opens offline (Chart.js needs a CDN fetch once; everything else is local).
- **Data-only.** This skill reads and renders; it never writes to the tracker CSV or the archive.
- **Idempotent.** Re-running overwrites the previous report at the same path — no accumulation.
- **Graceful on sparse data.** With only a few rows, charts still render correctly for small N; the table remains the primary value. Never suppress charts just because N is small.
- **No fabrication.** Every number in the report comes directly from the CSV or outcome files. Never infer or estimate missing fields.

---

## Edge Cases

| Situation | Handling |
|---|---|
| `job_search_tracker.csv` does not exist | Tell the user the CSV was not found and the expected path; do not generate an empty report |
| CSV exists but has zero data rows | Still generate the HTML shell; show "No applications tracked yet" instead of stat cards/charts |
| `documents/applications/` does not exist | Skip archive enrichment silently; proceed in CSV-only mode |
| An archive folder has no matching CSV row (by fuzzy company+role match) | Attach it as unmatched extra context in the report footer rather than dropping it |
| A CSV row has a `status` value not in the normalisation table | Fall back to `Active`; count it in an "N rows had an unmapped status" footer note |
| `date` is a bare year (e.g. `2025`) vs. a full date | Group by year either way; sort full dates before bare years within the same year |
| `source` value doesn't start with `http` | Render as plain text, not a link |
| A column (e.g. `contact_person`) is empty for every row | Omit that column from the rendered table entirely |
| Output path's parent directory doesn't exist | Create it (`mkdir -p`) before writing |
| Re-running with the same output path | Overwrite; never append or version the filename |
| User is offline when the report is later opened | Chart.js CDN fetch fails; charts area shows nothing but stat cards and table still render — never let a failed script tag blank the whole page |
| `--open` flag passed | Tell the user the file is ready and where it is; the skill cannot launch a browser itself |
