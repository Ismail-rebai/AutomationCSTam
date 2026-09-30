"""
Unit & Integration Tests for the Multi-Agent Proposal & PowerPoint Generation System.
"""

import sys
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pptx import Presentation

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proposal_generator import (
    DEFAULT_RATE_CARD,
    DEFAULT_CONTINGENCY_PERCENT,
    ProposalDeckData,
    generate_proposal_deck_data,
)
from src.pptx_builder import build_proposal_presentation
from src.api import app


@pytest.fixture
def sample_tender_input():
    return {
        "tender_id": "TENDER-TEST-001",
        "title": "Migration du système bancaire vers microservices",
        "client": "Banque Centrale de Tunisie",
        "requirements": [
            {
                "req_id": "REQ-01",
                "text": "Conception d'une architecture microservices hautement disponible",
                "tech_keywords": ["microservices", "spring boot", "cloud"],
            },
            {
                "req_id": "REQ-02",
                "text": "Développement backend Java 21 et conteneurisation Docker / Kubernetes",
                "tech_keywords": ["java", "kubernetes", "docker"],
            },
        ],
        "staffing_matches": [
            {
                "cv_id": "CV-003",
                "name": "Mohamed Kacem",
                "title": "Java/Spring Architect",
                "skills_matched": ["java", "spring boot", "kubernetes", "microservices"],
            },
            {
                "cv_id": "CV-001",
                "name": "Ahmed Ben Ali",
                "title": "Senior Full-Stack Engineer",
                "skills_matched": ["react", "docker", "postgresql"],
            },
        ],
        "fit_score": 0.95,
    }


class TestProposalGenerator:
    def test_proposal_data_structure(self, sample_tender_input):
        data = generate_proposal_deck_data(
            tender_id=sample_tender_input["tender_id"],
            title=sample_tender_input["title"],
            client=sample_tender_input["client"],
            requirements=sample_tender_input["requirements"],
            staffing_matches=sample_tender_input["staffing_matches"],
            fit_score=sample_tender_input["fit_score"],
        )

        assert isinstance(data, ProposalDeckData)
        assert data.tender_id == "TENDER-TEST-001"
        assert data.client_name == "Banque Centrale de Tunisie"
        assert data.total_duration_weeks >= 12
        assert len(data.phases) == 5
        assert len(data.staffing) >= 2
        assert len(data.business_objectives) >= 3
        assert len(data.risk_mitigations) >= 3

    def test_pricing_breakdown_math(self, sample_tender_input):
        data = generate_proposal_deck_data(
            tender_id=sample_tender_input["tender_id"],
            title=sample_tender_input["title"],
            client=sample_tender_input["client"],
            requirements=sample_tender_input["requirements"],
            staffing_matches=sample_tender_input["staffing_matches"],
        )
        pricing = data.pricing

        assert len(pricing.roles) == 5
        # Verify subtotal equals sum of roles
        computed_subtotal = sum(r.total_tnd for r in pricing.roles)
        assert pytest.approx(pricing.base_cost_tnd, 0.01) == computed_subtotal

        # Verify contingency calculation (12%)
        expected_contingency = round(pricing.base_cost_tnd * (DEFAULT_CONTINGENCY_PERCENT / 100.0), 2)
        assert pytest.approx(pricing.contingency_tnd, 0.01) == expected_contingency

        # Verify total price
        expected_total = round(pricing.base_cost_tnd + pricing.contingency_tnd, 2)
        assert pytest.approx(pricing.total_price_tnd, 0.01) == expected_total

        # Verify annual maintenance SLA (15%)
        assert pricing.maintenance_sla_annual_tnd > 0

    def test_domain_tailored_architecture(self):
        # 1. Banking / microservices domain
        data_banking = generate_proposal_deck_data(
            tender_id="T1",
            title="Refonte bancaire microservices",
            requirements=[{"text": "Spring Cloud Gateway et Kafka"}],
        )
        assert "Microservices" in data_banking.technical_solution.architecture_style
        assert "Spring Boot" in str(data_banking.technical_solution.tech_stack)

        # 2. SAP domain
        data_sap = generate_proposal_deck_data(
            tender_id="T2",
            title="Déploiement ERP SAP S/4HANA",
            requirements=[{"text": "Migration SAP Fiori et OData"}],
        )
        assert "SAP" in data_sap.technical_solution.architecture_style
        assert "SAP HANA" in str(data_sap.technical_solution.tech_stack)

        # 3. Data / analytics domain
        data_data = generate_proposal_deck_data(
            tender_id="T3",
            title="Plateforme Big Data et Analytics",
            requirements=[{"text": "Pipeline ETL Airflow et dashboards"}],
        )
        assert "Données" in data_data.technical_solution.architecture_style or "Data" in data_data.technical_solution.architecture_style


class TestPptxBuilder:
    def test_pptx_generation_creates_valid_file(self, sample_tender_input):
        data = generate_proposal_deck_data(
            tender_id=sample_tender_input["tender_id"],
            title=sample_tender_input["title"],
            client=sample_tender_input["client"],
            requirements=sample_tender_input["requirements"],
            staffing_matches=sample_tender_input["staffing_matches"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "test_deck.pptx"
            result_path = build_proposal_presentation(data, str(out_file))

            assert Path(result_path).exists()
            assert out_file.stat().st_size > 1000  # Non-trivial size

            # Inspect presentation slides with python-pptx
            prs = Presentation(str(out_file))
            assert len(prs.slides) == 8
            assert prs.slide_width.inches == pytest.approx(13.333, 0.01)
            assert prs.slide_height.inches == pytest.approx(7.5, 0.01)


class TestApiDeckEndpoints:
    @pytest.fixture
    def client(self):
        with TestClient(app) as client:
            yield client

    def test_generate_deck_endpoint(self, client, sample_tender_input):
        resp = client.post("/proposals/generate-deck", json=sample_tender_input)
        assert resp.status_code == 200
        data = resp.json()

        assert data["tender_id"] == "TENDER-TEST-001"
        assert data["total_price_tnd"] > 0
        assert data["total_duration_weeks"] >= 12
        assert data["slides_count"] == 8
        assert data["phases_count"] == 5
        assert Path(data["file_path"]).exists()

        # Test download endpoint
        dl_resp = client.get(data["download_url"])
        assert dl_resp.status_code == 200
        assert len(dl_resp.content) > 1000

    def test_download_nonexistent_returns_404(self, client):
        resp = client.get("/proposals/download/NON_EXISTENT_TENDER_ID")
        assert resp.status_code == 404
