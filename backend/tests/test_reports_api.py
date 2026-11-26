
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db

from app.models.report import Report, ReportStatus, ReportType
from app.models.report_record import ReportRecord


@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_reports_returns_empty_page(client):
    response = client.get("/api/v1/reports/")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 0
    assert data["total_pages"] == 0


def test_list_reports_filters_by_status(client, db_session):
    report = Report(
        original_filename="sample.csv",
        s3_key="uploads/sample.csv",
        file_size_bytes=100,
        content_type="text/csv",
        status=ReportStatus.DONE,
    )

    db_session.add(report)
    db_session.commit()

    response = client.get(
        "/api/v1/reports/",
        params={"status": "DONE"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["original_filename"] == "sample.csv"
    assert data["items"][0]["status"] == "DONE"


def test_get_report_details(client, db_session):
    report = Report(
        original_filename="financial.csv",
        s3_key="uploads/financial.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
        error_message=None,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    response = client.get(f"/api/v1/reports/{report.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == report.id
    assert data["original_filename"] == "financial.csv"
    assert data["status"] == "DONE"
    assert data["error_message"] is None


def test_get_report_not_found(client):
    response = client.get("/api/v1/reports/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found"


def test_get_report_records(client, db_session):
    report = Report(
        original_filename="financial.csv",
        s3_key="uploads/records-financial.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    record = ReportRecord(
        report_id=report.id,
        row_number=1,
        normalized_data={
            "date": "2026-11-01",
            "category": "Sales",
            "revenue": "50000",
            "expenses": "12000",
        },
        is_valid=True,
        validation_errors=[],
    )

    db_session.add(record)
    db_session.commit()

    response = client.get(
        f"/api/v1/reports/{report.id}/records"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["row_number"] == 1
    assert data["items"][0]["is_valid"] is True


def test_get_report_records_filters_by_validity(client, db_session):
    report = Report(
        original_filename="financial.csv",
        s3_key="uploads/records-filter.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    db_session.add_all([
        ReportRecord(
            report_id=report.id,
            row_number=1,
            normalized_data={"category": "Sales", "revenue": "50000"},
            is_valid=True,
            validation_errors=[],
        ),
        ReportRecord(
            report_id=report.id,
            row_number=2,
            normalized_data={"category": "", "revenue": "invalid"},
            is_valid=False,
            validation_errors=["Invalid revenue"],
        ),
    ])
    db_session.commit()

    response = client.get(
        f"/api/v1/reports/{report.id}/records",
        params={"is_valid": "false"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["row_number"] == 2
    assert data["items"][0]["is_valid"] is False


def test_financial_dashboard_returns_empty_summary(client):
    response = client.get("/api/v1/reports/dashboard/financial")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_revenue"] == "0"
    assert data["summary"]["total_expenses"] == "0"
    assert data["summary"]["net_income"] == "0"
    assert data["summary"]["transaction_count"] == 0

    assert data["trends"] == []
    assert data["expenses_by_category"] == []


def test_attendance_dashboard_returns_empty_summary(client):
    response = client.get("/api/v1/reports/dashboard/attendance")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_records"] == 0
    assert data["summary"]["attendance_rate"] == "0.00"
    assert data["summary"]["absences"] == 0
    assert data["summary"]["late_arrivals"] == 0

    assert data["status_breakdown"] == []
    assert data["trends"] == []


def test_project_dashboard_returns_empty_summary(client):
    response = client.get("/api/v1/reports/dashboard/projects")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_projects"] == 0
    assert data["summary"]["total_tasks"] == 0
    assert data["summary"]["completed_tasks"] == 0
    assert data["summary"]["overdue_tasks"] == 0
    assert data["summary"]["average_completion"] == "0.00"

    assert data["tasks_by_status"] == []
    assert data["progress_by_project"] == []


def test_financial_dashboard_calculates_totals(client, db_session):
    report = Report(
        original_filename="financial.csv",
        s3_key="uploads/dashboard-financial.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
        report_type=ReportType.FINANCIAL,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    db_session.add_all([
        ReportRecord(
            report_id=report.id,
            row_number=1,
            normalized_data={
                "date": "2026-11-01",
                "category": "Sales",
                "revenue": "50000",
                "expenses": "12000",
            },
            is_valid=True,
            validation_errors=[],
        ),
        ReportRecord(
            report_id=report.id,
            row_number=2,
            normalized_data={
                "date": "2026-11-02",
                "category": "Services",
                "revenue": "35000",
                "expenses": "8000",
            },
            is_valid=True,
            validation_errors=[],
        ),
    ])
    db_session.commit()

    response = client.get("/api/v1/reports/dashboard/financial")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_revenue"] == "85000"
    assert data["summary"]["total_expenses"] == "20000"
    assert data["summary"]["net_income"] == "65000"
    assert data["summary"]["transaction_count"] == 2

    assert len(data["trends"]) == 2
    assert len(data["expenses_by_category"]) == 2


def test_attendance_dashboard_calculates_metrics(client, db_session):
    report = Report(
        original_filename="attendance.csv",
        s3_key="uploads/dashboard-attendance.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
        report_type=ReportType.ATTENDANCE,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    attendance_rows = [
        ("PRESENT", 1),
        ("LATE", 2),
        ("ABSENT", 3),
        ("HALF_DAY", 4),
    ]

    db_session.add_all([
        ReportRecord(
            report_id=report.id,
            row_number=row_number,
            normalized_data={
                "employee": f"EMP00{row_number}",
                "date": "2026-11-25",
                "attendance_status": status,
            },
            is_valid=True,
            validation_errors=[],
        )
        for status, row_number in attendance_rows
    ])

    db_session.commit()

    response = client.get("/api/v1/reports/dashboard/attendance")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_records"] == 4
    assert data["summary"]["attendance_rate"] == "75.00"
    assert data["summary"]["absences"] == 1
    assert data["summary"]["late_arrivals"] == 1

    assert len(data["status_breakdown"]) == 4
    assert len(data["trends"]) == 1


def test_project_dashboard_calculates_metrics(client, db_session):
    report = Report(
        original_filename="projects.csv",
        s3_key="uploads/dashboard-projects.csv",
        file_size_bytes=250,
        content_type="text/csv",
        status=ReportStatus.DONE,
        report_type=ReportType.PROJECT_STATUS,
    )

    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    project_rows = [
        {
            "project": "Website Redesign",
            "task": "UI Design",
            "status": "IN_PROGRESS",
            "progress": "75",
            "due_date": "2026-12-01",
        },
        {
            "project": "Website Redesign",
            "task": "API Integration",
            "status": "COMPLETED",
            "progress": "100",
            "due_date": "2026-11-20",
        },
        {
            "project": "Mobile App",
            "task": "Backend Development",
            "status": "IN_PROGRESS",
            "progress": "40",
            "due_date": "2026-11-20",
        },
        {
            "project": "Mobile App",
            "task": "Testing",
            "status": "NOT_STARTED",
            "progress": "0",
            "due_date": "2026-12-10",
        },
    ]

    db_session.add_all([
        ReportRecord(
            report_id=report.id,
            row_number=index,
            normalized_data=row,
            is_valid=True,
            validation_errors=[],
        )
        for index, row in enumerate(project_rows, start=1)
    ])

    db_session.commit()

    response = client.get("/api/v1/reports/dashboard/projects")

    assert response.status_code == 200

    data = response.json()

    assert data["summary"]["total_projects"] == 2
    assert data["summary"]["total_tasks"] == 4
    assert data["summary"]["completed_tasks"] == 1
    assert data["summary"]["overdue_tasks"] == 1
    assert data["summary"]["average_completion"] == "53.75"

    assert len(data["tasks_by_status"]) == 3
    assert len(data["progress_by_project"]) == 2
