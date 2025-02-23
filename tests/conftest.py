import pytest
import json
import time
from datetime import datetime, timedelta

@pytest.fixture
def mock_internship_data():
    current_time = time.time()
    return [
        {
            "company_name": "Test Company 1",
            "title": "Software Engineering Intern",
            "location": "New York, NY",
            "url": "https://example.com/job1",
            "date_posted": current_time - 3600  # 1 hour ago
        },
        {
            "company_name": "Test Company 2",
            "title": "Data Science Intern",
            "locations": ["Remote", "San Francisco, CA"],
            "url": "https://example.com/job2",
            "date_posted": current_time - (5 * 24 * 3600)  # 5 days ago
        }
    ]

@pytest.fixture
def mock_newgrad_data():
    current_time = time.time()
    return [
        {
            "company_name": "Test Company 3",
            "title": "Software Engineer",
            "location": "Seattle, WA",
            "url": "https://example.com/job3",
            "date_posted": current_time - 3600  # 1 hour ago
        },
        {
            "company_name": "Test Company 4",
            "title": "Full Stack Engineer",
            "locations": ["Austin, TX", "Remote"],
            "url": "https://example.com/job4",
            "date_posted": current_time - (25 * 24 * 3600)  # 25 days ago
        }
    ]
