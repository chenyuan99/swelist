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
- View company name, job title, location, and application link
- Real-time data from GitHub repositories
- Easy-to-use command-line interface

## Installation

```bash
pip install swelist
```

## Usage

Basic usage:
```bash
# Show internship positions from last 24 hours (default)
swelist run

# Show new-grad positions from last 24 hours
swelist run --role newgrad

# Show internship positions from last week
swelist run --role internship --timeframe lastweek
```

### Options

- `--role`: Choose between `internship` (default) or `newgrad` positions
- `--timeframe`: Filter postings by time period: `lastday` (default), `lastweek`, or `lastmonth`

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
