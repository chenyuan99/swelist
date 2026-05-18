# Plan: SQLite Tracker Backend

## Goal

Add SQLite as an alternative to Notion for the `application-manager` skill,
so users who don't have a Notion workspace can still track job applications locally.

---

## Design Decisions

### 1. Single skill, branching backends

The Gmail search and status-mapping logic (Steps 1–2) is identical regardless of
where applications are stored. Only the storage operations (Steps 3–4: dedup,
create, update) differ. The `application-manager` skill will branch at Step 3
based on `tracker_backend` in `profile.md` — no separate skill file needed.

### 2. ~~sqlite3 CLI via Bash~~ → swelist tracker subcommand ✅

Originally planned to use raw `sqlite3` shell commands. Instead, a full
`swelist tracker` subcommand was added (`swelist/tracker.py`) with `init`,
`add`, `update`, `get`, `list`, and `export` commands. All DB access —
including from `application-manager` — now goes through this interface.

### 3. DB location

Default: `~/.offerplus/applications.db`
User-overridable via `sqlite_db_path` in `profile.md`.

---

## Schema

```sql
CREATE TABLE IF NOT EXISTS applications (
  name        TEXT PRIMARY KEY,          -- "Company — Role Title"
  status      TEXT NOT NULL,             -- Not started | In progress | Rejected | Done
  job_id      TEXT,
  applied_on  TEXT,                      -- ISO date
  notes       TEXT,
  updated_at  TEXT DEFAULT (datetime('now'))
);
```

Init command (run once on first use):
```bash
mkdir -p ~/.offerplus
sqlite3 ~/.offerplus/applications.db "
  CREATE TABLE IF NOT EXISTS applications (
    name       TEXT PRIMARY KEY,
    status     TEXT NOT NULL,
    job_id     TEXT,
    applied_on TEXT,
    notes      TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
  );
"
```

---

## Changes Required

### `skills/profile.md`

Add two fields to the **Integrations** section:

```
- **Tracker backend:** notion | sqlite  (default: notion)
- **SQLite DB path:** ~/.offerplus/applications.db
```

Update the Skill Config Reference table — `application-manager` now also needs
`tracker_backend` (and `sqlite_db_path` if using sqlite).

### `skills/application-manager.md`

**Step 0 — Load profile:** resolve `tracker_backend` and (if sqlite) `sqlite_db_path`.
If SQLite is selected and the DB doesn't exist yet, run the init command above.

**Step 3 — Dedup:** branch on backend:

```
IF tracker_backend == "notion":
  existing = notion_search(...)          # existing behaviour
ELSE:  # sqlite
  existing = sqlite3 query by name       # SELECT * FROM applications WHERE name = ?
```

**Step 4 — Apply changes:** branch on backend:

```
IF tracker_backend == "notion":
  notion_create_pages(batch)             # existing behaviour
  notion_update_page(...)
ELSE:  # sqlite
  INSERT OR IGNORE for creates
  UPDATE applications SET status=?, updated_at=datetime('now') WHERE name=? for updates
```

**Notion API Calls section:** rename to **Storage API Calls**, add a SQLite subsection
with ready-to-copy `sqlite3` shell commands for create, update, and search.

**MCP permissions note:** SQLite path needs `Bash(sqlite3 *)` in `.claude/settings.json`
instead of (or in addition to) the Notion MCP tools.

### `swelist/` Python package ✅

`swelist tracker` subcommand shipped in `swelist/tracker.py` with six commands:
`init`, `add`, `update`, `get`, `list`, `export`. 21 tests, 100% coverage.
`application-manager` uses `swelist tracker add/update/get` instead of raw `sqlite3`.

### `.claude/settings.local.json`

~~Add `Bash(sqlite3 *)` to the allow list for SQLite users.~~
No longer needed — all DB access goes through `swelist tracker` which is covered
by the existing `Bash(python *)` or the installed `swelist` binary.

---

## Implementation Order ✅ (all complete)

1. ✅ `profile.md` — added `tracker_backend` and `sqlite_db_path` fields
2. ✅ `application-manager.md` — Step 0 init logic + Step 3/4 branching
3. ✅ Run `./install-skills.sh` to sync updated skills to `~/.claude/`
4. ✅ `swelist tracker` CLI subcommand with full CRUD + tests

---

## Tradeoffs

| | Notion | SQLite |
|---|---|---|
| Setup | Notion account + DB ID | None (sqlite3 built-in) |
| UI | Web, rich properties | `swelist tracker list` or any DB browser |
| Offline | No | Yes |
| Export | Manual | `swelist tracker export --format csv` |
| MCP needed | Yes (Gmail + Notion) | Gmail only |
| Shareable | Yes (Notion collab) | No |
