
import pytest

from io import BytesIO

from openpyxl import Workbook

from app.processing.extractor import (
    ExtractionError,
    RejectedReportError,
    extract_csv,
    extract_xlsx,
    extract_file,
)


def test_extract_csv_with_duplicate_headers_and_blank_rows():
    content = (
        b"Date,Amount,Amount,\n"
        b"2026-11-01,100,200,\n"
        b"\n"
        b"2026-11-02,300,400,\n"
    )

    result = extract_csv(content)

    assert result.columns == [
        "Date",
        "Amount",
        "Amount_2",
        "column_4",
    ]

    assert len(result.rows) == 2
    assert result.rows[0]["Amount"] == "100"
    assert result.rows[0]["Amount_2"] == "200"


def test_extract_csv_with_windows_encoding():
    content = (
        "name,comment\n"
        "José,café\n"
    ).encode("cp1252")

    result = extract_csv(content)

    assert result.rows[0]["name"] == "José"
    assert result.rows[0]["comment"] == "café"


def test_extract_csv_rejects_empty_file():
    with pytest.raises(ExtractionError, match="empty"):
        extract_csv(b"")


def test_extract_csv_rejects_header_only_file():
    with pytest.raises(RejectedReportError, match="no data rows"):
        extract_csv(b"Date,Amount\n")


def create_test_xlsx(rows):
    workbook = Workbook()
    worksheet = workbook.active

    for row in rows:
        worksheet.append(row)

    buffer = BytesIO()
    workbook.save(buffer)

    return buffer.getvalue()


def test_extract_xlsx_with_duplicate_headers_and_blank_rows():
    content = create_test_xlsx([
        ["Date", "Amount", "Amount"],
        ["2026-11-01", 100, 200],
        [None, None, None],
        ["2026-11-02", 300, 400],
    ])

    result = extract_xlsx(content)

    assert result.columns == ["Date", "Amount", "Amount_2"]
    assert len(result.rows) == 2
    assert result.rows[0]["Amount"] == "100"
    assert result.rows[0]["Amount_2"] == "200"


def test_extract_xlsx_rejects_empty_file():
    with pytest.raises(ExtractionError, match="empty"):
        extract_xlsx(b"")


def test_extract_xlsx_rejects_corrupt_file():
    with pytest.raises(ExtractionError, match="Could not read XLSX"):
        extract_xlsx(b"this is not a valid Excel file")


def test_extract_xlsx_rejects_header_only_file():
    content = create_test_xlsx([
        ["Date", "Amount"],
    ])

    with pytest.raises(RejectedReportError, match="no data rows"):
        extract_xlsx(content)


def test_extract_file_dispatches_csv():
    content = (
        b"Date,Amount\n"
        b"2026-11-01,100\n"
    )

    result = extract_file(content, "report.csv")

    assert result.columns == ["Date", "Amount"]
    assert result.rows[0]["Amount"] == "100"


def test_extract_file_dispatches_xlsx():
    content = create_test_xlsx([
        ["Date", "Amount"],
        ["2026-11-01", 100],
    ])

    result = extract_file(content, "report.xlsx")

    assert result.columns == ["Date", "Amount"]
    assert result.rows[0]["Amount"] == "100"


def test_extract_file_rejects_unsupported_extension():
    with pytest.raises(ExtractionError, match="Unsupported file format"):
        extract_file(b"some content", "report.pdf")