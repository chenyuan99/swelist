import json
import time
import urllib.request
from datetime import datetime
import typer
from typing import Optional, Annotated
from rich import print
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

__version__ = "0.1.7"

# @app.command()
def version_callback():
    print(f"Awesome CLI Version: {__version__}")
    raise typer.Exit()

def main(
    version: Annotated[
        Optional[bool], typer.Option("--version", callback=version_callback)
    ] = None,
):
    pass


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
    
    print("[bold]Welcome to swelist.com[/bold]")
    print(f"Last updated: {current_time}")
    print(f"Found {internship_count} tech internships from 2025Summer-Internships")
    print(f"Found {newgrad_count} new-grad tech jobs from New-Grad-Positions")
    print("Sign-up below to receive updates when new internships/jobs are added")

@app.command()
def run(role="internship", timeframe="lastday"):
    """A CLI tool for job seekers to find internships and new-grad positions"""
    print_welcome_message()
    
    if role == "internship":
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
    
    if timeframe == "lastweek":
        time_threshold = 60 * 60 * 24 * 7  # 7 days in seconds
    elif timeframe == "lastmonth":
        time_threshold = 60 * 60 * 24 * 30  # 30 days in seconds

    
    recent_postings = [x for x in data if abs(x['date_posted']-current_time) < time_threshold]
    
    if not recent_postings:
        print(f"No new postings in {timeframe}")
        return
    
    print(f"\nFound {len(recent_postings)} postings in {timeframe}")
    
    for posting in recent_postings:
        print(f"\nCompany: {posting['company_name']}")
        print(f"Title: {posting['title']}")
        if posting.get('location'):
            print(f"Location: {posting['location']}")
        if posting.get('locations'):
            print(f"locations: {posting['locations']}")
        print(f"Link: {posting['url']}")


if __name__ == "__main__":
    app()