# CSTAM 3.0 — OliveSoft RFP Intelligence & Proposal Generation

**Competition:** IEEE Computer Society Tunisian Annual Meeting (CSTAM 3.0)  
**Challenge:** CSTAM-OliveSoft — *Automated RFP Intelligence & Commercial Proposal Generation System*  
**Team Solution:** End-to-End Orchestrated AI Pipeline connecting Multi-Source Tender Detection, LLM Pre-Filtering, OliveSoft RAG Capability Matching, and Automated Proposal Briefing.

---

## 📁 Repository Structure

- 📁 [**`n8n/`**](./n8n): Workflow automation orchestrator.
  - `Tender Detection.json`: Main workflow detecting tenders from TED Europa and public portals, pre-classifying with Groq LLM, evaluating OliveSoft capability fit via RAG, and generating proposal briefs.
  - `docker-compose.yml`: Multi-container n8n deployment with persistent volume.
- 📁 [**`rag_module/`**](./rag_module): Production-grade RAG & intelligence microservices.
  - `src/api.py`: FastAPI RAG retrieval service (`/search`, `/match-tender`, `/health`).
  - `src/hybrid_index.py`: Qdrant dense + BM25 sparse hybrid retrieval with Reciprocal Rank Fusion (RRF).
  - `data/`: 68 OliveSoft internal knowledge base assets (24 CVs, 14 projects, 8 clients, 22 tech stack profiles).
  - `tests/`: Comprehensive test suite (57 passing tests).
  - `docs/`: Architecture diagrams, API specs, jury demo script, and limitations.

---

## 🚀 Quickstart

### 1. Start the RAG Backend (:8000)
```bash
cd rag_module
pip install -r requirements.txt
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

### 2. Start n8n Orchestrator (:5678)
```bash
cd n8n
docker compose up -d
```
Open **`http://localhost:5678`** in your browser, import `n8n/Tender Detection.json`, and run the workflow.
