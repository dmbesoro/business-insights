
import json

import boto3

from app.core.config import settings


def get_sqs_client():
    return boto3.client(
        "sqs",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def publish_report_message(report_id: int):
    client = get_sqs_client()

    client.send_message(
        QueueUrl=settings.SQS_QUEUE_URL,
        MessageBody=json.dumps({
            "report_id": report_id,
        }),
    )
