---
name: Swelist — Tech Internship & Job Tracker
description: Helps you find tech internships and new-grad jobs, track every application locally, and prep for interviews — no sign-up needed
summary: >
  Use swelist to browse software engineering internships and new-graduate
  positions sourced live from SimplifyJobs, filtered by location and
  timeframe. Track every job application you have submitted in a local
  SQLite database — add entries, mark statuses as in progress, rejected,
  or done, add notes, and export your full pipeline as JSON or CSV.
  Includes an AI writing assistant (jobgpt) for generating behavioral
  interview answers in STAR format, compelling "why this company"
  responses, and general career advice. Works offline for tracking;
  no account, API key, or subscription required.
version: 0.1.9
homepage: https://pypi.org/project/swelist/
author: Yuan Chen
repository: https://github.com/chenyuan99/swelist
keywords:
  - internship
  - new-grad
  - job-search
  - job-tracker
  - tech-jobs
  - software-engineering
  - application-tracker
  - sqlite
  - career
  - job-listings
  - simplify-jobs
  - job-finder
  - swe-jobs
  - cs-internship
tags:
  - career
  - productivity
  - job-search
category: career
metadata:
  openclaw:
    emoji: "💼"
    requires:
      bins: ["swelist"]
    install:
      - id: uv
        kind: uv
        package: swelist
        bins: ["swelist"]
        label: "Install swelist (uv)"
---

# swelist

`swelist` is a job-seeker CLI for finding software engineering internships and new-grad positions in real time, plus a local SQLite tracker for every application — no account, no API key, no subscription required. It pulls live data from SimplifyJobs, filters by role, location, and timeframe, and pairs with an AI writing assistant (`jobgpt`) for interview prep.

------------------------------------------------------------------------

## When to Use This Skill

Trigger when the user asks to:

- Find or browse internship openings ("show me tech internships this week", "any CS internships remote?")
- Search for new-grad software engineering jobs ("new grad SWE jobs in NYC", "entry-level software engineer positions")
- Filter job listings by location, company, or recency ("jobs in Seattle last 7 days", "remote internships last month")
- Track a job application locally ("add Amazon SDE intern to my tracker", "log this application")
- Update or check an application status ("mark Stripe offer as done", "set Google to rejected")
- List or export tracked applications ("show all my applications", "export tracker as JSON")
- Get AI interview prep answers ("why do you want to work at Meta?", "STAR answer for conflict question")
- Get general career advice via jobgpt ("how do I negotiate salary?", "tips for my first internship")

Keywords: `find internships`, `new grad jobs`, `job listings`, `job search`, `application tracker`, `track my application`, `update application status`, `swelist`, `job search CLI`, `software engineer jobs`, `tech internship`, `interview prep`, `STAR answer`, `why this company`

------------------------------------------------------------------------

## Tool Identity

-   **Name:** swelist
-   **Type:** Command-Line Interface (CLI)
-   **Language:** Python
-   **Distribution:** PyPI
-   **Execution Model:**
    -   `swelist run` — stateless, read-only (fetches live data, no local state)
    -   `swelist jobgpt` — stateless (calls OpenAI API, no local state)
    -   `swelist tracker` — stateful (reads/writes local SQLite at `~/.offerplus/applications.db`)

------------------------------------------------------------------------

## Purpose

`swelist` is a job-seeker CLI with three subcommand groups:

-   **`swelist run`** — retrieves recently added technology internship and
    new‑graduate job postings from curated public GitHub repositories and
    renders them in a predictable, text-based format.
-   **`swelist jobgpt`** — AI-powered writing assistant for interview prep
    (behavioral answers, "why this company", general career Q&A).
-   **`swelist tracker`** — local SQLite application tracker; add, update,
    query, list, and export job applications without any external account.

It is optimized for: automation pipelines, periodic polling agents, and
human-in-the-loop job search workflows.

------------------------------------------------------------------------

## Data Sources

-   SimplifyJobs / Summer2025-Internships
-   SimplifyJobs / New-Grad-Positions

Data is fetched live at runtime.

------------------------------------------------------------------------

## Installation

``` bash
pip install swelist
```

------------------------------------------------------------------------

## Invocation Contract

``` bash
swelist [--role ROLE] [--timeframe TIMEFRAME] [--location LOCATION]
```

The tool accepts only CLI flags. No stdin is consumed.

------------------------------------------------------------------------

## Parameters

### --role

Controls which category of jobs to retrieve.

  Value        Meaning
  ------------ ----------------------------
  internship   Internship roles (default)
  newgrad      New‑graduate roles

Example:

``` bash
swelist --role newgrad
swelist --role internship --timeframe lastweek --location "Seattle, Remote"
```

------------------------------------------------------------------------

### --timeframe

Controls recency filtering.

  Value       Time Window
  ----------- ---------------
  lastday     Last 24 hours
  lastweek    Last 7 days
  lastmonth   Last 30 days

Example:

``` bash
swelist --timeframe lastweek
swelist --role newgrad --timeframe lastmonth --location "New York, Boston"
```

------------------------------------------------------------------------

### --location

Filters job postings by geographic location.

  Input                            Meaning
  -------------------------------- --------------------------------------------------
  Single location                  `Canada` or `Toronto`
  Multiple locations (comma-separated) `"Boston, New York, Remote"`
  State code (2-letter)            `CA` matches "San Francisco, CA"

Example:

``` bash
swelist --location Toronto
swelist --location "Boston, New York, Remote"
swelist --role newgrad --timeframe lastweek --location "San Francisco, Remote"
swelist --role internship --timeframe lastmonth --location CA
```

------------------------------------------------------------------------

## tracker subcommand

Local SQLite tracker for job applications synced from Gmail.

**Before invoking any tracker command, read `~/.claude/profile.md`:**

1. Check `Integrations > Tracker Backend` — if `tracker_backend` is `notion`,
   the tracker subcommand is not applicable; use the `application-manager` skill instead.
2. If `tracker_backend` is `sqlite` (or blank, defaulting to sqlite for local use),
   read `SQLite DB path` from profile.md. Use that value as `--db PATH`.
   Fall back to `~/.offerplus/applications.db` only if the field is blank.

``` bash
# Resolve DB_PATH from profile.md first, then:
swelist tracker init   [--db DB_PATH]
swelist tracker add    "<Company — Role>" --status <S> [--job-id <id>] [--applied-on YYYY-MM-DD] [--db DB_PATH]
swelist tracker update "<Company — Role>" --status <S> [--notes <text>] [--db DB_PATH]
swelist tracker get    "<Company — Role>" [--db DB_PATH]     # JSON; exit 1 + null if not found
swelist tracker list   [--status S] [--company C] [--db DB_PATH]
swelist tracker export [--format csv|json] [--db DB_PATH]
```

If the DB does not exist yet, run `tracker init` before any other tracker command.

### tracker add output sample

Input: `swelist tracker add "Stripe — Backend Engineer" --status "In progress" --job-id S789 --applied-on 2026-05-18`

```
Added: Stripe — Backend Engineer → In progress
```

Input (duplicate):

```
Skipped (already exists): Stripe — Backend Engineer
```

### tracker update output sample

Input: `swelist tracker update "Amazon — SDE, AWS" --status "Rejected"`

```
Updated: Amazon — SDE, AWS → Rejected
```

Input (not found):

```
Not found: Acme — Engineer
```

### tracker get output sample

Input: `swelist tracker get "Amazon — SDE, AWS"`

```json
{"name": "Amazon — SDE, AWS", "status": "Rejected", "job_id": "10414382", "applied_on": "2026-05-17", "notes": null, "updated_at": "2026-05-18 01:10:00"}
```

Input (not found) — exits with code 1:

```json
null
```

### tracker list output sample

Input: `swelist tracker list`

```
 Application                                    Status        Job ID      Applied       Updated
 Amazon — Software Development Engineer, AWS    In progress   10414382    2026-05-17    2026-05-17 18:30:00
 Amazon — Software Development Engineer         In progress   3146673     2026-04-21    2026-04-21 20:50:00
 Amazon — Software Development Engineer, Playback Team  Rejected  3083065  2025-12-02  2025-12-02 17:20:00

3 application(s)
```

Input: `swelist tracker list --status "In progress" --company amazon`

```
 Application                                    Status        Job ID      Applied       Updated
 Amazon — Software Development Engineer, AWS    In progress   10414382    2026-05-17    2026-05-17 18:30:00
 Amazon — Software Development Engineer         In progress   3146673     2026-04-21    2026-04-21 20:50:00

2 application(s)
```

### tracker export output sample

Input: `swelist tracker export --format json`

```json
[
  {
    "name": "Amazon — Software Development Engineer, AWS",
    "status": "In progress",
    "job_id": "10414382",
    "applied_on": "2026-05-17",
    "notes": null,
    "updated_at": "2026-05-17 18:30:00"
  },
  {
    "name": "Amazon — Software Development Engineer, Playback Team",
    "status": "Rejected",
    "job_id": "3083065",
    "applied_on": "2025-12-02",
    "notes": null,
    "updated_at": "2025-12-02 17:20:00"
  }
]
```

Input: `swelist tracker export --format csv`

```
name,status,job_id,applied_on,notes,updated_at
Amazon — Software Development Engineer,In progress,3146673,2026-04-21,,2026-04-21 20:50:00
Amazon — Software Development Engineer Playback Team,Rejected,3083065,2025-12-02,,2025-12-02 17:20:00
```

------------------------------------------------------------------------

## Output Contract

-   Output is written to **STDOUT**
-   Format is **human- and agent-readable plain text**
-   No JSON or structured serialization

### Job Posting Fields

Each job entry contains:

-   Company (string)
-   Title (string)
-   Location (string) — may be a single string or a list
-   Link (URL)

### Realistic output sample

Input: `swelist --role internship --timeframe lastweek --location "Seattle, Remote"`

```
Welcome to swelist.com
Last updated: Sun May 17 18:42:01 2026
Found 1284 tech internships from 2025Summer-Internships
Found 892 new-grad tech jobs from New-Grad-Positions
Sign-up below to receive updates when new internships/jobs are added

Found 3 postings for location 'Seattle, Remote' in TimeFilter.lastweek

Company: Amazon
Title: Software Development Engineer Intern
locations: ['Seattle, WA', 'Remote']
Link: https://www.amazon.jobs/en/jobs/2345678

Company: Microsoft
Title: Software Engineering Intern
locations: ['Redmond, WA', 'Remote']
Link: https://jobs.careers.microsoft.com/us/en/job/1234567

Company: Stripe
Title: Software Engineer, Intern
locations: ['Remote']
Link: https://stripe.com/jobs/listing/software-engineer-intern/9876543
```

### Empty-result output

When no postings match the filters:

```
# No jobs in the selected timeframe:
No postings found in TimeFilter.lastday

# Jobs exist but none match the location:
No postings found for location 'Austin' in TimeFilter.lastday
```

Agents should treat either message as a zero-result signal and not retry with the same flags.

------------------------------------------------------------------------

## Execution Guarantees

-   No side effects
-   No persistent storage
-   Safe for repeated execution
-   Deterministic given identical upstream data
-   No authentication required

------------------------------------------------------------------------

## Error Behavior

-   Network issues may raise runtime errors or result in empty output
-   Invalid flags produce CLI usage errors
-   Zero matching jobs produces valid empty result output

------------------------------------------------------------------------

## Environment Requirements

-   Python 3.8+
-   Internet access
-   Supported on macOS, Linux, Windows

------------------------------------------------------------------------

## Agent-Oriented Use Cases

-   Daily polling for new internship postings
-   Weekly new‑grad job aggregation
-   Feeding results into ranking, scoring, or alerting agents
-   Execution via cron, CI pipelines, or autonomous agents
-   Parsing job postings into structured JSON for downstream processing
-   Integration with AI agents for automated job application workflows

------------------------------------------------------------------------

## Known Limitations

-   No built‑in alerting
-   No local caching
-   No deduplication beyond source data
-   No JSON output format

------------------------------------------------------------------------

## Safety & Compliance

-   Uses only public data
-   No user tracking
-   No credential usage
-   No scraping of private systems

------------------------------------------------------------------------

## Versioning

Behavior may evolve with upstream data sources. CLI flags are considered
stable within a major version.

------------------------------------------------------------------------

# jobgpt

This document defines the operational capabilities, invocation contract,
and usage semantics of the `jobgpt` command for AI-powered job application
assistance.

------------------------------------------------------------------------

## Tool Identity

-   **Name:** jobgpt
-   **Type:** Command-Line Interface (CLI)
-   **Language:** Python
-   **Distribution:** Part of swelist package
-   **Execution Model:** Stateless, AI-powered writing assistant

------------------------------------------------------------------------

## Purpose

`jobgpt` is an AI writing assistant that helps job seekers prepare for
interviews and job applications by generating compelling answers and career
advice.

It is optimized for: - Interview preparation - Application materials - Career
guidance

------------------------------------------------------------------------

## Subcommands

### ask

Ask any career or job-search question.

``` bash
jobgpt ask "Your question here"
```

**Parameters:**

-   **question** (positional, required): Any job-search or career question

**Options:**

-   `--model`: OpenAI model to use (default: `gpt-4o`)
-   `--copy`: Copy output to clipboard (flag)

**Example:**

``` bash
jobgpt ask "What should I focus on in my first internship?"
jobgpt ask "How do I negotiate salary?" --copy
```

**Sample output:**

```
╭─ Career Advice ────────────────────────────────────────────────────╮
│                                                                     │
│  Focus on three things in your first internship:                   │
│                                                                     │
│  1. **Shipping something real** — even a small feature that goes   │
│     to production teaches you more than any tutorial.              │
│  2. **Building relationships** — your intern cohort and your       │
│     manager are your longest-lasting professional network.         │
│  3. **Asking good questions** — juniors who ask precise, well-     │
│     researched questions are remembered positively.                │
│                                                                     │
╰─────────────────────────────────────────────────────────────────────╯
```

------------------------------------------------------------------------

### why-company

Generate a compelling answer to "Why do you want to work at [Company]?"

``` bash
jobgpt why-company "Company Name" --background "Your background"
```

**Parameters:**

-   **company** (positional, required): Company name

**Options:**

-   `--background`: Your background summary (optional, recommended)
-   `--model`: OpenAI model to use (default: `gpt-4o`)
-   `--copy`: Copy output to clipboard (flag)

**Example:**

``` bash
jobgpt why-company "Google" --background "Software Engineering student with Python and web development experience"
jobgpt why-company "Meta" --background "Full-stack developer with React and Node.js expertise" --copy
```

------------------------------------------------------------------------

### behavioral

Generate a STAR-format answer to a behavioral interview question.

``` bash
jobgpt behavioral "Question here" [--resume path/to/resume.txt]
```

**Parameters:**

-   **question** (positional, required): The behavioral interview question

**Options:**

-   `--resume`: Path to resume text file (optional)
-   `--model`: OpenAI model to use (default: `gpt-4o`)
-   `--copy`: Copy output to clipboard (flag)

**Example:**

``` bash
jobgpt behavioral "Tell me about a time you dealt with conflict on a team"
jobgpt behavioral "Describe your biggest failure and how you learned from it" --resume resume.txt --copy
```

**Sample output:**

```
╭─ STAR Answer ───────────────────────────────────────────────────────╮
│                                                                      │
│  **Situation:** During my internship at Acme, our team disagreed    │
│  on the API design for a new service — two engineers wanted REST,   │
│  one pushed for GraphQL.                                            │
│                                                                      │
│  **Task:** As the engineer writing the initial spec, I needed to    │
│  drive us to a decision before our sprint planning the next day.    │
│                                                                      │
│  **Action:** I drafted a one-page trade-off doc comparing latency,  │
│  client complexity, and team familiarity for both options, then     │
│  scheduled a 30-minute sync. I proposed REST with a versioning      │
│  convention that addressed the GraphQL advocate's flexibility       │
│  concerns.                                                          │
│                                                                      │
│  **Result:** We reached consensus in 20 minutes. The service        │
│  shipped on time and has had zero breaking-change incidents in      │
│  six months.                                                        │
│                                                                      │
╰──────────────────────────────────────────────────────────────────────╯
```

------------------------------------------------------------------------

## Output Contract

-   Output is written to **STDOUT**
-   Format is **human-readable markdown** with rich text formatting
-   Organized in clear panels with proper section headers
-   Optimized for reading and copying to clipboard

------------------------------------------------------------------------

## Execution Guarantees

-   Requires OpenAI API key (set via `OPENAI_API_KEY` environment variable)
-   No persistent storage
-   Safe for repeated execution
-   Deterministic given identical input (within model capabilities)

------------------------------------------------------------------------

## Error Behavior

-   Missing `OPENAI_API_KEY` environment variable produces clear error message
-   Invalid OpenAI model names produce API errors
-   Missing resume file produces OSError with clear message
-   Network issues may raise runtime errors

------------------------------------------------------------------------

## Environment Requirements

-   Python 3.8+
-   OpenAI API key (`OPENAI_API_KEY`)
-   Internet access for API calls
-   Supported on macOS, Linux, Windows

------------------------------------------------------------------------

## Agent-Oriented Use Cases

-   Preprocessing candidate data for interview coaching bots
-   Generating interview preparation materials at scale
-   Feeding career advice into autonomous career planning agents
-   Integration with resume builders and application workflows

------------------------------------------------------------------------

## Known Limitations

-   Requires OpenAI API key and internet connection
-   Responses vary based on model capability
-   No local caching of responses
-   No built-in follow-up question handling

------------------------------------------------------------------------

## Safety & Compliance

-   Uses only public OpenAI API
-   No data persistence
-   No credential sharing or exposure
-   Respects OpenAI usage policies

------------------------------------------------------------------------

End of document.
