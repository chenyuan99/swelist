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
def callback():
    """
    A CLI tool for job seekers to find internships and new-grad positions
    """
    print_welcome_message()

@app.command()
def main(role: Role = typer.Option(..., prompt="Are you looking for an internship or a new-grad role?")):
    """Search for internships or new-grad positions"""
    if role == Role.internship:
        internship_url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(internship_url)
        data = json.load(response)
    else:
        newgrad_url = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/refs/heads/dev/.github/scripts/listings.json"
        response = urllib.request.urlopen(newgrad_url)
        data = json.load(response)
    
    # Filter for recent postings (last 24 hours)
    current_time = time.time()
    recent_postings = [x for x in data if abs(x['date_posted']-current_time) < (60 * 60 * 24)]
    
    if not recent_postings:
        typer.echo("No new postings in the last 24 hours.")
        return
    
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

@app.command()
def job():
    internship_url = "https://raw.githubusercontent.com/SimplifyJobs/Summer2025-Internships/refs/heads/dev/.github/scripts/listings.json"
    response = urllib.request.urlopen(internship_url)
    internship_data = json.load(response)
    # Filter python objects with list comprehensions
    current_time = time.time()
    output_dict = [x for x in internship_data if abs(x['date_posted']-current_time) < (60 * 60 * 24)]
    print(output_dict)

if __name__ == "__main__":
    app()