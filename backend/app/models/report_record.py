
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportRecord(Base):
    __tablename__ = "report_records"

    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "row_number",
            name="uq_report_record_row",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    report_id: Mapped[int] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    row_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    normalized_data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )

    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    validation_errors: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        default=list,
    )
