---
name: Interview Prep
description: Generate a structured interview prep doc for any company — pulls context from Gmail, Notion, and existing notes, then writes a timeline.md to the interviewGPT folder.
---

# Interview Prep

## When to Use This Skill

Trigger when the user asks to:

- Prepare for an upcoming interview ("prep notes for [Company] interview", "create interview prep for [Company]")
- Generate a prep document for a scheduled interview
- Update or add to an existing prep doc for a company
- Research a company before an interview

Keywords: `interview prep`, `prep notes`, `prepare for interview`, `interview at [company]`, `[company] interview`, `prep doc`

---

## Setup (first-time use)

Read `~/.claude/profile.md` first — it contains the career email and tracker backend config.

**Required inputs** (collect if not provided):
1. **Company name** — e.g. "Applied Intuition", "Amazon AWS"
2. **Interview date** — e.g. "June 9, 2026" or "2026-06-09"
3. **Role title** (optional) — infer from emails or Notion if not given
4. **Output path** (default) — `~/PycharmProjects/interviewGPT/<company-slug>/<YYYY-MM>-timeline.md`
   - company-slug: lowercase, spaces → hyphens, special chars stripped
     e.g. "Applied Intuition" → `applied_intuition`, "Amazon AWS" → `amazon`
   - YYYY-MM: derived from interview date
   - If a file already exists at that path, read it first and merge/update rather than overwrite

---

## Config: Role → Tech Topic Mapping

Infer the likely interview format from the role title and company domain.

| Role signals | Likely format | High-priority topics |
|---|---|---|
| "Software Engineer", "SWE", "Backend", "Infrastructure" | LC coding + system design | Arrays/strings, graphs/BFS/DFS, hash maps, binary search, system design |
| "Data Engineer", "Platform Engineer", "Data Infra" | LC coding + system design + SQL | Above + SQL, data pipelines, stream vs batch, partitioning |
| "Frontend", "Full-stack" | LC coding + UI/architecture | Arrays, trees, DOM/React patterns, web performance |
| "ML Engineer", "ML Infra" | LC coding + ML system design | Arrays, trees, ML pipelines, training infra, feature stores |
| "Quant", "Trading", "Finance SWE" | Math-heavy LC + probability/stats | Arrays, DP, probability, market data structures |
| _(unknown)_ | LC coding + behavioral | Arrays/strings, hash maps, BFS/DFS, binary search |

---

## Config: Company Context Templates

Use these as starting points when generating company context. Always check for more recent public information.

| Company signals | Key products / domain | Culture notes |
|---|---|---|
| Autonomous vehicles / AV / self-driving | Simulation platforms, sensor data pipelines, ADAS validation | C++/Python heavy, reliability > speed, enterprise B2B |
| Finance / investment bank / trading | Market data systems, risk models, order management | Low-latency, correctness critical, regulatory compliance |
| Cloud / infra / DevOps | Distributed systems, storage, networking | Scale-focused, SRE culture, on-call norms |
| Consumer tech / social | Web scale, ML recommendations, content delivery | Move fast, experimentation, A/B testing |
| Healthcare / biotech | Data compliance (HIPAA), ML models, EHR integration | Correctness, privacy, slow regulatory cycles |
| Startup (< 200 people) | 0→1 product, cross-functional ownership | Broad scope, ownership culture, wear many hats |

---

## Workflow

```
INPUT: company_name, interview_date, role_title (optional), existing_file_path (optional)

STEP 0  Load config
  Read ~/.claude/profile.md → CAREER_EMAIL, tracker_backend, DB_PATH or NOTION_DB_ID
  Derive:
    company_slug = company_name.lower().replace(" ", "_").strip()
    interview_year_month = interview_date[:7]  # "YYYY-MM"
    output_path = f"~/PycharmProjects/interviewGPT/{company_slug}/{interview_year_month}-timeline.md"

STEP 1  Check for existing notes
  IF existing file at output_path:
    Read it → note any pre-filled sections (contacts, logistics, company context)
    Set mode = "update"
  ELSE:
    Check for any .md files in ~/PycharmProjects/interviewGPT/{company_slug}/
    IF found: read them for context
    Set mode = "create"

STEP 2  Search Gmail for company emails
  query = f'"{company_name}" newer_than:6m'
  Fetch up to 10 threads via mcp__claude_ai_Gmail__search_threads
  For threads with ambiguous snippets, fetch full thread via mcp__claude_ai_Gmail__get_thread
  Extract:
    interview_datetime  = date + time of scheduled interview (e.g. "June 9, 4:00–4:45pm ET")
    interview_format    = "Video (Google Meet) + CoderPad" | "Phone" | "Onsite" | etc.
    access_code         = any CoderPad/HackerRank/Codility access codes found in body
    contacts[]          = { name, role, email } from From/Cc/signature
                          Include: recruiter, coordinator, interviewer
    timeline[]          = chronological list of { date, event } extracted from thread history
    job_link            = ATS URL if present (Greenhouse, Lever, etc.)
    role_title          = extract from subject line or body if not provided

STEP 3  Look up Notion page (if tracker_backend == "notion")
  notion_search(company_name) → find page in 2026 Career database
  Extract:
    status, next_action, applied_on, last_touch
    Page body: timeline, conversation notes, prep suggestions (if enriched)
  Merge with Gmail data — Gmail is authoritative for contacts and dates

STEP 4  Look up SQLite (if tracker_backend == "sqlite")
  sqlite3 DB_PATH "SELECT * FROM applications WHERE name LIKE '%{company_name}%'"
  Extract: status, applied_on, last_touch, interview_date, notes

STEP 5  Generate company context
  Based on company_name + role_title:
  - Write 4–6 bullet points about what the company does, its main products/platform
  - Note the tech stack if known (C++, Python, Scala, etc.)
  - Note the business model (enterprise, consumer, B2B SaaS, etc.)
  - Note why this matters for the interview (what they'll probe: scale, reliability, speed, etc.)
  Use knowledge up to August 2025 as baseline; note if you're uncertain.

STEP 6  Generate technical prep section
  Based on role_title + company domain → use Role→Tech Topic Mapping table:
  - Interview format estimate (timing, # of problems)
  - High-priority DSA topics (top 5)
  - 3 warm-up LeetCode problems (by number + name)
  - Coding environment tips (CoderPad / HackerRank / whiteboard)

STEP 7  Generate behavioral prep section
  - Draft a 2-minute intro template (fill in [X] placeholders for the user to complete)
  - List 3 STAR story frames relevant to the company/role (Scale, Ownership, Trade-off)
    Tailor to the company: AV → data reliability; finance → correctness under pressure; startup → ambiguity

STEP 8  Generate questions to ask
  Write 4–5 tailored questions for the interviewer based on:
  - The stage (initial screen / technical / hiring manager / onsite)
  - The company domain
  Always include: interview loop structure, team challenges, success definition

STEP 9  Build the day-of checklist
  Standard items + any extracted from emails (meeting links, access codes, dial-in numbers)

STEP 10  Write the prep doc
  Write to output_path (create parent directory if needed)
  Format: see "Output Format" section below
  IF mode == "update": preserve any sections the user has already filled in; only add/update blank ones
  Report: "Wrote prep doc to {output_path}"
```

---

## Output Format

The generated file should follow this template exactly. Fill every section from the data gathered; use `_(TBD)_` only if a field truly cannot be determined.

```markdown
# {Company Name} — Interview Prep

**Date:** {Day}, {Month} {Day}, {Year} · {Time} {Timezone}
**Format:** {format, e.g. "Video (Google Meet) + CoderPad"}
**Access code:** `{code}` _(or: _(none found)_)_

---

## Contacts

| Name | Role | Email |
|---|---|---|
| {name} | {role} | {email or —} |

---

## Timeline

| Date | Event |
|---|---|
| {YYYY-MM-DD} | {event summary} |
| **{interview date}** | **{interview description}** |

---

## Company Context

{4–6 bullet points covering: what the company does, main products/platform, tech stack, business model, and what the interview will likely probe}

---

## Technical Prep

### Format expectation
{N} min total: likely ~{N} min intro, ~{N} min coding ({N} problems on {platform}), ~{N} min Q&A.

### Practice resource
https://www.fastprep.io/dashboard/problems

### High-priority topics
1. **{topic}** — {brief note on what to practice}
2. **{topic}** — {brief note}
3. **{topic}** — {brief note}
4. **{topic}** — {brief note}
5. **{topic}** — {brief note}

### Coding environment tips
- {platform-specific tip}
- Think aloud from the start — the interviewer evaluates communication as much as correctness
- Write a brute-force first, then optimize — say it out loud before coding
- Test with edge cases: empty input, single element, duplicates, negative numbers

### Sample warm-up problems (do 1 timed before the interview)
- LeetCode {number} — {name}
- LeetCode {number} — {name}
- LeetCode {number} — {name}

---

## Behavioral Prep

### 2-minute intro
> "I'm a software engineer focused on {area}. Most recently I've been building [X] — [one sentence on impact]. I'm drawn to {Company} because [one specific reason tied to their mission/tech]. I'd love to learn more about the team's current challenges."

### 3 STAR stories to have ready

| Story | Situation | Action | Result |
|---|---|---|---|
| {theme} | {setup} | {what you did} | {outcome — include a number} |
| {theme} | {setup} | {what you did} | {outcome} |
| {theme} | {setup} | {what you did} | {outcome} |

---

## Questions to Ask

1. {tailored question about interview loop / next steps}
2. {tailored question about team's current biggest technical challenge}
3. What does success look like in the first 30/60/90 days for this role?
4. {tailored question specific to company domain / product}
5. {optional: team culture / eng org structure}

---

## Logistics Checklist (day of)

- [ ] Find meeting link + dial-in info in the {date} email from {recruiter/coordinator}
- [ ] {If CoderPad} Open CoderPad with access code `{code}` and test it runs
- [ ] Test audio/video 10 min before
- [ ] Have water nearby; mute notifications
- [ ] Open a scratch editor (VS Code / notes) alongside the coding platform
- [ ] Have this doc open on a second screen or phone
```

---

## Edge Cases

| Situation | How to handle |
|---|---|
| No Gmail threads found for company | Note it; generate doc from what's known; leave contacts/timeline blank with _(TBD)_ |
| Interview date not in emails | Ask user to confirm date before writing; don't invent it |
| Multiple roles at same company | Ask user which role this prep is for; use role in filename |
| File already exists at output path | Read it; update only blank/TBD sections; preserve user's hand-written notes |
| interviewGPT folder doesn't exist | Create it: `mkdir -p ~/PycharmProjects/interviewGPT/{company_slug}` |
| Notion page not found | Skip Notion step; note in report |
| Role type unclear | Default to SWE topics (arrays, graphs, hash maps, binary search, system design) |
| Company is a trading firm / quant shop | Emphasize: LC hard on arrays/DP, probability, market data; de-emphasize system design |
| Onsite / final round | Add note: "This is a later-stage round — expect system design + behavioral depth + leadership/values fit" |
