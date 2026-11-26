import json
import logging
import time

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.report import Report, ReportStatus
from app.services.queue import get_sqs_client

logger = logging.getLogger(__name__)


def process_dlq_message(message: dict) -> None:
    body = json.loads(message["Body"])
    report_id = body["report_id"]

    db = SessionLocal()

    try:
        report = db.get(Report, report_id)

        if report is None:
            logger.warning(
                "Report %s not found while processing DLQ message",
                report_id,
            )
            return

        if report.status in {
            ReportStatus.DONE,
            ReportStatus.REJECTED,
            ReportStatus.FAILED,
        }:
            logger.info(
                "Report %s is already in final state: %s",
                report_id,
                report.status.value,
            )
            return

        report.status = ReportStatus.FAILED
        report.error_message = (
            "Processing failed after maximum SQS delivery attempts."
        )

        db.commit()

        logger.error(
            "Report %s marked as FAILED after exhausting retries",
            report_id,
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def run_dlq_worker() -> None:
    client = get_sqs_client()

    logger.info("DLQ worker started")

    while True:
        response = client.receive_message(
            QueueUrl=settings.SQS_DLQ_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        for message in response.get("Messages", []):
            try:
                process_dlq_message(message)

                client.delete_message(
                    QueueUrl=settings.SQS_DLQ_URL,
                    ReceiptHandle=message["ReceiptHandle"],
                )

                logger.info("DLQ message processed and deleted")

            except Exception:
                logger.exception(
                    "DLQ message processing failed; leaving it for retry"
                )

        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_dlq_worker()