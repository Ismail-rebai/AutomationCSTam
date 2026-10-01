"""
RAG FastAPI service.

Endpoints:
  POST /search          — hybrid search over the KB
  POST /match-tender    — per-requirement matching for a structured tender
  GET  /health          — health check
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from .dashboard_data import BENCHMARK_TENDERS
from .documents import KBRecord, load_all_records
from .embeddings import get_backend
from .hybrid_index import HybridIndex, SearchResult
from .proposal_generator import ProposalDeckData, generate_proposal_deck_data
from .pptx_builder import build_proposal_presentation

logger = logging.getLogger(__name__)

# --- Global index (initialized at startup) ---
_index: Optional[HybridIndex] = None


def _build_index() -> HybridIndex:
    """Build the hybrid index from KB data."""
    backend = get_backend()
    records = load_all_records()
    index = HybridIndex(backend=backend)
    index.build(records)
    return index


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: build index on startup."""
    global _index
    logger.info("Building RAG index...")
    _index = _build_index()
    logger.info("RAG index ready (%d records)", _index.record_count)
    yield
    logger.info("RAG service shutting down")


app = FastAPI(
    title="OliveSoft RAG Service",
    description="Hybrid search (dense + BM25) over OliveSoft's internal knowledge base",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Request / Response Models ---


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    asset_type: Optional[str] = None  # cv | past_project | client | tech_stack
    dense_weight: Optional[float] = None
    fusion_method: Optional[str] = None  # rrf | weighted
    rerank: bool = False


class SearchResultItem(BaseModel):
    record_id: str
    record_type: str
    score: float
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    count: int
    backend: str
    fusion_method: str


class RequirementInput(BaseModel):
    req_id: str
    text: str
    category: Optional[str] = None
    tech_keywords: List[str] = Field(default_factory=list)


class MatchTenderRequest(BaseModel):
    """Input for tender matching."""
    tender_id: Optional[str] = None  # if stored, fetch from ingest DB
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[RequirementInput]] = None
    top_k: int = 5  # per requirement, per type


class RequirementMatch(BaseModel):
    req_id: str
    req_text: str
    matches: List[SearchResultItem]
    best_score: float
    coverage: str  # covered | partial | not_covered


class CoverageCell(BaseModel):
    req_id: str
    asset_id: str
    asset_type: str
    score: float
    status: str  # covered | partial | not_covered


class StaffingSuggestion(BaseModel):
    cv_id: str
    name: str
    title: str
    requirements_covered: List[str]
    coverage_count: int
    skills_matched: List[str]
    skills_gap: List[str]


class MatchTenderResponse(BaseModel):
    tender_id: str
    title: Optional[str] = None
    requirement_matches: List[RequirementMatch]
    coverage_matrix: List[CoverageCell]
    fit_score: float  # 0.0 to 1.0
    no_match: bool
    covered_count: int
    partial_count: int
    not_covered_count: int
    total_requirements: int
    staffing_suggestions: List[StaffingSuggestion] = Field(default_factory=list)


# --- Threshold calibration ---
# These thresholds are calibrated from the gold set.
# RRF scores: covered > 0.025, partial > 0.015, not_covered <= 0.015
# Weighted scores: covered > 0.3, partial > 0.15, not_covered <= 0.15
# We use RRF as default, so thresholds are for RRF scores.

COVERAGE_THRESHOLDS = {
    "rrf": {"covered": 0.025, "partial": 0.020},
    "weighted": {"covered": 0.3, "partial": 0.15},
}


def _get_thresholds(fusion_method: str) -> dict:
    return COVERAGE_THRESHOLDS.get(fusion_method, COVERAGE_THRESHOLDS["rrf"])


# --- Endpoints ---


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "index_size": _index.record_count if _index else 0,
        "backend": _index.backend.name if _index else "not_initialized",
    }


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if _index is None:
        raise HTTPException(status_code=503, detail="Index not ready")

    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = _index.search(
        query=req.query,
        top_k=req.top_k,
        asset_type=req.asset_type,
        dense_weight=req.dense_weight,
        fusion_method=req.fusion_method,
        rerank=req.rerank,
    )

    return SearchResponse(
        query=req.query,
        results=[
            SearchResultItem(
                record_id=r.record_id,
                record_type=r.record_type,
                score=round(r.score, 6),
                text=r.text[:500],
                metadata=r.metadata,
            )
            for r in results
        ],
        count=len(results),
        backend=_index.backend.name,
        fusion_method=_index.fusion_method,
    )


@app.post("/match-tender", response_model=MatchTenderResponse)
async def match_tender(req: MatchTenderRequest):
    """
    Match a structured tender against the KB.

    For each requirement: retrieve top-k per asset type, compute coverage.
    Returns coverage matrix, fit score, staffing suggestions.
    """
    if _index is None:
        raise HTTPException(status_code=503, detail="Index not ready")

    # Get requirements
    requirements = req.requirements
    if not requirements and req.description:
        try:
            from src.structuring import structure_tender
            structured = await structure_tender({
                "tender_id": req.tender_id or "UNKNOWN",
                "title": req.title or "",
                "description": req.description
            })
            if structured and structured.requirements:
                requirements = [
                    RequirementInput(
                        req_id=r.req_id,
                        text=r.text,
                        category=r.category,
                        tech_keywords=r.tech_keywords
                    )
                    for r in structured.requirements
                ]
            else:
                requirements = [
                    RequirementInput(
                        req_id="REQ-1",
                        text=req.description,
                        category="technical",
                        tech_keywords=[]
                    )
                ]
        except Exception as e:
            logger.warning("Structuring failed (%s), fallback to raw description", e)
            requirements = [
                RequirementInput(
                    req_id="REQ-1",
                    text=req.description,
                    category="technical",
                    tech_keywords=[]
                )
            ]

    if not requirements and req.tender_id:
        # Try to load from ingest DB
        raise HTTPException(
            status_code=400,
            detail="Provide requirements or description directly, or ensure tender is stored and structured."
        )

    if not requirements:
        raise HTTPException(
            status_code=400,
            detail="No requirements provided. Supply requirements list, a tender description, or a valid tender_id."
        )

    fm = _index.fusion_method
    thresholds = _get_thresholds(fm)

    asset_types = ["cv", "past_project", "client", "tech_stack"]
    requirement_matches: List[RequirementMatch] = []
    coverage_matrix: List[CoverageCell] = []
    cv_coverage: Dict[str, Dict] = {}  # cv_id -> {reqs covered, skills matched}

    for r in requirements:
        # Search across all types
        all_matches: List[SearchResult] = []
        for atype in asset_types:
            type_results = _index.search(
                query=r.text,
                top_k=req.top_k,
                asset_type=atype,
            )
            all_matches.extend(type_results)

        # Sort by score
        all_matches.sort(key=lambda m: m.score, reverse=True)
        top_matches = all_matches[: req.top_k * 2]  # Keep reasonable number

        best_score = top_matches[0].score if top_matches else 0.0

        # Determine coverage status
        if best_score >= thresholds["covered"]:
            coverage = "covered"
        elif best_score >= thresholds["partial"]:
            coverage = "partial"
        else:
            coverage = "not_covered"

        # Build result items
        match_items = [
            SearchResultItem(
                record_id=m.record_id,
                record_type=m.record_type,
                score=round(m.score, 6),
                text=m.text[:300],
                metadata=m.metadata,
            )
            for m in top_matches[:req.top_k]
        ]

        requirement_matches.append(
            RequirementMatch(
                req_id=r.req_id,
                req_text=r.text,
                matches=match_items,
                best_score=round(best_score, 6),
                coverage=coverage,
            )
        )

        # Coverage matrix: best match per type
        seen_types = set()
        for m in top_matches:
            if m.record_type not in seen_types:
                seen_types.add(m.record_type)
                cell_status = (
                    "covered" if m.score >= thresholds["covered"]
                    else "partial" if m.score >= thresholds["partial"]
                    else "not_covered"
                )
                coverage_matrix.append(
                    CoverageCell(
                        req_id=r.req_id,
                        asset_id=m.record_id,
                        asset_type=m.record_type,
                        score=round(m.score, 6),
                        status=cell_status,
                    )
                )

        # Track CV coverage for staffing
        for m in top_matches:
            if m.record_type == "cv" and m.score >= thresholds["partial"]:
                if m.record_id not in cv_coverage:
                    cv_coverage[m.record_id] = {
                        "name": m.metadata.get("name", ""),
                        "title": m.metadata.get("title", ""),
                        "skills": set(m.metadata.get("skills", [])),
                        "reqs": [],
                    }
                cv_coverage[m.record_id]["reqs"].append(r.req_id)

    # Compute stats
    covered_count = sum(1 for rm in requirement_matches if rm.coverage == "covered")
    partial_count = sum(1 for rm in requirement_matches if rm.coverage == "partial")
    not_covered_count = sum(1 for rm in requirement_matches if rm.coverage == "not_covered")
    total = len(requirements)

    fit_score = (covered_count + 0.5 * partial_count) / total if total > 0 else 0.0
    no_match = covered_count == 0 and partial_count == 0

    # Staffing suggestions
    staffing: List[StaffingSuggestion] = []
    # Collect all tech keywords from requirements
    all_tech_keywords = set()
    for r in requirements:
        all_tech_keywords.update(kw.lower() for kw in r.tech_keywords)

    for cv_id, info in sorted(cv_coverage.items(), key=lambda x: len(x[1]["reqs"]), reverse=True):
        cv_skills_lower = {s.lower() for s in info["skills"]}
        matched_skills = list(all_tech_keywords & cv_skills_lower)
        gap_skills = list(all_tech_keywords - cv_skills_lower)

        staffing.append(
            StaffingSuggestion(
                cv_id=cv_id,
                name=info["name"],
                title=info["title"],
                requirements_covered=list(set(info["reqs"])),
                coverage_count=len(set(info["reqs"])),
                skills_matched=matched_skills,
                skills_gap=gap_skills,
            )
        )

    return MatchTenderResponse(
        tender_id=req.tender_id or "unknown",
        title=req.title,
        requirement_matches=requirement_matches,
        coverage_matrix=coverage_matrix,
        fit_score=round(fit_score, 4),
        no_match=no_match,
        covered_count=covered_count,
        partial_count=partial_count,
        not_covered_count=not_covered_count,
        total_requirements=total,
        staffing_suggestions=staffing,
    )


# --- Proposal PowerPoint Presentation Generation ---

PROPOSALS_DIR = Path(os.getenv("RESULTS_DIR", "results")) / "proposals"


class GenerateDeckRequest(BaseModel):
    tender_id: str
    title: str
    client: Optional[str] = "Organisme Contractant"
    requirements: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    staffing_matches: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    fit_score: Optional[float] = 1.0


class GenerateDeckResponse(BaseModel):
    tender_id: str
    title: str
    client_name: str
    file_path: str
    file_name: str
    download_url: str
    total_price_tnd: float
    total_duration_weeks: int
    fit_score: float
    phases_count: int
    slides_count: int = 8
    proposal_data: ProposalDeckData


@app.post("/proposals/generate-deck", response_model=GenerateDeckResponse)
def generate_proposal_deck(req: GenerateDeckRequest) -> GenerateDeckResponse:
    """
    Generate an executive 8-slide PowerPoint (.pptx) presentation for a tender.
    Synthesizes technical solution, step-by-step 5-phase realization,
    timeline duration, and role-based TND pricing breakdown.
    """
    PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    clean_id = req.tender_id.replace("/", "_").replace("\\", "_").replace(" ", "_").strip()
    file_name = f"{clean_id}_OliveSoft_Proposal.pptx"
    output_path = PROPOSALS_DIR / file_name

    # Run multi-agent proposal synthesis
    proposal_data = generate_proposal_deck_data(
        tender_id=req.tender_id,
        title=req.title,
        client=req.client,
        requirements=req.requirements,
        staffing_matches=req.staffing_matches,
        fit_score=req.fit_score or 1.0,
    )

    # Compile .pptx file
    build_proposal_presentation(proposal_data, str(output_path))

    return GenerateDeckResponse(
        tender_id=req.tender_id,
        title=req.title,
        client_name=proposal_data.client_name,
        file_path=str(output_path),
        file_name=file_name,
        download_url=f"/proposals/download/{clean_id}",
        total_price_tnd=proposal_data.pricing.total_price_tnd,
        total_duration_weeks=proposal_data.total_duration_weeks,
        fit_score=proposal_data.fit_score,
        phases_count=len(proposal_data.phases),
        slides_count=8,
        proposal_data=proposal_data,
    )


@app.get("/proposals/download/{tender_id}")
def download_proposal_deck(tender_id: str):
    """Download the generated PowerPoint (.pptx) file for a given tender."""
    clean_id = tender_id.replace("/", "_").replace("\\", "_").replace(" ", "_").strip()
    file_name = f"{clean_id}_OliveSoft_Proposal.pptx"
    file_path = PROPOSALS_DIR / file_name

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Proposal presentation for tender '{tender_id}' not found. Generate it first via POST /proposals/generate-deck",
        )

    return FileResponse(
        path=str(file_path),
        filename=file_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )


# --- Sales & Commercial Review Dashboard (Person C & Phase 3) ---

TEMPLATES_DIR = Path(__file__).parent / "templates"


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    """Serve the OliveSoft RFP Intelligence & Proposal Review Dashboard."""
    dashboard_file = TEMPLATES_DIR / "dashboard.html"
    if not dashboard_file.exists():
        raise HTTPException(status_code=404, detail="Dashboard template not found")
    return HTMLResponse(content=dashboard_file.read_text(encoding="utf-8"))


@app.get("/", response_class=RedirectResponse)
def root_redirect():
    """Redirect root to /dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/api/benchmark-tenders")
def list_benchmark_tenders():
    """Return pre-structured benchmark tenders with prospect dossiers and coverage data."""
    return BENCHMARK_TENDERS


def get_index() -> Optional[HybridIndex]:
    """Get the current index (for testing/scripts)."""
    return _index

