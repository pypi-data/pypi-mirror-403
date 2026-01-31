"""Configuration module for LeCrapaud.

This module loads and provides access to environment variables used
throughout the LeCrapaud framework, including database connections,
logging, embedding providers, and Sentry monitoring.

Environment variables are loaded from a .env file using python-dotenv.
Test environment variables (prefixed with TEST_) are used when PYTHON_ENV
is set to "Test".

Attributes:
    PYTHON_ENV: Current environment (Development, Production, Test, Worker).
    LOGGING_LEVEL: Logging level (default: INFO).
    DB_USER: Database username.
    DB_PASSWORD: Database password.
    DB_HOST: Database host.
    DB_PORT: Database port.
    DB_NAME: Database name.
    DB_URI: Full database connection URI.
    OPENAI_API_KEY: OpenAI API key for embeddings.
    EMBEDDING_PROVIDER: Provider for embeddings (openai or ollama).
    OLLAMA_BASE_URL: Base URL for Ollama server.
    OLLAMA_EMBEDDING_MODEL: Model name for Ollama embeddings.
    LECRAPAUD_LOGFILE: Path to log file.
    LECRAPAUD_TABLE_PREFIX: Prefix for database tables.
    LECRAPAUD_OPTIMIZATION_BACKEND: Hyperparameter optimization backend.
    SENTRY_DSN: Sentry Data Source Name for error tracking.
    SENTRY_TRACES_SAMPLE_RATE: Sample rate for Sentry traces.
    SENTRY_PROFILES_SAMPLE_RATE: Sample rate for Sentry profiles.
    LECRAPAUD_SAVE_FULL_TRAIN_DATA: Whether to save full training data.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=False)

PYTHON_ENV = os.getenv("PYTHON_ENV")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")

DB_USER = (
    os.getenv("TEST_DB_USER") if PYTHON_ENV == "Test" else os.getenv("DB_USER", None)
)
DB_PASSWORD = (
    os.getenv("TEST_DB_PASSWORD", "")
    if PYTHON_ENV == "Test"
    else os.getenv("DB_PASSWORD", "")
)
DB_HOST = (
    os.getenv("TEST_DB_HOST") if PYTHON_ENV == "Test" else os.getenv("DB_HOST", None)
)
DB_PORT = (
    os.getenv("TEST_DB_PORT") if PYTHON_ENV == "Test" else os.getenv("DB_PORT", None)
)
DB_NAME = (
    os.getenv("TEST_DB_NAME") if PYTHON_ENV == "Test" else os.getenv("DB_NAME", None)
)
DB_URI: str = (
    os.getenv("TEST_DB_URI", None)
    if PYTHON_ENV == "Test"
    else os.getenv("DB_URI", None)
)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "qwen3-embedding:latest")

LECRAPAUD_LOGFILE = os.getenv("LECRAPAUD_LOGFILE")
LECRAPAUD_TABLE_PREFIX = os.getenv("LECRAPAUD_TABLE_PREFIX", "lecrapaud")
LECRAPAUD_OPTIMIZATION_BACKEND = os.getenv(
    "LECRAPAUD_OPTIMIZATION_BACKEND", "hyperopt"
).lower()

SENTRY_DSN = os.getenv("SENTRY_DSN")

try:
    SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0"))
except ValueError:
    SENTRY_TRACES_SAMPLE_RATE = 0.0

try:
    SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0"))
except ValueError:
    SENTRY_PROFILES_SAMPLE_RATE = 0.0

LECRAPAUD_SAVE_FULL_TRAIN_DATA = (
    os.getenv("LECRAPAUD_SAVE_FULL_TRAIN_DATA", "False").lower() == "true"
)
