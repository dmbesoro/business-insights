
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getReports } from "./api/reports";
import UploadPanel from "./components/UploadPanel";
import ReportDetails from "./components/ReportDetails";
import { useUIStore } from "./stores/uiStore";
import FinancialDashboard from "./components/FinancialDashboard";
import AttendanceDashboard from "./components/AttendanceDashboard";
import ProjectDashboard from "./components/ProjectDashboard";

export default function App() {
  const [selectedReportId, setSelectedReportId] = useState<number | null>(null);

  const reports = useQuery({
    queryKey: ["reports"],
    queryFn: getReports,
    refetchInterval: (query) => {
      const items = query.state.data?.items ?? [];

      const hasProcessingReports = items.some((report) =>
        ["UPLOADED", "EXTRACTED", "CLASSIFIED"].includes(
          report.status
        )
      );

      return hasProcessingReports ? 3000 : false;
    },
  });

  const isUploadPanelOpen = useUIStore(
    (state) => state.isUploadPanelOpen
  );
  const openUploadPanel = useUIStore(
    (state) => state.openUploadPanel
  );

  const [activeView, setActiveView] = useState<
    "reports" | "financial" | "attendance" | "projects"
  >("reports");

  if (selectedReportId !== null) {
    return (
      <ReportDetails
        reportId={selectedReportId}
        onBack={() => setSelectedReportId(null)}
      />
    );
  }

  return (
    <main>
      <header>
        <p className="eyebrow">BUSINESS INSIGHTS</p>
        <h1>Report workspace</h1>
        <p>Upload and understand your business reports.</p>

        <button type="button" onClick={openUploadPanel}>
          Upload report
        </button>

        <nav>
          <button onClick={() => setActiveView("reports")}>
            Reports
          </button>

          <button onClick={() => setActiveView("financial")}>
            Financial Dashboard
          </button>

          <button onClick={() => setActiveView("attendance")}>
            Attendance Dashboard
          </button>

          <button onClick={() => setActiveView("projects")}>
            Project Dashboard
          </button>
        </nav>
      </header>

      {isUploadPanelOpen && <UploadPanel />}

      {activeView === "financial" ? (
        <FinancialDashboard />
      ) : activeView === "attendance" ? (
        <AttendanceDashboard />
      ) : activeView === "projects" ? (
        <ProjectDashboard />
      ) : (
            <section className="panel">
              <h2>Reports</h2>

              {reports.isPending && <p>Loading reports...</p>}

              {reports.isError && (
                <p role="alert">
                  Unable to load reports. Check the API and try again.
                </p>
              )}

              {reports.isSuccess && reports.data.items.length === 0 && (
                <p>No reports yet. Upload your first report.</p>
              )}

              {reports.isSuccess && reports.data.items.length > 0 && (
                <ul>
                  {reports.data.items.map((report) => (
                    <li key={report.id}>
                      <button
                        type="button"
                        onClick={() => setSelectedReportId(report.id)}
                      >
                        {report.original_filename} â€” {report.status}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          )}


    </main>
  );
}
