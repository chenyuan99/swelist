import os
import subprocess
from typing import Optional
from typing_extensions import Annotated

import typer
from rich import print
from rich.markdown import Markdown
from rich.panel import Panel

jobgpt_app = typer.Typer(
    name="jobgpt",
    help="AI writing assistant for job applications.",
    no_args_is_help=True,
)

_SYSTEM_PROMPTS = {
    "why_company": (
        "You are an expert career coach helping candidates craft compelling, authentic answers "
        "to the 'Why do you want to work at [Company]?' interview question. "
        "Write in first person. Be specific, enthusiastic, and concise (2-3 paragraphs). "
        "Ground the answer in the candidate's actual background."
    ),
    "behavioral": (
        "You are an expert career coach helping candidates answer behavioral interview questions "
        "using the STAR method (Situation, Task, Action, Result). "
        "Write in first person. Be concrete and quantify results where possible. "
        "Keep the answer under 400 words."
    ),
    "general": (
        "You are an expert career coach and job application strategist. "
        "Provide clear, actionable, and tailored advice."
    ),
}

_USER_TEMPLATES = {
    "why_company": (
        "Company: {company}\n\n"
        "My background: {background}\n\n"
        "Write a compelling answer to 'Why do you want to work at {company}?' "
        "that connects my background to what this company is known for."
    ),
    "behavioral": (
        "Behavioral question: {question}\n\n"
        "{resume_section}"
        "Write a strong STAR-method answer for this question."
    ),
    "general": "{prompt}",
}


def _call_openai(system: str, user: str, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        print(
            "[bold red]Error:[/bold red] openai package not installed. "
            "Run: [cyan]pip install 'swelist[ai]'[/cyan]"
        )
        raise typer.Exit(1)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "[bold red]Error:[/bold red] OPENAI_API_KEY environment variable not set.\n"
            "Export it with: [cyan]export OPENAI_API_KEY=sk-...[/cyan]"
        )
        raise typer.Exit(1)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


def _render(title: str, content: str, copy: bool) -> None:
    print(Panel(Markdown(content), title=f"[bold]{title}[/bold]", border_style="cyan"))
    if copy:
        try:
            proc = subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=content.encode(),
                check=False,
            )
            if proc.returncode != 0:
                subprocess.run(["pbcopy"], input=content.encode(), check=True)
            print("[dim]Copied to clipboard.[/dim]")
        except Exception:
            print("[dim yellow]Could not copy to clipboard (install xclip or pbcopy).[/dim yellow]")


@jobgpt_app.command("why-company")
def why_company(
    company: Annotated[str, typer.Argument(help="Company name")],
    background: Annotated[str, typer.Option(help="Your background summary")] = "",
    model: Annotated[str, typer.Option(help="OpenAI model")] = "gpt-4o",
    copy: Annotated[bool, typer.Option("--copy", help="Copy output to clipboard")] = False,
):
    """Generate a 'Why this company?' answer for interviews."""
    user = _USER_TEMPLATES["why_company"].format(company=company, background=background)
    result = _call_openai(_SYSTEM_PROMPTS["why_company"], user, model)
    _render(f"Why {company}?", result, copy)


@jobgpt_app.command("behavioral")
def behavioral(
    question: Annotated[str, typer.Argument(help="Behavioral interview question")],
    resume: Annotated[Optional[str], typer.Option(help="Path to resume text file")] = None,
    model: Annotated[str, typer.Option(help="OpenAI model")] = "gpt-4o",
    copy: Annotated[bool, typer.Option("--copy", help="Copy output to clipboard")] = False,
):
    """Generate a STAR-format answer to a behavioral interview question."""
    resume_section = ""
    if resume:
        try:
            with open(resume) as f:
                resume_section = f"Resume context:\n{f.read()}\n\n"
        except OSError as e:
            typer.echo(f"Could not read resume file: {e}", err=True)
            raise typer.Exit(1)

    user = _USER_TEMPLATES["behavioral"].format(question=question, resume_section=resume_section)
    result = _call_openai(_SYSTEM_PROMPTS["behavioral"], user, model)
    _render("Behavioral Answer (STAR)", result, copy)


@jobgpt_app.command("ask")
def ask(
    question: Annotated[str, typer.Argument(help="Any job-search or career question")],
    model: Annotated[str, typer.Option(help="OpenAI model")] = "gpt-4o",
    copy: Annotated[bool, typer.Option("--copy", help="Copy output to clipboard")] = False,
):
    """Ask any career or job-search question."""
    user = _USER_TEMPLATES["general"].format(prompt=question)
    result = _call_openai(_SYSTEM_PROMPTS["general"], user, model)
    _render("Career Advice", result, copy)
