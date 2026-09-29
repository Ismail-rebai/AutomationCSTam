"""
Tender ingestion FastAPI service.

Endpoints:
  POST /tenders/ingest     — ingest one or more tender items (dedup by id)
  POST /tenders/structure  — structure a raw tender via LLM
  GET  /tenders            — list all ingested tenders
  GET  /tenders/{tender_id} — get a specific tender
  GET  /health             — health check

Storage: SQLite (replaces JSONL to fix O(n²) dedup).
"""

import json
import logging
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .structuring import StructuredTender, structure_tender, _create_fallback

logger = logging.getLogger(__name__)

# --- SQLite storage ---

DB_PATH = os.getenv("INGEST_DB_PATH", "data/ingest.db")


def _get_db() -> sqlite3.Connection:
    """Get a SQLite connection with WAL mode for concurrent access."""
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    """Create tables if they don't exist."""
    conn = _get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            tender_id TEXT PRIMARY KEY,
            source TEXT,
            raw_data TEXT NOT NULL,
            structured_data TEXT,
            structuring_status TEXT DEFAULT 'pending',
            ingested_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tenders_source
        ON tenders(source)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_tenders_status
        ON tenders(structuring_status)
    """)
    conn.commit()
    conn.close()
    logger.info("Ingest DB initialized at %s", DB_PATH)


# --- FastAPI app ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB on startup."""
    _init_db()
    yield
    logger.info("Ingest service shutting down")


app = FastAPI(
    title="OliveSoft Tender Ingest Service",
    description="Ingestion and structuring of tender/RFP data",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Request / Response Models ---


class TenderItem(BaseModel):
    """Raw tender item as received from n8n workflow."""
    id: Optional[str] = None
    tender_id: Optional[str] = None
    source: Optional[str] = None
    domain: Optional[str] = None
    description: Optional[str] = None
    title: Optional[str] = None
    reference: Optional[str] = None
    country: Optional[str] = None
    published_date: Optional[str] = None
    publication_date: Optional[str] = None
    deadline: Optional[str] = None
    submission_deadline: Optional[str] = None
    url: Optional[str] = None
    buyer: Optional[str] = None
    detected_at: Optional[str] = None
    status: Optional[str] = None
    llm_classified: Optional[bool] = None
    relevance_source: Optional[str] = None
    language: Optional[str] = "fr"

    # Allow extra fields
    model_config = {"extra": "allow"}


class IngestRequest(BaseModel):
    items: List[TenderItem] = Field(default_factory=list)
    # Also accept a single item
    item: Optional[TenderItem] = None


class IngestResult(BaseModel):
    tender_id: str
    status: str  # new | duplicate | error
    message: str


class IngestResponse(BaseModel):
    results: List[IngestResult]
    new_count: int
    duplicate_count: int
    error_count: int


class TenderRecord(BaseModel):
    tender_id: str
    source: Optional[str] = None
    raw_data: Dict[str, Any]
    structured_data: Optional[Dict[str, Any]] = None
    structuring_status: str
    ingested_at: str
    updated_at: Optional[str] = None


class StructureRequest(BaseModel):
    tender_id: str  # ID of already-ingested tender to structure
    force: bool = False  # re-structure even if already done


class StructureResponse(BaseModel):
    tender_id: str
    structuring_status: str
    structured_data: Optional[Dict[str, Any]] = None
    message: str


# --- Endpoints ---


@app.get("/health")
async def health():
    conn = _get_db()
    count = conn.execute("SELECT COUNT(*) FROM tenders").fetchone()[0]
    conn.close()
    return {
        "status": "healthy",
        "tender_count": count,
        "db_path": DB_PATH,
    }


@app.post("/tenders/ingest", response_model=IngestResponse)
async def ingest(req: IngestRequest):
    """Ingest one or more tender items. Deduplicates by tender_id."""
    items = list(req.items)
    if req.item:
        items.append(req.item)

    if not items:
        raise HTTPException(status_code=400, detail="No items to ingest")

    conn = _get_db()
    results: List[IngestResult] = []
    new_count = 0
    dup_count = 0
    err_count = 0

    structure_on_ingest = os.getenv("STRUCTURE_ON_INGEST", "false").lower() == "true"

    for item in items:
        tender_id = item.tender_id or item.id
        if not tender_id:
            err_count += 1
            results.append(IngestResult(
                tender_id="UNKNOWN",
                status="error",
                message="Missing tender_id/id field",
            ))
            continue

        try:
            # Check for duplicate
            existing = conn.execute(
                "SELECT tender_id FROM tenders WHERE tender_id = ?",
                (tender_id,),
            ).fetchone()

            if existing:
                dup_count += 1
                results.append(IngestResult(
                    tender_id=tender_id,
                    status="duplicate",
                    message="Already ingested",
                ))
                continue

            # Serialize raw data
            raw_dict = item.model_dump(exclude_none=True)
            raw_json = json.dumps(raw_dict, ensure_ascii=False)

            now = datetime.now(timezone.utc).isoformat()

            # Optionally structure on ingest
            structured_json = None
            structuring_status = "pending"

            if structure_on_ingest:
                try:
                    structured = await structure_tender(raw_dict)
                    structured_json = structured.model_dump_json()
                    structuring_status = structured.structuring_status
                except Exception as e:
                    logger.warning("Structuring failed for %s: %s", tender_id, e)
                    fallback = _create_fallback(raw_dict)
                    structured_json = fallback.model_dump_json()
                    structuring_status = "fallback"

            conn.execute(
                """INSERT INTO tenders
                   (tender_id, source, raw_data, structured_data,
                    structuring_status, ingested_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (tender_id, item.source, raw_json, structured_json,
                 structuring_status, now),
            )

            new_count += 1
            results.append(IngestResult(
                tender_id=tender_id,
                status="new",
                message=f"Ingested (structuring: {structuring_status})",
            ))

        except Exception as e:
            err_count += 1
            logger.error("Ingest error for %s: %s", tender_id, e)
            results.append(IngestResult(
                tender_id=tender_id or "UNKNOWN",
                status="error",
                message=str(e),
            ))

    conn.commit()
    conn.close()

    return IngestResponse(
        results=results,
        new_count=new_count,
        duplicate_count=dup_count,
        error_count=err_count,
    )


@app.post("/tenders/structure", response_model=StructureResponse)
async def structure_endpoint(req: StructureRequest):
    """Structure (or re-structure) an already-ingested tender."""
    conn = _get_db()

    row = conn.execute(
        "SELECT tender_id, raw_data, structuring_status FROM tenders WHERE tender_id = ?",
        (req.tender_id,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Tender {req.tender_id} not found in ingest DB",
        )

    if row["structuring_status"] == "success" and not req.force:
        conn.close()
        return StructureResponse(
            tender_id=req.tender_id,
            structuring_status="success",
            structured_data=json.loads(row["raw_data"]),
            message="Already structured. Use force=true to re-structure.",
        )

    raw_data = json.loads(row["raw_data"])

    try:
        structured = await structure_tender(raw_data)
        structured_dict = structured.model_dump()
        structured_json = json.dumps(structured_dict, ensure_ascii=False)

        conn.execute(
            """UPDATE tenders
               SET structured_data = ?, structuring_status = ?, updated_at = ?
               WHERE tender_id = ?""",
            (structured_json, structured.structuring_status,
             datetime.now(timezone.utc).isoformat(), req.tender_id),
        )
        conn.commit()
        conn.close()

        return StructureResponse(
            tender_id=req.tender_id,
            structuring_status=structured.structuring_status,
            structured_data=structured_dict,
            message=f"Structured via {structured.structuring_status}",
        )

    except Exception as e:
        conn.close()
        logger.error("Structuring failed for %s: %s", req.tender_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Structuring failed: {e}",
        )


@app.get("/tenders", response_model=List[TenderRecord])
async def list_tenders(
    source: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """List ingested tenders with optional filters."""
    conn = _get_db()

    query = "SELECT * FROM tenders WHERE 1=1"
    params: list = []

    if source:
        query += " AND source = ?"
        params.append(source)
    if status:
        query += " AND structuring_status = ?"
        params.append(status)

    query += " ORDER BY ingested_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    return [
        TenderRecord(
            tender_id=row["tender_id"],
            source=row["source"],
            raw_data=json.loads(row["raw_data"]),
            structured_data=json.loads(row["structured_data"]) if row["structured_data"] else None,
            structuring_status=row["structuring_status"],
            ingested_at=row["ingested_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


@app.get("/tenders/{tender_id}", response_model=TenderRecord)
async def get_tender(tender_id: str):
    """Get a specific tender by ID."""
    conn = _get_db()
    row = conn.execute(
        "SELECT * FROM tenders WHERE tender_id = ?",
        (tender_id,),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail=f"Tender {tender_id} not found")

    return TenderRecord(
        tender_id=row["tender_id"],
        source=row["source"],
        raw_data=json.loads(row["raw_data"]),
        structured_data=json.loads(row["structured_data"]) if row["structured_data"] else None,
        structuring_status=row["structuring_status"],
        ingested_at=row["ingested_at"],
        updated_at=row["updated_at"],
    )
