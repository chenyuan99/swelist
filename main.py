import json
import time
import urllib.request
from datetime import datetime, timedelta

import typer

app = typer.Typer()


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

def main:



if __name__ == "__main__":
    app()