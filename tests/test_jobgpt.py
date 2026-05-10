import pytest
from typer.testing import CliRunner
from unittest.mock import MagicMock, patch
from swelist.main import app

runner = CliRunner()


def _make_openai_mock(reply="Mocked AI response."):
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=reply))]
    )
    mock_ctor = MagicMock(return_value=mock_client)
    return mock_ctor, mock_client


def test_why_company_basic(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, client = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(app, ["jobgpt", "why-company", "Stripe"])
    assert result.exit_code == 0, result.output
    assert "Mocked AI response." in result.output


def test_why_company_with_background(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, client = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(app, ["jobgpt", "why-company", "Stripe", "--background", "5yr data eng"])
    assert result.exit_code == 0, result.output
    call_args = client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "5yr data eng" in user_msg


def test_behavioral_basic(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, _ = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(app, ["jobgpt", "behavioral", "Tell me about a conflict"])
    assert result.exit_code == 0, result.output
    assert "Mocked AI response." in result.output


def test_behavioral_with_resume(monkeypatch, tmp_path):
    resume = tmp_path / "resume.txt"
    resume.write_text("Senior engineer at AWS for 5 years.")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, client = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(
            app,
            ["jobgpt", "behavioral", "Tell me about a time you led a project", "--resume", str(resume)],
        )
    assert result.exit_code == 0, result.output
    call_args = client.chat.completions.create.call_args
    user_msg = call_args.kwargs["messages"][1]["content"]
    assert "Senior engineer at AWS" in user_msg


def test_behavioral_missing_resume(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    result = runner.invoke(app, ["jobgpt", "behavioral", "Question", "--resume", "/nonexistent/resume.txt"])
    assert result.exit_code != 0


def test_ask_basic(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, _ = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(app, ["jobgpt", "ask", "What salary should I negotiate?"])
    assert result.exit_code == 0, result.output
    assert "Mocked AI response." in result.output


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock_ctor, _ = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        result = runner.invoke(app, ["jobgpt", "ask", "Question"])
    assert result.exit_code != 0


def test_missing_openai_package(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    import sys
    with patch.dict(sys.modules, {"openai": None}):
        result = runner.invoke(app, ["jobgpt", "ask", "Question"])
    assert result.exit_code != 0


def test_system_prompt_used(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_ctor, client = _make_openai_mock()
    with patch("openai.OpenAI", mock_ctor):
        runner.invoke(app, ["jobgpt", "why-company", "Google"])
    call_args = client.chat.completions.create.call_args
    system_msg = call_args.kwargs["messages"][0]["content"]
    assert "career coach" in system_msg.lower()
