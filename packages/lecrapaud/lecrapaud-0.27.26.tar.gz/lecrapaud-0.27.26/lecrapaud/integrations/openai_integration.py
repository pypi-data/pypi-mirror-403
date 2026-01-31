import re
from openai import OpenAI
import tiktoken
from lecrapaud.utils import logger
from lecrapaud.config import OPENAI_API_KEY

# OpenAI’s max tokens per request for embeddings
OPENAI_MAX_TOKENS = 8192
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPEN_AI_MODEL = "gpt-4o-2024-08-06"
OPEN_AI_TOKENIZER = "cl100k_base"
OPEN_AI_EMBEDDING_DIM = 1536  # 3072 if embedding model is text-embedding-3-large
TPM_LIMIT = 5000000
TPR_LIMIT = 300_000  # known empirically because of a error message
MAX_LENGHT_ARRAY_FOR_BULK_EMBEDDINGS = 2048


def get_openai_client():
    if not OPENAI_API_KEY:
        raise ValueError(
            "Please set an OPENAI_API_KEY environment variable to use embeddings"
        )
    return OpenAI(api_key=OPENAI_API_KEY)


def get_openai_embedding(document: str | dict) -> list[float]:
    """embed a string into a vector using latest openai model, text-embedding-3-small

    :param document: the string to be embedded
    :return: the embedded vector
    """
    client = get_openai_client()

    if isinstance(document, dict):
        document = dict_to_markdown_headers_nested(document)
    if not isinstance(document, str):
        raise ValueError("document must be a string or dict")

    nb_tokens = number_of_tokens(document)
    if nb_tokens > OPENAI_MAX_TOKENS:
        document = truncate_text(document, OPENAI_MAX_TOKENS)
    elif nb_tokens == 0:
        return []

    res = client.embeddings.create(input=document, model=OPENAI_EMBEDDING_MODEL)

    return res.data[0].embedding


def get_openai_embeddings(
    documents: list[str | dict], dimensions=None
) -> list[list[float]]:
    """embed a string into a vector using latest openai model, text-embedding-3-small

    :param document: an array of documents
    :return: a array of embedded vector
    """
    _documents = documents.copy()
    client = get_openai_client()
    dimensions = dimensions or OPEN_AI_EMBEDDING_DIM

    if not isinstance(documents, list):
        raise ValueError("documents must be a list")

    for i, doc in enumerate(documents):
        if isinstance(doc, dict):
            doc = dict_to_markdown_headers_nested(doc)
            _documents[i] = doc
        if not isinstance(doc, str):
            raise ValueError("documents must be a list of strings or dict")

    # Calculate total tokens for all documents
    total_tokens = sum([number_of_tokens(doc) for doc in _documents])

    if total_tokens == 0:
        return []

    # Calculate how many documents we can process in one batch
    # We need to ensure we don't exceed TPR_LIMIT (300k tokens per request)
    # and MAX_LENGHT_ARRAY_FOR_BULK_EMBEDDINGS (2048 documents)
    avg_tokens_per_doc = total_tokens / len(_documents)
    docs_per_batch = min(
        MAX_LENGHT_ARRAY_FOR_BULK_EMBEDDINGS,
        max(1, int(TPR_LIMIT / avg_tokens_per_doc * 0.7)),  # 30 % safety margin
    )

    logger.debug(
        f"Processing {len(_documents)} chunks in batches of {docs_per_batch}"
        f" (avg {avg_tokens_per_doc:.0f} tokens per chunk)"
    )

    embeddings = []
    for i, doc_list_chunk in enumerate(
        [
            _documents[i : i + docs_per_batch]
            for i in range(0, len(_documents), docs_per_batch)
        ]
    ):
        total_tokens = total_number_of_tokens(doc_list_chunk)
        max_tokens = max_number_of_tokens(doc_list_chunk)
        logger.debug(
            f"Embedding batch {i+1} with {len(doc_list_chunk)} chunks, total tokens: {total_tokens}, max tokens: {max_tokens}..."
        )

        if total_tokens == 0:
            continue

        if total_tokens <= TPR_LIMIT:
            input = [doc if doc else "None" for doc in doc_list_chunk]
            res = client.embeddings.create(
                input=input,
                model=OPENAI_EMBEDDING_MODEL,
                dimensions=dimensions,
            )
            chunk_embeddings = [data.embedding for data in res.data]
        else:
            logger.warning(
                f"Batch {i+1} with {total_tokens} tokens exceeds limit of {TPR_LIMIT}. Inserting one by one..."
            )
            chunk_embeddings = []
            for doc in doc_list_chunk:
                res = client.embeddings.create(
                    input=doc,
                    model=OPENAI_EMBEDDING_MODEL,
                    dimensions=dimensions,
                )
                chunk_embeddings.extend([data.embedding for data in res.data])

        embeddings.extend(chunk_embeddings)

    return embeddings


def max_number_of_tokens(list):
    return max([number_of_tokens(str(item)) for item in list])


def total_number_of_tokens(list):
    return sum([number_of_tokens(str(item)) for item in list])


def number_of_tokens(string: str, encoding_name: str = OPEN_AI_TOKENIZER) -> int:
    """Count the number of token in string

    :param string: the string
    :param encoding_name: the encoding model
    :return: the number of tokens
    """
    if not string:
        return 0
    tokenizer = tiktoken.get_encoding(encoding_name)
    num_tokens = len(tokenizer.encode(string, disallowed_special=()))
    return num_tokens


def truncate_text(text, max_tokens=OPENAI_MAX_TOKENS):
    """Limits text to max_tokens or less by truncating."""
    words = text.split()
    truncated_text = []
    current_length = 0

    for word in words:
        token_length = number_of_tokens(word)  # Count tokens for word
        if current_length + token_length > max_tokens:
            break  # Stop once limit is reached

        truncated_text.append(word)
        current_length += token_length

    return " ".join(truncated_text)


def dict_to_markdown_headers_nested(
    data, level: int = 1, parent_key: str = None
) -> str:
    """
    Convert a nested dictionary or list into a markdown string with headers.

    Args:
        data: The input data (dict, list, or other)
        level: The header level to start with (1 for h1, 2 for h2, etc.)
        parent_key: The key of the parent dictionary (used for list items)

    Returns:
        str: Formatted markdown string with headers
    """
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            header = "#" * level + f" {key}"
            lines.append(header)
            if isinstance(value, (dict, list)):
                lines.append(dict_to_markdown_headers_nested(value, level + 1, key))
            else:
                lines.append(str(value).strip() if value is not None else "")
        return "\n".join(lines)
    elif isinstance(data, list):
        lines = []
        if parent_key:
            # Use singular form of the parent key if it ends with 's'
            item_name = (
                parent_key[:-1]
                if parent_key.endswith("s") and len(parent_key) > 1
                else parent_key
            )
            for i, item in enumerate(data, 1):
                header = "#" * level + f" {item_name.capitalize()} {i}"
                lines.append(header)
                if isinstance(item, (dict, list)):
                    lines.append(dict_to_markdown_headers_nested(item, level + 1))
                else:
                    lines.append(str(item).strip() if item is not None else "")
        else:
            # Fallback if no parent key is provided
            for i, item in enumerate(data, 1):
                header = "#" * level + f" Item {i}"
                lines.append(header)
                if isinstance(item, (dict, list)):
                    lines.append(dict_to_markdown_headers_nested(item, level + 1))
                else:
                    lines.append(str(item).strip() if item is not None else "")
        return "\n".join(lines)
    else:
        return str(data).strip() if data is not None else ""
