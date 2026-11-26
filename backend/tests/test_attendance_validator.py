
from datetime import date

from app.processing.validator import (
    validate_attendance_rows,
)


MAPPING = {
    "employee": "Employee ID",
    "date": "Attendance Date",
    "attendance_status": "Status",
    "check_in": "Time In",
    "check_out": "Time Out",
}


def test_valid_attendance_row():
    rows = [
        {
            "Employee ID": "EMP001",
            "Attendance Date": "2026-11-01",
            "Status": "Present",
            "Time In": "09:00",
            "Time Out": "18:00",
        }
    ]

    results = validate_attendance_rows(rows, MAPPING)

    assert results[0].is_valid is True
    assert results[0].data["employee"] == "EMP001"
    assert results[0].data["date"] == date(2026, 11, 1)
    assert results[0].data["attendance_status"] == "PRESENT"


def test_absent_employee_without_working_hours_is_valid():
    rows = [
        {
            "Employee ID": "EMP002",
            "Attendance Date": "2026-11-01",
            "Status": "Absent",
            "Time In": "",
            "Time Out": "",
        }
    ]

    results = validate_attendance_rows(rows, MAPPING)

    assert results[0].is_valid is True
    assert results[0].data["attendance_status"] == "ABSENT"


def test_invalid_attendance_status_rejects_row():
    rows = [
        {
            "Employee ID": "EMP001",
            "Attendance Date": "2026-11-01",
            "Status": "Unknown",
            "Time In": "",
            "Time Out": "",
        }
    ]

    results = validate_attendance_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert any(
        "Invalid attendance status" in error
        for error in results[0].errors
    )


def test_invalid_attendance_date_rejects_only_that_row():
    rows = [
        {
            "Employee ID": "EMP001",
            "Attendance Date": "bad-date",
            "Status": "Present",
            "Time In": "09:00",
            "Time Out": "18:00",
        },
        {
            "Employee ID": "EMP002",
            "Attendance Date": "2026-11-02",
            "Status": "Present",
            "Time In": "09:00",
            "Time Out": "18:00",
        },
    ]

    results = validate_attendance_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert results[1].is_valid is True


def test_missing_employee_rejects_row():
    rows = [
        {
            "Employee ID": "",
            "Attendance Date": "2026-11-01",
            "Status": "Present",
            "Time In": "09:00",
            "Time Out": "18:00",
        }
    ]

    results = validate_attendance_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert "Employee is required" in results[0].errors
