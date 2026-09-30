@echo off
echo ========================================================
echo   Starting CSTAM OliveSoft RFP Intelligence Platform
echo ========================================================

echo [1/3] Starting RAG Search & Match Service (Port 8000)...
start "OliveSoft RAG Service (:8000)" cmd /k "cd /d %~dp0rag_module && .venv\Scripts\python.exe -m uvicorn src.api:app --host 0.0.0.0 --port 8000"

echo [2/3] Starting Ingestion & Structuring Service (Port 8001)...
start "OliveSoft Ingest Service (:8001)" cmd /k "cd /d %~dp0rag_module && .venv\Scripts\python.exe -m uvicorn src.ingest_api:app --host 0.0.0.0 --port 8001"

echo [3/3] Starting n8n Workflow Orchestrator (Port 5678)...
start "OliveSoft n8n Orchestrator (:5678)" cmd /k "cd /d %~dp0 && start_n8n.bat"

echo.
echo ========================================================
echo All services have been launched!
echo   - RAG Service & Docs:    http://localhost:8000/docs
echo   - Ingest Service & Docs: http://localhost:8001/docs
echo   - n8n Workflow UI:       http://localhost:5678/
echo ========================================================
echo.
pause
