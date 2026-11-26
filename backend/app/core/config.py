
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    AWS_ENDPOINT_URL: str = "http://localstack:4566"
    AWS_REGION: str = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: str = "test"
    AWS_SECRET_ACCESS_KEY: str = "test"

    S3_BUCKET: str = "business-insights"

    MAX_UPLOAD_SIZE_MB: int = 20

    SQS_QUEUE_URL: str = (
        "http://localstack:4566/000000000000/report-processing"
    )
    SQS_DLQ_URL: str = (
        "http://localstack:4566/000000000000/report-processing-dlq"
    )

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()
