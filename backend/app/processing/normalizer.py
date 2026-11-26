import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation


def normalize_number(value: str) -> Decimal | None:
    """Convert formatted numeric strings into Decimal values."""
    if value is None or not str(value).strip():
        return None

    cleaned = str(value).strip()

    # Support accounting-style negative numbers: (1,200.50)
    is_negative = cleaned.startswith("(") and cleaned.endswith(")")
    if is_negative:
        cleaned = cleaned[1:-1]

    # Remove common currency symbols, thousands separators and spaces.
    cleaned = re.sub(r"[₱$€£¥,\s]", "", cleaned)
    cleaned = cleaned.replace("%", "")

    try:
        number = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid numeric value: {value}") from exc

    if is_negative:
        number = -number

    return number


def normalize_date(value: str) -> date | None:
    """Convert common date formats into Python date objects."""
    if value is None or not str(value).strip():
        return None

    value = str(value).strip()

    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%d-%b-%Y",
        "%Y-%m-%d %H:%M:%S",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            continue

    # Also accept ISO date-time strings.
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).date()
    except ValueError as exc:
        raise ValueError(f"Invalid date value: {value}") from exc


def normalize_status(value: str) -> str | None:
    """Normalize status text into uppercase snake case."""
    if value is None or not str(value).strip():
        return None

    normalized = re.sub(
        r"[^a-zA-Z0-9]+",
        "_",
        str(value).strip(),
    )

    return normalized.strip("_").upper()