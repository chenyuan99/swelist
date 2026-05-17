---
name: Application Manager
description: Sync job application statuses from Gmail into a Notion career tracker database
---

# Application Manager

## When to Use This Skill

Trigger when the user asks to:
- Sync / refresh application emails from Gmail into Notion
- Update the status of one or more specific applications
- Add new applications discovered in Gmail
- Check what emails arrived from a specific company
- Keywords: "update my application", "sync applications", "add to notion", "check my tracker"

---

## Setup (first-time use)

**Always read `profile.md` first** (it lives alongside this skill file in the project).
It contains the user's Notion database ID, Gmail label IDs, and career email.

If a required field is blank in `profile.md`, collect it from the user and write
it back to `profile.md` before continuing. Fields to resolve:

1. **Notion database ID** — `Integrations > Notion > Career tracker database ID`
   - If missing: ask the user to open their Notion career tracker and copy the URL.
     The ID is the UUID in `notion.so/<workspace>/<DATABASE_ID>?v=...`
2. **Gmail label IDs** — `Integrations > Gmail Labels` table
   - If missing: run `mcp__claude_ai_Gmail__list_labels`, show the user the list,
     ask which labels are job-related, then fill in the table in `profile.md`.
3. **Career email** — `Personal Info > Career email`
   - If missing: ask the user which email address receives job application emails.

Resolved values become:
- `NOTION_DB_ID` = the database UUID
- `COLLECTION_URL` = `collection://<NOTION_DB_ID>`
- `CAREER_EMAIL` = user's job-hunting email address

---

## Config: Company → Gmail

Populate this table from the user's own labels (run `mcp__claude_ai_Gmail__list_labels` to resolve IDs):

| Company key | Gmail sender pattern | Gmail label ID | Label name |
|---|---|---|---|
| `amazon` | `noreply@mail.amazon.jobs` | _(run list_labels)_ | e.g. `amazon` |
| `linkedin` | `jobs-noreply@linkedin.com` | _(run list_labels)_ | e.g. `linkedin` |
| `google` | `@google.com` | — | — |
| `meta` | `@meta.com` | — | — |
| `_any_` | — | — | — |

Add rows for any other companies the user has labeled. If no labels exist, rely on sender pattern alone.

---

## Config: Status Mapping

Map email signals → Notion `status` field (pick the **first** match):

| Priority | Signal (case-insensitive) | Notion status |
|---|---|---|
| 1 | "offer" OR "congratulations" OR "pleased to inform" OR "we'd like to extend" | `Done` |
| 2 | "interview" OR "move forward" OR "next steps" OR "schedule" OR "hiring manager" | `In progress` |
| 3 | "unable to move forward" OR "not selected" OR "no longer considering" OR "other candidates" OR "position has been filled" | `Rejected` |
| 4 | "application received" OR "thank you for applying" OR "keep track" OR "under review" | `In progress` |
| 5 | (no email found, only a job listing) | `Not started` |

If multiple threads exist for the same role, use the **most recent** email's status.

---

## Config: Notion Database

| Field | Value |
|---|---|
| Collection URL | `collection://<NOTION_DB_ID>` |
| Parent ID (for creates) | `<NOTION_DB_ID>` |

Expected schema (verify with the user's actual database):

| Property | Type | Allowed values |
|---|---|---|
| `Name` | title | `"Company — Role Title"` |
| `status` | select | `Not started`, `In progress`, `Rejected`, `Done` |
| `Tags` | multi-select | Only use values already in the options list |

If the user's database uses different property names or status values, adapt accordingly.

---

## Workflow

```
INPUT: company (optional), date_range (default: newer_than:6m)

STEP 0  Load profile
  Read profile.md → extract NOTION_DB_ID, COLLECTION_URL, CAREER_EMAIL, label table
  IF any required field is blank:
    collect from user → write back to profile.md → continue
  IF company given AND company not in label table:
    run list_labels → ask user to confirm label → append row to profile.md label table

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
    status       = map_status(thread)     # use Status Mapping table above
    date         = most_recent_message_date(thread)
    page_name    = f"{company_name} — {role_title}"
    APPEND { page_name, status, date, thread_id }

STEP 3  Deduplicate against Notion
  FOR each application:
    existing = notion_search(query=application.page_name,
                             data_source_url=COLLECTION_URL)
    IF existing found:
      application.notion_page_id = existing.id
      application.existing_status = existing.status
      application.action = "update" IF status != existing_status ELSE "skip"
    ELSE:
      application.action = "create"

STEP 4  Apply changes
  creates = [a for a in applications WHERE a.action == "create"]
  IF creates:
    notion_create_pages(batch=creates)    # one call for all new pages

  FOR each a WHERE a.action == "update":
    notion_update_page(page_id=a.notion_page_id,
                       properties={ "status": a.status })

STEP 5  Report
  print summary (see Report Format below)
```

---

## Query Builder

```
FUNCTION build_query(company_key, date_range="newer_than:6m"):
  cfg = COMPANY_CONFIG[company_key]
  parts = []
  IF cfg.sender:
    parts.append(f"from:{cfg.sender}")
  IF cfg.label_id:
    parts.append(f"label:{cfg.label_id}")
  subject_terms = 'subject:application OR subject:interview OR subject:offer OR subject:position'
  RETURN f'({" OR ".join(parts)}) ({subject_terms}) {date_range}'
```

Examples:
- Amazon with label → `(from:noreply@mail.amazon.jobs OR label:<amazon_label_id>) (subject:application OR ...) newer_than:6m`
- Unknown company → fall back to `from:@<company>.com` or name in subject

---

## Notion API Calls

### Create (batch)
```json
{
  "data_source_id": "<NOTION_DB_ID>",
  "pages": [
    {
      "properties": {
        "Name": "Amazon — Software Development Engineer, AWS",
        "status": "In progress"
      },
      "content": "Applied: <date>"
    }
  ]
}
```

### Update (single)
```json
{
  "page_id": "<page-id>",
  "command": "update_properties",
  "properties": { "status": "Rejected" },
  "content_updates": []
}
```

### Search (dedup check)
```json
{
  "query": "Amazon — Software Development Engineer",
  "data_source_url": "collection://<NOTION_DB_ID>",
  "filters": {}
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
Synced {N} application(s) on {date}

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
| Role title not in email | Use job ID or "Role" as placeholder; note it in content |
| Company exists in Notion under different name variant | Search by company name alone first, then prompt user to confirm merge |
| Email snippet enough to determine status | Skip full thread fetch to reduce API calls |
| `Tags` value not in options list | Omit `Tags`; do not create new options |
| Page name collision (same company, different role, same title) | Add a disambiguator: `Amazon — SDE, AWS (Job ID 12345)` |
| Notion DB ID or schema unknown | Fetch the database URL with `notion-fetch` to inspect schema before proceeding |
