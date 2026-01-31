# scibite_toolkit/termite_clients/exceptions.py
"""
TERMite-specific exceptions.

Re-exports common exceptions from the shared module and provides
TERMite-specific exception classes.
"""

# Re-export from shared exceptions module
from scibite_toolkit.exceptions import (
    SciBiteError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
    TimeoutError,
    ConnectionError,
    VocabularyNotFoundError,
    AnnotationError,
)

__all__ = [
    # Base
    "SciBiteError",
    # Common
    "AuthenticationError",
    "APIError",
    "NotFoundError",
    "ValidationError",
    "TimeoutError",
    "ConnectionError",
    # TERMite-specific
    "VocabularyNotFoundError",
    "AnnotationError",
]
