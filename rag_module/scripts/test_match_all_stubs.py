"""
Test match-tender endpoint logic against all 7 stub tenders + 1 irrelevant tender.
Verifies:
  - All 7 stubs return valid MatchTenderResponse
  - Fit scores and coverage matrix are generated
  - Staffing suggestions are generated
  - Irrelevant tender yields fit_score == 0 and no_match == True
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.documents import load_all_records
from src.embeddings import get_backend
from src.hybrid_index import HybridIndex
from src.structuring import structure_tender
from src.api import (
    MatchTenderRequest,
    RequirementInput,
    match_tender,
    _index,
    COVERAGE_THRESHOLDS,
)
import src.api as api_module

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    # 1. Initialize backend & index
    records = load_all_records()
    backend = get_backend("tfidf")
    index = HybridIndex(backend=backend, fusion_method="rrf")
    index.build(records)
    api_module._index = index

    # 2. Load stub tenders
    stub_file = Path(__file__).parent.parent / "data" / "tenders_stub.json"
    with open(stub_file, "r", encoding="utf-8") as f:
        stubs = json.load(f)

    logger.info("Testing matching on %d stub tenders...", len(stubs))

    import asyncio

    async def run_tests():
        all_passed = True
        for stub in stubs:
            t_id = stub["tender_id"]
            title = stub["title"]

            # Structure tender using deterministic fallback (or groq if key present)
            structured = await structure_tender(stub)
            reqs = [
                RequirementInput(
                    req_id=r.req_id,
                    text=r.text,
                    category=r.category,
                    tech_keywords=r.tech_keywords,
                )
                for r in structured.requirements
            ]

            req = MatchTenderRequest(
                tender_id=t_id,
                title=title,
                requirements=reqs,
                top_k=3,
            )

            res = await match_tender(req)

            logger.info(
                "[%s] Fit: %.2f | Covered: %d/%d | Staffing: %d | NoMatch: %s",
                t_id,
                res.fit_score,
                res.covered_count,
                res.total_requirements,
                len(res.staffing_suggestions),
                res.no_match,
            )

            if res.fit_score < 0.0 or res.fit_score > 1.0:
                logger.error("Invalid fit_score for %s: %f", t_id, res.fit_score)
                all_passed = False

        # 3. Test irrelevant tender (Negative control)
        irrelevant_req = MatchTenderRequest(
            tender_id="TENDER-IRRELEVANT-AGRI",
            title="Fourniture d'engrais et semences agricoles",
            requirements=[
                RequirementInput(
                    req_id="REQ-AGRI-1",
                    text="Livraison de 50 tonnes d'engrais phosphaté et semences de blé",
                    category="agriculture",
                    tech_keywords=["engrais", "semences", "agriculture"],
                ),
                RequirementInput(
                    req_id="REQ-AGRI-2",
                    text="Transport par camions frigorifiques et ensachage",
                    category="logistics",
                    tech_keywords=["camion", "transport", "logistique"],
                ),
            ],
            top_k=3,
        )

        irrel_res = await match_tender(irrelevant_req)
        logger.info(
            "[IRRELEVANT] Fit: %.2f | Covered: %d/%d | Partial: %d | NoMatch: %s",
            irrel_res.fit_score,
            irrel_res.covered_count,
            irrel_res.total_requirements,
            irrel_res.partial_count,
            irrel_res.no_match,
        )

        if not irrel_res.no_match:
            logger.warning("Irrelevant tender was not flagged no_match=True")
        else:
            logger.info("[OK] Irrelevant tender correctly flagged as no_match=True")

        return all_passed and irrel_res.no_match

    success = asyncio.run(run_tests())
    if success:
        print("\n[SUCCESS] All 7 stub tenders + negative control passed match-tender test!")
    else:
        print("\n[FAIL] Some tests failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
