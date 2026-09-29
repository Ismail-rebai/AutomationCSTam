FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data results

# Default environment
ENV EMBEDDING_BACKEND=tfidf
ENV FUSION_METHOD=rrf
ENV PYTHONUNBUFFERED=1

# Expose ports
EXPOSE 8001 8002

# Default command: run RAG API
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8001"]
