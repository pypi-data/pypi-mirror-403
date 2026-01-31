"""
Embedding Model Module
======================

Provides sentence transformer embedding functionality for semantic task search.
Uses lazy loading with background preload for fast server startup.
"""

import threading
from typing import List, Union, Optional
import numpy as np


class EmbeddingModelNotReadyError(Exception):
    """Raised when embedding model not loaded and timeout exceeded."""
    pass


class LazyEmbeddingModel:
    """Lazy-loading embedding model with background initialization."""

    def __init__(self, model_name: str, preload: bool = True):
        """
        Initialize lazy embedding model.

        Args:
            model_name: HuggingFace model name (e.g., 'sentence-transformers/all-MiniLM-L6-v2')
            preload: If True, start loading model in background immediately
        """
        self.model_name = model_name
        self._model = None
        self._lock = threading.Lock()
        self._ready_event = threading.Event()
        self._load_error: Optional[Exception] = None

        if preload:
            self._start_background_load()

    def _start_background_load(self) -> None:
        """Start model loading in background thread."""
        thread = threading.Thread(target=self._load_model, daemon=True)
        thread.start()

    def _load_model(self) -> None:
        """Load the model (runs in background thread)."""
        try:
            # DEFERRED IMPORT - only happens in background thread
            # This is the key optimization: sentence_transformers import is slow
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(self.model_name)
            with self._lock:
                self._model = model
                self._ready_event.set()
        except Exception as e:
            with self._lock:
                self._load_error = e
                self._ready_event.set()

    def _ensure_model(self, timeout: float = 30.0):
        """
        Ensure model is loaded, waiting up to timeout seconds.

        Args:
            timeout: Maximum seconds to wait for model

        Returns:
            Loaded SentenceTransformer model

        Raises:
            EmbeddingModelNotReadyError: If model not ready within timeout
        """
        if not self._ready_event.wait(timeout=timeout):
            raise EmbeddingModelNotReadyError(
                f"Embedding model not ready after {timeout}s. Try again shortly."
            )
        if self._load_error:
            raise EmbeddingModelNotReadyError(
                f"Failed to load embedding model: {self._load_error}"
            )
        return self._model

    def encode(self, text: Union[str, List[str]], timeout: float = 30.0) -> np.ndarray:
        """
        Encode text to embedding vector(s).

        Args:
            text: Single text string or list of texts
            timeout: Maximum seconds to wait for model

        Returns:
            Numpy array of embeddings (1D for single text, 2D for list)

        Raises:
            EmbeddingModelNotReadyError: If model not ready within timeout
        """
        model = self._ensure_model(timeout)
        embeddings = model.encode(text, convert_to_numpy=True)
        # Ensure float32 for sqlite-vec compatibility
        return embeddings.astype(np.float32)

    def encode_single(self, text: str, timeout: float = 30.0) -> np.ndarray:
        """
        Encode single text to embedding vector.

        Args:
            text: Single text string
            timeout: Maximum seconds to wait for model

        Returns:
            Numpy array of embedding (1D float32)

        Raises:
            EmbeddingModelNotReadyError: If model not ready within timeout
        """
        return self.encode(text, timeout)

    def get_embedding_dim(self, timeout: float = 30.0) -> int:
        """
        Get embedding dimension.

        Args:
            timeout: Maximum seconds to wait for model

        Returns:
            Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        model = self._ensure_model(timeout)
        return model.get_sentence_embedding_dimension()

    def is_ready(self) -> bool:
        """
        Check if model is loaded and ready.

        Returns:
            True if model is ready for encoding
        """
        return self._ready_event.is_set() and self._model is not None and self._load_error is None


def get_embedding_model(model_name: str, preload: bool = True) -> LazyEmbeddingModel:
    """
    Factory function to get embedding model instance.

    Args:
        model_name: HuggingFace model name
        preload: If True, start loading model in background immediately

    Returns:
        Initialized LazyEmbeddingModel instance
    """
    return LazyEmbeddingModel(model_name, preload=preload)
