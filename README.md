# swelist

[![CI](https://github.com/chenyuan99/swelist/actions/workflows/ci.yml/badge.svg)](https://github.com/chenyuan99/swelist/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/chenyuan99/swelist/branch/main/graph/badge.svg)](https://codecov.io/gh/chenyuan99/swelist)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/swelist.svg)](https://badge.fury.io/py/swelist)
[![Python Versions](https://img.shields.io/pypi/pyversions/swelist.svg)](https://pypi.org/project/swelist/)

A CLI tool for job seekers to track tech internships and new-grad positions. Data is sourced from the [Summer2025-Internships](https://github.com/SimplifyJobs/Summer2025-Internships) and [New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) repositories.

## Features

- Track both internships and new-grad positions
- Filter job postings by time (last day, week, or month)
- Filter job postings by locations
- View company name, job title, location, and application link
- Real-time data from GitHub repositories
- Local SQLite application tracker (`swelist tracker`)
- AI-powered interview prep via `swelist jobgpt`

## Installation

```bash
pip install swelist
```

## Usage

### Command Line

Basic usage:
```bash
# Show internship positions from last 24 hours (default)
swelist

# Show new-grad positions from last 24 hours
swelist --role newgrad

# Show internship positions from last week
swelist --role internship --timeframe lastweek

# Show internship positions for Toronto
swelist --role internship --location Toronto

# Show new-grad positions for last month for Boston and New York
swelist --role newgrad --timeframe lastmonth --location "Boston, New York"
```

### Options

- `--role`: Choose between `internship` (default) or `newgrad` positions
- `--timeframe`: Filter postings by time period: `lastday` (default), `lastweek`, or `lastmonth`
- `--location`: Filter locations by giving single location: `Canada` or multiple locations `"Boston, Toronto, New York"`

### Application Tracker

Track job applications locally with SQLite — no account required:

```bash
# Initialize (once)
swelist tracker init

# Add applications
swelist tracker add "Amazon — SDE, AWS" --status "In progress" --job-id 10414382 --applied-on 2026-05-17

# Update status
swelist tracker update "Amazon — SDE, AWS" --status "Rejected"

# View all
swelist tracker list
swelist tracker list --status "In progress" --company amazon

# Export
swelist tracker export --format json
swelist tracker export --format csv
```

### Agent Integration

`swelist` can be integrated into AI automation workflows to parse job postings and convert them to structured JSON:

```python
import subprocess
import json

# Get job postings
output = subprocess.run(['swelist', '--role', 'internship'], capture_output=True, text=True)

# Parse into structured JSON
jobs = []
current_job = {}
for line in output.stdout.splitlines():
    if line.startswith("Company:"):
        current_job = {"company": line.split(":", 1)[1].strip()}
    elif line.startswith("Title:"):
        current_job["title"] = line.split(":", 1)[1].strip()
    elif line.startswith("Location:"):
        current_job["location"] = line.split(":", 1)[1].strip()
    elif line.startswith("Link:"):
        current_job["link"] = line.split(":", 1)[1].strip()
        jobs.append(current_job)

print(json.dumps(jobs, indent=2))
```

This enables use cases like:
- Automated daily job tracking agents
- Integration with AI writing assistants for application workflows
- Real-time job aggregation pipelines

## Example Output

```
Welcome to swelist.com
Last updated: Sun Feb 23 13:03:45 2025
Found 1227 tech internships from 2025Summer-Internships
Found 103 new-grad tech jobs from New-Grad-Positions
Sign-up below to receive updates when new internships/jobs are added

Found 15 postings in the last day:

Company: Example Tech
Title: Software Engineering Intern
Location: New York, NY
Link: https://example.com/apply
...
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License
