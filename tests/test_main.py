import pytest
from typer.testing import CliRunner
from swelist.main import app, get_internship_count, get_newgrad_count
from unittest.mock import patch
import json
import urllib.request
import time

runner = CliRunner()

def test_get_internship_count(mocker, mock_internship_data):
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_internship_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    count = get_internship_count()
    assert count == 2

def test_get_newgrad_count(mocker, mock_newgrad_data):
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_newgrad_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    count = get_newgrad_count()
    assert count == 2

def test_run_internship_default(mocker, mock_internship_data):
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_internship_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    result = runner.invoke(app, ['run'])
    assert result.exit_code == 0
    assert "Test Company 1" in result.stdout
    assert "Test Company 2" not in result.stdout  # Should not show 7-day old posting in default view

def test_run_newgrad_lastmonth(mocker, mock_newgrad_data):
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_newgrad_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    result = runner.invoke(app, ['run', '--role', 'newgrad', '--timeframe', 'lastmonth'])
    assert result.exit_code == 0
    assert "Test Company 3" in result.stdout
    assert "Test Company 4" in result.stdout

def test_run_internship_lastweek(mocker, mock_internship_data):
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_internship_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    result = runner.invoke(app, ['run', '--timeframe', 'lastweek'])
    assert result.exit_code == 0
    assert "Test Company 1" in result.stdout
    assert "Test Company 2" in result.stdout

def test_api_error(mocker):
    mocker.patch('urllib.request.urlopen', side_effect=urllib.error.URLError("Test error"))
    
    count = get_internship_count()
    assert count == 0  # Should handle error gracefully


def test_run_with_locations(mocker):
    mock_data = [{
        "company_name": "Test Company",
        "title": "Software Engineer",
        "locations": ["New York, NY", "Remote"],
        "url": "https://example.com/job",
        "date_posted": time.time() - 3600
    }]
    mock_response = mocker.Mock()
    mock_response.read.return_value = json.dumps(mock_data).encode()
    mocker.patch('urllib.request.urlopen', return_value=mock_response)
    
    result = runner.invoke(app, ['run'])
    assert result.exit_code == 0
    assert "locations: ['New York, NY', 'Remote']" in result.stdout
