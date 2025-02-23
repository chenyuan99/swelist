import json
import time
import urllib.request
from datetime import datetime
import typer
from typing import Optional
from enum import Enum
import ssl

ssl._create_default_https_context = ssl._create_stdlib_context

class Role(str, Enum):
    internship = "internship"
    newgrad = "newgrad"

class TimeFilter(str, Enum):
    lastday = "lastday"
    lastweek = "lastweek"
    lastmonth = "lastmonth"

app = typer.Typer()

def get_internship_count():
    try:
        internship_url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(internship_url)
        internship_data = json.load(response)
        return len(internship_data)
    except:
        return 0

def get_newgrad_count():
    try:
        newgrad_url = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(newgrad_url)
        newgrad_data = json.load(response)
        return len(newgrad_data)
    except:
        return 0

def print_welcome_message():
    current_time = datetime.now().strftime("%c")
    internship_count = get_internship_count()
    newgrad_count = get_newgrad_count()
    
    typer.echo("Welcome to swelist.com")
    typer.echo(f"Last updated: {current_time}")
    typer.echo(f"Found {internship_count} tech internships from 2025Summer-Internships")
    typer.echo(f"Found {newgrad_count} new-grad tech jobs from New-Grad-Positions")
    typer.echo("Sign-up below to receive updates when new internships/jobs are added")


@app.callback()
def main(
    role: Role = typer.Option(..., prompt="Are you looking for an internship or a new-grad role?"),
    timeframe: TimeFilter = typer.Option(
        TimeFilter.lastday,
        "--timeframe",
        "-t",
        help="Show postings from last day, week, or month"
    )
):
    """Search for internships or new-grad positions"""
    if role == Role.internship:
        internship_url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(internship_url)
        data = json.load(response)
    else:
        newgrad_url = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(newgrad_url)
        data = json.load(response)
    
    # Filter for recent postings based on timeframe
    current_time = time.time()
    time_threshold = 60 * 60 * 24  # 24 hours in seconds
    
    if timeframe == TimeFilter.lastweek:
        time_threshold = 60 * 60 * 24 * 7  # 7 days in seconds
    elif timeframe == TimeFilter.lastmonth:
        time_threshold = 60 * 60 * 24 * 30  # 30 days in seconds
    
    recent_postings = [x for x in data if abs(x['date_posted']-current_time) < time_threshold]
    
    if not recent_postings:
        typer.echo(f"No new postings in the last {'month' if timeframe == TimeFilter.lastmonth else 'week' if timeframe == TimeFilter.lastweek else 'day'}.")
        return
    
    typer.echo(f"\nFound {len(recent_postings)} postings in the last {'month' if timeframe == TimeFilter.lastmonth else 'week' if timeframe == TimeFilter.lastweek else 'day'}:")
    
    for posting in recent_postings:
        typer.echo(f"\nCompany: {posting['company_name']}")
        typer.echo(f"Title: {posting['title']}")
        if posting.get('location'):
            typer.echo(f"Location: {posting['location']}")
        if posting.get('locations'):
            typer.echo(f"locations: {posting['locations']}")
        typer.echo(f"Link: {posting['url']}")

@app.command()
def hello(name: str):
    print(f"Hello {name}")

@app.command()
def goodbye(name: str, formal: bool = False):
    if formal:
        print(f"Goodbye Ms. {name}. Have a good day.")
    else:
        print(f"Bye {name}!")


if __name__ == "__main__":
    app()