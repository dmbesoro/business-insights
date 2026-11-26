# Business Insights

A full-stack data processing and analytics application that allows users to upload business reports, automatically classify and validate records, and explore the processed data through interactive dashboards.

Built as a full-stack coding exercise using React, FastAPI, PostgreSQL, Floci (local AWS service emulator), and Docker Compose.

## Features

### Report Processing
- Upload CSV and Excel reports.
- Store uploaded files in S3-compatible object storage.
- Process reports asynchronously through a message queue.
- Automatically classify supported business report types:
  - Financial
  - Attendance
  - Project Status
- Normalize extracted records into structured data.
- Validate records and identify rejected entries.
- Store processed records and validation results in PostgreSQL.
- Track report processing status and errors.

### Report Management
- View uploaded reports and their processing status.
- Inspect report metadata and processing results.
- Browse normalized records.
- Filter records by valid or rejected status.
- Navigate records using server-side pagination.

### Analytics Dashboards

Three dashboards provide summarized business insights:

**Financial Dashboard**
- Total revenue
- Total expenses
- Net income
- Transaction count
- Revenue and expense trends
- Expenses by category

**Attendance Dashboard**
- Total attendance records
- Attendance rate
- Absences
- Late arrivals
- Attendance status breakdown
- Attendance trends

**Project Dashboard**
- Total projects
- Total tasks
- Completed tasks
- Overdue tasks
- Average completion
- Tasks by status
- Progress by project

### Reliability
- Asynchronous report processing.
- Configurable retry and message delivery handling.
- Dead Letter Queue (DLQ) for messages that exhaust their delivery attempts.
- Failed report status tracking.
- Idempotent report persistence through record replacement,
  database uniqueness constraints, and transactional commits.
- Protection against reprocessing reports that have already
  reached a final state.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI data fetching | TanStack Query |
| State management | Zustand |
| Charts | Recharts |
| Backend | Python, FastAPI |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Object storage | Floci (S3-compatible) |
| Message queue | Floci (SQS-compatible) |
| Containerization | Docker, Docker Compose |
| Frontend testing | Vitest, React Testing Library |
| Backend testing | Pytest |

## Architecture

```text
                 User
                  |
                  v
          React Frontend
                  |
                  v
             FastAPI
                  |
          Upload Report
                  |
                  v
           Floci S3 Bucket
                  |
                  v
             Floci SQS Queue
                  |
                  v
          Processing Worker
                  |
        Extract / Classify
          Normalize / Validate
                  |
                  v
             PostgreSQL
                  |
                  v
          Dashboard APIs
                  |
                  v
          React Dashboards


       Failed Message Handling

             Floci SQS Queue
                  |
          Retry / Redelivery
                  |
                  v
          Floci DLQ Queue
                  |
                  v
              DLQ Worker
                  |
                  v
        Mark Report as FAILED
```

### Processing Workflow

1. The user uploads a CSV or Excel file through the frontend.
2. FastAPI validates the upload and stores the file in object storage.
3. A processing message containing the report identifier is published to the queue.
4. The background worker retrieves the message and downloads the uploaded file.
5. The worker extracts records and determines the report type.
6. Records are normalized and validated.
7. Valid and rejected records are persisted in PostgreSQL with their validation results.
8. The report status is updated as processing progresses.
9. The frontend retrieves report information and displays the results.
10. Dashboard APIs aggregate processed records for analytics.

### Failure Handling

The processing worker uses queue-based retries to handle transient processing failures.

Messages that exceed the configured delivery attempts are moved to the Dead Letter Queue. A separate DLQ worker consumes these messages and marks the corresponding report as `FAILED`.

This prevents repeatedly failing messages from blocking normal processing.

**Deployment note:** The current local implementation uses Docker-based background workers and Floci to emulate AWS S3 and SQS. It demonstrates asynchronous processing, message retries, and DLQ handling, but is not a deployed AWS Lambda integration or production AWS deployment.

## Getting Started

### Prerequisites

- Docker Desktop
- Docker Compose
- Git

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd business-insights
```

### 2. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Review `.env` and use local development credentials only.

On Windows PowerShell, you can use:

```powershell
Copy-Item .env.example .env
```

### 3. Start the application

```bash
docker compose up --build
```

### 4. Access the application

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| FastAPI documentation | http://localhost:8000/docs |
| API health check | http://localhost:8000/health |
| Floci (local AWS emulator) | http://localhost:4566 |

The local infrastructure initializes the following resources:

- S3 bucket: `business-insights`
- SQS queue: `report-processing`
- Dead Letter Queue: `report-processing-dlq`

## Running Tests

### Backend

```bash
docker compose exec backend pytest
```

### Frontend

```bash
docker compose exec frontend npm test
```

### Frontend production build

```bash
docker compose exec frontend npm run build
```

The frontend test suite currently contains 19 passing tests across 6 test files.

## Important Engineering Decisions

### Asynchronous Processing

File processing is separated from the upload request using a message queue.

This allows the API to respond without waiting for the entire processing pipeline to finish.

### Object Storage

Uploaded files are stored separately from the relational database. PostgreSQL stores report metadata and processed records rather than the original file contents.

### Retry and Dead Letter Queue

Transient failures can be retried without requiring users to upload the same file again. Messages that exhaust their delivery attempts are isolated through the DLQ.

### Server-Side Pagination

Report records are retrieved in pages instead of loading every record into the browser. This reduces unnecessary data transfer and frontend rendering overhead.

### Automated Testing

Backend and frontend tests help validate processing behavior, API interactions, component rendering, loading states, and error handling.

## Known Limitations and Future Improvements

- Configure and verify a real AWS deployment using S3, SQS, and Lambda with an event source mapping.
- Add authentication and role-based authorization.
- Improve structured logging, metrics, tracing, and operational monitoring.
- Add more extensive integration and end-to-end tests.
- Add deployment automation through CI/CD.
- Improve large-file processing and resource management.
- Add stronger production-grade idempotency and recovery guarantees.

## AI Usage Disclosure

AI-assisted development tools were used to support implementation, debugging, test development, and technical documentation.

Implementation decisions, code changes, and test results should be reviewed and validated by the developer.

## Security

- Do not commit `.env` files.
- Do not use real credentials in local development configuration.
- Use environment variables for sensitive configuration.
- Configure proper access controls and secrets management before deploying to production.

---

**Project:** Business Insights
**Purpose:** Full-Stack Coding Exercise
