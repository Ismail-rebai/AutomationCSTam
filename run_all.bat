@echo off
echo ========================================================
echo   Starting CSTAM OliveSoft RFP Intelligence Platform
echo ========================================================

set PY_CMD=python
if exist "%~dp0rag_module\.venv\Scripts\python.exe" set PY_CMD="%~dp0rag_module\.venv\Scripts\python.exe"

echo [1/3] Starting RAG & Dashboard Service (Port 8000)...
start "OliveSoft RAG Service (:8000)" cmd /k "cd /d %~dp0rag_module && %PY_CMD% -m uvicorn src.api:app --host 0.0.0.0 --port 8000"

echo [2/3] Starting Ingestion Service (Port 8001)...
start "OliveSoft Ingest Service (:8001)" cmd /k "cd /d %~dp0rag_module && %PY_CMD% -m uvicorn src.ingest_api:app --host 0.0.0.0 --port 8001"

echo [3/3] Starting n8n in Docker (Port 5678)...
docker compose -f "%~dp0n8n\docker-compose.yml" up -d

echo.
echo Waiting 3 seconds for services to initialize...
timeout /t 3 /nobreak >nul

echo Opening Executive Dashboard and n8n in your browser...
start http://localhost:8000/dashboard
start http://localhost:5678/

echo.
echo ========================================================
echo All services have been launched!
echo   - Executive Sales Dashboard: http://localhost:8000/dashboard
echo   - n8n Workflow UI:           http://localhost:5678/
echo   - RAG Interactive Docs:      http://localhost:8000/docs
echo   - Ingest Interactive Docs:   http://localhost:8001/docs
echo ========================================================
echo.
pause

