import pytest

from app.models.report import ReportType
from app.processing.classifier import (
    ClassificationError,
    classify_report,
)


def test_classifies_financial_report():
    columns = ["Date", "Category", "Revenue", "Expenses"]

    assert classify_report(columns) == ReportType.FINANCIAL


def test_classifies_attendance_report():
    columns = [
        "Employee ID",
        "Attendance Date",
        "Attendance Status",
        "Check In",
        "Check Out",
    ]

    assert classify_report(columns) == ReportType.ATTENDANCE


def test_classifies_project_status_report():
    columns = [
        "Project Name",
        "Task Name",
        "Task Status",
        "Progress",
        "Due Date",
    ]

    assert classify_report(columns) == ReportType.PROJECT_STATUS


def test_rejects_unknown_report():
    columns = ["Name", "Description", "Notes"]

    with pytest.raises(ClassificationError, match="could not be determined"):
        classify_report(columns)


def test_rejects_ambiguous_report():
    columns = [
        "Date",
        "Category",
        "Amount",
        "Employee ID",
        "Attendance Status",
    ]

    with pytest.raises(ClassificationError, match="ambiguous"):
        classify_report(columns)


def test_classifies_headers_with_different_formatting():
    columns = [
        " Employee ID ",
        "Attendance-Date",
        "Attendance Status",
        "Check-In",
    ]

    assert classify_report(columns) == ReportType.ATTENDANCE