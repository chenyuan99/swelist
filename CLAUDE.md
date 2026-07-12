# swelist (github.com/chenyuan99/swelist)

A Python CLI toolkit for job seekers published to PyPI as `swelist`. The repo also ships
a set of Claude Code skills for managing job applications via Gmail and Notion.

---

## Development Quick Reference

```bash
pytest                          # run full test suite with coverage
python -m build                 # build distribution artifacts
twine check dist/*              # validate package before publishing
swelist run                     # list recent internship postings
swelist jobgpt ask "..."        # AI career advice (requires OPENAI_API_KEY)
swelist tracker init            # create local SQLite application tracker
swelist tracker add "Co — Role" --status "In progress"
swelist tracker update "Co — Role" --status "Rejected"
swelist tracker get "Co — Role" # JSON lookup (exit 1 if not found)
swelist tracker list            # display all tracked applications
swelist tracker export --format json
swelist tracker report          # generate a self-contained HTML dashboard
swelist profile report          # generate an HTML career profile from profile.md
```

Python 3.9–3.12 supported. Install dev deps: `pip install -r requirements.txt`

---

## Project Layout

```
swelist/               Python package (CLI source)
  main.py              swelist run — job listings from SimplifyJobs GitHub repos
  jobgpt.py            swelist jobgpt — OpenAI-powered interview prep subcommands
  tracker.py           swelist tracker — local SQLite application tracker (add/update/get/list/export/report)
  profile_cli.py       swelist profile — career profile report subcommands
  report.py            HTML dashboard generator used by `swelist tracker report`
  profile.py           HTML career profile generator used by `swelist profile report`
  agent.py             prototype: parses swelist output into JSON via LLM
tests/                 pytest suite
skills/                Claude Code skill files (see Skill System below)
  application-manager.md
  profile.md           shared user config (career email, Notion DB, Gmail labels)
install-skills.sh      syncs skills/ → ~/.claude/skills/ (see Skill System below)
SKILLS.md              machine-readable CLI contract for automation agents
README.md              user-facing documentation
.github/               CI (pytest + coverage) and PyPI publish workflows
```

---

## CLI Architecture

**Entry point**: `swelist` (typer app in `swelist/main.py`)

Three top-level commands:
- `swelist run` — fetches live job JSON from GitHub, filters by timeframe/location, prints plain text
- `swelist jobgpt <subcommand>` — delegates to `swelist/jobgpt.py` (requires `openai` extra)
- `swelist tracker <subcommand>` — local SQLite application tracker (`swelist/tracker.py`); subcommands: `init`, `add`, `update`, `get`, `list`, `export`, `report`

**Key conventions**:
- Output is always plain text to stdout — no JSON, no color — so it can be piped to agents
- No local state, no auth required for `swelist run`
- `OPENAI_API_KEY` env var required only for jobgpt subcommands
- `swelist tracker report` is the one command that writes a file (a self-contained HTML dashboard, default `reports/application-dashboard.html`) rather than only printing to stdout; it reads via `swelist/report.py` and adapts to whichever tracker schema columns exist (base v0.2.x or the richer v0.5.0 set with `company`/`tags`/`next_action`/etc.) — see `skills/html-report/SKILL.md` for the equivalent Claude-skill version of the same report

---

## Skill System

This repo ships **Claude Code skills** — markdown files that Claude reads to perform
multi-step tasks on behalf of the user.

### Skill files location

Skills live in `skills/`. The canonical file for each skill is here; the version
cached in `~/.claude/skills/` is what Claude Code actually loads at invocation.

**Install / update all skills:**
```bash
./install-skills.sh           # install or update stale skills
./install-skills.sh --check   # dry-run: show what's out of date (exits 1 if stale)
```

`profile.md` installs flat to `~/.claude/profile.md` (global, not a skill folder)
so every skill package can find it at a known path.

### Shared profile

`skills/profile.md` is the **single source of truth for user config** (career email,
Notion DB ID, Gmail label IDs, resume, etc.). Every skill should:

1. Read `skills/profile.md` at step 0
2. Collect any missing required fields from the user
3. Write new values back to `skills/profile.md` before finishing

### Writing a new skill

Skill files must have this frontmatter:
```yaml
---
name: Skill Name
description: One-line description (shown in skill picker)
---
```

Then follow this structure:
1. **When to Use** — trigger phrases / user intents
2. **Setup** — point to `profile.md` sections needed; list fields to resolve if blank
3. **Config** — structured tables (not prose) for any mappings or lookups
4. **Workflow** — pseudocode `STEP N` blocks with clear input/output
5. **API Calls** — ready-to-copy JSON examples for each MCP tool call
6. **Report Format** — what the skill prints when done
7. **Edge Cases** — table of known edge cases and how to handle them

### MCP permissions

The `application-manager` skill needs these MCP tools allowed in `.claude/settings.json`:
```json
"mcp__claude_ai_Gmail__search_threads",
"mcp__claude_ai_Gmail__get_thread",
"mcp__claude_ai_Notion__notion-search",
"mcp__claude_ai_Notion__notion-fetch",
"mcp__claude_ai_Notion__notion-create-pages",
"mcp__claude_ai_Notion__notion-update-page"
```

---

## Testing

```bash
pytest                          # all tests
pytest tests/test_main.py       # job listing tests only
pytest tests/test_jobgpt.py     # jobgpt tests only (mocks OpenAI)
pytest tests/test_tracker.py    # tracker CLI tests (28 tests, 100% coverage)
pytest tests/test_report.py     # HTML dashboard generator tests (report.py, 99% coverage)
pytest --co -q                  # list all test names without running
```

`test_agent.py` is skipped automatically when the `openai` package is not installed.

---

## Publishing

Version lives in `setup.py` (`version=`). Bump it, then push a GitHub release —
the `release.yml` workflow builds and uploads to PyPI automatically via trusted publisher.

---

## Environment

Copy `.env.example` → `.env` and fill in at minimum:
```
OPENAI_API_KEY=...   # required for jobgpt subcommands
```

Other keys in `.env.example` (Supabase, DeepSeek, etc.) are unused by the current CLI.
