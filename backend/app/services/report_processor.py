
import logging

from sqlalchemy.orm import Session

from app.models.report import Report, ReportStatus
from app.processing.extractor import (
    extract_file,
    RejectedReportError,
)
from app.processing.classifier import (
    ClassificationError,
    classify_report,
)
from app.processing.mapper import (
    MappingError,
    map_columns,
)
from app.processing.validator import validate_rows
from app.services.record_persistence import persist_report_records
from app.services.storage import download_file

logger = logging.getLogger(__name__)


def process_report(db: Session, report_id: int) -> Report:
    report = db.get(Report, report_id)

    if report is None:
        raise ValueError(f"Report {report_id} does not exist")

    if report.status in {
        ReportStatus.DONE,
        ReportStatus.REJECTED,
        ReportStatus.FAILED,
    }:
        logger.info(
            "Report %s is already in final state %s",
            report.id,
            report.status.value,
        )
        return report

    if report.status != ReportStatus.UPLOADED:
        raise ValueError(
            f"Report {report_id} cannot be processed from status {report.status.value}"
        )

    try:
        # 1. Download original file
        file_bytes = download_file(report.s3_key)

        # 2. Extract spreadsheet rows
        result = extract_file(
            file_bytes,
            report.original_filename,
        )
        report.status = ReportStatus.EXTRACTED

        # 3. Detect report type
        report_type = classify_report(result.columns)
        report.report_type = report_type
        report.status = ReportStatus.CLASSIFIED

        # 4. Map spreadsheet columns
        mapping = map_columns(
            result.columns,
            report_type,
        )

        # 5. Normalize and validate individual rows
        validation_results = validate_rows(
            report_type,
            result.rows,
            mapping,
        )

        # 6. Save valid and rejected rows
        persist_report_records(
            db,
            report.id,
            validation_results,
        )

        # 7. Mark complete only after records are saved
        report.status = ReportStatus.DONE
        report.error_message = None

        db.commit()
        db.refresh(report)

        logger.info(
            "Report %s completed: type=%s, rows=%s, valid=%s, rejected=%s",
            report_id,
            report_type.value,
            len(validation_results),
            sum(row.is_valid for row in validation_results),
            sum(not row.is_valid for row in validation_results),
        )

        return report

    except (
        RejectedReportError,
        ClassificationError,
        MappingError,
    ) as exc:
        db.rollback()

        report = db.get(Report, report_id)
        report.status = ReportStatus.REJECTED
        report.error_message = str(exc)

        db.commit()
        db.refresh(report)

        logger.warning(
            "Report %s rejected: %s",
            report_id,
            exc,
        )

        return report

    except Exception:
        db.rollback()

        logger.exception(
            "Report %s processing failed; allowing retry",
            report_id,
        )

        raise
