
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import { getReports } from "./api/reports";

vi.mock("./api/reports", () => ({
  getReports: vi.fn(),
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows the workspace heading", () => {
    vi.mocked(getReports).mockResolvedValue({
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
        <App />
      </QueryClientProvider>
    );

    expect(screen.getByText("Report workspace")).toBeInTheDocument();
  });


  it("displays reports returned by the API", async () => {
    vi.mocked(getReports).mockResolvedValue({
      items: [
        {
          id: 1,
          original_filename: "sales-report.csv",
          status: "DONE",
          report_type: "FINANCIAL",
          created_at: "2026-11-27T10:00:00Z",
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
        <App />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("sales-report.csv — DONE")
    ).toBeInTheDocument();
  });

  it("displays an error when reports cannot be loaded", async () => {
    vi.mocked(getReports).mockRejectedValue(
      new Error("API unavailable")
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <App />
      </QueryClientProvider>
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent(
      "Unable to load reports. Check the API and try again."
    );
  });

  it("displays an empty-state message when there are no reports", async () => {
    vi.mocked(getReports).mockResolvedValue({
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
        <App />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("No reports yet. Upload your first report.")
    ).toBeInTheDocument();
  });
});
