"""Self-contained HTML profile generator.

Reads profile.md and renders a professional profile page as a single offline-friendly
`.html` file with personal info, career profile, resume, and integrations.
"""

import os
from datetime import date
from html import escape
from pathlib import Path
from typing import Optional


def parse_profile_md(profile_path: str) -> dict:
    """Parse profile.md and extract sections into a structured dict."""
    if not os.path.exists(profile_path):
        return {
            "personal": {},
            "career": {},
            "resume": "",
            "integrations": {},
        }

    with open(profile_path, "r", encoding="utf-8") as f:
        content = f.read()

    result = {
        "personal": {},
        "career": {},
        "resume": "",
        "integrations": {},
    }

    # Extract Personal Info section
    if "## Personal Info" in content:
        start = content.find("## Personal Info")
        end = content.find("---", start)
        section = content[start:end]
        result["personal"] = _parse_key_value(section)

    # Extract Career Profile section
    if "## Career Profile" in content:
        start = content.find("## Career Profile")
        end = content.find("---", start)
        section = content[start:end]
        result["career"] = _parse_key_value(section)

    # Extract Resume section
    if "## Resume" in content:
        start = content.find("## Resume")
        # Get everything after the code fence markers
        code_start = content.find("```", start)
        if code_start != -1:
            code_end = content.find("```", code_start + 3)
            if code_end != -1:
                result["resume"] = content[code_start + 3 : code_end].strip()

    # Extract Integrations section
    if "## Integrations" in content:
        start = content.find("## Integrations")
        end = content.find("## Skill Config", start)
        if end == -1:
            end = content.find("## How to Update", start)
        if end == -1:
            end = len(content)
        section = content[start:end]
        result["integrations"] = _parse_key_value(section)

    return result


def _parse_key_value(section: str) -> dict:
    """Parse markdown key-value pairs from a section."""
    result = {}
    for line in section.split("\n"):
        line = line.strip()
        if line.startswith("- **"):
            # Format: - **Key:** Value
            parts = line.split(":**", 1)
            if len(parts) == 2:
                key = parts[0].replace("- **", "").strip()
                value = parts[1].strip()
                result[key] = value
    return result


def _e(value: Optional[str]) -> str:
    """HTML escape, return em-dash for empty."""
    if not value or not value.strip():
        return "—"
    return escape(value.strip())


def render_html(profile: dict) -> str:
    """Render profile data as self-contained HTML."""
    generated = date.today().isoformat()

    personal = profile.get("personal", {})
    career = profile.get("career", {})
    resume = profile.get("resume", "")
    integrations = profile.get("integrations", {})

    # Build personal info section
    personal_html = ""
    if personal:
        rows = []
        for key, value in personal.items():
            if value and value != "—":
                url = ""
                if key.lower() == "linkedin url" and value.startswith("http"):
                    url = f' <a href="{escape(value)}" target="_blank">View</a>'
                rows.append(
                    f'<tr><td class="label">{escape(key)}</td><td>{_e(value)}{url}</td></tr>'
                )
        if rows:
            personal_html = (
                '<section class="card"><h2>Personal Info</h2>'
                '<table class="info-table">' + "".join(rows) + '</table></section>'
            )

    # Build career profile section
    career_html = ""
    if career:
        rows = []
        for key, value in career.items():
            if value and value != "—":
                rows.append(
                    f'<tr><td class="label">{escape(key)}</td><td>{_e(value)}</td></tr>'
                )
        if rows:
            career_html = (
                '<section class="card"><h2>Career Profile</h2>'
                '<table class="info-table">' + "".join(rows) + '</table></section>'
            )

    # Build resume section
    resume_html = ""
    if resume:
        resume_preview = resume[:500] + ("..." if len(resume) > 500 else "")
        resume_html = f'''<section class="card">
<h2>Resume</h2>
<pre class="resume-text">{escape(resume_preview)}</pre>
<p class="note">Showing first 500 characters. Full resume available in profile.md</p>
</section>'''

    # Build integrations section
    integrations_html = ""
    if integrations:
        rows = []
        for key, value in integrations.items():
            if value and value != "—":
                rows.append(
                    f'<tr><td class="label">{escape(key)}</td><td>{_e(value)}</td></tr>'
                )
        if rows:
            integrations_html = (
                '<section class="card"><h2>Integrations</h2>'
                '<table class="info-table">' + "".join(rows) + '</table></section>'
            )

    body_content = (
        personal_html + career_html + resume_html + integrations_html
    )

    if not body_content.strip():
        body_content = '<p class="empty">No profile data found. Edit profile.md to add your information.</p>'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Career Profile</title>
<style>
  :root {{
    --bg: #f8fafc; --card: #ffffff; --text: #0f172a; --muted: #64748b; --border: #e2e8f0;
    --accent: #3b82f6;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); margin: 0; padding: 24px;
  }}
  .container {{ max-width: 900px; margin: 0 auto; }}
  header {{ margin-bottom: 32px; }}
  header h1 {{ font-size: 2rem; margin: 0 0 8px; }}
  header .subtitle {{ color: var(--muted); font-size: .9rem; }}
  .card {{
    background: var(--card); border-radius: 10px; padding: 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,.08); margin-bottom: 20px;
  }}
  .card h2 {{ margin: 0 0 16px; font-size: 1.2rem; border-bottom: 2px solid var(--accent); padding-bottom: 8px; }}
  .info-table {{ width: 100%; border-collapse: collapse; }}
  .info-table td {{ padding: 10px 0; border-bottom: 1px solid var(--border); }}
  .info-table .label {{ font-weight: 600; width: 200px; color: var(--accent); vertical-align: top; }}
  .info-table a {{ color: var(--accent); text-decoration: none; }}
  .info-table a:hover {{ text-decoration: underline; }}
  .resume-text {{
    background: #f1f5f9; padding: 16px; border-radius: 6px; border-left: 4px solid var(--accent);
    font-size: .875rem; line-height: 1.5; overflow-x: auto;
  }}
  .note {{ color: var(--muted); font-size: .85rem; margin: 12px 0 0; }}
  .empty {{ color: var(--muted); padding: 40px 20px; text-align: center; font-size: .95rem; }}
  footer {{ margin-top: 40px; color: var(--muted); font-size: .8rem; text-align: center; }}
</style>
</head>
<body>
<div class="container">
<header>
  <h1>📋 Career Profile</h1>
  <div class="subtitle">Generated: {generated}</div>
</header>
{body_content}
<footer>Generated by swelist &middot; {generated}</footer>
</div>
</body>
</html>
"""


def build_profile_report(profile_path: str, output_path: str) -> dict:
    """Generate the profile HTML and write it to output_path. Returns status."""
    profile = parse_profile_md(profile_path)
    html = render_html(profile)

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return {"generated": output_path, "profile": profile}
