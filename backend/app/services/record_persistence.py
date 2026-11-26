
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models.report_record import ReportRecord
from app.processing.validator import RowValidationResult


def make_json_safe(value):
    """Convert Python values into JSON-compatible values."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        # Keep decimal precision instead of converting to float.
        return str(value)

    if isinstance(value, dict):
        return {
            key: make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [make_json_safe(item) for item in value]

    return value


def persist_report_records(
    db: Session,
    report_id: int,
    results: list[RowValidationResult],
) -> int:
    """
    Replace all existing records for a report.

    The caller controls the transaction and must commit after
    the report records and report status have been updated.
    """
    db.execute(
        delete(ReportRecord).where(
            ReportRecord.report_id == report_id
        )
    )

    records = [
        ReportRecord(
            report_id=report_id,
            row_number=result.row_number,
            normalized_data=make_json_safe(result.data),
            is_valid=result.is_valid,
            validation_errors=result.errors,
        )
        for result in results
    ]

    db.add_all(records)
    db.flush()

    return len(records)
