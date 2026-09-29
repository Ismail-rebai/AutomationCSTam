# RAG Evaluation Report

**Backend:** TfidfBackend  
**Fusion:** rrf  
**Dense weight:** 0.5  
**Top-k:** 10  
**KB size:** 68 records  
**Min score policy:** 0.0  

## Overall Metrics (excluding no-match cases)

| Metric | Value |
|--------|-------|
| Cases | 17 |
| Precision@10 | 0.2552 |
| Recall@10 | 0.5814 |
| MRR | 0.6196 |
| nDCG@10 | 0.5503 |
| Hit Rate | 0.7059 |

## Per-Tier Breakdown

### exact (n=8)

| Metric | Value |
|--------|-------|
| Precision@10 | 0.3286 |
| Recall@10 | 1.0 |
| MRR | 0.9167 |
| nDCG@10 | 0.9237 |
| Hit Rate | 1.0 |

### paraphrase_semantic (n=6)

| Metric | Value |
|--------|-------|
| Precision@10 | 0.0516 |
| Recall@10 | 0.1389 |
| MRR | 0.2 |
| nDCG@10 | 0.1177 |
| Hit Rate | 0.3333 |

### ambiguous_any_of (n=3)

| Metric | Value |
|--------|-------|
| Precision@10 | 0.4667 |
| Recall@10 | 0.35 |
| MRR | 0.6667 |
| nDCG@10 | 0.4197 |
| Hit Rate | 0.6667 |

### no_match_expected (n=2)

| Metric | Value |
|--------|-------|
| True Negative Rate | 0.5 |
| Avg Top Score | 0.02459 |
