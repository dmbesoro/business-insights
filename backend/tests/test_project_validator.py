
from datetime import date
from decimal import Decimal

from app.processing.validator import validate_project_rows


MAPPING = {
    "project": "Project Name",
    "task": "Task Name",
    "status": "Status",
    "progress": "Progress",
    "due_date": "Due Date",
}


def test_valid_project_row():
    rows = [
        {
            "Project Name": "Website Revamp",
            "Task Name": "UI Design",
            "Status": "Completed",
            "Progress": "100%",
            "Due Date": "2026-11-20",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is True
    assert results[0].data["project"] == "Website Revamp"
    assert results[0].data["status"] == "COMPLETED"
    assert results[0].data["progress"] == Decimal("100")
    assert results[0].data["due_date"] == date(2026, 11, 20)


def test_progress_below_zero_is_invalid():
    rows = [
        {
            "Project Name": "Website Revamp",
            "Task Name": "UI Design",
            "Status": "In Progress",
            "Progress": "-5",
            "Due Date": "2026-11-20",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert "Progress must be between 0 and 100" in results[0].errors


def test_progress_above_100_is_invalid():
    rows = [
        {
            "Project Name": "Website Revamp",
            "Task Name": "UI Design",
            "Status": "In Progress",
            "Progress": "150",
            "Due Date": "2026-11-20",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is False


def test_invalid_project_status_is_rejected():
    rows = [
        {
            "Project Name": "Website Revamp",
            "Task Name": "UI Design",
            "Status": "Unknown",
            "Progress": "50",
            "Due Date": "2026-11-20",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert any("Invalid project status" in error for error in results[0].errors)


def test_missing_project_rejects_row():
    rows = [
        {
            "Project Name": "",
            "Task Name": "UI Design",
            "Status": "In Progress",
            "Progress": "50",
            "Due Date": "2026-11-20",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert "Project is required" in results[0].errors


def test_invalid_due_date_rejects_row():
    rows = [
        {
            "Project Name": "Website Revamp",
            "Task Name": "UI Design",
            "Status": "In Progress",
            "Progress": "50",
            "Due Date": "invalid-date",
        }
    ]

    results = validate_project_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert any("Invalid date" in error for error in results[0].errors)
