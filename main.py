import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

from report_data import get_report_data
from renderer import generate_report_html, render_pdf

DB_NAME = "report.db"
REPORTS_DIR = "reports"

app = FastAPI(title="PDF Report Generator API")


def init_db():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/reports", status_code=status.HTTP_201_CREATED)
async def create_report():
    init_db()
    
    # 1. Fetch aggregated data & generate HTML
    data = get_report_data(DB_NAME)
    html_content = generate_report_html(data)

    # 2. Insert record into DB to acquire ID
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", ("", created_at))
    report_id = cursor.lastrowid
    
    pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
    cursor.execute("UPDATE reports SET path = ? WHERE id = ?", (pdf_path, report_id))
    conn.commit()
    conn.close()

    # 3. Render PDF to disk
    await render_pdf(html_content, pdf_path)

    # 4. Return 201 response with link
    return {
        "id": report_id,
        "file": f"/reports/{report_id}/file",
        "created_at": created_at
    }


@app.get("/reports/{report_id}")
def get_report_metadata(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, path, created_at FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    return {
        "id": row["id"],
        "path": row["path"],
        "file": f"/reports/{row['id']}/file",
        "created_at": row["created_at"]
    }


@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, path FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_path = row["path"]
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Report file does not exist on disk")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"report_{report_id}.pdf"
    )
