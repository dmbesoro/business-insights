from unittest.mock import patch, MagicMock

import pytest

from app.models.report import ReportStatus
from app.worker.sqs_worker import process_message, run_worker


def test_process_message_returns_true_when_report_is_done():
    message = {
        "Body": '{"report_id": 1}'
    }

    mock_report = type(
        "ReportResult",
        (),
        {"status": ReportStatus.DONE},
    )()

    with patch(
        "app.worker.sqs_worker.SessionLocal"
    ), patch(
        "app.worker.sqs_worker.process_report",
        return_value=mock_report,
    ):
        result = process_message(message)

    assert result is True


def test_process_message_raises_when_processing_fails():
    message = {
        "Body": '{"report_id": 1}'
    }

    with patch(
        "app.worker.sqs_worker.SessionLocal"
    ), patch(
        "app.worker.sqs_worker.process_report",
        side_effect=Exception("S3 unavailable"),
    ):
        with pytest.raises(Exception, match="S3 unavailable"):
            process_message(message)


def test_worker_deletes_message_after_successful_processing():
    message = {
        "Body": '{"report_id": 1}',
        "ReceiptHandle": "receipt-123",
    }

    mock_client = MagicMock()
    mock_client.receive_message.side_effect = [
        {"Messages": [message]},
        KeyboardInterrupt,
    ]

    with patch(
        "app.worker.sqs_worker.get_sqs_client",
        return_value=mock_client,
    ), patch(
        "app.worker.sqs_worker.process_message",
        return_value=True,
    ), patch(
        "app.worker.sqs_worker.time.sleep",
        side_effect=KeyboardInterrupt,
    ):
        with pytest.raises(KeyboardInterrupt):
            run_worker()

    mock_client.delete_message.assert_called_once_with(
        QueueUrl=mock_client.delete_message.call_args.kwargs["QueueUrl"],
        ReceiptHandle="receipt-123",
    )


def test_worker_does_not_delete_message_when_processing_fails():
    message = {
        "Body": '{"report_id": 1}',
        "ReceiptHandle": "receipt-123",
    }

    mock_client = MagicMock()
    mock_client.receive_message.return_value = {
        "Messages": [message]
    }

    with patch(
        "app.worker.sqs_worker.get_sqs_client",
        return_value=mock_client,
    ), patch(
        "app.worker.sqs_worker.process_message",
        side_effect=Exception("S3 unavailable"),
    ), patch(
        "app.worker.sqs_worker.time.sleep",
        side_effect=KeyboardInterrupt,
    ):
        with pytest.raises(KeyboardInterrupt):
            run_worker()

    mock_client.delete_message.assert_not_called()