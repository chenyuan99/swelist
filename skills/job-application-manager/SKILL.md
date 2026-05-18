---
name: Application Manager
description: Sync job application statuses from Gmail into Notion or a local SQLite database
version: 1.0.0
metadata:
  openclaw:
    emoji: "📋"
    requires:
      bins: []
      env: []
      mcp:
        - name: claude_ai_Gmail
          reason: Search and read job application emails
          optional: false
        - name: claude_ai_Notion
          reason: Create and update application entries in Notion
          optional: true
    config:
      - key: tracker_backend
        description: Storage backend — notion or sqlite
        default: notion
      - key: sqlite_db_path
        description: Path to SQLite database (sqlite backend only)
        default: ~/.offerplus/applications.db
---

# Application Manager

## When to Use This Skill

Trigger when the user asks to:
- Sync / refresh application emails from Gmail into their tracker
- Update the status of one or more specific applications
- Add new applications discovered in Gmail
- Check what emails arrived from a specific company
- Keywords: "update my application", "sync applications", "add to notion", "check my tracker", "update my sqlite tracker"

---

## Setup (first-time use)

**Always read `profile.md` first.** It contains the user's tracker backend choice,
Notion database ID or SQLite path, Gmail label IDs, and career email.

Resolve these fields before continuing (collect from user + write back to `profile.md`):

1. **Tracker backend** — `Integrations > Tracker Backend`
   - If blank: ask the user — "Do you use Notion or would you prefer a local SQLite file?"
   - Set to `notion` or `sqlite`

2. **If notion** — resolve `Integrations > Notion > Career tracker database ID`
   - If missing: ask user to open their Notion career tracker and copy the URL.
     The ID is the UUID in `notion.so/<workspace>/<DATABASE_ID>?v=...`
   - Derive: `NOTION_DB_ID`, `COLLECTION_URL = collection://<NOTION_DB_ID>`

3. **If sqlite** — resolve `Integrations > Tracker Backend > SQLite DB path`
   - Default: `~/.offerplus/applications.db`
   - On first use, initialize the DB: `swelist tracker init --db <path>`
     Or directly: `sqlite3 <path> "CREATE TABLE IF NOT EXISTS applications (name TEXT PRIMARY KEY, status TEXT NOT NULL, job_id TEXT, applied_on TEXT, notes TEXT, updated_at TEXT DEFAULT (datetime('now')));"`

4. **Gmail label IDs** — `Integrations > Gmail Labels` table
   - If missing: run `mcp__claude_ai_Gmail__list_labels`, show the list, ask the user
     which labels are job-related, fill in the table in `profile.md`.

5. **Career email** — `Personal Info > Career email`
   - If missing: ask the user which email address receives job application emails.

---

## Config: Company → Gmail

Populate from the user's own labels (`mcp__claude_ai_Gmail__list_labels`):

| Company key | Gmail sender pattern | Gmail label ID | Label name |
|---|---|---|---|
| `amazon` | `noreply@mail.amazon.jobs` | _(run list_labels)_ | e.g. amazon |
| `linkedin` | `jobs-noreply@linkedin.com` | _(run list_labels)_ | e.g. linkedin |
| `google` | `@google.com` | — | — |
| `meta` | `@meta.com` | — | — |
| `_any_` | — | — | — |

Add rows for any other companies the user has labeled. If no labels exist, rely on sender pattern alone.

---

## Config: Status Mapping

Map email signals → status value (pick the **first** match):

| Priority | Signal (case-insensitive) | Status |
|---|---|---|
| 1 | "offer" OR "congratulations" OR "pleased to inform" OR "we'd like to extend" | `Done` |
| 2 | "interview" OR "move forward" OR "next steps" OR "schedule" OR "hiring manager" | `In progress` |
| 3 | "unable to move forward" OR "not selected" OR "no longer considering" OR "other candidates" OR "position has been filled" | `Rejected` |
| 4 | "application received" OR "thank you for applying" OR "keep track" OR "under review" | `In progress` |
| 5 | (no email found, only a job listing) | `Not started` |

If multiple threads exist for the same role, use the **most recent** email's status.

---

## Config: Notion Database

_(skip if tracker_backend is sqlite)_

| Field | Value |
|---|---|
| Collection URL | `collection://<NOTION_DB_ID>` |
| Parent ID (for creates) | `<NOTION_DB_ID>` |

Expected schema:

| Property | Type | Allowed values |
|---|---|---|
| `Name` | title | `"Company — Role Title"` |
| `status` | select | `Not started`, `In progress`, `Rejected`, `Done` |
| `Tags` | multi-select | Only use values already in the options list |

---

## Config: SQLite Schema

_(skip if tracker_backend is notion)_

```sql
CREATE TABLE IF NOT EXISTS applications (
  name        TEXT PRIMARY KEY,   -- "Company — Role Title"
  status      TEXT NOT NULL,      -- Not started | In progress | Rejected | Done
  job_id      TEXT,
  applied_on  TEXT,               -- ISO date YYYY-MM-DD
  notes       TEXT,
  updated_at  TEXT DEFAULT (datetime('now'))
);
```

---

## Workflow

```
INPUT: company (optional), date_range (default: newer_than:6m)

STEP 0  Load profile
  Read profile.md → extract tracker_backend, CAREER_EMAIL, label table
  IF tracker_backend == "notion":  resolve NOTION_DB_ID, COLLECTION_URL
  IF tracker_backend == "sqlite":  resolve DB_PATH; run init if DB does not exist
  IF any required field blank: collect from user → write to profile.md → continue
  IF company given AND not in label table:
    run list_labels → confirm with user → append to profile.md label table

STEP 1  Search Gmail
  IF company given:
    query = build_query(company)          # see Query Builder below
  ELSE:
    query = 'subject:"application" OR subject:"your application" OR subject:"interview" newer_than:6m'
  threads = gmail_search(query, max_results=20)
  FOR each thread WHERE snippet is ambiguous:
    fetch full thread via gmail_get_thread(thread_id)

STEP 2  Parse threads → applications[]
  FOR each thread:
    company_name = extract_company(thread)
    role_title   = extract_role(thread)
    status       = map_status(thread)       # use Status Mapping table above
    date         = most_recent_message_date(thread)
    job_id       = extract_job_id(thread)   # if present in email
    page_name    = f"{company_name} — {role_title}"
    APPEND { page_name, status, date, job_id, thread_id }

STEP 3  Deduplicate
  IF tracker_backend == "notion":
    FOR each application:
      existing = notion_search(query=application.page_name,
                               data_source_url=COLLECTION_URL)
      IF found: set existing_status, action = "update" or "skip"
      ELSE:     action = "create"

  IF tracker_backend == "sqlite":
    FOR each application:
      result = swelist tracker get "<page_name>" --db DB_PATH
      IF result is not null: set existing_status, action = "update" or "skip"
      ELSE:                   action = "create"

STEP 4  Apply changes
  IF tracker_backend == "notion":
    creates → notion_create_pages(batch)
    updates → notion_update_page per entry

  IF tracker_backend == "sqlite":
    FOR each create:
      swelist tracker add "<name>" --status <status> --job-id <id> --applied-on <date> --db DB_PATH
    FOR each update:
      swelist tracker update "<name>" --status <status> --db DB_PATH

STEP 5  Report
  print summary (see Report Format below)
```

---

## Query Builder

```
FUNCTION build_query(company_key, date_range="newer_than:6m"):
  cfg = COMPANY_CONFIG[company_key]
  parts = []
  IF cfg.sender:   parts.append(f"from:{cfg.sender}")
  IF cfg.label_id: parts.append(f"label:{cfg.label_id}")
  subject_terms = 'subject:application OR subject:interview OR subject:offer OR subject:position'
  RETURN f'({" OR ".join(parts)}) ({subject_terms}) {date_range}'
```

Examples:
- Amazon with label → `(from:noreply@mail.amazon.jobs OR label:<label_id>) (subject:application OR ...) newer_than:6m`
- Unknown company → fall back to `from:@<company>.com` or company name in subject

---

## Storage API Calls

### Notion — Create (batch)
```json
{
  "data_source_id": "<NOTION_DB_ID>",
  "pages": [
    {
      "properties": { "Name": "Amazon — SDE, AWS", "status": "In progress" },
      "content": "Applied: <date>"
    }
  ]
}
```

### Notion — Update (single)
```json
{
  "page_id": "<page-id>",
  "command": "update_properties",
  "properties": { "status": "Rejected" },
  "content_updates": []
}
```

### Notion — Search (dedup)
```json
{
  "query": "Amazon — Software Development Engineer",
  "data_source_url": "collection://<NOTION_DB_ID>",
  "filters": {}
}
```

### SQLite — Create
```bash
swelist tracker add "Amazon — SDE, AWS" \
  --status "In progress" \
  --job-id 10414382 \
  --applied-on 2026-05-17 \
  --db <DB_PATH>
```

### SQLite — Update
```bash
swelist tracker update "Amazon — SDE, AWS" \
  --status "Rejected" \
  --db <DB_PATH>
```

### SQLite — Search (dedup)
```bash
swelist tracker get "Amazon — SDE, AWS" --db <DB_PATH>
# Returns JSON object if found, null if not found. Exit code 1 when not found.
```

### SQLite — List all
```bash
swelist tracker list --db <DB_PATH>
swelist tracker export --format json --db <DB_PATH>
```

---

## Naming Convention

```
"{Company} — {Role Title}"
```

| Good | Bad |
|---|---|
| `Amazon — Software Development Engineer, AWS` | `SDE at Amazon` |
| `Google — Software Engineer II, Early Career` | `Google SWE` |
| `Goldman Sachs — Software Engineer - Associate` | `Goldman` |

Rules:
- Em dash (`—`), not hyphen
- Company name in title case
- Role title verbatim from the job posting or email subject when possible

---

## Report Format

```
Synced {N} application(s) on {date}  [{backend}: notion|sqlite]

Created:
  ✦ {Company} — {Role} → {status}

Updated:
  ↑ {Company} — {Role} → {new_status}  (was: {old_status})

Skipped (already up to date):
  · {Company} — {Role} → {status}

Errors:
  ✕ {description of issue}
```

---

## Edge Cases

| Situation | Handling |
|---|---|
| Multiple threads for same role | Use most recent thread's status |
| Role title not in email | Use job ID or "Role" as placeholder; note it in content/notes |
| Company exists under a different name variant | Search by company name alone first, prompt user to confirm merge |
| Email snippet enough to determine status | Skip full thread fetch to reduce API calls |
| `Tags` value not in Notion options list | Omit `Tags`; do not create new options |
| Page name collision (same company, same title, different role) | Add disambiguator: `Amazon — SDE, AWS (Job ID 12345)` |
| Notion DB ID or schema unknown | Fetch database URL with `notion-fetch` to inspect schema first |
| SQLite DB does not exist | Run `swelist tracker init` or the CREATE TABLE statement before Step 3 |
| SQLite DB path missing from profile.md | Use default `~/.offerplus/applications.db`; confirm with user |
