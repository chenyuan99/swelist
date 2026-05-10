---
name: swelist
description: retrieves recently added technology internship and new‑graduate job postings.
homepage: https://pypi.org/project/swelist/
metadata:
  {
    "openclaw":
      {
        "emoji": "💼",
        "requires": { "bins": ["swelist"] },
        "install":
          [
            {
              "id": "uv",
              "kind": "uv",
              "package": "swelist",
              "bins": ["swelist"],
              "label": "Install swelist (uv)",
            },
          ],
      },
  }
---
# swelist

This document defines the operational capabilities, invocation contract,
and usage semantics of the `swelist` CLI tool for AI agents, schedulers,
and automation systems.

------------------------------------------------------------------------

## Tool Identity

-   **Name:** swelist
-   **Type:** Command-Line Interface (CLI)
-   **Language:** Python
-   **Distribution:** PyPI
-   **Execution Model:** Stateless, read-only

------------------------------------------------------------------------

## Purpose

`swelist` retrieves recently added technology internship and
new‑graduate job postings from curated public GitHub repositories and
renders them in a predictable, text-based format.

It is optimized for: - Automation pipelines - Periodic polling agents -
Human-in-the-loop job search workflows

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
```

------------------------------------------------------------------------

### --location

Filters job postings by geographic location.

  Input                            Meaning
  -------------------------------- --------------------------------------------------
  Single location                  `Canada` or `Toronto`
  Multiple locations (comma-separated) `"Boston, New York, Remote"`

Example:

``` bash
swelist --location Toronto
swelist --location "Boston, New York, Remote"
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
-   Location (string)
-   Link (URL)

Example:

    Company: Example Corp
    Title: Software Engineer Intern
    Location: Remote
    Link: https://example.com/apply

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
