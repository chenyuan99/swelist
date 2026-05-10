import os
import subprocess
import json
import ast
import pytest
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()
SKILLS_PATH = "SKILLS.md"


def run_cmd(cmd: str) -> str:
    """Execute shell command and return stdout."""
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "Command failed")
    return p.stdout


def parse_job_postings(output: str) -> list[dict]:
    """Parse swelist job postings into structured JSON."""
    jobs = []
    cur = {}
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Company:"):
            if cur:
                jobs.append(cur)
            cur = {"company": line.split("Company:", 1)[1].strip()}
        elif line.startswith("Title:"):
            cur["title"] = line.split("Title:", 1)[1].strip()
        elif line.startswith("locations:") or line.startswith("Location:"):
            value = line.split(":", 1)[1].strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    locations = ast.literal_eval(value)
                    cur["location"] = locations[0] if locations else ""
                except ValueError:
                    cur["location"] = value
            else:
                cur["location"] = value
        elif line.startswith("Link:"):
            cur["link"] = line.split("Link:", 1)[1].strip()
    if cur:
        jobs.append(cur)
    return jobs


def test_swelist_agent():
    """Test agent can understand swelist contract and generate correct command."""
    skills = open(SKILLS_PATH, "r", encoding="utf-8").read()

    prompt = f"""
You are an automation agent. Use ONLY the contract in the skills.md.
Generate a command to list internship postings from lastday and return JSON array with company,title,location,link.

Return STRICT JSON with:
{{
  "command": "...",
  "parse_rules": ["...","..."]
}}
SKILLS_MD:
{skills}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at reading CLI documentation. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    plan = json.loads(resp.choices[0].message.content)
    assert "command" in plan
    assert "parse_rules" in plan
    assert "swelist" in plan["command"]
    print("✓ Agent generated swelist plan:", plan["command"])


def test_swelist_execution():
    """Test swelist command executes and returns job postings."""
    output = run_cmd("swelist run --role internship --timeframe lastday")
    assert "Company:" in output
    assert "Title:" in output
    assert "Link:" in output
    print("✓ swelist command executed successfully")


def test_swelist_parsing():
    """Test parsing swelist output into structured JSON."""
    output = run_cmd("swelist run --role internship --timeframe lastday")
    jobs = parse_job_postings(output)

    if jobs:  # Only assert if there are postings
        job = jobs[0]
        assert "company" in job
        assert "title" in job
        assert "link" in job
        print(f"✓ Parsed {len(jobs)} job postings with correct structure")
    else:
        print("✓ No postings found (valid result for empty timeframe)")


def test_jobgpt_why_company_agent():
    """Test agent can understand jobgpt why-company contract."""
    skills = open(SKILLS_PATH, "r", encoding="utf-8").read()

    prompt = f"""
You are an automation agent. Use ONLY the contract in the skills.md.
Generate a jobgpt command to create a why-company answer for Google with background:
"Software engineer with Python and web development experience"

Return STRICT JSON with:
{{
  "command": "...",
  "validation": ["...","..."]
}}
SKILLS_MD:
{skills}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at reading CLI documentation. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    plan = json.loads(resp.choices[0].message.content)
    assert "command" in plan
    assert "validation" in plan
    assert "jobgpt" in plan["command"]
    assert "why-company" in plan["command"]
    print("✓ Agent generated jobgpt why-company plan:", plan["command"])


def test_jobgpt_behavioral_agent():
    """Test agent can understand jobgpt behavioral contract."""
    skills = open(SKILLS_PATH, "r", encoding="utf-8").read()

    prompt = f"""
You are an automation agent. Use ONLY the contract in the skills.md.
Generate a jobgpt command to create a STAR-format answer to this behavioral question:
"Tell me about a time you resolved conflict on a team"

Return STRICT JSON with:
{{
  "command": "...",
  "validation": ["...","..."]
}}
SKILLS_MD:
{skills}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at reading CLI documentation. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    plan = json.loads(resp.choices[0].message.content)
    assert "command" in plan
    assert "validation" in plan
    assert "jobgpt" in plan["command"]
    assert "behavioral" in plan["command"]
    print("✓ Agent generated jobgpt behavioral plan:", plan["command"])


def test_jobgpt_ask_agent():
    """Test agent can understand jobgpt ask contract."""
    skills = open(SKILLS_PATH, "r", encoding="utf-8").read()

    prompt = f"""
You are an automation agent. Use ONLY the contract in the skills.md.
Generate a jobgpt command to answer this career question:
"How do I negotiate my internship offer?"

Return STRICT JSON with:
{{
  "command": "...",
  "validation": ["...","..."]
}}
SKILLS_MD:
{skills}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an expert at reading CLI documentation. Return ONLY valid JSON.",
            },
            {"role": "user", "content": prompt},
        ],
    )

    plan = json.loads(resp.choices[0].message.content)
    assert "command" in plan
    assert "validation" in plan
    assert "jobgpt" in plan["command"]
    assert "ask" in plan["command"]
    print("✓ Agent generated jobgpt ask plan:", plan["command"])


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING SWELIST AND JOBGPT AGENT CAPABILITIES")
    print("=" * 60 + "\n")

    print("SWELIST TESTS:")
    print("-" * 60)
    test_swelist_agent()
    test_swelist_execution()
    test_swelist_parsing()

    print("\nJOBGPT TESTS:")
    print("-" * 60)
    test_jobgpt_why_company_agent()
    test_jobgpt_behavioral_agent()
    test_jobgpt_ask_agent()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60 + "\n")