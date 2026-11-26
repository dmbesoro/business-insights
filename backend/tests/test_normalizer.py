from datetime import date
from decimal import Decimal

import pytest

from app.processing.normalizer import (
    normalize_number,
    normalize_date,
    normalize_status,
)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("$50,000.00", Decimal("50000.00")),
        ("12,500", Decimal("12500")),
        ("₱1,250.50", Decimal("1250.50")),
        ("(1,200.00)", Decimal("-1200.00")),
        ("95%", Decimal("95")),
        ("", None),
    ],
)
def test_normalize_number(value, expected):
    assert normalize_number(value) == expected


def test_normalize_number_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid numeric value"):
        normalize_number("not-a-number")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("2026-11-01", date(2026, 11, 1)),
        ("11/01/2026", date(2026, 11, 1)),
        ("Nov 1, 2026", date(2026, 11, 1)),
        ("2026/11/01", date(2026, 11, 1)),
        ("", None),
    ],
)
def test_normalize_date(value, expected):
    assert normalize_date(value) == expected


def test_normalize_date_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid date value"):
        normalize_date("not-a-date")


@pytest.mark.parametrize(
    "value, expected",
    [
        ("In Progress", "IN_PROGRESS"),
        ("Completed", "COMPLETED"),
        ("Not Started", "NOT_STARTED"),
        ("Present", "PRESENT"),
        ("", None),
    ],
)
def test_normalize_status(value, expected):
    assert normalize_status(value) == expected