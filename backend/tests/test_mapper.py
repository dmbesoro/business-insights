import pytest

from app.models.report import ReportType
from app.processing.mapper import (
    MappingError,
    map_columns,
)


def test_map_financial_columns():
    columns = [
        "Transaction Date",
        "Expense Category",
        "Sales Amount",
        "Cost",
    ]

    result = map_columns(columns, ReportType.FINANCIAL)

    assert result == {
        "date": "Transaction Date",
        "category": "Expense Category",
        "revenue": "Sales Amount",
        "expenses": "Cost",
    }


def test_map_financial_columns_with_standard_names():
    columns = ["Date", "Category", "Revenue", "Expenses"]

    result = map_columns(columns, ReportType.FINANCIAL)

    assert result["date"] == "Date"
    assert result["revenue"] == "Revenue"


def test_map_financial_columns_with_missing_required_column():
    columns = ["Date", "Category", "Revenue"]

    with pytest.raises(MappingError, match="Missing required columns"):
        map_columns(columns, ReportType.FINANCIAL)


def test_map_financial_columns_with_reordered_columns():
    columns = ["Expenses", "Revenue", "Category", "Date"]

    result = map_columns(columns, ReportType.FINANCIAL)

    assert result["date"] == "Date"
    assert result["expenses"] == "Expenses"


def test_map_attendance_columns():
    columns = [
        "Employee ID",
        "Attendance Date",
        "Attendance Status",
        "Time In",
        "Time Out",
    ]

    result = map_columns(columns, ReportType.ATTENDANCE)

    assert result == {
        "employee": "Employee ID",
        "date": "Attendance Date",
        "attendance_status": "Attendance Status",
        "check_in": "Time In",
        "check_out": "Time Out",
    }


def test_map_attendance_without_check_in_and_check_out():
    columns = [
        "Employee Name",
        "Work Date",
        "Status",
    ]

    result = map_columns(columns, ReportType.ATTENDANCE)

    assert result == {
        "employee": "Employee Name",
        "date": "Work Date",
        "attendance_status": "Status",
    }


def test_map_attendance_missing_required_column():
    columns = [
        "Employee ID",
        "Attendance Date",
    ]

    with pytest.raises(MappingError, match="Missing required columns"):
        map_columns(columns, ReportType.ATTENDANCE)
