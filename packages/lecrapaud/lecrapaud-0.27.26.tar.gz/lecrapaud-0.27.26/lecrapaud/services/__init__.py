"""Services module for LeCrapaud.

This module provides service classes and functions for artifact management
and text embeddings.

Classes:
    ArtifactService: Manages storage and retrieval of ML artifacts
        (models, scalers, DataFrames) in the database.

Functions:
    get_embedding: Get embedding vector for a single text.
    get_embeddings: Get embedding vectors for multiple texts.
    get_embedding_provider: Get the configured embedding provider name.
    get_embedding_dimension: Get the dimension of embedding vectors.
"""

from lecrapaud.services.artifact_service import ArtifactService
from lecrapaud.services.embedding_service import (
    get_embedding,
    get_embeddings,
    get_embedding_provider,
    get_embedding_dimension,
)

__all__ = [
    "ArtifactService",
    "get_embedding",
    "get_embeddings",
    "get_embedding_provider",
    "get_embedding_dimension",
]
