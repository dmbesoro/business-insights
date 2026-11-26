import re
from app.models.report import ReportType


class ClassificationError(Exception):
    """Raised when a report cannot be classified confidently."""


# Each group represents one meaningful business concept.
# Matching multiple groups gives us stronger classification confidence.
REPORT_SIGNATURES = {
    ReportType.FINANCIAL: {
        "date": {
            "date",
            "transaction_date",
            "invoice_date",
            "payment_date",
        },
        "revenue": {
            "revenue",
            "sales",
            "income",
            "sales_amount",
        },
        "expenses": {
            "expenses",
            "expense",
            "cost",
            "costs",
            "expenditure",
        },
        "category": {
            "category",
            "expense_category",
            "transaction_category",
        },
        "amount": {
            "amount",
            "total_amount",
            "net_amount",
        },
    },
    ReportType.ATTENDANCE: {
        "employee": {
            "employee",
            "employee_id",
            "employee_name",
            "staff_id",
            "staff_name",
        },
        "date": {
            "date",
            "attendance_date",
            "work_date",
        },
        "attendance_status": {
            "attendance_status",
            "attendance",
            "status",
        },
        "check_in": {
            "check_in",
            "checkin",
            "time_in",
            "clock_in",
        },
        "check_out": {
            "check_out",
            "checkout",
            "time_out",
            "clock_out",
        },
    },
    ReportType.PROJECT_STATUS: {
        "project": {
            "project",
            "project_name",
            "project_id",
        },
        "task": {
            "task",
            "task_name",
            "task_id",
        },
        "status": {
            "status",
            "task_status",
            "project_status",
        },
        "progress": {
            "progress",
            "completion",
            "completion_percentage",
            "percent_complete",
        },
        "due_date": {
            "due_date",
            "deadline",
            "target_date",
        },
    },
}


def normalize_header(header: str) -> str:
    """Normalize headers for consistent comparison."""
    value = header.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def classify_report(columns: list[str]) -> ReportType:
    """
    Classify a report using its column headers.

    Requires at least two matching business concepts.
    Raises ClassificationError when there is no confident
    or unique match.
    """
    normalized_columns = {
        normalize_header(column)
        for column in columns
        if column.strip()
    }

    scores = {}

    for report_type, signature in REPORT_SIGNATURES.items():
        matched_groups = 0

        for aliases in signature.values():
            if normalized_columns.intersection(aliases):
                matched_groups += 1

        scores[report_type] = matched_groups

    highest_score = max(scores.values(), default=0)

    if highest_score < 2:
        raise ClassificationError(
            "Report type could not be determined from the column headers"
        )

    winners = [
        report_type
        for report_type, score in scores.items()
        if score == highest_score
    ]

    if len(winners) > 1:
        raise ClassificationError(
            "Report type is ambiguous based on the column headers"
        )

    return winners[0]