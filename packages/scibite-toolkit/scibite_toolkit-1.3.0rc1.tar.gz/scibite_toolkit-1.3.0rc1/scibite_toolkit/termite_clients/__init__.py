# scibite_toolkit/termite_clients/__init__.py
"""
Modular TERMite client library.

This package provides a modular client library for interacting with
TERMite 7 APIs. The base client handles authentication, retries, and
HTTP requests, while specialized clients provide domain-specific operations.

Example
-------
>>> from scibite_toolkit.termite_clients import TermiteClient, TermiteMetadataClient
>>> client = TermiteMetadataClient(
...     base_url="https://termite.example.com",
...     token_url="https://auth.example.com"
... )
>>> client.set_oauth2("client_id", "client_secret")
>>> status = client.get_status()
"""

from scibite_toolkit.termite_clients.base import TermiteClient
from scibite_toolkit.termite_clients.metadata import TermiteMetadataClient
from scibite_toolkit.termite_clients.annotate import TermiteAnnotateClient
from scibite_toolkit.termite_clients.lookup import TermiteLookupClient
from scibite_toolkit.termite_clients.exceptions import (
    SciBiteError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
    VocabularyNotFoundError,
    AnnotationError,
)

__all__ = [
    # Clients
    "TermiteClient",
    "TermiteMetadataClient",
    "TermiteAnnotateClient",
    "TermiteLookupClient",
    # Exceptions
    "SciBiteError",
    "AuthenticationError",
    "APIError",
    "NotFoundError",
    "ValidationError",
    "VocabularyNotFoundError",
    "AnnotationError",
]
