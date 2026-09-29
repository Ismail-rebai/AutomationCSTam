# CSTAM 3.0: OliveSoft RFP Intelligence - End-to-End Demo Script

This script provides step-by-step instructions and commands to demonstrate the **RAG Module** for the **CSTAM-OliveSoft: Automated RFP Intelligence & Commercial Proposal Generation System**.

---

## 1. Prerequisites & Environment Setup

### 1.1 Start the RAG Module Services

Open two terminal windows (or run in background):

**Terminal 1 — RAG Retrieval & Matching Service (Port 8000):**
```bash
# Set embedding backend (tfidf for offline/instant mode, e5 for multilingual dense mode)
export EMBEDDING_BACKEND=tfidf
# On Windows PowerShell:
# $env:EMBEDDING_BACKEND="tfidf"

uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Ingestion & Structuring Service (Port 8001):**
```bash
# Ensure GROQ_API_KEY is set for LLM structuring (fallback works automatically without it)
# $env:GROQ_API_KEY="gsk_..."

uvicorn src.ingest_api:app --host 0.0.0.0 --port 8001 --reload
```

---

## 2. Health Checks

Verify both microservices are running and healthy.

### Check RAG Service:
```bash
curl -s http://localhost:8000/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "index_size": 68,
  "backend": "TfidfBackend"
}
```

### Check Ingest Service:
```bash
curl -s http://localhost:8001/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "tender_count": 0,
  "groq_available": false
}
```

---

## 3. Demo Step 1: Hybrid Cross-Lingual & Technical Search (`POST /search`)

Show how the hybrid index retrieves relevant assets from the Knowledge Base (CVs, Past Projects, Client Portfolios, Tech Stack entries) using technical token preservation and French/English query handling.

### Query 1: French banking + Spring Boot query
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Développement et architecture microservices Java Spring Boot pour secteur bancaire",
    "top_k": 3
  }'
```

**What to highlight to the jury:**
- Notice how the search returns both matching CVs (e.g., Senior Java/Spring Boot Engineers with banking experience) and matching past projects (e.g., Core Banking microservices migration).
- The hybrid fusion combines BM25 keyword matching with dense semantic embeddings using Reciprocal Rank Fusion (RRF).

### Query 2: Asset-specific filter (CVs only)
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Consultant SAP S/4HANA certifié FI/CO et ABAP",
    "asset_type": "cv",
    "top_k": 2
  }'
```

**What to highlight:**
- Strict asset filtering isolates only consultant profiles.
- Technical token handling preserves terms like `S/4HANA` and `FI/CO` without breaking on slashes or punctuation.

---

## 4. Demo Step 2: Tender Ingestion & Structuring (`POST /tenders/structure`)

Demonstrate extracting structured requirements, technical tags, and evaluation criteria from raw French tender text.

```bash
curl -X POST http://localhost:8001/tenders/structure \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Appel d offres: Modernisation du portail e-gouvernement. Lot 1: Développement web réactif sous React et Node.js. Lot 2: Sécurisation et authentification SSO conforme RGPD. Lot 3: Mise en place d une infrastructure cloud Docker et Kubernetes. Délais: 6 mois. Expérience minimale exigée: 3 ans en projets secteur public.",
    "title_hint": "Portail e-Gouvernement",
    "buyer_hint": "Ministère des Technologies"
  }'
```

**What to highlight:**
- Structured output conforms to Pydantic v2 validation.
- Extracts `requirements` with `req_id`, `text`, `category`, and normalized `tech_keywords` (`["react", "node.js", "docker", "kubernetes", "sso"]`).
- Gracefully works using Groq `llama-3.3-70b-versatile` or instant deterministic NLP fallback when offline.

---

## 5. Demo Step 3: Tender Matching, Coverage Matrix & Staffing (`POST /match-tender`)

This is the centerpiece of the OliveSoft RFP Intelligence system. It takes structured tender requirements, queries the Knowledge Base across all 4 asset dimensions, and builds an exhaustive **Requirement-by-Asset Coverage Matrix**, overall **Fit Score**, and **Staffing Recommendations**.

```bash
curl -X POST http://localhost:8000/match-tender \
  -H "Content-Type: application/json" \
  -d '{
    "tender_id": "DEMO-TENDER-003",
    "title": "Migration du système bancaire vers une architecture microservices",
    "requirements": [
      {
        "req_id": "REQ-01",
        "text": "Audit et conception de l architecture cible microservices, API Gateway et orchestrateur",
        "category": "technical",
        "tech_keywords": ["microservices", "api gateway", "architecture"]
      },
      {
        "req_id": "REQ-02",
        "text": "Développement des services core banking avec Java et Spring Boot",
        "category": "technical",
        "tech_keywords": ["java", "spring boot", "banking"]
      },
      {
        "req_id": "REQ-03",
        "text": "Migration des données depuis le système legacy Oracle Forms vers base relationnelle",
        "category": "technical",
        "tech_keywords": ["oracle", "database", "migration"]
      },
      {
        "req_id": "REQ-04",
        "text": "Mise en place de tests de performance et conformité sécurité bancaire",
        "category": "security",
        "tech_keywords": ["security", "pentest", "iso 27001"]
      }
    ],
    "top_k": 3
  }'
```

**Expected Response Breakdown to Highlight:**
1. **`fit_score`**: Calculated between `0.0` and `1.0` based on `(covered_count + 0.5 * partial_count) / total_requirements`. (Typically `0.85` - `1.0` for this core competency tender).
2. **`coverage_matrix`**:
   - Each requirement is mapped against matching CVs, Past Projects, and Client Portfolios with coverage status (`covered`, `partial`, `not_covered`).
3. **`staffing_suggestions`**:
   - OliveSoft team members ranked by requirement coverage.
   - Highlights matched skills (e.g., `["java", "spring boot", "microservices"]`) and identified skills gaps.
4. **`no_match: false`**: Signals to the proposal generator that OliveSoft has strong qualifications to bid on this tender.

---

## 6. Demo Step 4: Irrelevant Tender Handling (`no_match: true`)

Demonstrate the safety mechanism preventing OliveSoft from bidding on completely out-of-scope tenders (e.g. agricultural supply or road construction).

```bash
curl -X POST http://localhost:8000/match-tender \
  -H "Content-Type: application/json" \
  -d '{
    "tender_id": "DEMO-TENDER-OUT-OF-SCOPE",
    "title": "Fourniture de semences agricoles et engrais chimiques",
    "requirements": [
      {
        "req_id": "REQ-AGRI-01",
        "text": "Fourniture de 50 tonnes de blé dur certifié et semences sélectionnées",
        "category": "logistics",
        "tech_keywords": ["agriculture", "semences", "engrais"]
      },
      {
        "req_id": "REQ-AGRI-02",
        "text": "Livraison sur les entrepôts régionaux du ministère de l agriculture",
        "category": "transport",
        "tech_keywords": ["transport", "logistique", "stockage"]
      }
    ]
  }'
```

**Expected Response:**
```json
{
  "tender_id": "DEMO-TENDER-OUT-OF-SCOPE",
  "fit_score": 0.0,
  "no_match": true,
  "covered_count": 0,
  "partial_count": 0,
  "not_covered_count": 2,
  "total_requirements": 2,
  "staffing_suggestions": []
}
```

**What to highlight:**
- `no_match: true` prevents wasted resources drafting non-viable proposals.
- In n8n, this branches to an automated "NO-GO / Disqualified" notification.

---

## 7. Demo Step 5: n8n Workflow Demonstration

Show the jury how the RAG API connects seamlessly to the n8n orchestrator:

1. Open n8n web interface (`http://localhost:5678`).
2. Import `n8n/rag_integration_workflow.json` (or `n8n/demo_simulated_workflow.json`).
3. Walk through the pipeline nodes:
   - **Simulated Tender Feed (Cron / Trigger)**: Emits tender records without scraping forbidden sites.
   - **Ingest & Deduplication Node**: Calls `POST http://localhost:8001/tenders/ingest`.
   - **LLM Structuring Node**: Calls `POST http://localhost:8001/tenders/structure`.
   - **RAG Match Tender Node**: Calls `POST http://localhost:8000/match-tender`.
   - **Decision Switch (Fit Score Check)**:
     - If `fit_score >= 0.5` and `no_match == false` $\to$ Route to **Commercial Proposal Generator Node**.
     - If `no_match == true` $\to$ Route to **Slack / Email Disqualification Notice**.

---

## 8. Summary of Benchmark Results for the Presentation

| Benchmark Metric | TF-IDF + BM25 RRF (Offline) | Multilingual E5-base + BM25 |
|------------------|-----------------------------|------------------------------|
| **Exact Tech Match Recall@10** | **100% (1.000)** | **100% (1.000)** |
| **Exact Tech Match MRR** | **0.9375** | **0.9650** |
| **Overall Hit Rate** | **70.59%** | **94.12%** |
| **Indexing Latency (68 docs)** | **< 150 ms** | **~ 2.4 s (CPU)** |
| **Query Latency** | **< 12 ms** | **~ 35 ms (CPU)** |
| **Out-of-Scope TN Rate** | **100%** | **100%** |

*(Exact live evaluation can be executed during the demo via `python -m src.evaluation`)*.
