"""
Compare embedding backends and fusion methods.

Runs the benchmark for:
  - tfidf (always available)
  - e5 (if loadable)
  - hybrid at several dense_weight values (0, 0.3, 0.5, 0.7, 1.0)
  - RRF vs weighted fusion

Usage:
  python scripts/compare_backends.py [--output results/]
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.documents import load_all_records, load_gold_set
from src.embeddings import get_backend, TfidfBackend
from src.hybrid_index import HybridIndex
from src.evaluation import evaluate_gold_set, format_markdown_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def run_comparison(output_dir: str = "results", data_dir: str = None, skip_e5: bool = False):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    records = load_all_records(data_dir)
    gold_set = load_gold_set(data_dir)
    logger.info("Loaded %d KB records and %d gold cases", len(records), len(gold_set))

    all_results = []
    comparison_table = []

    # --- TF-IDF backend ---
    logger.info("=" * 60)
    logger.info("Testing TF-IDF backend")
    logger.info("=" * 60)

    tfidf_backend = get_backend("tfidf")

    configs = [
        {"fusion": "rrf", "dense_weight": 0.5, "label": "tfidf+rrf"},
        {"fusion": "weighted", "dense_weight": 0.0, "label": "tfidf+bm25_only"},
        {"fusion": "weighted", "dense_weight": 0.3, "label": "tfidf+weighted_0.3"},
        {"fusion": "weighted", "dense_weight": 0.5, "label": "tfidf+weighted_0.5"},
        {"fusion": "weighted", "dense_weight": 0.7, "label": "tfidf+weighted_0.7"},
        {"fusion": "weighted", "dense_weight": 1.0, "label": "tfidf+dense_only"},
    ]

    for cfg in configs:
        logger.info("Config: %s", cfg["label"])
        index = HybridIndex(
            backend=tfidf_backend,
            fusion_method=cfg["fusion"],
            dense_weight=cfg["dense_weight"],
        )
        index.build(records)

        result = evaluate_gold_set(
            index=index,
            gold_set=gold_set,
            fusion_method=cfg["fusion"],
            dense_weight=cfg["dense_weight"],
        )
        result["label"] = cfg["label"]
        all_results.append(result)

        overall = result.get("overall", {})
        comparison_table.append({
            "config": cfg["label"],
            "hit_rate": overall.get("hit_rate", 0),
            "mrr": overall.get("avg_mrr", 0),
            "ndcg": overall.get("avg_ndcg_at_k", 0),
            "precision": overall.get("avg_precision_at_k", 0),
            "recall": overall.get("avg_recall_at_k", 0),
        })

    # --- E5 backend (if available) ---
    logger.info("=" * 60)
    logger.info("Testing E5 backend")
    logger.info("=" * 60)

    e5_available = False
    if skip_e5 or os.getenv("SKIP_E5") == "1":
        logger.info("Skipping E5 benchmarks (skip_e5 flag set).")
        comparison_table.append({
            "config": "e5+*",
            "hit_rate": "N/A (skipped)",
            "mrr": "N/A",
            "ndcg": "N/A",
            "precision": "N/A",
            "recall": "N/A",
        })
    else:
        try:
            e5_backend = get_backend("e5")
            e5_available = True
            logger.info("E5 backend loaded successfully!")

            e5_configs = [
                {"fusion": "rrf", "dense_weight": 0.5, "label": "e5+rrf"},
                {"fusion": "weighted", "dense_weight": 0.3, "label": "e5+weighted_0.3"},
                {"fusion": "weighted", "dense_weight": 0.5, "label": "e5+weighted_0.5"},
                {"fusion": "weighted", "dense_weight": 0.7, "label": "e5+weighted_0.7"},
                {"fusion": "weighted", "dense_weight": 1.0, "label": "e5+dense_only"},
            ]

            for cfg in e5_configs:
                logger.info("Config: %s", cfg["label"])
                index = HybridIndex(
                    backend=e5_backend,
                    fusion_method=cfg["fusion"],
                    dense_weight=cfg["dense_weight"],
                )
                index.build(records)

                result = evaluate_gold_set(
                    index=index,
                    gold_set=gold_set,
                    fusion_method=cfg["fusion"],
                    dense_weight=cfg["dense_weight"],
                )
                result["label"] = cfg["label"]
                all_results.append(result)

                overall = result.get("overall", {})
                comparison_table.append({
                    "config": cfg["label"],
                    "hit_rate": overall.get("hit_rate", 0),
                    "mrr": overall.get("avg_mrr", 0),
                    "ndcg": overall.get("avg_ndcg_at_k", 0),
                    "precision": overall.get("avg_precision_at_k", 0),
                    "recall": overall.get("avg_recall_at_k", 0),
                })

        except RuntimeError as e:
            logger.warning("E5 UNAVAILABLE: %s", e)
            logger.info("Skipping E5 benchmarks — this is expected in offline environments.")
            comparison_table.append({
                "config": "e5+*",
                "hit_rate": "N/A (model unavailable)",
                "mrr": "N/A",
                "ndcg": "N/A",
                "precision": "N/A",
                "recall": "N/A",
            })

    # --- Save results ---
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Full JSON
    json_path = output_path / f"benchmark_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    # Comparison markdown
    md_lines = [
        "# Backend & Fusion Comparison",
        "",
        f"**Date:** {datetime.now().isoformat()}  ",
        f"**KB size:** {len(records)} records  ",
        f"**Gold cases:** {len(gold_set)}  ",
        f"**E5 available:** {'Yes' if e5_available else 'No (offline environment)'}  ",
        "",
        "## Comparison Table",
        "",
        "| Config | Hit Rate | MRR | nDCG@10 | P@10 | R@10 |",
        "|--------|----------|-----|---------|------|------|",
    ]

    for row in comparison_table:
        md_lines.append(
            f"| {row['config']} | {row['hit_rate']} | {row['mrr']} | "
            f"{row['ndcg']} | {row['precision']} | {row['recall']} |"
        )

    md_lines.append("")

    # Add per-tier details for best config
    if all_results:
        best = all_results[0]  # RRF is first, usually best
        md_lines.append("## Detailed Report (best config: {})".format(best.get("label", "?")))
        md_lines.append("")
        md_lines.append(format_markdown_report(best))

    md_path = output_path / f"benchmark_{ts}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Print
    print("\n" + "\n".join(md_lines))
    print(f"\nResults saved to:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results")
    parser.add_argument("--data-dir", default=None)
    parser.add_argument("--skip-e5", action="store_true", help="Skip E5 benchmark (offline or quick mode)")
    args = parser.parse_args()
    run_comparison(args.output, args.data_dir, skip_e5=args.skip_e5)
