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

# Function to filter by location
def filter_by_location(postings, location):
    """Filter job postings by location."""
    if location.lower() == "all":
        return postings

    filtered = []
    # Split input by comma, strip whitespace, lowercase
    user_locations = [loc.strip().lower() for loc in location.split(",")]

    for job in postings:
        job_locations = [job_location.lower() for job_location in job.get("locations", [])]

        user_locations = [loc.strip().lower() for loc in location.split(",")]
        filtered = []

    for job in postings:
        job_locations = [l.lower() for l in job.get("locations", [])]

        for user_loc in user_locations:
            for loc_norm in job_locations:
                if len(user_loc) == 2:  # treat as state code
                    if loc_norm.endswith(user_loc):
                        filtered.append(job)
                        break  # no need to check other job locations
                else:  # city or country
                    if user_loc in loc_norm:
                        filtered.append(job)
                        break
            else:
                continue
            break  # job already matched one of the user locations

    return filtered

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
def run(role="internship", timeframe="lastday", location="all"):
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

    # Filter by locations
    location_based_postings = filter_by_location(recent_postings, location)
    
    if not location_based_postings:
        if location.lower() == "all":
            # No jobs in the selected timeframe at all
            print(f"No postings found in {timeframe}")
        else:
            # No jobs matched both location & timeframe
            print(f"No postings found for location '{location}' in {timeframe}")
        return

    print(f"\nFound {len(location_based_postings)} postings for location '{location}' in {timeframe}")

    for posting in location_based_postings:
        print(f"\nCompany: {posting['company_name']}")
        print(f"Title: {posting['title']}")
        if posting.get('location'):
            print(f"Location: {posting['location']}")
        if posting.get('locations'):
            print(f"locations: {posting['locations']}")
        print(f"Link: {posting['url']}")


if __name__ == "__main__":
    app()