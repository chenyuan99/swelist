import os, subprocess, json

from keyring.core import load_env
from openai import OpenAI

from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

SKILLS_PATH = "skills.md"

def run_cmd(cmd: str) -> str:
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "Command failed")
    return p.stdout

skills = open(SKILLS_PATH, "r", encoding="utf-8").read()

goal = "List internship postings from lastday and return JSON array with company,title,location,link."

prompt = f"""
You are an automation agent. Use ONLY the contract in the skills.md.
Decide the exact shell command to run.
Then describe how to parse its stdout into JSON objects with keys:
company,title,location,link.

Return STRICT JSON with:
{{
  "command": "...",
  "parse_rules": ["...","..."]
}}
SKILLS_MD:
{skills}
"""

resp = client.responses.create(
    model="gpt-4.1-mini",
    input=prompt
)

plan = json.loads(resp.output_text)
print("PLAN:", plan)

out = run_cmd(plan["command"])
print("RAW OUTPUT:\n", out[:1500])

# Super simple parser for the example format
jobs = []
cur = {}
for line in out.splitlines():
    line = line.strip()
    if line.startswith("Company:"):
        if cur:
            jobs.append(cur); cur = {}
        cur["company"] = line.split("Company:",1)[1].strip()
    elif line.startswith("Title:"):
        cur["title"] = line.split("Title:",1)[1].strip()
    elif line.startswith("locations:") or line.startswith("Location:"):
        # Handle both 'locations:' (list format) and 'Location:' (string format)
        value = line.split(":",1)[1].strip()
        if value.startswith("[") and value.endswith("]"):
            # Parse list format: ['City, State']
            import ast
            try:
                locations = ast.literal_eval(value)
                cur["location"] = locations[0] if locations else ""
            except ValueError:
                cur["location"] = value
        else:
            cur["location"] = value
    elif line.startswith("Link:"):
        cur["link"] = line.split("Link:",1)[1].strip()
if cur:
    jobs.append(cur)

print("\nPARSED JSON (first 5):")
print(json.dumps(jobs[:5], indent=2))