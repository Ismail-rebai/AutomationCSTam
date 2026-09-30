@echo off
set N8N_PORT=5678
set N8N_HOST=localhost
set N8N_PROTOCOL=http
set WEBHOOK_URL=http://localhost:5678/
set N8N_DIAGNOSTICS_ENABLED=false
set N8N_PERSONALIZATION_ENABLED=false
set INGEST_API_URL=http://localhost:8001
set RAG_API_URL=http://localhost:8000
"C:\Program Files\nodejs\npx.cmd" n8n start
