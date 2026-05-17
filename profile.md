# User Profile

This file is the single source of truth for user-specific configuration.
All skills in this project read from here first. Any skill can update this
file when the user provides new information.

---

## Personal Info

- **Name:**
- **Career email:**
- **LinkedIn URL:**
- **Location:**
- **Phone:** _(optional, for resume/cover letter skills)_

---

## Career Profile

- **Current role / background:**
- **Years of experience:**
- **Target roles:** _(e.g. "Software Engineer, Backend Engineer, SDE")_
- **Target companies:** _(e.g. "Google, Meta, Amazon, startups")_
- **Target locations:** _(e.g. "San Francisco, Remote, New York")_
- **Target salary range:** _(e.g. "$150k–$200k base + equity")_
- **Work authorization:** _(e.g. "US citizen", "requires H-1B sponsorship")_

---

## Resume

Paste resume text here, or provide a file path:

**File path:** _(e.g. `./resume.pdf` or `./resume.txt`)_

```
[paste resume text here]
```

---

## Integrations

### Notion

- **Career tracker database ID:** _(UUID from the Notion database URL)_
- **Career tracker URL:**
- **Collection URL:** `collection://<paste database ID above>`

### Gmail Labels

Run `mcp__claude_ai_Gmail__list_labels` and fill in the label IDs for
any job-related labels you use:

| Label name | Label ID |
|---|---|
| e.g. amazon | e.g. Label_XXXX |
| e.g. reject | e.g. Label_XXXX |
| e.g. linkedin | e.g. Label_XXXX |

---

## Skill Config Reference

Which sections each skill uses — so you know what to fill in:

| Skill | Sections needed |
|---|---|
| `application-manager` | Integrations (Notion + Gmail), Personal Info (career email) |
| `resume-tailor` | Personal Info, Career Profile, Resume |
| `cover-letter-generator` | Personal Info, Career Profile, Resume |
| `interview-prep-generator` | Personal Info, Career Profile, Resume |
| `job-description-analyzer` | Career Profile |
| `salary-negotiation-prep` | Career Profile (target salary, role, location) |
| `offer-comparison-analyzer` | Career Profile (target salary) |
| `linkedin-profile-optimizer` | Personal Info (LinkedIn URL), Career Profile, Resume |
| `tech-resume-optimizer` | Personal Info, Career Profile, Resume |
| `resume-quantifier` | Resume |
| `resume-bullet-writer` | Career Profile, Resume |
| `resume-ats-optimizer` | Career Profile, Resume |

---

## How to Update This File

Any skill will offer to save new information here when it collects it.
You can also ask directly: _"save my Notion database ID to my profile"_
or _"update my profile with my career email"_.
