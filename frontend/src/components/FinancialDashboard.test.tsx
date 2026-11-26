import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import FinancialDashboard from "./FinancialDashboard";
import { getFinancialDashboard } from "../api/reports";

vi.mock("../api/reports", () => ({
  getFinancialDashboard: vi.fn(),
}));

describe("FinancialDashboard", () => {
  it("displays financial summary data", async () => {
    vi.mocked(getFinancialDashboard).mockResolvedValue({
      summary: {
        total_revenue: 50000,
        total_expenses: 20000,
        net_income: 30000,
        transaction_count: 15,
      },
      trends: [
        { date: "2026-11-01", revenue: 25000, expenses: 10000 },
      ],
      expenses_by_category: [
        { category: "Operations", total_expenses: 20000 },
      ],
    } as Awaited<ReturnType<typeof getFinancialDashboard>>);

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <FinancialDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByText("Financial Dashboard")
    ).toBeInTheDocument();

    expect(screen.getByText("Total Revenue: 50000")).toBeInTheDocument();
    expect(screen.getByText("Total Expenses: 20000")).toBeInTheDocument();
    expect(screen.getByText("Net Income: 30000")).toBeInTheDocument();
    expect(screen.getByText("Transactions: 15")).toBeInTheDocument();

    expect(screen.getByText("Revenue vs Expenses")).toBeInTheDocument();
    expect(screen.getByText("Expenses by Category")).toBeInTheDocument();
  });

  it("displays a loading message while fetching data", () => {
    vi.mocked(getFinancialDashboard).mockReturnValue(
      new Promise(() => {})
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <FinancialDashboard />
      </QueryClientProvider>
    );

    expect(
      screen.getByText("Loading financial dashboard...")
    ).toBeInTheDocument();
  });

  it("displays an error message when fetching data fails", async () => {
    vi.mocked(getFinancialDashboard).mockRejectedValue(
      new Error("API unavailable")
    );

    const client = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={client}>
        <FinancialDashboard />
      </QueryClientProvider>
    );

    expect(
      await screen.findByRole("alert")
    ).toHaveTextContent("Unable to load financial dashboard.");
  });
});
