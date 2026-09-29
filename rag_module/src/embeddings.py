"""
Pluggable embedding backends.

Two implementations:
- TfidfBackend: works offline, lexical only.
- E5Backend: intfloat/multilingual-e5-* for cross-lingual dense retrieval.

Selected via EMBEDDING_BACKEND env var (default: tfidf).
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingBackend(ABC):
    """Abstract embedding backend interface."""

    @abstractmethod
    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        """
        Encode a list of texts into vectors.

        Args:
            texts: list of strings to encode
            is_query: if True, texts are queries; if False, passages/documents.
                      (E5 requires different prefixes for queries vs passages.)

        Returns:
            np.ndarray of shape (len(texts), dim)
        """
        ...

    @abstractmethod
    def dim(self) -> int:
        """Return embedding dimensionality."""
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class TfidfBackend(EmbeddingBackend):
    """
    TF-IDF based embedding backend.

    Works offline, no model download needed.  Lexical matching only.
    Must call fit() with corpus before encode().
    """

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self._vectorizer = TfidfVectorizer(
            max_features=10_000,
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"(?u)\b\w[\w#.+/]*\b",  # Keep C#, .NET, CI/CD
        )
        self._fitted = False
        self._dim: int = 0

    def fit(self, corpus: List[str]) -> "TfidfBackend":
        """Fit the TF-IDF vectorizer on the corpus."""
        self._vectorizer.fit(corpus)
        self._fitted = True
        self._dim = len(self._vectorizer.vocabulary_)
        logger.info("TfidfBackend fitted with %d features", self._dim)
        return self

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("TfidfBackend.fit() must be called before encode()")
        matrix = self._vectorizer.transform(texts)
        return matrix.toarray().astype(np.float32)

    def dim(self) -> int:
        return self._dim


class E5Backend(EmbeddingBackend):
    """
    intfloat/multilingual-e5-* dense embedding backend.

    Supports batch encoding, model caching, device auto-detection.
    Degrades gracefully if model cannot be loaded (raises clear error on init).

    Configure model via E5_MODEL env var:
      - intfloat/multilingual-e5-small  (471M)
      - intfloat/multilingual-e5-base   (1.1G)
      - intfloat/multilingual-e5-large  (2.2G)  [default]
    """

    # Prefixes required by E5 models
    QUERY_PREFIX = "query: "
    PASSAGE_PREFIX = "passage: "

    def __init__(self, model_name: Optional[str] = None, batch_size: int = 32):
        self._model_name = model_name or os.getenv(
            "E5_MODEL", "intfloat/multilingual-e5-base"
        )
        self._batch_size = batch_size
        self._model = None
        self._tokenizer = None
        self._device = None
        self._embedding_dim: int = 0

        self._load_model()

    def _load_model(self):
        """Load model with clear error messages."""
        try:
            import torch
            from transformers import AutoModel, AutoTokenizer
        except ImportError as e:
            raise RuntimeError(
                f"E5Backend requires 'torch' and 'transformers' packages. "
                f"Install with: pip install torch transformers\n"
                f"Original error: {e}"
            ) from e

        # Auto-detect device
        if torch.cuda.is_available():
            self._device = torch.device("cuda")
            logger.info("E5Backend: using CUDA GPU")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self._device = torch.device("mps")
            logger.info("E5Backend: using Apple MPS")
        else:
            self._device = torch.device("cpu")
            logger.info("E5Backend: using CPU")

        try:
            logger.info("Loading E5 model: %s", self._model_name)
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
            self._model = AutoModel.from_pretrained(self._model_name)
            self._model.to(self._device)
            self._model.eval()

            # Determine embedding dim from config
            self._embedding_dim = self._model.config.hidden_size
            logger.info(
                "E5Backend loaded: %s (dim=%d, device=%s)",
                self._model_name,
                self._embedding_dim,
                self._device,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load E5 model '{self._model_name}'. "
                f"This may be due to no internet access or insufficient disk space. "
                f"Set EMBEDDING_BACKEND=tfidf to use the offline backend.\n"
                f"Original error: {e}"
            ) from e

    def encode(self, texts: List[str], is_query: bool = False) -> np.ndarray:
        import torch

        prefix = self.QUERY_PREFIX if is_query else self.PASSAGE_PREFIX
        prefixed = [f"{prefix}{t}" for t in texts]

        all_embeddings = []
        for i in range(0, len(prefixed), self._batch_size):
            batch = prefixed[i : i + self._batch_size]
            encoded = self._tokenizer(
                batch,
                max_length=512,
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(self._device)

            with torch.no_grad():
                outputs = self._model(**encoded)
                # Mean pooling over token embeddings (masked)
                attention_mask = encoded["attention_mask"]
                token_embeddings = outputs.last_hidden_state
                input_mask_expanded = (
                    attention_mask.unsqueeze(-1)
                    .expand(token_embeddings.size())
                    .float()
                )
                summed = torch.sum(token_embeddings * input_mask_expanded, dim=1)
                counts = torch.clamp(input_mask_expanded.sum(dim=1), min=1e-9)
                embeddings = summed / counts

                # L2 normalize
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                all_embeddings.append(embeddings.cpu().numpy())

        return np.vstack(all_embeddings).astype(np.float32)

    def dim(self) -> int:
        return self._embedding_dim


def get_backend(name: Optional[str] = None) -> EmbeddingBackend:
    """
    Factory function. Returns the configured embedding backend.

    Args:
        name: 'tfidf' or 'e5'. Defaults to EMBEDDING_BACKEND env var.

    Returns:
        An EmbeddingBackend instance.

    Raises:
        RuntimeError if E5 is requested but cannot be loaded.
    """
    backend_name = (name or os.getenv("EMBEDDING_BACKEND", "tfidf")).lower().strip()

    if backend_name == "tfidf":
        logger.info("Using TF-IDF embedding backend")
        return TfidfBackend()
    elif backend_name == "e5":
        logger.info("Using E5 embedding backend")
        return E5Backend()
    else:
        raise ValueError(
            f"Unknown embedding backend: '{backend_name}'. "
            f"Choose 'tfidf' or 'e5'."
        )
