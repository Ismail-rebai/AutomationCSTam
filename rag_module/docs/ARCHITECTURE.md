# Architecture — OliveSoft RAG Module

## System Overview

The RAG module provides hybrid semantic search over OliveSoft's internal knowledge base, matching tender requirements against available expertise (CVs, past projects, client portfolios, technical stack).

## Architecture Diagram

```mermaid
graph TB
    subgraph "Tender Sources"
        TS1["Simulated Feed (JSON/CSV)"]
        TS2["Official Ministry / TUNEPS Pages"]
        TS3["n8n Cron Workflow"]
    end

    subgraph "Ingestion Layer"
        IA["Ingest API<br/>(FastAPI :8002)"]
        DB["SQLite<br/>(Dedup + Storage)"]
        ST["Structuring Engine<br/>(Groq LLM)"]
    end

    subgraph "RAG Core"
        EMB["Embedding Backend<br/>(TF-IDF | E5 Multilingual)"]
        BM25["BM25 Sparse Index<br/>(rank_bm25)"]
        QD["Qdrant Dense Index<br/>(Server | In-Memory)"]
        FUS["Fusion Engine<br/>(RRF | Weighted)"]
        RR["Cross-Encoder Reranker<br/>(Optional)"]
    end

    subgraph "Knowledge Base"
        CV["CVs (24)"]
        PR["Projects (14)"]
        CL["Clients (8)"]
        TE["Tech Stack (22)"]
    end

    subgraph "RAG API (FastAPI :8001)"
        SEARCH["/search"]
        MATCH["/match-tender"]
        HEALTH["/health"]
    end

    subgraph "Consumers (Teammates)"
        PRA["Prospect Research Agent"]
        DG["Deck Generator"]
        UI["Review UI"]
    end

    TS1 --> IA
    TS2 --> IA
    TS3 --> IA

    IA --> DB
    IA --> ST
    ST -->|"Groq API"| DB

    CV --> EMB
    PR --> EMB
    CL --> EMB
    TE --> EMB

    EMB --> QD
    EMB --> BM25

    SEARCH --> FUS
    MATCH --> FUS
    FUS --> QD
    FUS --> BM25
    FUS --> RR

    MATCH --> PRA
    MATCH --> DG
    SEARCH --> UI
```

## Data Flow

### 1. Ingestion → Structuring → Indexing

```mermaid
sequenceDiagram
    participant N as n8n Workflow
    participant I as Ingest API
    participant DB as SQLite
    participant G as Groq LLM
    participant R as RAG Index

    N->>I: POST /tenders/ingest (raw items)
    I->>DB: Check dedup (tender_id PK)
    alt New tender
        I->>DB: INSERT raw_data
        alt STRUCTURE_ON_INGEST=true
            I->>G: Extract structured schema
            G-->>I: StructuredTender JSON
            I->>DB: UPDATE structured_data
        end
        I-->>N: {status: "new"}
    else Duplicate
        I-->>N: {status: "duplicate"}
    end

    Note over R: KB indexed at startup from JSON files
    Note over R: Tenders indexed on-demand via /match-tender
```

### 2. Retrieval → Matching

```mermaid
sequenceDiagram
    participant C as Client (n8n / UI)
    participant A as RAG API
    participant E as Embeddings
    participant Q as Qdrant
    participant B as BM25
    participant F as Fusion

    C->>A: POST /match-tender (requirements[])
    loop For each requirement
        A->>E: Encode query
        E-->>A: Query vector
        A->>Q: Dense search (per asset_type)
        Q-->>A: Dense results
        A->>B: BM25 search (per asset_type)
        B-->>A: Sparse results
        A->>F: Fuse (RRF / Weighted)
        F-->>A: Fused ranking
    end
    A-->>C: Coverage matrix + fit score + staffing
```

## Component Details

### Embedding Backends

| Backend | Model | Dim | Cross-lingual | Offline |
|---------|-------|-----|---------------|---------|
| TF-IDF | scikit-learn | 10K | ❌ Lexical only | ✅ |
| E5 | intfloat/multilingual-e5-* | 384-1024 | ✅ FR↔EN | ❌ (download) |

### Fusion Methods

| Method | Algorithm | Strengths |
|--------|-----------|-----------|
| RRF (default) | 1/(k+rank) summed across rankings | Scale-invariant, robust |
| Weighted | α·norm(dense) + (1-α)·norm(BM25) | Tunable, interpretable |

### Storage

| Store | Technology | Purpose |
|-------|-----------|---------|
| KB Documents | JSON files | CVs, Projects, Clients, Tech Stack |
| Ingested Tenders | SQLite | Dedup (PK), raw + structured data |
| Dense Vectors | Qdrant | Approximate nearest neighbor search |
| Sparse Index | rank_bm25 (in-memory) | BM25 term-frequency search |

### Tokenizer (BM25)

Pipeline: lowercase → accent folding → tech token protection → punctuation strip → stopword removal

Protected tech tokens: `C#`, `.NET`, `Node.js`, `CI/CD`, `S/4HANA`, `FI/CO`, `Spring Boot`, `Power BI`, etc.
