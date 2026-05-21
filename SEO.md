# clawhub SEO Journey

Tracking all optimization work done to improve search discoverability of the
`swelist` and `job-application-manager` skills on [clawhub.ai](https://clawhub.ai).

---

## Skills

| Skill | Slug | URL |
|---|---|---|
| Swelist | `swelist` | https://clawhub.ai/chenyuan99/swelist |
| Job Application Manager | `job-application-manager` | https://clawhub.ai/chenyuan99/job-application-manager |

---

## Baseline (before optimization)

### swelist
- **description:** "retrieves tech internship and new-grad job postings; tracks job applications in local SQLite."
- **No** keywords, tags, author, repository, category, or summary fields
- **Category on clawhub:** Other

### job-application-manager
- **description:** "Sync job application statuses from Gmail into Notion or a local SQLite database"
- **No** keywords, tags, author, repository, category, or summary fields
- **No** "When to Use" trigger phrases

### Baseline search rankings (clawhub vector search)

| Query | swelist | job-application-manager |
|---|---|---|
| "swelist" | #1 (4.2) | — |
| "internship job search" | not ranked | — |
| "job tracker" | not ranked | not ranked |
| "new grad jobs" | #1 (0.613) | — |
| "find tech internships" | #1 (0.613) | — |
| "job application tracker" | — | not ranked |
| "notion job tracker" | — | not ranked |

---

## Round 1 — Frontmatter enrichment

**Commits:** `c74b8e9`, `f540eeb`

Changes applied to both skills:
- Rewrote `description` to be action-oriented and keyword-rich
- Added `keywords` array (14 terms each)
- Added `tags` array
- Added `category: career`

### Results
- `category` field did not immediately update from "Other" on clawhub (pending re-index)
- No measurable ranking change observed at this stage

---

## Round 2 — Author, repository, body content

**Commit:** `7602522`

Changes applied to both skills:
- Added `author: Yuan Chen` and `repository:` fields
- Rewrote opening paragraph of swelist body with keyword-rich prose
- Added **"When to Use"** section to swelist (was missing entirely)
- Expanded "When to Use" trigger phrases in job-application-manager
- Added `summary` field (longer semantic prose for embedding coverage)

### Results (post-index)

| Query | swelist | job-application-manager |
|---|---|---|
| "job tracker" | not ranked | **#5 (0.421)** ← new |
| "new grad jobs" | #1 (0.613) | — |
| "find tech internships" | #1 (0.613) | — |
| "job application tracker" | — | #1 (0.421) |
| "notion job tracker" | — | #1 (0.877) |
| "internship job search" | not ranked | — |
| "gmail job sync" | — | not ranked |

**Lesson:** Adding the `summary` field and "When to Use" section helped
`job-application-manager` appear for "job tracker" queries. Scores improved
slightly but remained low (~0.4–0.9) vs top competitors at 2.9–4.0.

---

## Round 3 — Display name update

**Commit:** `f581e3c`

- swelist `name` → `Swelist — Tech Internship & Job Tracker`
- job-application-manager `name` → `Job Application Manager — Gmail & Notion Sync`

### Results
No ranking change. **Lesson:** clawhub's vector embedding uses the **slug**
as the primary text input, not the frontmatter `name` field. Display name
changes have no effect on search scores.

---

## Round 4 — Description rewrite (sync-focused) for job-application-manager

**Commit:** `1449a6d`

- Rewrote description to lead with "Syncs" and use "sync" language throughout
- Rewrote summary to include: "sync your job applications from Gmail",
  "job pipeline", "career dashboard", "application spreadsheet", "email inbox"

### Results

| Query | Before | After |
|---|---|---|
| "gmail job sync" | not ranked | **#1 (0.869)** ✅ |
| "notion job tracker" | #1 (0.877) | #1 (0.875) — same |
| "job application tracker" | #1 (0.421) | #1 (0.421) — same |
| "job offer rejection email" | #1 (0.421) | #1 (0.421) — same |
| "job tracker" | #5 (0.421) | #5 (0.421) — same |
| "sync applications gmail" | not ranked | not ranked |
| "application status tracker" | #1 (0.421) | not ranked ↓ |

**Lesson:** Leading with "sync" unlocked "gmail job sync" (#1 at 0.869) — a
direct gain from the description rewrite. "sync applications gmail" (reversed
word order) still misses, likely below clawhub's display threshold rather than
a content gap. "application status tracker" regressed — the old description
contained "updates…statuses" which matched that phrase; removing it caused the
drop. Worth restoring "statuses" language in the next round.

---

## Round 5 — Restore "statuses" language (regression fix)

**Commit:** `5d00bfd`

- Added "updates statuses" back into description while keeping "sync" lead
- Final description: "Syncs job application emails from Gmail and updates statuses in your Notion or SQLite tracker — detects offers, rejections, and interview invitations"

### Results

| Query | Before | After |
|---|---|---|
| "application status tracker" | not ranked ↓ | **#1 (0.421)** ✅ restored |
| "gmail job sync" | #1 (0.869) | #1 (0.868) — same |
| "job application tracker" | #1 (0.421) | #1 (0.421) — same |
| "notion job tracker" | #1 (0.875) | #1 (0.873) — same |

**Lesson:** Restoring "statuses" recovered the regressed query with no cost to
the gains from Round 4. The description now holds four ranked queries simultaneously.
Both "sync" and "statuses" can coexist — word choice is additive, not zero-sum.

---

## Key Findings

### What works
- **Keywords and tags** are indexed and visible on the skill listing page
- **Summary/description** is the primary field clawhub uses for full-text and vector search
- **"When to Use" section** in skill body helps Claude's own skill-matching

### What doesn't work
- **Display `name` field** — has no effect on vector search scores (slug is used instead)
- **Category field** — slow to re-index; may not update immediately

### Root cause of low scores
The `swelist` slug is a brand name with no semantic relationship to "internship",
"job search", or "job tracker". Competing skills that rank at 2.9–4.0 all have
descriptive slugs: `job-tracker`, `job-hunt-tracker`, `internship-daily-reflection`.

The `job-application-manager` slug is descriptive and performs better, but scores
still cap around 0.877 — likely because the description/summary need more iterations.

---

## Backlog

- [ ] **Rename `swelist` slug** to `tech-job-tracker` (or similar) via:
  ```
  clawhub skill rename swelist tech-job-tracker
  ```
  Old slug kept as redirect; no impact on existing installs.
  Expected score jump from ~0.6 to ~2.9+ for "internship" and "job tracker" queries.

---

## Benchmark Commands

```bash
# Check indexed metadata
clawhub inspect swelist
clawhub inspect job-application-manager

# Search ranking benchmarks
clawhub search "internship job search"
clawhub search "job tracker"
clawhub search "find tech internships"
clawhub search "new grad jobs"
clawhub search "gmail job sync"
clawhub search "job application tracker"
clawhub search "notion job tracker"
clawhub search "sync applications gmail"
clawhub search "application status tracker"
```
