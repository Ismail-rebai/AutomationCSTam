"""Tests for fusion methods, evaluation metrics, structuring, and APIs."""

import json
import math
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation import (
    hit_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


# ============================================================
# Evaluation Metrics Tests
# ============================================================


class TestPrecisionAtK:
    def test_all_relevant(self):
        assert precision_at_k(["A", "B", "C"], {"A", "B", "C"}, 3) == 1.0

    def test_none_relevant(self):
        assert precision_at_k(["X", "Y", "Z"], {"A", "B"}, 3) == 0.0

    def test_partial(self):
        assert precision_at_k(["A", "X", "B"], {"A", "B"}, 3) == pytest.approx(2 / 3)

    def test_k_smaller_than_results(self):
        assert precision_at_k(["A", "X", "B"], {"A", "B"}, 1) == 1.0

    def test_empty_retrieved(self):
        assert precision_at_k([], {"A"}, 5) == 0.0


class TestRecallAtK:
    def test_all_found(self):
        assert recall_at_k(["A", "B", "C"], {"A", "B"}, 3) == 1.0

    def test_none_found(self):
        assert recall_at_k(["X", "Y"], {"A", "B"}, 2) == 0.0

    def test_partial_recall(self):
        assert recall_at_k(["A", "X"], {"A", "B"}, 2) == 0.5

    def test_no_relevant(self):
        assert recall_at_k(["A", "B"], set(), 2) == 1.0


class TestMRR:
    def test_first_position(self):
        assert mrr(["A", "B", "C"], {"A"}) == 1.0

    def test_second_position(self):
        assert mrr(["X", "A", "C"], {"A"}) == 0.5

    def test_not_found(self):
        assert mrr(["X", "Y", "Z"], {"A"}) == 0.0


class TestNDCG:
    def test_perfect_ranking(self):
        assert ndcg_at_k(["A", "B"], {"A", "B"}, 2) == pytest.approx(1.0)

    def test_empty_results(self):
        assert ndcg_at_k([], {"A"}, 5) == 0.0

    def test_no_relevant(self):
        assert ndcg_at_k(["X", "Y"], set(), 2) == 1.0


class TestHitAtK:
    def test_hit_present(self):
        assert hit_at_k(["A", "B"], {"A"}, 2) is True

    def test_no_hit(self):
        assert hit_at_k(["X", "Y"], {"A"}, 2) is False

    def test_hit_with_min_score(self):
        assert hit_at_k(["A"], {"A"}, 1, scores=[0.5], min_score=0.0) is True
        assert hit_at_k(["A"], {"A"}, 1, scores=[0.0], min_score=0.0) is False


# ============================================================
# Structuring Tests (mocked LLM)
# ============================================================


class TestStructuringFallback:
    def test_fallback_no_api_key(self):
        """Structuring should produce valid fallback without API key."""
        from src.structuring import _create_fallback

        raw = {
            "tender_id": "TEST-001",
            "description": "Acquisition de matériels informatiques",
            "buyer": "Ministère Test",
            "source": "simulated",
        }

        result = _create_fallback(raw)

        assert result.tender_id == "TEST-001"
        assert result.structuring_status == "fallback"
        assert len(result.requirements) == 1
        assert result.requirements[0].text == raw["description"]
        assert result.buyer.name == "Ministère Test"

    def test_fallback_missing_fields(self):
        """Fallback should handle minimal input without crashing."""
        from src.structuring import _create_fallback

        result = _create_fallback({"id": "T-002"})
        assert result.tender_id == "T-002"
        assert result.structuring_status == "fallback"

    def test_fallback_empty_description(self):
        from src.structuring import _create_fallback

        result = _create_fallback({"tender_id": "T-003", "description": ""})
        assert result.tender_id == "T-003"
        assert len(result.requirements) == 0


class TestStructuringParsing:
    def test_parse_valid_json(self):
        from src.structuring import _parse_llm_output

        valid_json = json.dumps({
            "tender_id": "T-001",
            "language": "fr",
            "requirements": [
                {"req_id": "R1", "text": "Java developer", "category": "technical", "tech_keywords": ["Java"]}
            ],
        })

        result = _parse_llm_output(valid_json, "T-001")
        assert result.tender_id == "T-001"
        assert len(result.requirements) == 1

    def test_parse_with_markdown_fences(self):
        from src.structuring import _parse_llm_output

        fenced = '```json\n{"tender_id": "T-002", "language": "fr"}\n```'
        result = _parse_llm_output(fenced, "T-002")
        assert result.tender_id == "T-002"

    def test_parse_with_leading_text(self):
        from src.structuring import _parse_llm_output

        text = 'Here is the result:\n{"tender_id": "T-003", "language": "fr"}'
        result = _parse_llm_output(text, "T-003")
        assert result.tender_id == "T-003"

    def test_parse_invalid_json_raises(self):
        from src.structuring import _parse_llm_output

        with pytest.raises(json.JSONDecodeError):
            _parse_llm_output("not json at all {{{", "T-004")


# ============================================================
# Ingest Dedup Tests
# ============================================================


class TestIngestDedup:
    """Test that ingestion deduplicates by tender_id using SQLite."""

    def test_ingest_dedup(self, tmp_path):
        """Test dedup via direct DB operations (no API server needed)."""
        import sqlite3

        db_path = tmp_path / "test_ingest.db"
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE tenders (
                tender_id TEXT PRIMARY KEY,
                source TEXT,
                raw_data TEXT NOT NULL,
                structured_data TEXT,
                structuring_status TEXT DEFAULT 'pending',
                ingested_at TEXT NOT NULL,
                updated_at TEXT
            )
        """)

        # Insert first item
        conn.execute(
            "INSERT INTO tenders (tender_id, source, raw_data, ingested_at) VALUES (?, ?, ?, ?)",
            ("T-001", "test", '{"id": "T-001"}', "2026-01-01"),
        )
        conn.commit()

        # Try inserting duplicate — should fail
        try:
            conn.execute(
                "INSERT INTO tenders (tender_id, source, raw_data, ingested_at) VALUES (?, ?, ?, ?)",
                ("T-001", "test", '{"id": "T-001"}', "2026-01-02"),
            )
            conn.commit()
            assert False, "Should have raised IntegrityError"
        except sqlite3.IntegrityError:
            pass

        # Verify only one record
        count = conn.execute("SELECT COUNT(*) FROM tenders").fetchone()[0]
        assert count == 1
        conn.close()


# ============================================================
# API Tests (TestClient)
# ============================================================


class TestRAGAPI:
    """Test the RAG API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from fastapi.testclient import TestClient
        from src.api import app, _build_index
        import src.api as api_module

        # Build index for tests
        api_module._index = _build_index()
        self.client = TestClient(app)

    def test_health(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["index_size"] > 0

    def test_search_basic(self):
        resp = self.client.post("/search", json={
            "query": "Java Spring Boot developer",
            "top_k": 5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        assert data["query"] == "Java Spring Boot developer"

    def test_search_with_asset_type(self):
        resp = self.client.post("/search", json={
            "query": "Java developer",
            "top_k": 5,
            "asset_type": "cv",
        })
        assert resp.status_code == 200
        data = resp.json()
        for result in data["results"]:
            assert result["record_type"] == "cv"

    def test_search_empty_query(self):
        resp = self.client.post("/search", json={
            "query": "",
            "top_k": 5,
        })
        assert resp.status_code == 400

    def test_match_tender_basic(self):
        resp = self.client.post("/match-tender", json={
            "tender_id": "TEST-001",
            "title": "Test Tender",
            "requirements": [
                {"req_id": "R1", "text": "Java Spring Boot developer", "tech_keywords": ["Java", "Spring Boot"]},
                {"req_id": "R2", "text": "Blockchain cryptocurrency expert", "tech_keywords": ["Blockchain"]},
            ],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_requirements"] == 2
        assert data["tender_id"] == "TEST-001"
        assert 0.0 <= data["fit_score"] <= 1.0

    def test_match_tender_no_requirements(self):
        resp = self.client.post("/match-tender", json={
            "tender_id": "TEST-002",
        })
        assert resp.status_code == 400

    def test_dashboard_endpoint(self):
        resp = self.client.get("/dashboard")
        assert resp.status_code == 200
        assert "OliveSoft RFP Intelligence" in resp.text
        assert "text/html" in resp.headers.get("content-type", "")

    def test_root_redirect(self):
        resp = self.client.get("/", follow_redirects=False)
        assert resp.status_code in (302, 307)
        assert resp.headers.get("location") == "/dashboard"

    def test_benchmark_tenders_endpoint(self):
        resp = self.client.get("/api/benchmark-tenders")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 7
        assert any(t["tender_id"] == "AO-2026-TN-042" for t in data)
        assert any(t["tender_id"] == "OUT-OF-SCOPE-AGRI" for t in data)


class TestIngestAPI:
    """Test the Ingest API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        import src.ingest_api as ingest_module

        # Use temp DB
        ingest_module.DB_PATH = str(tmp_path / "test_ingest.db")
        ingest_module._init_db()

        from fastapi.testclient import TestClient
        self.client = TestClient(ingest_module.app)

    def test_health(self):
        resp = self.client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_ingest_single(self):
        resp = self.client.post("/tenders/ingest", json={
            "items": [{
                "id": "TENDER-TEST-001",
                "source": "test",
                "description": "Test tender description",
            }],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["new_count"] == 1

    def test_ingest_duplicate(self):
        # First ingest
        self.client.post("/tenders/ingest", json={
            "items": [{"id": "TENDER-DUP-001", "source": "test", "description": "Test"}],
        })

        # Second ingest (duplicate)
        resp = self.client.post("/tenders/ingest", json={
            "items": [{"id": "TENDER-DUP-001", "source": "test", "description": "Test"}],
        })
        data = resp.json()
        assert data["duplicate_count"] == 1
        assert data["new_count"] == 0

    def test_ingest_no_id(self):
        resp = self.client.post("/tenders/ingest", json={
            "items": [{"description": "No ID tender"}],
        })
        data = resp.json()
        assert data["error_count"] == 1

    def test_list_tenders(self):
        # Ingest one
        self.client.post("/tenders/ingest", json={
            "items": [{"id": "TENDER-LIST-001", "source": "test", "description": "Test"}],
        })

        resp = self.client.get("/tenders")
        assert resp.status_code == 200
        tenders = resp.json()
        assert len(tenders) >= 1

    def test_get_tender(self):
        # Ingest one
        self.client.post("/tenders/ingest", json={
            "items": [{"id": "TENDER-GET-001", "source": "test", "description": "Test"}],
        })

        resp = self.client.get("/tenders/TENDER-GET-001")
        assert resp.status_code == 200
        assert resp.json()["tender_id"] == "TENDER-GET-001"

    def test_get_tender_not_found(self):
        resp = self.client.get("/tenders/NONEXISTENT")
        assert resp.status_code == 404
