# API Reference — OliveSoft RAG Module

All endpoints return JSON. FastAPI auto-generates interactive docs at `/docs` (Swagger UI).

## RAG API (default: http://localhost:8001)

### GET /health

Health check.

```bash
curl http://localhost:8001/health
```

```json
{
  "status": "healthy",
  "index_size": 68,
  "backend": "TfidfBackend"
}
```

### POST /search

Hybrid search over the knowledge base.

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Java Spring Boot developer for banking",
    "top_k": 5,
    "asset_type": "cv",
    "fusion_method": "rrf"
  }'
```

**Request body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Search query (French or English) |
| `top_k` | int | 10 | Number of results |
| `asset_type` | string | null | Filter: `cv`, `past_project`, `client`, `tech_stack` |
| `dense_weight` | float | 0.5 | Dense weight (for weighted fusion) |
| `fusion_method` | string | config | `rrf` or `weighted` |
| `rerank` | bool | false | Apply cross-encoder reranking |

**Response:**

```json
{
  "query": "Java Spring Boot developer for banking",
  "results": [
    {
      "record_id": "CV-001",
      "record_type": "cv",
      "score": 0.032787,
      "text": "Ahmed Ben Ali - Senior Java Developer...",
      "metadata": {"name": "Ahmed Ben Ali", "skills": ["Java", "Spring Boot"]}
    }
  ],
  "count": 5,
  "backend": "TfidfBackend",
  "fusion_method": "rrf"
}
```

### POST /match-tender

Match a structured tender against the KB. Returns per-requirement matches, coverage matrix, fit score, and staffing suggestions.

```bash
curl -X POST http://localhost:8001/match-tender \
  -H "Content-Type: application/json" \
  -d '{
    "tender_id": "TENDER-003",
    "title": "Migration du système bancaire",
    "requirements": [
      {
        "req_id": "R1",
        "text": "Expérience en développement Java/Spring Boot",
        "category": "technical",
        "tech_keywords": ["Java", "Spring Boot"]
      },
      {
        "req_id": "R2",
        "text": "Connaissance du domaine bancaire",
        "category": "compliance",
        "tech_keywords": []
      }
    ],
    "top_k": 5
  }'
```

**Response:**

```json
{
  "tender_id": "TENDER-003",
  "title": "Migration du système bancaire",
  "requirement_matches": [
    {
      "req_id": "R1",
      "req_text": "...",
      "matches": [...],
      "best_score": 0.035,
      "coverage": "covered"
    }
  ],
  "coverage_matrix": [
    {"req_id": "R1", "asset_id": "CV-001", "asset_type": "cv", "score": 0.035, "status": "covered"}
  ],
  "fit_score": 0.75,
  "no_match": false,
  "covered_count": 1,
  "partial_count": 1,
  "not_covered_count": 0,
  "total_requirements": 2,
  "staffing_suggestions": [
    {
      "cv_id": "CV-001",
      "name": "Ahmed Ben Ali",
      "title": "Senior Java Developer",
      "requirements_covered": ["R1", "R2"],
      "coverage_count": 2,
      "skills_matched": ["java", "spring boot"],
      "skills_gap": []
    }
  ]
}
```

## Ingest API (default: http://localhost:8002)

### GET /health

```bash
curl http://localhost:8002/health
```

### POST /tenders/ingest

Ingest one or more tender items. Deduplicates by ID.

```bash
curl -X POST http://localhost:8002/tenders/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "id": "APPELOFFRES-778613",
        "source": "simulated",
        "description": "Acquisition de matériels informatiques",
        "country": "Tunisie",
        "published_date": "24/09/2026"
      }
    ]
  }'
```

**Response:**

```json
{
  "results": [
    {"tender_id": "APPELOFFRES-778613", "status": "new", "message": "Ingested (structuring: pending)"}
  ],
  "new_count": 1,
  "duplicate_count": 0,
  "error_count": 0
}
```

### POST /tenders/structure

Structure an already-ingested tender via LLM.

```bash
curl -X POST http://localhost:8002/tenders/structure \
  -H "Content-Type: application/json" \
  -d '{"tender_id": "APPELOFFRES-778613", "force": false}'
```

### GET /tenders

List all ingested tenders.

```bash
curl "http://localhost:8002/tenders?limit=10&source=simulated"
```

### GET /tenders/{tender_id}

Get a specific tender by ID.

```bash
curl http://localhost:8002/tenders/APPELOFFRES-778613
```
