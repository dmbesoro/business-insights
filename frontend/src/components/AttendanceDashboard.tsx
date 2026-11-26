import { useQuery } from "@tanstack/react-query";
import { getAttendanceDashboard } from "../api/reports";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
} from "recharts";

export default function AttendanceDashboard() {
  const dashboard = useQuery({
    queryKey: ["dashboard", "attendance"],
    queryFn: getAttendanceDashboard,
  });

  if (dashboard.isPending) {
    return <p>Loading attendance dashboard...</p>;
  }

  if (dashboard.isError) {
    return (
      <p role="alert">
        Unable to load attendance dashboard.
      </p>
    );
  }

  const { summary, status_breakdown, trends } = dashboard.data;

  return (
    <main>
      <h2>Attendance Dashboard</h2>

      <section className="panel">
        <h3>Attendance Summary</h3>

        <p>Total Records: {summary.total_records}</p>
        <p>Attendance Rate: {summary.attendance_rate}%</p>
        <p>Absences: {summary.absences}</p>
        <p>Late Arrivals: {summary.late_arrivals}</p>
      </section>

      <section className="panel">
        <h3>Attendance Status Breakdown</h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={status_breakdown}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="status" />
            <YAxis />
            <Tooltip />

            <Bar dataKey="count" fill="#2563eb" name="Records" />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="panel">
        <h3>Attendance Trends</h3>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trends}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip />
            <Legend />

            <Line
              type="monotone"
              dataKey="present"
              stroke="#16a34a"
              name="Present"
            />

            <Line
              type="monotone"
              dataKey="absent"
              stroke="#dc2626"
              name="Absent"
            />

            <Line
              type="monotone"
              dataKey="late"
              stroke="#d97706"
              name="Late"
            />
          </LineChart>
        </ResponsiveContainer>
      </section>
    </main>
  );
}