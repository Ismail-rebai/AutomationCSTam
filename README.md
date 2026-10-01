# CSTAM 3.0 — OliveSoft RFP Intelligence & Proposal Generation

**Competition:** IEEE Computer Society Tunisian Annual Meeting (CSTAM 3.0)  
**Challenge:** CSTAM-OliveSoft — *Automated RFP Intelligence & Commercial Proposal Generation System*  
**Team Solution:** End-to-End Orchestrated AI Pipeline connecting Multi-Source Tender Detection, Agentic Prospect Research, OliveSoft RAG Capability Matching, Executive Sales Review Dashboard, and Automated Commercial PowerPoint Proposal Generation (.pptx).

---

## 🌟 Key Highlights & Capabilities

- 📊 **Executive Sales Review Dashboard (:8000/dashboard)**: Modern, dark-mode, glassmorphic UI for sales managers to review incoming tenders, inspect RAG coverage matrices, review buyer dossiers, and download proposal decks with 1 click.
- 🔍 **Hybrid Cross-Lingual RAG Engine**: Qdrant dense vector search + BM25 sparse lexical search with technical token preservation and French accent folding, fused via Reciprocal Rank Fusion (RRF, $k=60$) over 68 OliveSoft internal assets (24 CVs, 14 projects, 8 clients, 22 tech profiles).
- 🤖 **Agentic Prospect Research**: Autonomous agent (Serper + Groq LLM) extracting buyer sector, budget scale, pain points, strategic goals, and evaluation criteria.
- 📑 **Automated Commercial Proposal Generator (.pptx)**: Multi-agent synthesis creating branded 8-slide PowerPoint presentations with role-based TND pricing and duration in weeks.
- ⚡ **Master n8n Orchestrator**: Modular architecture connecting 4 sub-workflows (Detection $\to$ Research $\to$ RAG $\to$ Deliverable).
- 🛡️ **Tested & Calibrated**: **66/66 unit and integration tests passing green** (`pytest tests/ -v`).

---

## 📁 Repository Structure

- 📁 [**`n8n/`**](./n8n): Master Orchestrator and sub-workflows.
  - `RFP Intelligence Orchestrator.json`: Master orchestration pipeline.
  - `Tender Detection.json`: Multi-source crawler (TED Europa + public procurement) and LLM classifier.
  - `Prospect Research.json`: Buyer intelligence and dossier agent.
  - `RAG & Proposal Engine.json`: RAG capability matching and deck generation.
- 📁 [**`rag_module/`**](./rag_module): Production-grade RAG & intelligence microservices.
  - `src/api.py`: FastAPI RAG retrieval service (`/search`, `/match-tender`, `/dashboard`, `/proposals/download/{id}`).
  - `src/templates/dashboard.html`: Executive Sales Review Dashboard UI.
  - `src/pptx_builder.py` & `src/proposal_generator.py`: 8-slide PowerPoint deck generator.
  - `data/`: 68 OliveSoft internal knowledge base assets.
  - `tests/`: Comprehensive test suite (66 passing tests).
- 📄 **`run_all.bat`**: 1-click startup script for RAG API, Ingest API, and n8n.
- 📄 **`run_pipeline.py`**: Automated end-to-end runner generating PowerPoint decks for all benchmark tenders.

---

## 🚀 Quickstart

### 0. Environment Setup (API Keys)
Create your local `.env` file from the provided template:
```bash
copy .env.example .env
```
Fill in your free API keys for [Groq](https://console.groq.com/keys) (`GROQ_API_KEY`) and [Serper](https://serper.dev) (`SERPER_API_KEY`).

### Option 1: 1-Click Launch (Windows)
Double-click or run:
```cmd
run_all.bat
```
Then open:
* **Executive Sales Dashboard:** `http://localhost:8000/dashboard`
* **n8n Orchestrator UI:** `http://localhost:5678/`
* **FastAPI Interactive Docs:** `http://localhost:8000/docs`

### Option 2: Run End-to-End Pipeline in Terminal
```bash
python run_pipeline.py
```
Automatically matches all benchmark tenders, evaluates fit scores, and compiles `.pptx` decks into `rag_module/results/proposals/`.

