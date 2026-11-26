
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import AttendanceDashboard from "./AttendanceDashboard";
import { getAttendanceDashboard } from "../api/reports";

vi.mock("../api/reports", () => ({
  getAttendanceDashboard: vi.fn(),
}));

describe("AttendanceDashboard", () => {
  it("displays attendance summary data", async () => {
    vi.mocked(getAttendanceDashboard).mockResolvedValue({
      summary: {
        total_records: 100,
        attendance_rate: 95,
        absences: 5,
        late_arrivals: 8,
      },
      status_breakdown: [
        { status: "PRESENT", count: 87 },
        { status: "ABSENT", count: 5 },
        { status: "LATE", count: 8 },
      ],
      trends: [
        {
          date: "2026-11-01",
          present: 87,
          absent: 5,
          late: 8,
        },
      ],
    } as Awaited<ReturnType<typeof getAttendanceDashboard>>);

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <AttendanceDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("Attendance Dashboard")
    ).toBeInTheDocument();

    expect(screen.getByText("Total Records: 100")).toBeInTheDocument();
    expect(screen.getByText("Attendance Rate: 95%")).toBeInTheDocument();
    expect(screen.getByText("Absences: 5")).toBeInTheDocument();
    expect(screen.getByText("Late Arrivals: 8")).toBeInTheDocument();

    expect(screen.getByText("Attendance Status Breakdown")).toBeInTheDocument();
    expect(screen.getByText("Attendance Trends")).toBeInTheDocument();
  });

  it("displays a loading message while fetching data", () => {
    vi.mocked(getAttendanceDashboard).mockReturnValue(
      new Promise(() => {})
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <AttendanceDashboard />
      </QueryClientProvider>
    );

    expect(
      screen.getByText("Loading attendance dashboard...")
    ).toBeInTheDocument();
  });

  it("displays an error message when fetching data fails", async () => {
    vi.mocked(getAttendanceDashboard).mockRejectedValue(
      new Error("API unavailable")
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <AttendanceDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Unable to load attendance dashboard.");
  });
});
