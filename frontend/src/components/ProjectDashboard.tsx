import { useQuery } from "@tanstack/react-query";
import { getProjectDashboard } from "../api/reports";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";

export default function ProjectDashboard() {
  const dashboard = useQuery({
    queryKey: ["dashboard", "projects"],
    queryFn: getProjectDashboard,
  });

  if (dashboard.isPending) {
    return <p>Loading project dashboard...</p>;
  }

  if (dashboard.isError) {
    return (
      <p role="alert">
        Unable to load project dashboard.
      </p>
    );
  }

  const { summary, tasks_by_status, progress_by_project } = dashboard.data;

  return (
    <main>
      <h2>Project Dashboard</h2>

      <section className="panel">
        <h3>Project Summary</h3>

        <p>Total Projects: {summary.total_projects}</p>
        <p>Total Tasks: {summary.total_tasks}</p>
        <p>Completed Tasks: {summary.completed_tasks}</p>
        <p>Overdue Tasks: {summary.overdue_tasks}</p>
        <p>Average Completion: {summary.average_completion}%</p>
      </section>

      <section className="panel">
        <h3>Tasks by Status</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={tasks_by_status}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="status" />
            <YAxis />
            <Tooltip />

            <Bar dataKey="count" fill="#2563eb" name="Tasks" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="panel">
        <h3>Progress by Project</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={progress_by_project}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="project" />
            <YAxis domain={[0, 100]} />
            <Tooltip formatter={(value) => `${value}%`} />

            <Bar
              dataKey="average_progress"
              fill="#16a34a"
              name="Completion"
            />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </main>
  );
}