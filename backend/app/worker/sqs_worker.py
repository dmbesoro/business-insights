
import json
import logging
import time

from app.services.queue import get_sqs_client
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.report_processor import process_report
from app.models.report import ReportStatus

logger = logging.getLogger(__name__)


def process_message(message: dict) -> bool:
    body = json.loads(message["Body"])
    report_id = body["report_id"]

    db = SessionLocal()

    try:
        logger.info("Processing report %s", report_id)

        report = process_report(db, report_id)

        if report.status in {
            ReportStatus.DONE,
            ReportStatus.REJECTED,
            ReportStatus.FAILED,
        }:
            logger.info(
                "Report %s finished with status %s",
                report_id,
                report.status.value,
            )
            return True

        raise RuntimeError(
            f"Report {report_id} returned unexpected status "
            f"{report.status.value}"
        )

    finally:
        db.close()


def run_worker() -> None:
    client = get_sqs_client()

    logger.info("SQS worker started")

    while True:
        response = client.receive_message(
            QueueUrl=settings.SQS_QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=60,
        )

        for message in response.get("Messages", []):
            try:
                acknowledged = process_message(message)

                if acknowledged:
                    client.delete_message(
                        QueueUrl=settings.SQS_QUEUE_URL,
                        ReceiptHandle=message["ReceiptHandle"],
                    )

            except Exception:
                logger.exception(
                    "Message processing failed; SQS will retry it"
                )

        time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker()
