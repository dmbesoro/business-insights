
from datetime import date
from decimal import Decimal

from app.models.report import Report, ReportStatus
from app.models.report_record import ReportRecord
from app.processing.validator import RowValidationResult
from app.services.record_persistence import persist_report_records


def create_test_report(db_session):
    report = Report(
        original_filename="financial.csv",
        s3_key="reports/test-financial.csv",
        file_size_bytes=100,
        content_type="text/csv",
        status=ReportStatus.CLASSIFIED,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    return report


def test_persist_valid_and_invalid_records(db_session):
    report = create_test_report(db_session)

    results = [
        RowValidationResult(
            row_number=1,
            data={
                "date": date(2026, 11, 1),
                "category": "Sales",
                "revenue": Decimal("50000.00"),
                "expenses": Decimal("12000.00"),
            },
            errors=[],
        ),
        RowValidationResult(
            row_number=2,
            data={
                "date": None,
                "category": "Services",
                "revenue": Decimal("35000"),
                "expenses": Decimal("8000"),
            },
            errors=["Date is required"],
        ),
    ]

    count = persist_report_records(
        db_session,
        report.id,
        results,
    )

    db_session.commit()

    records = (
        db_session.query(ReportRecord)
        .filter_by(report_id=report.id)
        .order_by(ReportRecord.row_number)
        .all()
    )

    assert count == 2
    assert len(records) == 2
    assert records[0].is_valid is True
    assert records[1].is_valid is False
    assert records[1].validation_errors == ["Date is required"]


def test_persist_converts_decimal_and_date_to_json_safe_values(
    db_session,
):
    report = create_test_report(db_session)

    results = [
        RowValidationResult(
            row_number=1,
            data={
                "date": date(2026, 11, 1),
                "revenue": Decimal("50000.25"),
            },
            errors=[],
        )
    ]

    persist_report_records(db_session, report.id, results)
    db_session.commit()

    record = (
        db_session.query(ReportRecord)
        .filter_by(report_id=report.id)
        .one()
    )

    assert record.normalized_data["date"] == "2026-11-01"
    assert record.normalized_data["revenue"] == "50000.25"


def test_persist_replaces_existing_records_on_reprocessing(
    db_session,
):
    report = create_test_report(db_session)

    first_results = [
        RowValidationResult(
            row_number=1,
            data={"category": "Old Category"},
            errors=[],
        )
    ]

    persist_report_records(db_session, report.id, first_results)
    db_session.commit()

    second_results = [
        RowValidationResult(
            row_number=1,
            data={"category": "Updated Category"},
            errors=[],
        ),
        RowValidationResult(
            row_number=2,
            data={"category": "New Category"},
            errors=[],
        ),
    ]

    persist_report_records(db_session, report.id, second_results)
    db_session.commit()

    records = (
        db_session.query(ReportRecord)
        .filter_by(report_id=report.id)
        .order_by(ReportRecord.row_number)
        .all()
    )

    assert len(records) == 2
    assert records[0].normalized_data["category"] == "Updated Category"
    assert records[1].normalized_data["category"] == "New Category"
