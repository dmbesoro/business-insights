import pytest
from unittest.mock import MagicMock, patch

from app.models.report import ReportStatus
from app.worker.dlq_worker import process_dlq_message


def test_dlq_message_marks_report_as_failed():
    message = {
        "Body": '{"report_id": 1}'
    }

    report = MagicMock()
    report.status = ReportStatus.UPLOADED

    db = MagicMock()
    db.get.return_value = report

    with patch(
        "app.worker.dlq_worker.SessionLocal",
        return_value=db,
    ):
        process_dlq_message(message)

    assert report.status == ReportStatus.FAILED
    assert "maximum SQS delivery attempts" in report.error_message
    db.commit.assert_called_once()


def test_dlq_message_does_not_overwrite_done_report():
    message = {
        "Body": '{"report_id": 1}'
    }

    report = MagicMock()
    report.status = ReportStatus.DONE

    db = MagicMock()
    db.get.return_value = report

    with patch(
        "app.worker.dlq_worker.SessionLocal",
        return_value=db,
    ):
        process_dlq_message(message)

    assert report.status == ReportStatus.DONE
    db.commit.assert_not_called()


def test_dlq_message_handles_missing_report():
    message = {
        "Body": '{"report_id": 999}'
    }

    db = MagicMock()
    db.get.return_value = None

    with patch(
        "app.worker.dlq_worker.SessionLocal",
        return_value=db,
    ):
        process_dlq_message(message)

    db.commit.assert_not_called()


def test_dlq_message_rolls_back_when_commit_fails():
    message = {
        "Body": '{"report_id": 1}'
    }

    report = MagicMock()
    report.status = ReportStatus.UPLOADED

    db = MagicMock()
    db.get.return_value = report
    db.commit.side_effect = Exception("Database unavailable")

    with patch(
        "app.worker.dlq_worker.SessionLocal",
        return_value=db,
    ):
        with pytest.raises(Exception, match="Database unavailable"):
            process_dlq_message(message)

    db.rollback.assert_called_once()
    db.close.assert_called_once()