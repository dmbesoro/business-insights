from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportStatus, ReportType


class ReportUploadResponse(BaseModel):
    id: int
    original_filename: str
    status: ReportStatus
    report_type: ReportType | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportListItem(BaseModel):
    id: int
    original_filename: str
    status: ReportStatus
    report_type: ReportType | None
    file_size_bytes: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedReportsResponse(BaseModel):
    items: list[ReportListItem]
    page: int
    page_size: int
    total: int
    total_pages: int


class ReportDetailResponse(ReportListItem):
    error_message: str | None = None


class ReportRecordResponse(BaseModel):
    id: int
    row_number: int
    normalized_data: dict
    is_valid: bool
    validation_errors: list

    model_config = ConfigDict(from_attributes=True)


class PaginatedRecordsResponse(BaseModel):
    items: list[ReportRecordResponse]
    page: int
    page_size: int
    total: int
    total_pages: int


class FinancialSummaryResponse(BaseModel):
    total_revenue: Decimal
    total_expenses: Decimal
    net_income: Decimal
    transaction_count: int


class FinancialTrendItem(BaseModel):
    date: date
    revenue: Decimal
    expenses: Decimal


class ExpenseCategoryItem(BaseModel):
    category: str
    total_expenses: Decimal


class FinancialDashboardResponse(BaseModel):
    summary: FinancialSummaryResponse
    trends: list[FinancialTrendItem]
    expenses_by_category: list[ExpenseCategoryItem]


class AttendanceSummaryResponse(BaseModel):
    total_records: int
    attendance_rate: Decimal
    absences: int
    late_arrivals: int


class AttendanceStatusItem(BaseModel):
    status: str
    count: int


class AttendanceTrendItem(BaseModel):
    date: date
    present: int
    absent: int
    late: int


class AttendanceDashboardResponse(BaseModel):
    summary: AttendanceSummaryResponse
    status_breakdown: list[AttendanceStatusItem]
    trends: list[AttendanceTrendItem]


class ProjectSummaryResponse(BaseModel):
    total_projects: int
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    average_completion: Decimal


class ProjectStatusItem(BaseModel):
    status: str
    count: int


class ProjectProgressItem(BaseModel):
    project: str
    average_progress: Decimal
    total_tasks: int
    completed_tasks: int


class ProjectDashboardResponse(BaseModel):
    summary: ProjectSummaryResponse
    tasks_by_status: list[ProjectStatusItem]
    progress_by_project: list[ProjectProgressItem]
