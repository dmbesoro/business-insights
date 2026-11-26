
import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    CLASSIFIED = "CLASSIFIED"
    DONE = "DONE"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ReportType(str, enum.Enum):
    FINANCIAL = "FINANCIAL"
    ATTENDANCE = "ATTENDANCE"
    PROJECT_STATUS = "PROJECT_STATUS"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, native_enum=False),
        nullable=False,
        default=ReportStatus.UPLOADED,
    )

    report_type: Mapped[ReportType | None] = mapped_column(
        Enum(ReportType, native_enum=False),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
