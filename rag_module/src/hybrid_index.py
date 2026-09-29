"""
Hybrid search index: Qdrant (dense) + BM25 (sparse), fused.

Supports two fusion strategies:
- Reciprocal Rank Fusion (RRF) — default, robust to score scale differences.
- Weighted linear fusion with min-max normalization (legacy).

Optional cross-encoder reranker hook for precision boost.
"""

import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from rank_bm25 import BM25Okapi

from .documents import KBRecord
from .embeddings import EmbeddingBackend, TfidfBackend
from .tokenizer import tokenize

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    record_id: str
    record_type: str
    score: float
    text: str
    metadata: Dict[str, Any]


class HybridIndex:
    """
    Hybrid dense + sparse search index.

    Dense: Qdrant (server or local/in-memory fallback).
    Sparse: BM25Okapi with improved tokenizer.
    """

    def __init__(
        self,
        backend: EmbeddingBackend,
        collection_name: str = "olivesoft_kb",
        qdrant_url: Optional[str] = None,
        fusion_method: Optional[str] = None,
        dense_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        self.backend = backend
        self.collection_name = collection_name
        self.fusion_method = (
            fusion_method
            or os.getenv("FUSION_METHOD", "rrf")
        ).lower()
        self.dense_weight = dense_weight
        self.rrf_k = int(os.getenv("RRF_K", str(rrf_k)))

        # BM25 state
        self._bm25: Optional[BM25Okapi] = None
        self._bm25_corpus_tokens: List[List[str]] = []

        # Record storage (id -> KBRecord)
        self._records: Dict[str, KBRecord] = {}
        self._record_ids: List[str] = []  # ordered, same as Qdrant point order

        # Qdrant client
        self._qdrant = None
        self._qdrant_url = qdrant_url or os.getenv("QDRANT_URL", "")
        self._init_qdrant()

        # Cross-encoder reranker (lazy-loaded)
        self._reranker = None
        self._reranker_model_name = os.getenv("RERANKER_MODEL", "")

    def _init_qdrant(self):
        """Initialize Qdrant client with server → local → memory fallback."""
        from qdrant_client import QdrantClient

        if self._qdrant_url:
            try:
                self._qdrant = QdrantClient(url=self._qdrant_url, timeout=5)
                # Test connection
                self._qdrant.get_collections()
                logger.info("Connected to Qdrant server: %s", self._qdrant_url)
                return
            except Exception as e:
                logger.warning(
                    "Cannot connect to Qdrant at %s: %s. Falling back to in-memory.",
                    self._qdrant_url,
                    e,
                )

        # Fallback: in-memory
        self._qdrant = QdrantClient(location=":memory:")
        logger.info("Using Qdrant in-memory mode")

    def build(self, records: List[KBRecord]) -> "HybridIndex":
        """
        Index all KB records.

        Args:
            records: list of KBRecord to index.

        Returns:
            self for chaining.
        """
        if not records:
            logger.warning("No records to index")
            return self

        self._records = {r.record_id: r for r in records}
        self._record_ids = [r.record_id for r in records]

        texts = [r.text for r in records]

        # --- Build BM25 index ---
        self._bm25_corpus_tokens = [tokenize(t) for t in texts]
        self._bm25 = BM25Okapi(self._bm25_corpus_tokens)
        logger.info("BM25 index built with %d documents", len(records))

        # --- Build dense index ---
        if isinstance(self.backend, TfidfBackend):
            self.backend.fit(texts)

        vectors = self.backend.encode(texts, is_query=False)

        # Create/recreate Qdrant collection
        from qdrant_client.models import Distance, PointStruct, VectorParams

        # Delete if exists
        try:
            self._qdrant.delete_collection(self.collection_name)
        except Exception:
            pass

        self._qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vectors.shape[1],
                distance=Distance.COSINE,
            ),
        )

        # Upload points
        points = []
        for i, rec in enumerate(records):
            points.append(
                PointStruct(
                    id=i,
                    vector=vectors[i].tolist(),
                    payload={
                        "record_id": rec.record_id,
                        "record_type": rec.record_type,
                        "text": rec.text[:500],  # truncate for payload size
                        "metadata": rec.metadata,
                    },
                )
            )

        # Batch upload
        batch_size = 100
        for i in range(0, len(points), batch_size):
            self._qdrant.upsert(
                collection_name=self.collection_name,
                points=points[i : i + batch_size],
            )

        logger.info(
            "Dense index built: %d vectors of dim %d",
            len(records),
            vectors.shape[1],
        )

        return self

    def search(
        self,
        query: str,
        top_k: int = 10,
        asset_type: Optional[str] = None,
        dense_weight: Optional[float] = None,
        fusion_method: Optional[str] = None,
        rerank: bool = False,
    ) -> List[SearchResult]:
        """
        Hybrid search: dense + BM25, fused.

        Args:
            query: search query string.
            top_k: number of results to return.
            asset_type: filter by record type (cv, past_project, client, tech_stack).
            dense_weight: override default dense weight (for weighted fusion).
            fusion_method: override default fusion method ('rrf' or 'weighted').
            rerank: if True, apply cross-encoder reranking.

        Returns:
            List of SearchResult, sorted by score descending.
        """
        if not self._records:
            return []

        dw = dense_weight if dense_weight is not None else self.dense_weight
        fm = (fusion_method or self.fusion_method).lower()

        # --- Dense search (retrieve more than top_k for fusion) ---
        fetch_k = min(top_k * 3, len(self._records))
        dense_results = self._dense_search(query, fetch_k, asset_type)

        # --- BM25 search ---
        bm25_results = self._bm25_search(query, fetch_k, asset_type)

        # --- Fusion ---
        if fm == "rrf":
            fused = self._rrf_fuse(dense_results, bm25_results, top_k)
        else:
            fused = self._weighted_fuse(dense_results, bm25_results, dw, top_k)

        # --- Optional reranking ---
        if rerank and fused:
            fused = self._rerank(query, fused, top_k)

        return fused[:top_k]

    def _dense_search(
        self, query: str, top_k: int, asset_type: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """Dense vector search via Qdrant."""
        query_vector = self.backend.encode([query], is_query=True)[0]

        # Build filter
        query_filter = None
        if asset_type:
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="record_type",
                        match=MatchValue(value=asset_type),
                    )
                ]
            )

        if hasattr(self._qdrant, "query_points"):
            response = self._qdrant.query_points(
                collection_name=self.collection_name,
                query=query_vector.tolist(),
                limit=top_k,
                query_filter=query_filter,
            )
            results = response.points
        else:
            results = self._qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=top_k,
                query_filter=query_filter,
            )

        # Only keep results with positive similarity score
        return [(r.payload["record_id"], r.score) for r in results if r.score > 0.05]

    def _bm25_search(
        self, query: str, top_k: int, asset_type: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """BM25 sparse search."""
        if self._bm25 is None:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)

        # Pair with record ids and optionally filter
        scored = []
        for i, score in enumerate(scores):
            if score <= 0.0:
                continue
            rid = self._record_ids[i]
            rec = self._records[rid]
            if asset_type and rec.record_type != asset_type:
                continue
            scored.append((rid, float(score)))

        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _rrf_fuse(
        self,
        dense_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        top_k: int,
    ) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion.

        RRF score for document d = sum over rankings R:
            1 / (k + rank_R(d))

        where k is a constant (default 60).
        """
        k = self.rrf_k
        rrf_scores: Dict[str, float] = {}

        for rank, (rid, _) in enumerate(dense_results):
            rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (k + rank + 1)

        for rank, (rid, _) in enumerate(bm25_results):
            rrf_scores[rid] = rrf_scores.get(rid, 0.0) + 1.0 / (k + rank + 1)

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        results = []
        for rid, score in sorted_ids[:top_k]:
            rec = self._records.get(rid)
            if rec:
                results.append(
                    SearchResult(
                        record_id=rec.record_id,
                        record_type=rec.record_type,
                        score=score,
                        text=rec.text,
                        metadata=rec.metadata,
                    )
                )
        return results

    def _weighted_fuse(
        self,
        dense_results: List[Tuple[str, float]],
        bm25_results: List[Tuple[str, float]],
        dense_weight: float,
        top_k: int,
    ) -> List[SearchResult]:
        """
        Weighted linear fusion with min-max normalization.

        fused_score = dense_weight * norm(dense_score) + (1 - dense_weight) * norm(bm25_score)
        """
        def _normalize(scored: List[Tuple[str, float]]) -> Dict[str, float]:
            if not scored:
                return {}
            scores = [s for _, s in scored]
            min_s, max_s = min(scores), max(scores)
            rng = max_s - min_s
            if rng < 1e-9:
                # All scores equal — assign 0.5 to avoid collapse
                return {rid: 0.5 for rid, _ in scored}
            return {rid: (s - min_s) / rng for rid, s in scored}

        dense_norm = _normalize(dense_results)
        bm25_norm = _normalize(bm25_results)

        # Combine
        all_ids = set(dense_norm.keys()) | set(bm25_norm.keys())
        combined: Dict[str, float] = {}
        for rid in all_ids:
            d_score = dense_norm.get(rid, 0.0)
            b_score = bm25_norm.get(rid, 0.0)
            combined[rid] = dense_weight * d_score + (1 - dense_weight) * b_score

        sorted_ids = sorted(combined.items(), key=lambda x: x[1], reverse=True)

        results = []
        for rid, score in sorted_ids[:top_k]:
            rec = self._records.get(rid)
            if rec:
                results.append(
                    SearchResult(
                        record_id=rec.record_id,
                        record_type=rec.record_type,
                        score=score,
                        text=rec.text,
                        metadata=rec.metadata,
                    )
                )
        return results

    def _rerank(
        self, query: str, results: List[SearchResult], top_k: int
    ) -> List[SearchResult]:
        """
        Cross-encoder reranking (optional, off by default).

        Enable by setting RERANKER_MODEL env var to a cross-encoder model name.
        """
        if not self._reranker_model_name:
            return results

        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder

                self._reranker = CrossEncoder(self._reranker_model_name)
                logger.info("Loaded cross-encoder reranker: %s", self._reranker_model_name)
            except Exception as e:
                logger.warning("Cannot load reranker %s: %s", self._reranker_model_name, e)
                return results

        pairs = [(query, r.text[:512]) for r in results]
        rerank_scores = self._reranker.predict(pairs)

        for i, score in enumerate(rerank_scores):
            results[i].score = float(score)

        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def get_record(self, record_id: str) -> Optional[KBRecord]:
        """Get a specific record by ID."""
        return self._records.get(record_id)

    @property
    def record_count(self) -> int:
        return len(self._records)

    @property
    def records(self) -> Dict[str, KBRecord]:
        return self._records
