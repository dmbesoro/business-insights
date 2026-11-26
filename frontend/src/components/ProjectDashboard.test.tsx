import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import ProjectDashboard from "./ProjectDashboard";
import { getProjectDashboard } from "../api/reports";

vi.mock("../api/reports", () => ({
  getProjectDashboard: vi.fn(),
}));

describe("ProjectDashboard", () => {
  it("displays project summary data", async () => {
    vi.mocked(getProjectDashboard).mockResolvedValue({
      summary: {
        total_projects: 10,
        total_tasks: 50,
        completed_tasks: 35,
        overdue_tasks: 3,
        average_completion: 70,
      },
      tasks_by_status: [
        { status: "COMPLETED", count: 35 },
        { status: "IN_PROGRESS", count: 10 },
        { status: "PENDING", count: 5 },
      ],
      progress_by_project: [
        { project: "Project Alpha", average_progress: 80 },
      ],
    } as Awaited<ReturnType<typeof getProjectDashboard>>);

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ProjectDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("Project Dashboard")
    ).toBeInTheDocument();

    expect(screen.getByText("Total Projects: 10")).toBeInTheDocument();
    expect(screen.getByText("Total Tasks: 50")).toBeInTheDocument();
    expect(screen.getByText("Completed Tasks: 35")).toBeInTheDocument();
    expect(screen.getByText("Overdue Tasks: 3")).toBeInTheDocument();
    expect(screen.getByText("Average Completion: 70%")).toBeInTheDocument();

    expect(screen.getByText("Tasks by Status")).toBeInTheDocument();
    expect(screen.getByText("Progress by Project")).toBeInTheDocument();
  });

  it("displays a loading message while fetching data", () => {
    vi.mocked(getProjectDashboard).mockReturnValue(
      new Promise(() => {})
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ProjectDashboard />
      </QueryClientProvider>
    );

    expect(
      screen.getByText("Loading project dashboard...")
    ).toBeInTheDocument();
  });

  it("displays an error message when fetching data fails", async () => {
    vi.mocked(getProjectDashboard).mockRejectedValue(
      new Error("API unavailable")
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <ProjectDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Unable to load project dashboard.");
  });
});
