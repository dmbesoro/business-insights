
from datetime import date
from decimal import Decimal

from app.models.report import ReportType
from app.processing.normalizer import normalize_date, normalize_number, normalize_status


VALID_ATTENDANCE_STATUSES = {
    "PRESENT",
    "ABSENT",
    "LATE",
    "HALF_DAY",
    "ON_LEAVE",
    "HOLIDAY",
    "REST_DAY",
}


VALID_PROJECT_STATUSES = {
    "NOT_STARTED",
    "IN_PROGRESS",
    "COMPLETED",
    "ON_HOLD",
    "CANCELLED",
    "BLOCKED",
}


class RowValidationResult:
    def __init__(
        self,
        row_number: int,
        data: dict,
        errors: list[str],
    ):
        self.row_number = row_number
        self.data = data
        self.errors = errors

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_financial_rows(
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[RowValidationResult]:

    results = []

    for row_number, row in enumerate(rows, start=1):
        errors = []
        normalized = {}

        # Validate date
        try:
            normalized["date"] = normalize_date(
                row.get(mapping["date"])
            )
            if normalized["date"] is None:
                errors.append("Date is required")
        except ValueError as exc:
            errors.append(str(exc))

        # Validate category
        category = row.get(mapping["category"], "").strip()

        if not category:
            errors.append("Category is required")

        normalized["category"] = category or None

        # Validate revenue
        try:
            normalized["revenue"] = normalize_number(
                row.get(mapping["revenue"])
            )
            if normalized["revenue"] is None:
                errors.append("Revenue is required")
        except ValueError as exc:
            errors.append(str(exc))

        # Validate expenses
        try:
            normalized["expenses"] = normalize_number(
                row.get(mapping["expenses"])
            )
            if normalized["expenses"] is None:
                errors.append("Expenses is required")
        except ValueError as exc:
            errors.append(str(exc))

        results.append(
            RowValidationResult(
                row_number=row_number,
                data=normalized,
                errors=errors,
            )
        )

    return results


def validate_attendance_rows(
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[RowValidationResult]:

    results = []

    for row_number, row in enumerate(rows, start=1):
        errors = []
        normalized = {}

        # Employee
        employee = row.get(mapping["employee"], "").strip()

        if not employee:
            errors.append("Employee is required")

        normalized["employee"] = employee or None

        # Attendance date
        try:
            normalized["date"] = normalize_date(
                row.get(mapping["date"])
            )

            if normalized["date"] is None:
                errors.append("Date is required")

        except ValueError as exc:
            errors.append(str(exc))

        # Attendance status
        attendance_status = normalize_status(
            row.get(mapping["attendance_status"])
        )

        if attendance_status is None:
            errors.append("Attendance status is required")

        elif attendance_status not in VALID_ATTENDANCE_STATUSES:
            errors.append(
                f"Invalid attendance status: {attendance_status}"
            )

        normalized["attendance_status"] = attendance_status

        # Optional working hours
        normalized["check_in"] = (
            row.get(mapping["check_in"], "").strip()
            if "check_in" in mapping else None
        )

        normalized["check_out"] = (
            row.get(mapping["check_out"], "").strip()
            if "check_out" in mapping else None
        )

        results.append(
            RowValidationResult(
                row_number=row_number,
                data=normalized,
                errors=errors,
            )
        )

    return results


def validate_project_rows(
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[RowValidationResult]:

    results = []

    for row_number, row in enumerate(rows, start=1):
        errors = []
        normalized = {}

        # Project
        project = row.get(mapping["project"], "").strip()

        if not project:
            errors.append("Project is required")

        normalized["project"] = project or None

        # Task
        task = row.get(mapping["task"], "").strip()

        if not task:
            errors.append("Task is required")

        normalized["task"] = task or None

        # Status
        project_status = normalize_status(
            row.get(mapping["status"])
        )

        if project_status is None:
            errors.append("Project status is required")

        elif project_status not in VALID_PROJECT_STATUSES:
            errors.append(
                f"Invalid project status: {project_status}"
            )

        normalized["status"] = project_status

        # Progress
        if "progress" in mapping:
            try:
                progress = normalize_number(
                    row.get(mapping["progress"])
                )

                if progress is None:
                    errors.append("Progress is required")
                elif not Decimal("0") <= progress <= Decimal("100"):
                    errors.append("Progress must be between 0 and 100")

                normalized["progress"] = progress

            except ValueError as exc:
                errors.append(str(exc))

        else:
            normalized["progress"] = None

        # Due date is optional
        if "due_date" in mapping:
            try:
                normalized["due_date"] = normalize_date(
                    row.get(mapping["due_date"])
                )
            except ValueError as exc:
                errors.append(str(exc))
        else:
            normalized["due_date"] = None

        results.append(
            RowValidationResult(
                row_number=row_number,
                data=normalized,
                errors=errors,
            )
        )

    return results


def validate_rows(
    report_type: ReportType,
    rows: list[dict[str, str]],
    mapping: dict[str, str],
) -> list[RowValidationResult]:

    if report_type == ReportType.FINANCIAL:
        return validate_financial_rows(rows, mapping)

    if report_type == ReportType.ATTENDANCE:
        return validate_attendance_rows(rows, mapping)

    if report_type == ReportType.PROJECT_STATUS:
        return validate_project_rows(rows, mapping)

    raise NotImplementedError(
        f"Validation is not yet implemented for {report_type.value}"
    )