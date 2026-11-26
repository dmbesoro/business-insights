
import boto3

from app.core.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_ENDPOINT_URL,
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def upload_file(file_bytes: bytes, s3_key: str, content_type: str):
    client = get_s3_client()

    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
        Body=file_bytes,
        ContentType=content_type,
    )

    return s3_key


def download_file(s3_key: str) -> bytes:
    client = get_s3_client()

    response = client.get_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
    )

    return response["Body"].read()


def delete_file(s3_key: str):
    client = get_s3_client()

    client.delete_object(
        Bucket=settings.S3_BUCKET,
        Key=s3_key,
    )
