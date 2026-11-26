import { useQuery } from "@tanstack/react-query";
import { getFinancialDashboard } from "../api/reports";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
Bar,
} from "recharts";

export default function FinancialDashboard() {
  const dashboard = useQuery({
    queryKey: ["dashboard", "financial"],
    queryFn: getFinancialDashboard,
  });

  if (dashboard.isPending) {
    return <p>Loading financial dashboard...</p>;
  }

  if (dashboard.isError) {
    return (
      <p role="alert">
        Unable to load financial dashboard.
      </p>
    );
  }

  const { summary, trends, expenses_by_category } = dashboard.data;

  return (
    <main>
      <h2>Financial Dashboard</h2>

      <section className="panel">
        <h3>Financial Summary</h3>

        <p>Total Revenue: {summary.total_revenue}</p>
        <p>Total Expenses: {summary.total_expenses}</p>
        <p>Net Income: {summary.net_income}</p>
        <p>Transactions: {summary.transaction_count}</p>
      </section>

      <section className="panel">
        <h3>Revenue vs Expenses</h3>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />

            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#2563eb"
              name="Revenue"
            />

            <Line
              type="monotone"
              dataKey="expenses"
              stroke="#dc2626"
              name="Expenses"
            />
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="panel">
        <h3>Expenses by Category</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={expenses_by_category}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" />
            <YAxis />
            <Tooltip />

            <Bar
              dataKey="total_expenses"
              fill="#2563eb"
              name="Expenses"
            />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </main>
  );
}
