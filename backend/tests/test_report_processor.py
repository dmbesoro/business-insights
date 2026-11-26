from unittest.mock import patch

import pytest

from app.models.report import Report, ReportStatus, ReportType
from app.processing.extractor import (
    ExtractionError,
    RejectedReportError,
)
from app.services.report_processor import process_report
from app.models.report_record import ReportRecord


@pytest.fixture
def uploaded_report(db_session):
    report = Report(
        original_filename="sample.csv",
        s3_key="reports/sample.csv",
        file_size_bytes=100,
        content_type="text/csv",
        status=ReportStatus.UPLOADED,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    return report


def test_process_report_success(db_session, uploaded_report):
    csv_bytes = (
        b"date,category,revenue,expenses\n"
        b"2026-11-01,Sales,50000,12000\n"
    )

    with patch(
        "app.services.report_processor.download_file",
        return_value=csv_bytes,
    ):
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.DONE
    assert result.report_type.value == "FINANCIAL"
    assert result.error_message is None

    # Verify that the extracted financial row was saved.
    records = (
        db_session.query(ReportRecord)
        .filter_by(report_id=result.id)
        .all()
    )

    assert len(records) == 1
    assert records[0].is_valid is True
    assert records[0].normalized_data["category"] == "Sales"
    assert records[0].normalized_data["revenue"] == "50000"


def test_process_report_rejected(db_session, uploaded_report):
    with patch(
        "app.services.report_processor.download_file",
        return_value=b"date,category,revenue\n",
    ):
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.REJECTED
    assert "no data rows" in result.error_message


def test_process_report_raises_on_processing_failure(
    db_session,
    uploaded_report,
):
    with patch(
        "app.services.report_processor.download_file",
        side_effect=Exception("S3 unavailable"),
    ):
        with pytest.raises(Exception, match="S3 unavailable"):
            process_report(db_session, uploaded_report.id)

    db_session.refresh(uploaded_report)

    assert uploaded_report.status == ReportStatus.UPLOADED


def test_process_report_rejects_unknown_report(
    db_session,
    uploaded_report,
):
    csv_bytes = (
        b"name,description,notes\n"
        b"Sample,Example,Nothing special\n"
    )

    with patch(
        "app.services.report_processor.download_file",
        return_value=csv_bytes,
    ):
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.REJECTED
    assert "could not be determined" in result.error_message


def test_process_attendance_report_success(db_session, uploaded_report):
    csv_bytes = (
        b"employee_id,date,attendance_status,check_in,check_out\n"
        b"EMP001,2026-11-25,Present,08:00,17:00\n"
        b"EMP002,2026-11-25,Late,09:15,17:00\n"
    )

    with patch(
        "app.services.report_processor.download_file",
        return_value=csv_bytes,
    ):
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.DONE
    assert result.report_type == ReportType.ATTENDANCE

    records = (
        db_session.query(ReportRecord)
        .filter_by(report_id=result.id)
        .order_by(ReportRecord.row_number)
        .all()
    )

    assert len(records) == 2
    assert all(record.is_valid for record in records)
    assert records[0].normalized_data["employee"] == "EMP001"
    assert records[0].normalized_data["attendance_status"] == "PRESENT"
    assert records[1].normalized_data["attendance_status"] == "LATE"


def test_process_project_report_success(db_session, uploaded_report):
    csv_bytes = (
        b"project_name,task_name,status,progress,due_date\n"
        b"Website Redesign,UI Design,In Progress,75%,2026-12-01\n"
        b"Website Redesign,API Integration,Completed,100%,2026-11-20\n"
    )

    with patch(
        "app.services.report_processor.download_file",
        return_value=csv_bytes,
    ):
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.DONE
    assert result.report_type == ReportType.PROJECT_STATUS

    records = (
        db_session.query(ReportRecord)
        .filter_by(report_id=result.id)
        .order_by(ReportRecord.row_number)
        .all()
    )

    assert len(records) == 2
    assert all(record.is_valid for record in records)
    assert records[0].normalized_data["project"] == "Website Redesign"
    assert records[0].normalized_data["status"] == "IN_PROGRESS"
    assert records[0].normalized_data["progress"] == "75"
    assert records[1].normalized_data["status"] == "COMPLETED"


def test_process_completed_report_is_idempotent(db_session, uploaded_report):
    uploaded_report.status = ReportStatus.DONE
    db_session.commit()

    with patch(
        "app.services.report_processor.download_file"
    ) as mock_download:
        result = process_report(db_session, uploaded_report.id)

    assert result.status == ReportStatus.DONE
    mock_download.assert_not_called()
