
from datetime import date
from decimal import Decimal

from app.processing.validator import validate_financial_rows


MAPPING = {
    "date": "Transaction Date",
    "category": "Expense Category",
    "revenue": "Sales Amount",
    "expenses": "Cost",
}


def test_valid_financial_row():
    rows = [
        {
            "Transaction Date": "2026-11-01",
            "Expense Category": "Sales",
            "Sales Amount": "50,000",
            "Cost": "12,000",
        }
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert len(results) == 1
    assert results[0].is_valid is True
    assert results[0].data["date"] == date(2026, 11, 1)
    assert results[0].data["revenue"] == Decimal("50000")
    assert results[0].data["expenses"] == Decimal("12000")


def test_invalid_date_rejects_only_that_row():
    rows = [
        {
            "Transaction Date": "invalid-date",
            "Expense Category": "Sales",
            "Sales Amount": "50000",
            "Cost": "12000",
        },
        {
            "Transaction Date": "2026-11-02",
            "Expense Category": "Services",
            "Sales Amount": "35000",
            "Cost": "8000",
        },
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert any("Invalid date" in error for error in results[0].errors)
    assert results[1].is_valid is True


def test_missing_category_rejects_row():
    rows = [
        {
            "Transaction Date": "2026-11-01",
            "Expense Category": "",
            "Sales Amount": "50000",
            "Cost": "12000",
        }
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert "Category is required" in results[0].errors


def test_invalid_number_rejects_row():
    rows = [
        {
            "Transaction Date": "2026-11-01",
            "Expense Category": "Sales",
            "Sales Amount": "abc",
            "Cost": "12000",
        }
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert any("Invalid numeric value" in error for error in results[0].errors)


def test_missing_numeric_value_rejects_row():
    rows = [
        {
            "Transaction Date": "2026-11-01",
            "Expense Category": "Sales",
            "Sales Amount": "",
            "Cost": "12000",
        }
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert "Revenue is required" in results[0].errors


def test_multiple_invalid_fields_return_multiple_errors():
    rows = [
        {
            "Transaction Date": "bad-date",
            "Expense Category": "",
            "Sales Amount": "abc",
            "Cost": "",
        }
    ]

    results = validate_financial_rows(rows, MAPPING)

    assert results[0].is_valid is False
    assert len(results[0].errors) == 4
