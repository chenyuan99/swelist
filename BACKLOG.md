# Backlog

## clawhub

- [ ] Rename `swelist` slug to a descriptive alternative (e.g. `tech-job-tracker`) to improve vector search ranking. The brand-name slug scores ~0.6 vs competitors at 2.9–4.0. Old slug is kept as a redirect so existing installs are unaffected.
  ```
  clawhub skill rename swelist tech-job-tracker
  ```
  After renaming, re-run benchmarks: `clawhub search "internship job search"`, `clawhub search "job tracker"`.
