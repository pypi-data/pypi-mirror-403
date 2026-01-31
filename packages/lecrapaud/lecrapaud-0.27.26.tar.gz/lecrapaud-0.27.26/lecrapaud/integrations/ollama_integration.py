"""Ollama integration for running local embeddings."""

import requests
from lecrapaud.utils import logger
from lecrapaud.config import OLLAMA_BASE_URL, OLLAMA_EMBEDDING_MODEL


def is_ollama_available() -> bool:
    """Check if Ollama is running."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def get_ollama_embedding(document: str | dict) -> list[float]:
    """Embed a string into a vector using Ollama.

    :param document: the string to be embedded
    :return: the embedded vector
    """
    if isinstance(document, dict):
        from lecrapaud.integrations.openai_integration import (
            dict_to_markdown_headers_nested,
        )

        document = dict_to_markdown_headers_nested(document)
    if not isinstance(document, str):
        raise ValueError("document must be a string or dict")

    if not document:
        return []

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embed",
        json={
            "model": OLLAMA_EMBEDDING_MODEL,
            "input": [document],
        },
        timeout=120,
    )
    response.raise_for_status()
    embeddings = response.json()["embeddings"]

    return embeddings[0] if embeddings else []


def get_ollama_embeddings(
    documents: list[str | dict], dimensions=None
) -> list[list[float]]:
    """Embed a list of strings into vectors using Ollama.

    :param documents: an array of documents
    :param dimensions: ignored for Ollama (model determines dimensions)
    :return: an array of embedded vectors
    """
    if not isinstance(documents, list):
        raise ValueError("documents must be a list")

    _documents = documents.copy()

    for i, doc in enumerate(documents):
        if isinstance(doc, dict):
            from lecrapaud.integrations.openai_integration import (
                dict_to_markdown_headers_nested,
            )

            doc = dict_to_markdown_headers_nested(doc)
            _documents[i] = doc
        if not isinstance(doc, str):
            raise ValueError("documents must be a list of strings or dict")

    # Filter out empty documents but keep track of their positions
    non_empty_indices = []
    non_empty_docs = []
    for i, doc in enumerate(_documents):
        if doc:
            non_empty_indices.append(i)
            non_empty_docs.append(doc)

    if not non_empty_docs:
        return []

    # Ollama's embed endpoint supports batching
    # Process in batches to avoid timeouts on large inputs
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(non_empty_docs), batch_size):
        batch = non_empty_docs[i : i + batch_size]
        logger.debug(
            f"Embedding batch {i // batch_size + 1} with {len(batch)} documents..."
        )

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embed",
            json={
                "model": OLLAMA_EMBEDDING_MODEL,
                "input": batch,
            },
            timeout=300,
        )
        response.raise_for_status()
        batch_embeddings = response.json()["embeddings"]
        all_embeddings.extend(batch_embeddings)

    # Reconstruct the full list with empty vectors for empty documents
    if len(non_empty_indices) == len(_documents):
        return all_embeddings

    # Get embedding dimension from first result
    embedding_dim = len(all_embeddings[0]) if all_embeddings else 0
    result = []
    embedding_idx = 0

    for i in range(len(_documents)):
        if i in non_empty_indices:
            result.append(all_embeddings[embedding_idx])
            embedding_idx += 1
        else:
            result.append([0.0] * embedding_dim)

    return result
