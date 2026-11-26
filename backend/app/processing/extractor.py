
from pathlib import Path
import csv
import io
from dataclasses import dataclass

from datetime import date, datetime
from io import BytesIO

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException


class ExtractionError(Exception):
    """Raised when a file cannot be extracted into tabular data."""


class RejectedReportError(Exception):
    """Raised when a readable report does not contain usable data."""


@dataclass
class ExtractionResult:
    columns: list[str]
    rows: list[dict[str, str]]
    encoding: str


def make_unique_headers(headers: list[str]) -> list[str]:
    """
    Remove surrounding whitespace and make duplicate or blank
    column names unique.
    """
    result = []
    used = set()

    for index, header in enumerate(headers, start=1):
        name = header.strip() or f"column_{index}"

        candidate = name
        suffix = 2

        while candidate in used:
            candidate = f"{name}_{suffix}"
            suffix += 1

        result.append(candidate)
        used.add(candidate)

    return result


def extract_csv(file_bytes: bytes) -> ExtractionResult:
    if not file_bytes:
        raise ExtractionError("The uploaded CSV file is empty")

    # Try common encodings in order.
    decoded_text = None
    detected_encoding = None

    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            decoded_text = file_bytes.decode(encoding)
            detected_encoding = encoding
            break
        except UnicodeDecodeError:
            continue

    if decoded_text is None:
        raise ExtractionError("Could not decode CSV file")

    try:
        sample = decoded_text[:8192]

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=",;\t|",
            )
        except csv.Error:
            dialect = csv.excel

        reader = csv.reader(
            io.StringIO(decoded_text, newline=""),
            dialect,
        )

        raw_rows = list(reader)

    except csv.Error as exc:
        raise ExtractionError(f"Invalid CSV structure: {exc}") from exc

    if not raw_rows:
        raise ExtractionError("CSV file contains no rows")

    # The first row contains the column headers.
    raw_headers = [str(value).strip() for value in raw_rows[0]]

    if not raw_headers or all(not value for value in raw_headers):
        raise ExtractionError("CSV file does not contain valid headers")

    # Ignore completely blank data rows.
    data_rows = [
        [str(value).strip() for value in row]
        for row in raw_rows[1:]
        if any(str(value).strip() for value in row)
    ]

    if not data_rows:
        raise RejectedReportError(
            "CSV file contains headers but no data rows"
        )

    # Account for data rows containing more fields than the header.
    max_columns = max(
        len(raw_headers),
        max(len(row) for row in data_rows),
    )

    while len(raw_headers) < max_columns:
        raw_headers.append("")

    headers = make_unique_headers(raw_headers)

    # Convert each row into a dictionary.
    records = []

    for row in data_rows:
        row = row + [""] * (max_columns - len(row))

        record = {
            headers[index]: value
            for index, value in enumerate(row)
        }

        records.append(record)

    return ExtractionResult(
        columns=headers,
        rows=records,
        encoding=detected_encoding,
    )


def _cell_to_string(value) -> str:
    """Convert an Excel cell value into a consistent string."""
    if value is None:
        return ""

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    return str(value)


def extract_xlsx(file_bytes: bytes) -> ExtractionResult:
    if not file_bytes:
        raise ExtractionError("The uploaded XLSX file is empty")

    try:
        workbook = load_workbook(
            BytesIO(file_bytes),
            read_only=True,
            data_only=True,
        )
    except Exception as exc:
        raise ExtractionError(
            f"Could not read XLSX file: {exc}"
        ) from exc

    try:
        if not workbook.worksheets:
            raise ExtractionError("XLSX file contains no worksheets")

        worksheet = workbook.worksheets[0]

        raw_rows = list(worksheet.iter_rows(values_only=True))

        if not raw_rows:
            raise ExtractionError("XLSX file contains no rows")

        raw_headers = [
            _cell_to_string(value).strip()
            for value in raw_rows[0]
        ]

        if not raw_headers or all(not value for value in raw_headers):
            raise ExtractionError("XLSX file does not contain valid headers")

        data_rows = [
            [_cell_to_string(value).strip() for value in row]
            for row in raw_rows[1:]
            if any(value is not None and str(value).strip() for value in row)
        ]

        if not data_rows:
            raise RejectedReportError(
                "XLSX file contains headers but no data rows"
            )

        max_columns = max(
            len(raw_headers),
            max(len(row) for row in data_rows),
        )

        while len(raw_headers) < max_columns:
            raw_headers.append("")

        headers = make_unique_headers(raw_headers)

        records = []

        for row in data_rows:
            row = row + [""] * (max_columns - len(row))

            record = {
                headers[index]: value
                for index, value in enumerate(row)
            }

            records.append(record)

        return ExtractionResult(
            columns=headers,
            rows=records,
            encoding="xlsx",
        )

    finally:
        workbook.close()


def extract_file(file_bytes: bytes, filename: str) -> ExtractionResult:
    """
    Select the appropriate extractor based on the file extension.
    """
    extension = Path(filename).suffix.lower()

    if extension == ".csv":
        return extract_csv(file_bytes)

    if extension == ".xlsx":
        return extract_xlsx(file_bytes)

    raise ExtractionError(
        f"Unsupported file format: {extension or 'unknown'}"
    )