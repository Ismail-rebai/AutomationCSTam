# n8n Integration — OliveSoft RAG Module

## Overview

Two n8n workflow JSON files are provided for integration with the RAG system:

1. **`rag_integration_workflow.json`** — Production workflow fragment
2. **`demo_simulated_workflow.json`** — Demo workflow using simulated feed

## How to Import

1. Open n8n (typically at `http://localhost:5678`)
2. Go to **Workflows** → **Import from File**
3. Select the desired `.json` file
4. Update environment variables (see below)

## Environment Variables

Set these in n8n's environment or credential configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `INGEST_API_URL` | `http://localhost:8002` | URL of the Ingest API service |
| `RAG_API_URL` | `http://localhost:8001` | URL of the RAG API service |
| `SIMULATED_FEED_URL` | — | URL for tender feed (placeholder) |

If using Docker Compose, the service names resolve automatically:
- `INGEST_API_URL=http://ingest-api:8002`
- `RAG_API_URL=http://rag-api:8001`

## Workflow 1: Production Integration

**File:** `rag_integration_workflow.json`

This workflow attaches after the relevance-classifier `If (true)` branch:

```
Fetch Tender Feed → Relevance Filter → POST /tenders/ingest
    → POST /tenders/structure → POST /match-tender
    → If (has match) → Prospect Research Agent
    → If (no match) → Skip
```

### How to attach to existing workflow

1. Import the workflow
2. Connect the **Fetch Tender Feed** node's input to your existing relevance classifier's `true` output
3. Connect the **→ Prospect Research Agent** output to your teammate's prospect research workflow
4. Update the **Fetch Tender Feed** URL to your actual source (NOT appeloffres.net/.com)

## Workflow 2: Demo with Simulated Feed

**File:** `demo_simulated_workflow.json`

Self-contained demo workflow:
- Runs every 5 minutes (cron trigger)
- Uses 7 hardcoded French tender stubs (no website dependency)
- Deduplicates against already-ingested tenders
- Ingests and matches each new tender

**Use this for the MVP demo video.**

## API Endpoints Used

| Endpoint | Method | Service | Purpose |
|----------|--------|---------|---------|
| `/tenders/ingest` | POST | Ingest API | Store raw tender, dedup by ID |
| `/tenders/structure` | POST | Ingest API | LLM-structure tender into schema |
| `/match-tender` | POST | RAG API | Match requirements against KB |
| `/tenders` | GET | Ingest API | List ingested tenders |
| `/health` | GET | Both | Health check |

## Important Notes

- **No hard-coded source URLs:** The workflow uses environment variable placeholders
- **No scraping of blocked sites:** appeloffres.net/.com are explicitly blocked
- **Fallback structuring:** If no Groq API key is set, structuring falls back to wrapping the description as a single requirement
