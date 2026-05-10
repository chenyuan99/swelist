import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch, call
from swelist.main import app

runner = CliRunner()

MOCK_REPLY = "Mocked AI response."


def test_why_company_basic():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY) as mock_call:
        result = runner.invoke(app, ["jobgpt", "why-company", "Stripe"])
    assert result.exit_code == 0, result.output
    assert MOCK_REPLY in result.output


def test_why_company_with_background():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY) as mock_call:
        result = runner.invoke(app, ["jobgpt", "why-company", "Stripe", "--background", "5yr data eng"])
    assert result.exit_code == 0, result.output
    _, user, _ = mock_call.call_args.args
    assert "5yr data eng" in user


def test_behavioral_basic():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY):
        result = runner.invoke(app, ["jobgpt", "behavioral", "Tell me about a conflict"])
    assert result.exit_code == 0, result.output
    assert MOCK_REPLY in result.output


def test_behavioral_with_resume(tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("Senior engineer at AWS for 5 years.")
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY) as mock_call:
        result = runner.invoke(
            app,
            ["jobgpt", "behavioral", "Tell me about a time you led a project", "--resume", str(resume)],
        )
    assert result.exit_code == 0, result.output
    _, user, _ = mock_call.call_args.args
    assert "Senior engineer at AWS" in user


def test_behavioral_missing_resume():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY):
        result = runner.invoke(app, ["jobgpt", "behavioral", "Question", "--resume", "/nonexistent/resume.txt"])
    assert result.exit_code != 0


def test_ask_basic():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY):
        result = runner.invoke(app, ["jobgpt", "ask", "What salary should I negotiate?"])
    assert result.exit_code == 0, result.output
    assert MOCK_REPLY in result.output


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import sys
    with patch.dict(sys.modules, {"openai": MagicMock()}):
        result = runner.invoke(app, ["jobgpt", "ask", "Question"])
    assert result.exit_code != 0


def test_missing_openai_package(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    import sys
    with patch.dict(sys.modules, {"openai": None}):
        result = runner.invoke(app, ["jobgpt", "ask", "Question"])
    assert result.exit_code != 0


def test_system_prompt_used():
    with patch("swelist.jobgpt._call_openai", return_value=MOCK_REPLY) as mock_call:
        runner.invoke(app, ["jobgpt", "why-company", "Google"])
    system, _, _ = mock_call.call_args.args
    assert "career coach" in system.lower()
