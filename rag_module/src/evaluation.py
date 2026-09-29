"""
Evaluation module: proper IR metrics on the gold set.

Metrics per difficulty tier and overall:
  - Precision@k, Recall@k
  - MRR (Mean Reciprocal Rank)
  - nDCG@k
  - Hit@k (at least one expected asset in top-k)
  - No-match true-negative rate

CLI usage:
  python -m src.evaluation --top-k 10 --fusion rrf --output results/
"""

import argparse
import json
import logging
import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import numpy as np

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.documents import load_all_records, load_gold_set
from src.embeddings import get_backend
from src.hybrid_index import HybridIndex, SearchResult

logger = logging.getLogger(__name__)


def precision_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Precision@k: fraction of retrieved items that are relevant."""
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_in_k = sum(1 for rid in top_k if rid in relevant_ids)
    return relevant_in_k / len(top_k)


def recall_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Recall@k: fraction of relevant items that are retrieved."""
    if not relevant_ids:
        return 1.0  # No relevant items — vacuously true
    top_k = retrieved_ids[:k]
    relevant_in_k = sum(1 for rid in top_k if rid in relevant_ids)
    return relevant_in_k / len(relevant_ids)


def mrr(retrieved_ids: List[str], relevant_ids: Set[str]) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant item."""
    for i, rid in enumerate(retrieved_ids):
        if rid in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def ndcg_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int) -> float:
    """Normalized Discounted Cumulative Gain @ k."""
    top_k = retrieved_ids[:k]
    dcg = 0.0
    for i, rid in enumerate(top_k):
        if rid in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)  # +2 because i is 0-indexed

    # Ideal DCG: all relevant items at top
    ideal_count = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_count))

    if idcg == 0:
        return 1.0 if not relevant_ids else 0.0
    return dcg / idcg


def hit_at_k(retrieved_ids: List[str], relevant_ids: Set[str], k: int,
             scores: Optional[List[float]] = None, min_score: float = 0.0) -> bool:
    """Hit@k: is at least one relevant item in top-k (with score above min_score)?"""
    top_k = retrieved_ids[:k]
    for i, rid in enumerate(top_k):
        if rid in relevant_ids:
            if scores and i < len(scores) and scores[i] <= min_score:
                continue  # Skip zero-score ties
            return True
    return False


def evaluate_gold_set(
    index: HybridIndex,
    gold_set: list,
    top_k: int = 10,
    min_score: float = 0.0,
    fusion_method: Optional[str] = None,
    dense_weight: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Run evaluation on the gold set.

    Returns:
        Dict with metrics per difficulty tier and overall.
    """
    tier_results = defaultdict(list)
    all_results = []

    for case in gold_set:
        case_id = case["case_id"]
        difficulty = case["difficulty"]
        query = case["query"]
        expected_ids = set(case["expected_asset_ids"])
        is_no_match = difficulty == "no_match_expected"

        # Search
        results = index.search(
            query=query,
            top_k=top_k,
            fusion_method=fusion_method,
            dense_weight=dense_weight,
        )

        retrieved_ids = [r.record_id for r in results]
        scores = [r.score for r in results]

        if is_no_match:
            # For no-match cases, success = top result score is low
            top_score = scores[0] if scores else 0.0
            # Calibrate: if best score is below the "partial" threshold, it's a true negative
            # For RRF: partial threshold ~0.015
            tn_threshold = 0.020  # Conservative
            is_true_negative = top_score < tn_threshold

            case_result = {
                "case_id": case_id,
                "difficulty": difficulty,
                "query": query,
                "top_score": top_score,
                "true_negative": is_true_negative,
                "top_result": retrieved_ids[0] if retrieved_ids else None,
            }
        else:
            p_at_k = precision_at_k(retrieved_ids, expected_ids, top_k)
            r_at_k = recall_at_k(retrieved_ids, expected_ids, top_k)
            mrr_val = mrr(retrieved_ids, expected_ids)
            ndcg_val = ndcg_at_k(retrieved_ids, expected_ids, top_k)
            hit = hit_at_k(retrieved_ids, expected_ids, top_k, scores, min_score)

            case_result = {
                "case_id": case_id,
                "difficulty": difficulty,
                "query": query,
                "precision_at_k": p_at_k,
                "recall_at_k": r_at_k,
                "mrr": mrr_val,
                "ndcg_at_k": ndcg_val,
                "hit": hit,
                "top_score": scores[0] if scores else 0.0,
                "expected_ids": list(expected_ids),
                "retrieved_ids": retrieved_ids[:5],
            }

        tier_results[difficulty].append(case_result)
        all_results.append(case_result)

    # Aggregate metrics by tier
    tier_summary = {}
    for tier, cases in tier_results.items():
        if tier == "no_match_expected":
            tn_rate = sum(1 for c in cases if c["true_negative"]) / len(cases) if cases else 0
            tier_summary[tier] = {
                "count": len(cases),
                "true_negative_rate": round(tn_rate, 4),
                "avg_top_score": round(np.mean([c["top_score"] for c in cases]), 6),
            }
        else:
            tier_summary[tier] = {
                "count": len(cases),
                "avg_precision_at_k": round(np.mean([c["precision_at_k"] for c in cases]), 4),
                "avg_recall_at_k": round(np.mean([c["recall_at_k"] for c in cases]), 4),
                "avg_mrr": round(np.mean([c["mrr"] for c in cases]), 4),
                "avg_ndcg_at_k": round(np.mean([c["ndcg_at_k"] for c in cases]), 4),
                "hit_rate": round(sum(1 for c in cases if c["hit"]) / len(cases), 4),
            }

    # Overall (excluding no_match)
    match_cases = [c for c in all_results if c["difficulty"] != "no_match_expected"]
    overall = {}
    if match_cases:
        overall = {
            "count": len(match_cases),
            "avg_precision_at_k": round(np.mean([c["precision_at_k"] for c in match_cases]), 4),
            "avg_recall_at_k": round(np.mean([c["recall_at_k"] for c in match_cases]), 4),
            "avg_mrr": round(np.mean([c["mrr"] for c in match_cases]), 4),
            "avg_ndcg_at_k": round(np.mean([c["ndcg_at_k"] for c in match_cases]), 4),
            "hit_rate": round(sum(1 for c in match_cases if c["hit"]) / len(match_cases), 4),
        }

    return {
        "config": {
            "backend": index.backend.name,
            "fusion_method": fusion_method or index.fusion_method,
            "dense_weight": dense_weight if dense_weight is not None else index.dense_weight,
            "top_k": top_k,
            "min_score": min_score,
            "record_count": index.record_count,
        },
        "overall": overall,
        "per_tier": tier_summary,
        "details": all_results,
    }


def format_markdown_report(eval_result: Dict[str, Any]) -> str:
    """Format evaluation results as a Markdown table."""
    cfg = eval_result["config"]
    lines = [
        f"# RAG Evaluation Report",
        f"",
        f"**Backend:** {cfg['backend']}  ",
        f"**Fusion:** {cfg['fusion_method']}  ",
        f"**Dense weight:** {cfg['dense_weight']}  ",
        f"**Top-k:** {cfg['top_k']}  ",
        f"**KB size:** {cfg['record_count']} records  ",
        f"**Min score policy:** {cfg['min_score']}  ",
        f"",
        f"## Overall Metrics (excluding no-match cases)",
        f"",
    ]

    overall = eval_result.get("overall", {})
    if overall:
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Cases | {overall['count']} |")
        lines.append(f"| Precision@{cfg['top_k']} | {overall['avg_precision_at_k']} |")
        lines.append(f"| Recall@{cfg['top_k']} | {overall['avg_recall_at_k']} |")
        lines.append(f"| MRR | {overall['avg_mrr']} |")
        lines.append(f"| nDCG@{cfg['top_k']} | {overall['avg_ndcg_at_k']} |")
        lines.append(f"| Hit Rate | {overall['hit_rate']} |")
    lines.append("")

    lines.append("## Per-Tier Breakdown")
    lines.append("")

    for tier, summary in eval_result["per_tier"].items():
        lines.append(f"### {tier} (n={summary['count']})")
        lines.append("")

        if tier == "no_match_expected":
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| True Negative Rate | {summary['true_negative_rate']} |")
            lines.append(f"| Avg Top Score | {summary['avg_top_score']} |")
        else:
            lines.append(f"| Metric | Value |")
            lines.append(f"|--------|-------|")
            lines.append(f"| Precision@{cfg['top_k']} | {summary['avg_precision_at_k']} |")
            lines.append(f"| Recall@{cfg['top_k']} | {summary['avg_recall_at_k']} |")
            lines.append(f"| MRR | {summary['avg_mrr']} |")
            lines.append(f"| nDCG@{cfg['top_k']} | {summary['avg_ndcg_at_k']} |")
            lines.append(f"| Hit Rate | {summary['hit_rate']} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="RAG Evaluation CLI")
    parser.add_argument("--top-k", type=int, default=10, help="Top-k for retrieval")
    parser.add_argument("--fusion", type=str, default=None, help="Fusion method (rrf|weighted)")
    parser.add_argument("--dense-weight", type=float, default=None, help="Dense weight")
    parser.add_argument("--min-score", type=float, default=0.0, help="Min score to count as hit")
    parser.add_argument("--backend", type=str, default=None, help="Embedding backend (tfidf|e5)")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    parser.add_argument("--data-dir", type=str, default=None, help="Data directory")

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Build index
    logger.info("Loading KB records...")
    records = load_all_records(args.data_dir)
    gold_set = load_gold_set(args.data_dir)

    logger.info("Building index with backend=%s...", args.backend or "default")
    try:
        backend = get_backend(args.backend)
    except RuntimeError as e:
        logger.error("Backend unavailable: %s", e)
        logger.info("Falling back to TF-IDF")
        backend = get_backend("tfidf")

    index = HybridIndex(backend=backend)
    index.build(records)

    # Evaluate
    logger.info("Running evaluation (top_k=%d)...", args.top_k)
    result = evaluate_gold_set(
        index=index,
        gold_set=gold_set,
        top_k=args.top_k,
        min_score=args.min_score,
        fusion_method=args.fusion,
        dense_weight=args.dense_weight,
    )

    # Output
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backend_name = backend.name.lower()

    json_path = output_dir / f"benchmark_{backend_name}_{ts}.json"
    md_path = output_dir / f"benchmark_{backend_name}_{ts}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    md_report = format_markdown_report(result)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    # Print to console
    print(md_report)
    print(f"\nResults saved to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    main()
