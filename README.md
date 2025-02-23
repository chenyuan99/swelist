# swelist

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
swelist
```

This will:
1. Show current statistics for available positions
2. Prompt you to choose between internship or new-grad roles
3. Display recent job postings (default: last 24 hours)

### Time Filters

You can view positions from different time periods using the `--timeframe` or `-t` option:

```bash
# Show positions from last 24 hours (default)
swelist -t lastday

# Show positions from last week
swelist -t lastweek

# Show positions from last month
swelist -t lastmonth
```

### Options

- `--timeframe`, `-t`: Filter postings by time period [lastday|lastweek|lastmonth]
- Role selection will be prompted during execution

## Example Output

```
Welcome to swelist.com
Last updated: Sun Feb 23 11:15:03 2025
Found 1227 tech internships from 2025Summer-Internships
Found 103 new-grad tech jobs from New-Grad-Positions
Sign-up below to receive updates when new internships/jobs are added

Are you looking for an internship or a new-grad role? [internship/newgrad]: internship

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
