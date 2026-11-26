import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  getReport,
  getReportRecords,
} from "../api/reports";

interface ReportDetailsProps {
  reportId: number;
  onBack: () => void;
}

export default function ReportDetails({
  reportId,
  onBack,
}: ReportDetailsProps) {
  const [page, setPage] = useState(1);
  const [filter, setFilter] = useState<
    "all" | "valid" | "rejected"
  >("all");

  const isValid =
    filter === "all"
      ? undefined
      : filter === "valid";

  const report = useQuery({
    queryKey: ["report", reportId],
    queryFn: () => getReport(reportId),
  });

  const records = useQuery({
    queryKey: ["report-records", reportId, page, filter],
    queryFn: () => getReportRecords(reportId, page, 20, isValid),
    enabled: report.data?.status === "DONE",
  });

  return (
    <main>
      <button type="button" onClick={onBack}>
        Back to reports
      </button>

      <h2>Report details</h2>

      {report.isPending && <p>Loading report...</p>}

      {report.isError && (
        <p role="alert">Unable to load report details.</p>
      )}

      {report.isSuccess && (
        <section className="panel">
          <h3>{report.data.original_filename}</h3>
          <p>Status: {report.data.status}</p>
          <p>Type: {report.data.report_type ?? "Not classified"}</p>
          <p>File size: {report.data.file_size_bytes} bytes</p>
        </section>
      )}

      {records.isPending && report.data?.status === "DONE" && (
        <p>Loading records...</p>
      )}

      {records.isError && (
        <p role="alert">Unable to load report records.</p>
      )}

      {records.isSuccess && (
        <section className="panel">
          <h3>Records</h3>

          <p>Total records: {records.data.total}</p>

          <div>
            <button
              type="button"
              onClick={() => {
                setFilter("all");
                setPage(1);
              }}
            >
              All
            </button>

            <button
              type="button"
              onClick={() => {
                setFilter("valid");
                setPage(1);
              }}
            >
              Valid
            </button>

            <button
              type="button"
              onClick={() => {
                setFilter("rejected");
                setPage(1);
              }}
            >
              Rejected
            </button>
          </div>

          {records.data.items.length === 0 ? (
            <p>No records found.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Normalized data</th>
                  <th>Validation</th>
                  <th>Errors</th>
                </tr>
              </thead>

              <tbody>
                {records.data.items.map((record) => (
                  <tr key={record.id}>
                    <td>{record.row_number}</td>
                    <td>
                      <pre>
                        {JSON.stringify(record.normalized_data, null, 2)}
                      </pre>
                    </td>
                    <td>
                      {record.is_valid ? "Valid" : "Rejected"}
                    </td>
                    <td>
                      {record.validation_errors.length > 0
                        ? record.validation_errors.join(", ")
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div>
            <button
              type="button"
              disabled={page <= 1}
              onClick={() => setPage((current) => current - 1)}
            >
              Previous
            </button>

            <span>
              Page {records.data.page} of {records.data.total_pages}
            </span>

            <button
              type="button"
              disabled={page >= records.data.total_pages}
              onClick={() => setPage((current) => current + 1)}
            >
              Next
            </button>
          </div>
        </section>
      )}
    </main>
  );
}