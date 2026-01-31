"""Embedding service that routes to the configured provider (OpenAI or Ollama)."""

from lecrapaud.config import EMBEDDING_PROVIDER
from lecrapaud.utils import logger


def get_embedding(document: str | dict) -> list[float]:
    """Embed a string into a vector using the configured provider.

    :param document: the string to be embedded
    :return: the embedded vector
    """
    if EMBEDDING_PROVIDER == "ollama":
        from lecrapaud.integrations.ollama_integration import get_ollama_embedding

        return get_ollama_embedding(document)
    else:
        from lecrapaud.integrations.openai_integration import get_openai_embedding

        return get_openai_embedding(document)


def get_embeddings(documents: list[str | dict], dimensions=None) -> list[list[float]]:
    """Embed a list of strings into vectors using the configured provider.

    :param documents: an array of documents
    :param dimensions: embedding dimensions (only used for OpenAI)
    :return: an array of embedded vectors
    """
    if EMBEDDING_PROVIDER == "ollama":
        from lecrapaud.integrations.ollama_integration import get_ollama_embeddings

        logger.info(f"Using Ollama for embeddings ({len(documents)} documents)")
        return get_ollama_embeddings(documents, dimensions)
    else:
        from lecrapaud.integrations.openai_integration import get_openai_embeddings

        logger.info(f"Using OpenAI for embeddings ({len(documents)} documents)")
        return get_openai_embeddings(documents, dimensions)


def get_embedding_provider() -> str:
    """Return the current embedding provider name."""
    return EMBEDDING_PROVIDER


def get_embedding_dimension() -> int:
    """Return the embedding dimension for the current provider."""
    if EMBEDDING_PROVIDER == "ollama":
        from lecrapaud.config import OLLAMA_EMBEDDING_MODEL

        # Common Ollama embedding model dimensions
        model_dimensions = {
            "nomic-embed-text": 768,
            "mxbai-embed-large": 1024,
            "all-minilm": 384,
            "snowflake-arctic-embed": 1024,
        }
        # Return known dimension or default
        for model_name, dim in model_dimensions.items():
            if model_name in OLLAMA_EMBEDDING_MODEL:
                return dim
        return 768  # Default for unknown models
    else:
        from lecrapaud.integrations.openai_integration import OPEN_AI_EMBEDDING_DIM

        return OPEN_AI_EMBEDDING_DIM
