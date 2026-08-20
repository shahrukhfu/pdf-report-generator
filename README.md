![PDF Report Generator Banner](banner.svg)

An automated PDF report generation and streaming service engineered with **FastAPI**, **Playwright (Chromium)**, and **SQLite**. The system aggregates sales datasets using optimized SQL queries, constructs responsive HTML templates governed by strict print CSS rules, renders multi-page PDF documents via headless Chromium, and serves them through the "Store and Link" pattern.

---

## Architecture Breakdown

![Pipeline Workflow](pipeline.svg)

1. **Query**: Aggregates ~200 order records from `report.db` into core performance metrics, top product rankings, daily revenue trends, and detailed order rows.
2. **Render**: Injects aggregated data into an HTML document configured with `@page` styling, `thead` repetition rules, and page-break isolation (`break-inside: avoid`).
3. **Store**: Spawns headless Chromium via Playwright, renders HTML to A4 PDF, saves to disk (`reports/<id>.pdf`), and logs metadata in the database `reports` table.
4. **Serve**: Exposes REST endpoints to query report status or stream PDF binary streams directly (`GET /reports/{id}/file`).

---

## Setup and Installation

### 1. Environment Preparation

```bash
# Clone the repository
git clone https://github.com/shahrukhfu/pdf-report-generator.git
cd "PDF Report Generator"

# Install Python dependencies
pip install fastapi uvicorn playwright pypdf

# Install headless Chromium browser
playwright install chromium
```

### 2. Database Seeding

Initialize and populate `report.db` with ~200 randomized sales records:

```bash
python seed.py
```

### 3. Launch Web Server

```bash
uvicorn main:app --reload
```
Server active at: `http://127.0.0.1:8000`

---

## Data Aggregation SQL Queries

The core data pipeline executes four distinct SQL queries in `report_data.py`:

* **Total Orders**:
  ```sql
  SELECT COUNT(*) FROM orders;
  ```

* **Total Revenue**:
  ```sql
  SELECT SUM(amount) FROM orders;
  ```

* **Top 5 Products by Revenue**:
  ```sql
  SELECT product, SUM(amount) AS total_sales, COUNT(*) AS count 
  FROM orders 
  GROUP BY product 
  ORDER BY total_sales DESC 
  LIMIT 5;
  ```

* **Daily Orders (Last 7 Days)**:
  ```sql
  SELECT date(created_at) AS day, COUNT(*) AS order_count, SUM(amount) AS daily_revenue 
  FROM orders 
  GROUP BY date(created_at) 
  ORDER BY day DESC 
  LIMIT 7;
  ```

---

## API Documentation & cURL Verification

### Health Endpoint
```bash
curl -X GET http://127.0.0.1:8000/health
```
**Response (200 OK):**
```json
{"status": "ok"}
```

### Generate Report (POST /reports)

* **Standard Deduplicated Request:**
  ```bash
  curl -X POST http://127.0.0.1:8000/reports
  ```
  *Returns an existing report generated today with status `200 OK`, or creates a new report returning `201 Created`.*

* **Forced Generation Request:**
  ```bash
  curl -X POST http://127.0.0.1:8000/reports \
    -H "Content-Type: application/json" \
    -d '{"force": true}'
  ```

**Response (201 Created / 200 OK):**
```json
{
  "id": 1,
  "file": "/reports/1/file",
  "created_at": "2026-08-20 22:16:21"
}
```

### Report Metadata (GET /reports/{id})
```bash
curl -X GET http://127.0.0.1:8000/reports/1
```
**Response (200 OK):**
```json
{
  "id": 1,
  "path": "reports/1.pdf",
  "file": "/reports/1/file",
  "created_at": "2026-08-20 22:16:21"
}
```

### Download PDF File (GET /reports/{id}/file)
```bash
curl -X GET http://127.0.0.1:8000/reports/1/file --output report_download.pdf
```

---

## Technical & Architectural Insights

1. **Synchronous PDF Rendering Latency & Queue Offloading**:
   Executing headless browser invocations synchronously within an HTTP request lifecycle introduces significant latency (500ms–2000ms+ per document). Under elevated concurrency, synchronous Playwright rendering consumes substantial CPU cores and worker threads, causing queue congestion and request timeouts. To maintain high availability and responsiveness, production systems offload PDF rendering tasks to an asynchronous background worker queue (such as Celery, RQ, or ARQ), returning an immediate `202 Accepted` job token to the client.

2. **Idempotency & Cost Optimization**:
   Implementing date-bounded deduplication on report generation requests prevents redundant Chromium rendering cycles for identical daily windows. Re-serving cached report assets eliminates unnecessary CPU processing, lowers disk I/O load, and optimizes storage resource utilization.

---

## Report Output Sample

Below is an exported preview of Page 1 of the generated PDF document:

![Report Preview Page 1](report_preview.png)
