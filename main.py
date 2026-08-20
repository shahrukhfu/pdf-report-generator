import os
import sqlite3
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse

from report_data import get_report_data
from renderer import generate_report_html, render_pdf

DB_NAME = "report.db"
REPORTS_DIR = "reports"

app = FastAPI(title="PDF Report Generator API")


class ReportRequest(BaseModel):
    force: bool = False


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


@app.post("/reports")
async def create_report(req: Optional[ReportRequest] = None):
    init_db()
    force = req.force if req is not None else False
    today_str = datetime.now().strftime("%Y-%m-%d")

    # If force is False, check for existing report created today
    if not force:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, path, created_at FROM reports 
            WHERE date(created_at) = ? 
            ORDER BY id DESC LIMIT 1
        """, (today_str,))
        existing = cursor.fetchone()
        conn.close()

        if existing and os.path.exists(existing["path"]):
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "id": existing["id"],
                    "file": f"/reports/{existing['id']}/file",
                    "created_at": existing["created_at"]
                }
            )

    # Fetch aggregated data & generate HTML
    data = get_report_data(DB_NAME)
    html_content = generate_report_html(data)

    # Insert record into DB to acquire ID
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", ("", created_at))
    report_id = cursor.lastrowid
    
    pdf_path = os.path.join(REPORTS_DIR, f"{report_id}.pdf")
    cursor.execute("UPDATE reports SET path = ? WHERE id = ?", (pdf_path, report_id))
    conn.commit()
    conn.close()

    # Render PDF to disk
    await render_pdf(html_content, pdf_path)

    # Return 201 Created response
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "id": report_id,
            "file": f"/reports/{report_id}/file",
            "created_at": created_at
        }
    )


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
