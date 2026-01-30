"""Shared utilities and configuration for OCR Vector DB."""

__version__ = "0.1.0"

from .config import load_config
from .db_pool import close_pool, get_pool
from .exceptions import SharedError
from .hashing import HashingService, Slugifier, format_vector_literal
from .text_utils import TextPreprocessor

__all__ = [
    "__version__",
    "load_config",
    "get_pool",
    "close_pool",
    "SharedError",
    "HashingService",
    "Slugifier",
    "format_vector_literal",
    "TextPreprocessor",
]
