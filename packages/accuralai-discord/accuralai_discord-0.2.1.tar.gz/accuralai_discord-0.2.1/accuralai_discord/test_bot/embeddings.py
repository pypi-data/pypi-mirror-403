"""Embedding service using Google GenAI for RAG functionality."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

LOGGER = logging.getLogger("accuralai.discord.test")

try:
    from google import genai  # type: ignore[attr-defined]
except ImportError:
    genai = None  # type: ignore[assignment]

try:
    from accuralai_core.config.loader import load_settings
except ImportError:
    load_settings = None  # type: ignore[assignment]


class EmbeddingService:
    """Service for generating embeddings using Google GenAI."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-embedding-001"):
        """
        Initialize embedding service.

        Args:
            api_key: Google GenAI API key (or uses config/GOOGLE_GENAI_API_KEY env var)
            model: Embedding model to use (default: gemini-embedding-001)
        """
        if genai is None:
            raise ImportError(
                "google-genai is not installed. Install it to use embedding-based search: "
                "pip install google-genai"
            )

        # Try to get API key from parameter first
        self.api_key = api_key
        
        # If not provided, try to load from AccuralAI config
        if not self.api_key and load_settings is not None:
            try:
                config_path = os.getenv("ACCURALAI_CONFIG_PATH")
                if config_path:
                    config_path = config_path.strip('"').strip("'")
                    config_path = os.path.expanduser(config_path)
                    if not os.path.isabs(config_path):
                        config_path = os.path.abspath(config_path)
                    
                    if os.path.exists(config_path):
                        settings = load_settings(config_paths=[config_path])
                        # Extract API key from Google backend config
                        if "google" in settings.backends:
                            google_backend = settings.backends["google"]
                            if google_backend.options:
                                api_key_from_config = google_backend.options.get("api_key")
                                if api_key_from_config:
                                    self.api_key = api_key_from_config
            except Exception as e:
                LOGGER.debug(f"Failed to load API key from config: {e}")
        
        # Fall back to environment variable
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_GENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "Google GenAI API key missing. Provide via api_key parameter, "
                "AccuralAI config file (backends.google.options.api_key), or "
                "GOOGLE_GENAI_API_KEY environment variable."
            )

        self.model = model
        self._client: Optional[Any] = None
        self._embedding_dimension: Optional[int] = None  # Will be determined on first use

    @property
    def client(self) -> Any:
        """Lazy initialization of Google GenAI client."""
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text (dimension will match model output)
            dim = self._get_embedding_dimension()
            return [0.0] * dim

        try:
            # Use asyncio.to_thread for the synchronous API call
            response = await asyncio.to_thread(
                self.client.models.embed_content,
                model=self.model,
                contents=text,
            )

            # Extract embedding from response
            # Response structure: response.embeddings -> List[ContentEmbedding]
            # ContentEmbedding has .values attribute
            
            embedding_vector: Optional[List[float]] = None
            
            # Try accessing embeddings list
            if hasattr(response, "embeddings"):
                embeddings_list = response.embeddings
                if embeddings_list and len(embeddings_list) > 0:
                    embedding = embeddings_list[0]
                    # Check for values attribute
                    if hasattr(embedding, "values"):
                        values = embedding.values
                        if values is not None:
                            embedding_vector = list(values) if not isinstance(values, list) else values
                    # Check if it's a dict-like object
                    elif isinstance(embedding, dict) and "values" in embedding:
                        values = embedding["values"]
                        embedding_vector = list(values) if not isinstance(values, list) else values

            # Fallback: check if response has values directly
            if embedding_vector is None:
                if hasattr(response, "values"):
                    values = response.values
                    if values is not None:
                        embedding_vector = list(values) if not isinstance(values, list) else values
                elif isinstance(response, dict) and "values" in response:
                    values = response["values"]
                    embedding_vector = list(values) if not isinstance(values, list) else values
                # Last resort: check if response itself is a list of floats
                elif isinstance(response, (list, tuple)) and len(response) > 0:
                    if all(isinstance(x, (int, float)) for x in response):
                        embedding_vector = [float(x) for x in response]

            if embedding_vector:
                # Cache the dimension for future zero vectors
                if self._embedding_dimension is None:
                    self._embedding_dimension = len(embedding_vector)
                return embedding_vector

            LOGGER.warning(f"Unexpected embedding response format: {type(response)}, dir: {dir(response) if hasattr(response, '__dict__') else 'N/A'}")
            dim = self._get_embedding_dimension()
            return [0.0] * dim

        except Exception as e:
            LOGGER.error(f"Failed to generate embedding: {e}", exc_info=True)
            # Return zero vector on error
            dim = self._get_embedding_dimension()
            return [0.0] * dim

    def _get_embedding_dimension(self) -> int:
        """
        Get embedding dimension (cached after first use).
        
        Default dimension fallback: 1024 (reasonable default for gemini-embedding-001
        which supports up to 3072 dimensions, but actual dimension is detected from
        first embedding response).
        """
        if self._embedding_dimension is None:
            # Default fallback dimension (will be replaced by actual dimension from first embedding)
            # gemini-embedding-001 supports up to 3072 dimensions, but uses a reasonable default
            self._embedding_dimension = 1024
        return self._embedding_dimension

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process per batch

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        results: List[List[float]] = []

        # Process in batches to avoid overwhelming the API
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = await asyncio.gather(
                *[self.embed_text(text) for text in batch],
                return_exceptions=True,
            )

            for embedding in batch_embeddings:
                if isinstance(embedding, Exception):
                    LOGGER.error(f"Error generating embedding: {embedding}")
                    dim = self._get_embedding_dimension()
                    results.append([0.0] * dim)
                else:
                    results.append(embedding)
                    # Cache dimension from first successful embedding
                    if self._embedding_dimension is None and embedding:
                        self._embedding_dimension = len(embedding)

        return results


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"Vectors must have same length: {len(vec1)} != {len(vec2)}")

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a * a for a in vec1) ** 0.5
    magnitude2 = sum(b * b for b in vec2) ** 0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


