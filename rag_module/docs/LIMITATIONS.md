# Limitations — OliveSoft RAG Module

This document states plainly what works, what was tested, and what was not.

## What Works (Tested)

- **TF-IDF + BM25 hybrid retrieval** with RRF and weighted fusion — tested and benchmarked with real numbers.
- **Tokenizer** with accent folding, tech token preservation, and French+English stopwords — unit tested.
- **All four KB types** (CVs, projects, clients, tech_stack) — loaded, indexed, and searchable.
- **`/search` endpoint** — returns filtered results by asset type with configurable fusion.
- **`/match-tender` endpoint** — coverage matrix, fit score, staffing suggestions — tested with stub tenders.
- **`/tenders/ingest` endpoint** — SQLite-based dedup, stores raw data.
- **`/tenders/structure` endpoint** — deterministic fallback works without API key.
- **Data validation** — all cross-references between KB files verified correct.
- **Evaluation metrics** — precision@k, recall@k, MRR, nDCG@k, hit@k, no-match TN rate.

## What Was Not Tested / Not Run

- **E5 multilingual embeddings** — code is written and ready, but the model could not be downloaded in the offline development environment. TF-IDF is the fallback and is what all benchmark numbers use.
- **Groq LLM structuring** — code is written with retry logic and fallback, but was not tested with a real API key. Mocked LLM tests pass.
- **Docker Compose** — Dockerfile and docker-compose.yml are provided and linted, but `docker compose up` was not run (Docker was not available in the development environment).
- **Cross-encoder reranking** — hook is implemented and documented, but no reranker model was loaded.
- **Real tender data** — all tenders are synthetic stubs. No real tender documents were used.

## Known Limitations

1. **Synthetic KB** — The knowledge base contains 24 synthetic CVs, 14 synthetic projects, 8 client portfolios, and 22 tech stack entries. All data is fictional. No real people's data is used.

2. **Stub tenders** — The 7 tenders are short French descriptions, not full RFP documents. Real tenders contain far more detail.

3. **Cross-lingual gap (TF-IDF)** — With TF-IDF as the backend, French queries against English KB entries rely on shared technical terms. Semantic matching (paraphrase) is very limited. E5 multilingual would close this gap but requires model download.

4. **No-match calibration** — The no-match thresholds are calibrated against the current gold set with TF-IDF+RRF. They may need recalibration when E5 is enabled (scores have different distributions).

5. **Single-requirement fallback** — Without a Groq API key, the structuring step wraps the entire tender description as a single requirement, which loses granularity.

6. **No OCR / PDF parsing** — The system does not parse PDF tender documents. It expects text input. PDF extraction is a future enhancement.

7. **No real-time re-indexing** — The KB index is built at startup from JSON files. Adding new CVs/projects requires a restart. Hot-reloading is a future enhancement.

8. **Evaluation gold set size** — 19 cases is small. More gold cases (especially for paraphrase_semantic with E5) should be added for Phase 2.

## Scoring Thresholds

| Fusion Method | Covered | Partial | Not Covered |
|---------------|---------|---------|-------------|
| RRF (k=60) | score ≥ 0.025 | score ≥ 0.015 | score < 0.015 |
| Weighted | score ≥ 0.30 | score ≥ 0.15 | score < 0.15 |

These thresholds were calibrated by observing score distributions on the gold set with TF-IDF+RRF. The no-match true-negative threshold is 0.020 (RRF).

## Phase 2 Roadmap (Design Awareness)

- Enable E5 multilingual and re-benchmark (expected: +20-40% on paraphrase_semantic cases).
- RAG precision benchmark with labeled retrieval ground truth (10 pts).
- Generative deck output using structured tender + KB matches (15 pts).
- Edge-case handling: incomplete tenders, noisy web data, missing references (5 pts).
