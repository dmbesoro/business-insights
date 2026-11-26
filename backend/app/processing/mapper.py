
from app.models.report import ReportType
from app.processing.classifier import normalize_header


COLUMN_MAPPINGS = {
    ReportType.FINANCIAL: {
        "date": ["date", "transaction_date", "invoice_date", "payment_date"],
        "category": ["category", "expense_category", "transaction_category"],
        "revenue": ["revenue", "sales", "income", "sales_amount"],
        "expenses": ["expenses", "expense", "cost", "costs", "expenditure"],
    },

    ReportType.ATTENDANCE: {
        "employee": [
            "employee", "employee_id", "employee_name",
            "staff_id", "staff_name",
        ],
        "date": ["date", "attendance_date", "work_date"],
        "attendance_status": [
            "attendance_status", "attendance", "status",
        ],
        "check_in": [
            "check_in", "checkin", "time_in", "clock_in",
        ],
        "check_out": [
            "check_out", "checkout", "time_out", "clock_out",
        ],
    },

    ReportType.PROJECT_STATUS: {
        "project": ["project", "project_name", "project_id"],
        "task": ["task", "task_name", "task_id"],
        "status": ["status", "task_status", "project_status"],
        "progress": [
            "progress", "completion",
            "completion_percentage", "percent_complete",
        ],
        "due_date": ["due_date", "deadline", "target_date"],
    },
}


REQUIRED_COLUMNS = {
    ReportType.FINANCIAL: [
        "date", "category", "revenue", "expenses",
    ],
    ReportType.ATTENDANCE: [
        "employee", "date", "attendance_status",
    ],
    ReportType.PROJECT_STATUS: [
        "project", "task", "status",
    ],
}


class MappingError(Exception):
    """Raised when required report columns cannot be mapped."""


def map_columns(
    columns: list[str],
    report_type: ReportType,
) -> dict[str, str]:

    if report_type not in COLUMN_MAPPINGS:
        raise MappingError(
            f"Mapping is not yet implemented for {report_type.value}"
        )

    normalized_columns = {
        normalize_header(column): column
        for column in columns
    }

    mapping = {}

    for standard_name, aliases in COLUMN_MAPPINGS[report_type].items():
        for alias in aliases:
            if alias in normalized_columns:
                mapping[standard_name] = normalized_columns[alias]
                break

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS[report_type]
        if column not in mapping
    ]

    if missing_columns:
        raise MappingError(
            f"Missing required columns: {', '.join(missing_columns)}"
        )

    return mapping
