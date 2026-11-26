import { apiClient } from "./client";

export interface Report {
  id: number;
  original_filename: string;
  status: "UPLOADED" | "EXTRACTED" | "CLASSIFIED" | "DONE" | "REJECTED" | "FAILED";
  report_type: "FINANCIAL" | "ATTENDANCE" | "PROJECT_STATUS" | null;
  created_at: string;
}

export interface ReportList {
  items: Report[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export async function getReports(): Promise<ReportList> {
  const response = await apiClient.get<ReportList>("/reports/");
  return response.data;
}

export async function uploadReport(file: File): Promise<Report> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<Report>(
    "/reports/upload",
    formData,
    {
      headers: {
        "Content-Type": undefined,
      },
      onUploadProgress: (event) => {
        if (event.total) {
          const progress = Math.round(
            (event.loaded * 100) / event.total
          );
          console.log(`Upload progress: ${progress}%`);
        }
      },
    }
  );

  return response.data;
}

export interface ReportDetail extends Report {
  file_size_bytes: number;
  updated_at: string;
  error_message: string | null;
}

export interface ReportRecord {
  id: number;
  row_number: number;
  normalized_data: Record<string, unknown>;
  is_valid: boolean;
  validation_errors: string[];
}

export interface ReportRecordList {
  items: ReportRecord[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export async function getReport(
  reportId: number
): Promise<ReportDetail> {
  const response = await apiClient.get<ReportDetail>(
    `/reports/${reportId}`
  );

  return response.data;
}

export async function getReportRecords(
  reportId: number,
  page = 1,
  pageSize = 20,
  isValid?: boolean
): Promise<ReportRecordList> {
  const response = await apiClient.get<ReportRecordList>(
    `/reports/${reportId}/records`,
    {
      params: {
        page,
        page_size: pageSize,
        is_valid: isValid,
      },
    }
  );

  return response.data;
}

export interface FinancialDashboard {
  summary: {
    total_revenue: number;
    total_expenses: number;
    net_income: number;
    transaction_count: number;
  };
  trends: {
    date: string;
    revenue: number;
    expenses: number;
  }[];
  expenses_by_category: {
    category: string;
    total_expenses: number;
  }[];
}

export interface AttendanceDashboard {
  summary: {
    total_records: number;
    attendance_rate: number;
    absences: number;
    late_arrivals: number;
  };
  status_breakdown: {
    status: string;
    count: number;
  }[];
  trends: {
    date: string;
    present: number;
    absent: number;
    late: number;
  }[];
}

export interface ProjectDashboard {
  summary: {
    total_projects: number;
    total_tasks: number;
    completed_tasks: number;
    overdue_tasks: number;
    average_completion: number;
  };
  tasks_by_status: {
    status: string;
    count: number;
  }[];
  progress_by_project: {
    project: string;
    average_progress: number;
    total_tasks: number;
    completed_tasks: number;
  }[];
}

export async function getFinancialDashboard(): Promise<FinancialDashboard> {
  const response = await apiClient.get<FinancialDashboard>(
    "/reports/dashboard/financial"
  );

  return response.data;
}

export async function getAttendanceDashboard(): Promise<AttendanceDashboard> {
  const response = await apiClient.get<AttendanceDashboard>(
    "/reports/dashboard/attendance"
  );

  return response.data;
}

export async function getProjectDashboard(): Promise<ProjectDashboard> {
  const response = await apiClient.get<ProjectDashboard>(
    "/reports/dashboard/projects"
  );

  return response.data;
}