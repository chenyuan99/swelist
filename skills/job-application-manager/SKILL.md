---
name: Job Application Manager — Gmail & Notion Sync
description: Syncs job application emails from Gmail and updates statuses in your Notion or SQLite tracker — detects offers, rejections, and interview invitations
summary: >
  Use this skill to sync your job applications automatically from Gmail
  into Notion or a local SQLite database. It scans your inbox for emails
  from companies you have applied to, classifies each message as an offer,
  rejection, or interview invitation, and syncs the application status into
  your tracker without any manual effort. Supports Gmail label filters and
  sender-pattern matching for accurate company detection. Works with both
  Notion (cloud career tracker) and SQLite (local, no account required).
  Deduplicates entries so running it multiple times is safe. When syncing
  a specific company, it also enriches the Notion page with a timeline,
  conversation notes, key contacts, and preparation suggestions. Detects
  stale applications (no email activity in 30+ days) and flags them for
  follow-up. Extracts scheduled interview dates and optionally creates
  Google Calendar events.
version: 0.3.0
author: Yuan Chen
repository: https://github.com/chenyuan99/swelist
keywords:
  - gmail
  - notion
  - job-applications
  - application-tracker
  - career-management
  - offer-detection
  - interview-tracker
  - rejection-tracker
  - job-status
  - sync
  - automation
  - sqlite
  - email-parsing
  - career-tracker
tags:
  - career
  - productivity
  - gmail
  - notion
  - job-search
category: career
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
        - name: claude_ai_Google_Calendar
          reason: Create calendar events for scheduled interviews
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

- Sync or refresh job application emails from Gmail ("sync my applications", "check my job emails", "refresh my tracker")
- Update the status of one or more specific applications ("mark Amazon as rejected", "I got an offer from Stripe", "update my application status")
- Add new applications discovered in Gmail ("add this application to my tracker", "log this job email")
- Check what emails arrived from a specific company ("did Google email me back?", "any updates from Meta?")
- Track offers, rejections, or interview invitations automatically ("did I hear back from anyone?", "what's my interview pipeline?")
- Sync applications into Notion ("add to my Notion tracker", "update my Notion job board")
- Sync applications into a local SQLite database ("add to my sqlite tracker", "update my local tracker")
- Export or review their full application pipeline ("show my application pipeline", "what's the status of all my applications?")
- Update a specific company's page with conversation details, contacts, or prep notes
- Flag stale applications that haven't had activity in 30+ days ("what's gone quiet?", "flag stale apps", "what needs follow-up?")

Keywords: `sync applications`, `update my application`, `job tracker`, `application status`, `add to notion`, `update notion`, `check my tracker`, `update my sqlite tracker`, `got an offer`, `got rejected`, `interview invite`, `job emails`, `Gmail job sync`, `career tracker`, `application manager`, `track job applications`

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

Map email signals → pipeline status value (pick the **first** match).
The pipeline is ordered from early to late stage; never move a status *backwards*.

| Priority | Signal (case-insensitive) | Status |
|---|---|---|
| 1 | "offer" OR "congratulations" OR "pleased to inform" OR "we'd like to extend" OR "offer letter" | `Offer` |
| 2 | "on-site" OR "final round" OR "technical interview" OR "virtual interview" OR "interview loop" | `Interviewing` |
| 3 | "schedule" OR "next steps" OR "move forward" OR "hiring manager" OR "phone interview" OR "video call" | `Interviewing` |
| 4 | "online assessment" OR "coding challenge" OR "hackerrank" OR "codility" OR "take-home" OR "assessment link" | `OA` |
| 5 | "recruiter" OR "phone screen" OR "initial screen" OR "introductory call" OR "talent acquisition" | `Recruiter screen` |
| 6 | "unable to move forward" OR "not selected" OR "no longer considering" OR "other candidates" OR "position has been filled" OR "not moving forward" | `Rejected` |
| 7 | "application received" OR "thank you for applying" OR "keep track" OR "under review" OR "successfully submitted" | `Applied / Received` |
| 8 | (no email found, only a job listing) | `Applied / Received` |

If multiple threads exist for the same role, use the **most recent** email's status.

---

## Config: Next Action Mapping

Auto-set `Next action` when creating or updating a Notion page:

| Status | Next action |
|---|---|
| `Applied / Received` | `Waiting` |
| `OA` | `Prep` |
| `Recruiter screen` | `Prep` |
| `Interviewing` | `Prep` |
| `Offer` | `Send availability` |
| `Rejected` | _(leave blank / clear)_ |
| `Withdrawn` | _(leave blank / clear)_ |

---

## Config: Notion Database

_(skip if tracker_backend is sqlite)_

| Field | Value |
|---|---|
| Collection URL | `collection://<NOTION_DB_ID>` |
| Parent ID (for creates) | `<NOTION_DB_ID>` |

Expected schema (updated pipeline schema):

| Property | Type | Allowed values / notes |
|---|---|---|
| `Name` | title | `"Company — Role Title"` |
| `status` | select | `Applied / Received`, `OA`, `Recruiter screen`, `Interviewing`, `Offer`, `Rejected`, `Withdrawn` |
| `Company` | multi-select | Company name (e.g. `Google`, `Amazon`) |
| `Tags` | multi-select | Labels like `Referral`, `Remote`, `NYC`, `Top choice`, `Visa`, `OA`, `Onsite` |
| `Applied on` | date | ISO date when first applied |
| `Last touch` | date | Date of most recent email in the thread |
| `Interview date` | date | Parsed date of the next scheduled interview (if any) |
| `Next action` | select | `Waiting`, `Prep`, `Follow up`, `Send availability` |
| `Link` | url | Job posting URL or Greenhouse/application portal link |

**If the database still uses the old schema** (status values `Not started`, `In progress`, `Done` instead of the pipeline above), notify the user and map as follows until they upgrade:

| Old value | Maps to in old schema |
|---|---|
| `Applied / Received` | `In progress` |
| `OA` | `In progress` |
| `Recruiter screen` | `In progress` |
| `Interviewing` | `In progress` |
| `Offer` | `Done` |
| `Rejected` | `Rejected` |
| `Withdrawn` | `Rejected` |

---

## Config: SQLite Schema

_(skip if tracker_backend is notion)_

**Current (v0.3.0) schema:**

```sql
CREATE TABLE IF NOT EXISTS applications (
  name           TEXT PRIMARY KEY,   -- "Company — Role Title"
  status         TEXT NOT NULL,      -- pipeline status (see Status Mapping)
  job_id         TEXT,
  company        TEXT,
  applied_on     TEXT,               -- ISO date YYYY-MM-DD
  last_touch     TEXT,               -- ISO date of most recent email
  interview_date TEXT,               -- ISO date of next scheduled interview
  next_action    TEXT,               -- Waiting | Prep | Follow up | Send availability
  link           TEXT,               -- job posting or portal URL
  notes          TEXT,
  updated_at     TEXT DEFAULT (datetime('now'))
);
```

**Migration from v0.2.x** (run once if the DB already exists):

```sql
ALTER TABLE applications ADD COLUMN company        TEXT;
ALTER TABLE applications ADD COLUMN last_touch     TEXT;
ALTER TABLE applications ADD COLUMN interview_date TEXT;
ALTER TABLE applications ADD COLUMN next_action    TEXT;
ALTER TABLE applications ADD COLUMN link           TEXT;
```

Run via: `sqlite3 <DB_PATH> < migration.sql`
Or inline: `sqlite3 ~/.offerplus/applications.db "ALTER TABLE applications ADD COLUMN last_touch TEXT; ..."`

At Step 0, check whether `last_touch` column exists (`PRAGMA table_info(applications)`) and run the migration automatically if not.

---

## Workflow

```
INPUT: company (optional), date_range (default: newer_than:6m)

STEP 0  Load profile
  Read profile.md → extract tracker_backend, CAREER_EMAIL, label table
  IF tracker_backend == "notion":  resolve NOTION_DB_ID, COLLECTION_URL
  IF tracker_backend == "sqlite":
    resolve DB_PATH; run init if DB does not exist
    check PRAGMA table_info(applications) for last_touch column
    IF missing: run migration SQL (see Config: SQLite Schema)
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
    company_name   = extract_company(thread)
    role_title     = extract_role(thread)
    status         = map_status(thread)         # use Status Mapping table above
    next_action    = map_next_action(status)    # use Next Action Mapping table above
    date           = most_recent_message_date(thread)
    applied_date   = earliest_message_date(thread)
    job_id         = extract_job_id(thread)     # if present in email
    interview_date = extract_interview_date(thread)
                     # scan body for patterns: "June 9", "Monday June 9 at 2pm PT",
                     # "scheduled for <date>", "your interview is on <date>"
                     # normalise to ISO date YYYY-MM-DD; set null if not found
    page_name      = f"{company_name} — {role_title}"
    APPEND { page_name, company_name, status, next_action, date, applied_date,
             job_id, interview_date, thread_id }

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
    creates → notion_create_pages(batch) with all new fields incl. Interview date
    updates → notion_update_page per entry with status, Last touch, Next action,
              Interview date (if extracted)

  IF tracker_backend == "sqlite":
    FOR each create:
      sqlite3 DB_PATH "INSERT OR IGNORE INTO applications
        (name,status,company,job_id,applied_on,last_touch,interview_date,next_action)
        VALUES (?,?,?,?,?,?,?,?)"
    FOR each update:
      sqlite3 DB_PATH "UPDATE applications SET status=?, last_touch=?,
        next_action=?, interview_date=COALESCE(?,interview_date),
        updated_at=datetime('now') WHERE name=?"

STEP 5  Enrich page content (Notion only, when company is given OR when status changed)
  FOR each application that was created or updated (and tracker is notion):
    fetch full thread via gmail_get_thread(thread_id)
    extract:
      timeline[]       = list of { date, event_summary } sorted chronologically
      key_contacts[]   = list of { name, email, role } from From/Cc headers
      conversation[]   = key quotes or summaries from each email in thread
      prep_suggestions = generate 3-5 bullet prep suggestions based on status + role
    Build structured page content:
      ## Timeline
      | Date | Event |
      ...
      ## Key Contacts
      | Name | Email | Role |
      ...
      ## Conversation Notes
      [bullet summary of each email in thread]
      ## Preparation
      [3-5 tailored bullet points based on company + role + stage]
    notion_update_page(page_id, content=structured_content)

    IF interview_date is not null AND Google Calendar MCP is available:
      ask user: "Create a calendar event for <company> interview on <date>?"
      IF yes:
        google_calendar_create_event(
          summary  = "<company> — <role> Interview",
          start    = interview_date + "T09:00:00",  # use extracted time if available
          end      = interview_date + "T10:00:00",
          description = "Application tracked in 2026 Career Notion database."
        )

STEP 6  Staleness detection
  stale_threshold = today - 30 days
  IF tracker_backend == "notion":
    all_pages = notion_fetch(COLLECTION_URL)
    stale = [p for p in all_pages
             if p.status NOT IN ("Rejected", "Withdrawn", "Offer")
             AND (p.last_touch < stale_threshold OR p.last_touch is null)
             AND p.next_action != "Follow up"]
    FOR each stale page:
      notion_update_page(page_id, properties={"Next action": "Follow up"})

  IF tracker_backend == "sqlite":
    stale = sqlite3 DB_PATH "SELECT name, status, last_touch FROM applications
      WHERE status NOT IN ('Rejected','Withdrawn','Offer')
      AND (date(COALESCE(last_touch, updated_at)) < date('now','-30 days'))
      AND COALESCE(next_action,'') != 'Follow up'"
    FOR each stale row:
      sqlite3 DB_PATH "UPDATE applications SET next_action='Follow up',
        updated_at=datetime('now') WHERE name=?"

STEP 7  Report
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
  subject_terms = 'subject:application OR subject:interview OR subject:offer OR subject:position OR subject:assessment OR subject:next steps'
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
      "properties": {
        "Name": "Amazon — SDE, AWS",
        "status": "Applied / Received",
        "Company": ["Amazon"],
        "Applied on": "2026-05-17",
        "Last touch": "2026-05-17",
        "Interview date": null,
        "Next action": "Waiting"
      },
      "content": "Applied: 2026-05-17\n\n## Timeline\n| Date | Event |\n|---|---|\n| 2026-05-17 | Application submitted |\n\n## Preparation\n- Research AWS products and services\n- Practice system design at scale"
    }
  ]
}
```

### Notion — Update (single, status + dates + next action)
```json
{
  "page_id": "<page-id>",
  "command": "update_properties",
  "properties": {
    "status": "Interviewing",
    "Last touch": "2026-05-28",
    "Interview date": "2026-06-09",
    "Next action": "Prep"
  },
  "content_updates": []
}
```

### Notion — Update (single, staleness flag)
```json
{
  "page_id": "<page-id>",
  "command": "update_properties",
  "properties": {
    "Next action": "Follow up"
  },
  "content_updates": []
}
```

### Notion — Update (single, full page enrichment)
```json
{
  "page_id": "<page-id>",
  "command": "update_properties",
  "properties": {
    "status": "Interviewing",
    "Last touch": "2026-05-28",
    "Next action": "Prep"
  },
  "content": "## Timeline\n| Date | Event |\n|---|---|\n| 2026-05-01 | Application submitted |\n| 2026-05-20 | Recruiter reached out |\n| 2026-05-28 | Interview scheduled for June 9 |\n\n## Key Contacts\n| Name | Email | Role |\n|---|---|---|\n| Jane Smith | jane@company.com | Recruiter |\n\n## Conversation Notes\n- 2026-05-28: Email from Jane Smith scheduling a technical interview for June 9 at 2pm PT.\n\n## Preparation\n- Review data structures and algorithms\n- Prepare STAR stories for behavioral questions\n- Research company mission and recent products\n- Practice whiteboard-style coding problems\n- Prepare 3–5 questions to ask the interviewer"
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
  --status "Applied / Received" \
  --job-id 10414382 \
  --applied-on 2026-05-17 \
  --db <DB_PATH>
```

### SQLite — Update
```bash
swelist tracker update "Amazon — SDE, AWS" \
  --status "Interviewing" \
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

### SQLite — Staleness query
```bash
sqlite3 ~/.offerplus/applications.db \
  "SELECT name, status, COALESCE(last_touch, updated_at) AS last_activity
   FROM applications
   WHERE status NOT IN ('Rejected','Withdrawn','Offer')
   AND date(COALESCE(last_touch, updated_at)) < date('now','-30 days')
   ORDER BY last_activity ASC;"
```

### Google Calendar — Create interview event
```json
{
  "summary": "Applied Intuition — Software Engineer Interview",
  "start": { "dateTime": "2026-06-09T14:00:00", "timeZone": "America/Los_Angeles" },
  "end":   { "dateTime": "2026-06-09T15:00:00", "timeZone": "America/Los_Angeles" },
  "description": "Application tracked in 2026 Career Notion database."
}
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
  ✦ {Company} — {Role} → {status}  [next: {next_action}]

Updated:
  ↑ {Company} — {Role} → {new_status}  (was: {old_status})  [next: {next_action}]
  + Page enriched: timeline, key contacts, prep notes added
  📅 Interview date: {date}  (calendar event created / skipped)

Skipped (already up to date):
  · {Company} — {Role} → {status}

Flagged as stale (no activity > 30 days → Follow up):
  ⏰ {Company} — {Role}  [last touch: {date}]

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
| Email snippet enough to determine status | Skip full thread fetch for status; still fetch for page enrichment when company is given |
| `Company` or `Tags` value not in Notion options list | Omit the field; do not create new options automatically |
| Page name collision (same company, same title, different role) | Add disambiguator: `Amazon — SDE, AWS (Job ID 12345)` |
| Notion DB ID or schema unknown | Fetch database URL with `notion-fetch` to inspect schema first |
| Notion DB uses old 4-status schema | Map pipeline status to old values (see Config: Notion Database), notify user to upgrade |
| SQLite DB does not exist | Run `swelist tracker init` or the CREATE TABLE statement before Step 3 |
| SQLite DB path missing from profile.md | Use default `~/.offerplus/applications.db`; confirm with user |
| Status would move backwards (e.g. Interviewing → Applied) | Keep existing status; only update Last touch date |
| Key contacts not extractable from thread | Omit key contacts section; do not hallucinate names or emails |
| No prep suggestions applicable | Omit Preparation section rather than generating generic advice |
| Interview date ambiguous (e.g. "sometime next week") | Set interview_date to null; note ambiguity in conversation notes |
| Interview date already in the past | Still write it to the page; do not create a calendar event for past dates |
| Google Calendar MCP not connected | Skip calendar event creation; note it in the report |
| SQLite DB exists but missing new columns (v0.2.x) | Run migration SQL automatically at Step 0 before proceeding |
| Staleness check finds 0 stale rows | Omit the stale section from the report entirely |
| next_action already "Follow up" | Skip staleness update for that row; it's already flagged |
