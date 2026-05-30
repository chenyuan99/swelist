# Backlog

## clawhub

- [ ] Rename `swelist` slug to a descriptive alternative (e.g. `tech-job-tracker`) to improve vector search ranking. The brand-name slug scores ~0.6 vs competitors at 2.9–4.0. Old slug is kept as a redirect so existing installs are unaffected.
  ```
  clawhub skill rename swelist tech-job-tracker
  ```
  After renaming, re-run benchmarks: `clawhub search "internship job search"`, `clawhub search "job tracker"`.

---

## job-application-manager skill

Features suggested but not yet implemented, in rough priority order.

### Medium priority

- [ ] **Link extraction** — scan email bodies and footers for Greenhouse, Lever, Workday, and Ashby URLs and write them to the `Link` property automatically. Most ATS platforms have recognisable URL patterns (`boards.greenhouse.io`, `jobs.lever.co`, `apply.workday.com`). Currently the `Link` property exists in the schema but is never populated by the skill.

- [ ] **Auto-tag suggestions** — infer `Tags` values from email content: add `Referral` if the email mentions someone referring the applicant by name, `Remote` if the role description says remote, `Urgent` if a response deadline is mentioned. Present suggestions to the user before writing; never write Tags that aren't already in the Notion options list.

- [ ] **Funnel summary in report** — after a full sync (no specific company given), print a one-line pipeline breakdown at the top of the report:
  ```
  Pipeline: 8 Applied · 3 OA · 2 Interviewing · 1 Offer · 5 Rejected
  ```
  Gives an at-a-glance view of the job search health without opening Notion.

### Lower priority

- [ ] **Fuzzy company dedup** — "Meta" and "Meta Platforms", "Google" and "Google DeepMind", etc. currently create separate rows. Add a company alias table (or edit-distance check with threshold ≤ 2) to detect these variants and prompt the user to confirm a merge before writing.

- [ ] **Bulk re-enrichment mode** — add a `--enrich-all` flag (or trigger phrase "re-enrich all pages") that runs Step 5 page enrichment (timeline, key contacts, prep notes) against every existing Notion page, not just ones touched in the current sync run. Useful for pages created before v0.2.0 or via the old Notion AI flow.
