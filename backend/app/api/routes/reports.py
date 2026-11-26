
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, Query
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.report import Report, ReportStatus, ReportType
from app.models.report_record import ReportRecord
from app.schemas.report import ReportUploadResponse, PaginatedReportsResponse, PaginatedRecordsResponse, AttendanceDashboardResponse, ProjectDashboardResponse, ReportDetailResponse
from app.services.storage import upload_file, delete_file
from app.services.queue import publish_report_message

from math import ceil

from collections import defaultdict
from decimal import Decimal
from datetime import date

from app.schemas.report import FinancialDashboardResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["Reports"])

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


@router.post(
    "/upload",
    response_model=ReportUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # 1. Validate the filename and extension.
    filename = Path(file.filename.replace("\\", "/")).name if file.filename else ""

    if not filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and XLSX files are supported",
        )

    # 2. Read the file in chunks and enforce the size limit.
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_buffer = bytearray()

    while True:
        chunk = await file.read(1024 * 1024)

        if not chunk:
            break

        file_buffer.extend(chunk)

        if len(file_buffer) > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
            )

    if not file_buffer:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    content_type = file.content_type or "application/octet-stream"

    # 3. Generate a unique S3 object key.
    s3_key = f"reports/{uuid.uuid4()}{extension}"

    # 4. Upload the original file to S3.
    try:
        upload_file(bytes(file_buffer), s3_key, content_type)
    except Exception:
        logger.exception("Failed to upload file to S3")
        raise HTTPException(
            status_code=502,
            detail="Could not store uploaded file",
        )

    # 5. Save report metadata in PostgreSQL.
    report = Report(
        original_filename=filename,
        s3_key=s3_key,
        file_size_bytes=len(file_buffer),
        content_type=content_type,
    )

    try:
        db.add(report)
        db.commit()
        db.refresh(report)

    except SQLAlchemyError:
        db.rollback()

        # Compensating cleanup if the database operation fails.
        try:
            delete_file(s3_key)
        except Exception:
            logger.exception("Failed to clean up S3 object: %s", s3_key)

        logger.exception("Failed to save report metadata")
        raise HTTPException(
            status_code=500,
            detail="Could not save report metadata",
        )

    # 6. Publish the report ID to SQS.
    try:
        publish_report_message(report.id)

    except Exception:
        logger.exception(
            "Failed to publish report %s to SQS",
            report.id,
        )

        # Compensate for the failed queue operation.
        try:
            db.delete(report)
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception(
                "Failed to remove report metadata for report %s",
                report.id,
            )

        try:
            delete_file(s3_key)
        except Exception:
            logger.exception(
                "Failed to clean up S3 object: %s",
                s3_key,
            )

        raise HTTPException(
            status_code=502,
            detail="Report was uploaded but could not be scheduled for processing",
        )

    return report



@router.get("/", response_model=PaginatedReportsResponse)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    report_status: ReportStatus | None = Query(default=None, alias="status"),
    report_type: ReportType | None = Query(default=None),
    db: Session = Depends(get_db),
):
    filters = []

    if report_status:
        filters.append(Report.status == report_status)

    if report_type:
        filters.append(Report.report_type == report_type)

    total = db.scalar(
        select(func.count()).select_from(Report).where(*filters)
    ) or 0

    reports = db.scalars(
        select(Report)
        .where(*filters)
        .order_by(Report.created_at.desc(), Report.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": reports,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    return report


@router.get("/{report_id}/records", response_model=PaginatedRecordsResponse)
def list_report_records(
    report_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    is_valid: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    report = db.get(Report, report_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found",
        )

    filters = [ReportRecord.report_id == report_id]

    if is_valid is not None:
        filters.append(ReportRecord.is_valid == is_valid)

    total = db.scalar(
        select(func.count())
        .select_from(ReportRecord)
        .where(*filters)
    ) or 0

    records = db.scalars(
        select(ReportRecord)
        .where(*filters)
        .order_by(ReportRecord.row_number.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": records,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


@router.get(
    "/dashboard/financial",
    response_model=FinancialDashboardResponse,
)
def get_financial_dashboard(
    db: Session = Depends(get_db),
):
    records = db.scalars(
        select(ReportRecord)
        .join(Report, Report.id == ReportRecord.report_id)
        .where(
            Report.status == ReportStatus.DONE,
            Report.report_type == ReportType.FINANCIAL,
            ReportRecord.is_valid.is_(True),
        )
    ).all()

    total_revenue = Decimal("0")
    total_expenses = Decimal("0")

    trends = defaultdict(
        lambda: {
            "revenue": Decimal("0"),
            "expenses": Decimal("0"),
        }
    )

    categories = defaultdict(lambda: Decimal("0"))

    for record in records:
        data = record.normalized_data

        revenue = Decimal(str(data.get("revenue") or "0"))
        expenses = Decimal(str(data.get("expenses") or "0"))
        transaction_date = data.get("date")
        category = data.get("category") or "Uncategorized"

        total_revenue += revenue
        total_expenses += expenses

        trends[transaction_date]["revenue"] += revenue
        trends[transaction_date]["expenses"] += expenses

        categories[category] += expenses

    return {
        "summary": {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_income": total_revenue - total_expenses,
            "transaction_count": len(records),
        },
        "trends": [
            {
                "date": transaction_date,
                **values,
            }
            for transaction_date, values in sorted(trends.items())
        ],
        "expenses_by_category": [
            {
                "category": category,
                "total_expenses": amount,
            }
            for category, amount in sorted(categories.items())
        ],
    }



@router.get(
    "/dashboard/attendance",
    response_model=AttendanceDashboardResponse,
)
def get_attendance_dashboard(
    db: Session = Depends(get_db),
):
    records = db.scalars(
        select(ReportRecord)
        .join(Report, Report.id == ReportRecord.report_id)
        .where(
            Report.status == ReportStatus.DONE,
            Report.report_type == ReportType.ATTENDANCE,
            ReportRecord.is_valid.is_(True),
        )
    ).all()

    status_counts = defaultdict(int)
    trends = defaultdict(
        lambda: {
            "present": 0,
            "absent": 0,
            "late": 0,
        }
    )

    total_scheduled = 0
    absences = 0
    late_arrivals = 0

    for record in records:
        data = record.normalized_data
        attendance_status = data.get("attendance_status")
        attendance_date = data.get("date")

        if not attendance_status:
            continue

        status_counts[attendance_status] += 1

        if attendance_date:
            if attendance_status == "PRESENT":
                trends[attendance_date]["present"] += 1
            elif attendance_status == "ABSENT":
                trends[attendance_date]["absent"] += 1
            elif attendance_status == "LATE":
                trends[attendance_date]["late"] += 1

        if attendance_status in {"PRESENT", "LATE", "HALF_DAY", "ABSENT"}:
            total_scheduled += 1

        if attendance_status == "ABSENT":
            absences += 1

        if attendance_status == "LATE":
            late_arrivals += 1

    attended = (
        status_counts["PRESENT"]
        + status_counts["LATE"]
        + status_counts["HALF_DAY"]
    )

    attendance_rate = (
        Decimal(attended) / Decimal(total_scheduled) * Decimal("100")
        if total_scheduled
        else Decimal("0")
    )

    return {
        "summary": {
            "total_records": len(records),
            "attendance_rate": attendance_rate.quantize(Decimal("0.01")),
            "absences": absences,
            "late_arrivals": late_arrivals,
        },
        "status_breakdown": [
            {"status": status, "count": count}
            for status, count in sorted(status_counts.items())
            if count > 0
        ],
        "trends": [
            {"date": day, **values}
            for day, values in sorted(trends.items())
        ],
    }


@router.get(
    "/dashboard/projects",
    response_model=ProjectDashboardResponse,
)
def get_project_dashboard(
    db: Session = Depends(get_db),
):
    records = db.scalars(
        select(ReportRecord)
        .join(Report, Report.id == ReportRecord.report_id)
        .where(
            Report.status == ReportStatus.DONE,
            Report.report_type == ReportType.PROJECT_STATUS,
            ReportRecord.is_valid.is_(True),
        )
    ).all()

    status_counts = defaultdict(int)
    project_data = defaultdict(
        lambda: {
            "progress_total": Decimal("0"),
            "progress_count": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
        }
    )

    total_tasks = 0
    completed_tasks = 0
    overdue_tasks = 0
    all_progress = []

    today = date.today()

    for record in records:
        data = record.normalized_data

        project = data.get("project")
        task_status = data.get("status")
        due_date = data.get("due_date")
        progress = data.get("progress")

        if not project or not task_status:
            continue

        total_tasks += 1
        status_counts[task_status] += 1

        current_project = project_data[project]
        current_project["total_tasks"] += 1

        if task_status == "COMPLETED":
            completed_tasks += 1
            current_project["completed_tasks"] += 1

        if (
            due_date
            and date.fromisoformat(due_date) < today
            and task_status not in {"COMPLETED", "CANCELLED"}
        ):
            overdue_tasks += 1

        if progress is not None:
            progress_value = Decimal(str(progress))
            all_progress.append(progress_value)
            current_project["progress_total"] += progress_value
            current_project["progress_count"] += 1

    average_completion = (
        sum(all_progress, Decimal("0")) / len(all_progress)
        if all_progress
        else Decimal("0")
    )

    progress_by_project = []

    for project, values in sorted(project_data.items()):
        average_progress = (
            values["progress_total"] / values["progress_count"]
            if values["progress_count"]
            else Decimal("0")
        )

        progress_by_project.append({
            "project": project,
            "average_progress": average_progress.quantize(Decimal("0.01")),
            "total_tasks": values["total_tasks"],
            "completed_tasks": values["completed_tasks"],
        })

    return {
        "summary": {
            "total_projects": len(project_data),
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "overdue_tasks": overdue_tasks,
            "average_completion": average_completion.quantize(
                Decimal("0.01")
            ),
        },
        "tasks_by_status": [
            {"status": status, "count": count}
            for status, count in sorted(status_counts.items())
        ],
        "progress_by_project": progress_by_project,
    }
