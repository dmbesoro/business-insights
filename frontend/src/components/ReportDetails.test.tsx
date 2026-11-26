
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import ReportDetails from "./ReportDetails";
import { getReport, getReportRecords } from "../api/reports";

vi.mock("../api/reports", () => ({
  getReport: vi.fn(),
  getReportRecords: vi.fn(),
}));

describe("ReportDetails", () => {
  it("displays report metadata and records", async () => {
    vi.mocked(getReport).mockResolvedValue({
      id: 1,
      original_filename: "sales-report.csv",
      status: "DONE",
      report_type: "FINANCIAL",
      file_size_bytes: 1024,
      created_at: "2026-11-27T10:00:00Z",
      updated_at: "2026-11-27T10:05:00Z",
      error_message: null,
    });

    vi.mocked(getReportRecords).mockResolvedValue({
      items: [
        {
          id: 1,
          row_number: 2,
          normalized_data: { amount: 1500 },
          is_valid: true,
          validation_errors: [],
        },
      ],
      page: 1,
      page_size: 20,
      total: 1,
      total_pages: 1,
    });

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ReportDetails reportId={1} onBack={vi.fn()} />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("sales-report.csv")
    ).toBeInTheDocument();

    expect(screen.getByText("Status: DONE")).toBeInTheDocument();
    expect(screen.getByText("Type: FINANCIAL")).toBeInTheDocument();
    expect(
      await screen.findByText("Total records: 1")
    ).toBeInTheDocument();
    expect(screen.getAllByText("Valid").length).toBeGreaterThan(0);
    expect(screen.getByText(/1500/)).toBeInTheDocument();
  });

  it("filters records to show rejected records", async () => {
    vi.mocked(getReport).mockResolvedValue({
      id: 1,
      original_filename: "sales-report.csv",
      status: "DONE",
      report_type: "FINANCIAL",
      file_size_bytes: 1024,
      created_at: "2026-11-27T10:00:00Z",
      updated_at: "2026-11-27T10:05:00Z",
      error_message: null,
    });

    vi.mocked(getReportRecords).mockResolvedValue({
      items: [],
      page: 1,
      page_size: 20,
      total: 0,
      total_pages: 0,
    });

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ReportDetails reportId={1} onBack={vi.fn()} />
      </QueryClientProvider>
    );

    await screen.findByText("Total records: 0");

    fireEvent.click(screen.getByRole("button", { name: "Rejected" }));

    await waitFor(() => {
      expect(getReportRecords).toHaveBeenLastCalledWith(1, 1, 20, false);
    });
  });

  it("loads the next page when Next is clicked", async () => {
    vi.mocked(getReport).mockResolvedValue({
      id: 1,
      original_filename: "sales-report.csv",
      status: "DONE",
      report_type: "FINANCIAL",
      file_size_bytes: 1024,
      created_at: "2026-11-27T10:00:00Z",
      updated_at: "2026-11-27T10:05:00Z",
      error_message: null,
    });

    vi.mocked(getReportRecords).mockImplementation(
      async (_id, page) => ({
        items: [],
        page: page ?? 1,
        page_size: 20,
        total: 40,
        total_pages: 2,
      })
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ReportDetails reportId={1} onBack={vi.fn()} />
      </QueryClientProvider>
    );

    await screen.findByText(/Page 1 of 2/);

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    expect(await screen.findByText(/Page 2 of 2/)).toBeInTheDocument();

    await waitFor(() => {
      expect(getReportRecords).toHaveBeenLastCalledWith(1, 2, 20, undefined);
    });
  });
});
