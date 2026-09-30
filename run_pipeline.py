"""
End-to-End Pipeline Runner for OliveSoft RFP Intelligence & Proposal Generation.

Executes the complete commercial intelligence flow:
1. Loads tenders from data/tenders_stub.json
2. Ingests and deduplicates tenders via Ingest API (:8001)
3. Evaluates capability fit and coverage matrix via RAG API (:8000)
4. For qualified tenders (fit_score >= 0.5):
   Executes the multi-agent system to generate 8-slide PowerPoint (.pptx) decks
5. Displays executive summary table with pricing (TND), duration (weeks) and download links.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

# Force UTF-8 for Windows PowerShell / CMD output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT_DIR = Path(__file__).parent
DATA_PATH = ROOT_DIR / "rag_module" / "data" / "tenders_stub.json"

RAG_API_URL = os.getenv("RAG_API_URL", "http://localhost:8000")
INGEST_API_URL = os.getenv("INGEST_API_URL", "http://localhost:8001")


def post_json(url: str, data: dict) -> dict:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    print("=" * 70)
    print("  OLIVESOFT RFP INTELLIGENCE & PROPOSAL PIPELINE")
    print("=" * 70)

    # 1. Health check
    try:
        rag_h = urllib.request.urlopen(f"{RAG_API_URL}/health")
        ing_h = urllib.request.urlopen(f"{INGEST_API_URL}/health")
        print(f"[OK] RAG Service is healthy on {RAG_API_URL}")
        print(f"[OK] Ingest Service is healthy on {INGEST_API_URL}")
    except Exception as e:
        print(f"[ERROR] Services are not running: {e}")
        print("Please start them first using run_all.bat")
        sys.exit(1)

    # 2. Ingest benchmark tenders
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        tenders = json.load(f)

    print(f"\n[1/3] Ingesting {len(tenders)} benchmark tenders into Ingestion Engine...")
    ingest_res = post_json(f"{INGEST_API_URL}/tenders/ingest", {"items": tenders})
    print(f"      -> Ingested: {ingest_res.get('new_count', 0)} new, {ingest_res.get('duplicate_count', 0)} existing.")

    # 3. Match tenders via RAG & Generate PowerPoint Decks
    print(f"\n[2/3] Evaluating RAG Capability Fit & Generating Commercial Decks...\n")

    results = []

    for t in tenders:
        t_id = t["tender_id"]
        title = t["title"]
        buyer = t.get("buyer", "Client")

        # Create structured requirement from description
        match_payload = {
            "tender_id": t_id,
            "title": title,
            "requirements": [
                {
                    "req_id": "REQ-01",
                    "text": t["description"][:300],
                    "category": "technical",
                    "tech_keywords": []
                }
            ],
            "top_k": 3
        }

        match_res = post_json(f"{RAG_API_URL}/match-tender", match_payload)
        fit_score = match_res.get("fit_score", 0.0)
        staffing = match_res.get("staffing_suggestions", [])

        # Qualification Gate: Fit Score >= 0.5
        is_qualified = fit_score >= 0.5

        deck_res = None
        if is_qualified:
            deck_payload = {
                "tender_id": t_id,
                "title": title,
                "client": buyer,
                "requirements": match_payload["requirements"],
                "staffing_matches": staffing,
                "fit_score": fit_score
            }
            deck_res = post_json(f"{RAG_API_URL}/proposals/generate-deck", deck_payload)

        results.append({
            "tender_id": t_id,
            "title": title,
            "buyer": buyer,
            "fit_score": fit_score,
            "qualified": is_qualified,
            "deck": deck_res
        })

        status_str = "[GO QUALIFIED]" if is_qualified else "[NO-GO DISQUALIFIED]"
        print(f" - {t_id:12} | Fit: {fit_score * 100:5.1f}% | {status_str:22} | {title[:35]}...")
        if deck_res:
            print(f"   --> Deck generated: {deck_res['total_price_tnd']:,.2f} TND | {deck_res['total_duration_weeks']} Semaines | {deck_res['file_name']}")

    # 4. Final Executive Summary Table
    print("\n" + "=" * 70)
    print("  EXECUTIVE PROPOSAL SUMMARY & POWERPOINT DELIVERABLES")
    print("=" * 70)
    print(f"{'Tender ID':<12} | {'Acheteur':<22} | {'Fit':<6} | {'Budget Estimé (TND)':<20} | {'Durée':<8} | {'PowerPoint (.pptx)'}")
    print("-" * 100)

    for r in results:
        if r["deck"]:
            d = r["deck"]
            print(f"{r['tender_id']:<12} | {r['buyer'][:20]:<22} | {r['fit_score']*100:4.0f}%  | {d['total_price_tnd']:>15,.2f} TND | {d['total_duration_weeks']:>2} sem. | {d['file_name']}")
        else:
            print(f"{r['tender_id']:<12} | {r['buyer'][:20]:<22} | {r['fit_score']*100:4.0f}%  | {'N/A (Disqualifié)':<20} | {'--':<8} | Non-produit (Score < 50%)")

    print("\n[SUCCESS] Pipeline execution finished! All presentations saved in:")
    print(f"          {ROOT_DIR / 'rag_module' / 'results' / 'proposals'}\n")


if __name__ == "__main__":
    main()
