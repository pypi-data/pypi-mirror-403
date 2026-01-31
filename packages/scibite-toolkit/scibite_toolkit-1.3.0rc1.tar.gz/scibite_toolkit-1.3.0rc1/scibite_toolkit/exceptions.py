# scibite_toolkit/exceptions.py
"""
Shared exceptions for the SciBite toolkit.

This module provides a standardized exception hierarchy for all SciBite
toolkit modules. All exceptions inherit from SciBiteError, allowing users
to catch all toolkit-related exceptions with a single except clause.

Example
-------
>>> from scibite_toolkit.exceptions import AuthenticationError, APIError
>>> try:
...     client.authenticate()
... except AuthenticationError:
...     print("Login failed")
... except APIError as e:
...     print(f"API error {e.status_code}: {e}")
"""

from __future__ import annotations

from typing import Any, Optional


# ── Base Exception ─────────────────────────────────────────────────
class SciBiteError(Exception):
    """
    Base exception for all SciBite toolkit errors.

    All toolkit-specific exceptions inherit from this class, allowing
    users to catch all toolkit errors with a single handler.

    Example
    -------
    >>> try:
    ...     # Any toolkit operation
    ... except SciBiteError as e:
    ...     print(f"Toolkit error: {e}")
    """

    pass


# ── Common Exceptions ──────────────────────────────────────────────
class AuthenticationError(SciBiteError):
    """
    Authentication or authorization failed.

    Raised when OAuth2 authentication fails, tokens are invalid or expired,
    or the user lacks permission for the requested operation.
    """

    pass


class APIError(SciBiteError):
    """
    API request failed.

    Raised when an HTTP request to a SciBite API returns an error response.
    Includes the HTTP status code and response body for debugging.

    Parameters
    ----------
    message : str
        Human-readable error description.
    status_code : int, optional
        HTTP status code (e.g., 400, 404, 500).
    response : Any, optional
        The raw response object or body for debugging.

    Attributes
    ----------
    status_code : int or None
        The HTTP status code.
    response : Any
        The response object or body.

    Example
    -------
    >>> try:
    ...     client.get("/api/resource")
    ... except APIError as e:
    ...     if e.status_code == 404:
    ...         print("Resource not found")
    ...     else:
    ...         print(f"API error {e.status_code}: {e}")
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Any = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(SciBiteError):
    """
    Requested resource not found.

    Base class for resource-not-found errors. Subclasses provide
    more specific context (e.g., OntologyNotFoundError, VocabularyNotFoundError).
    """

    pass


class ValidationError(SciBiteError):
    """
    Invalid input parameters.

    Raised when user-provided input fails validation before making
    an API request (e.g., missing required fields, invalid formats).
    """

    pass


class TimeoutError(SciBiteError):
    """
    Request timed out.

    Raised when an API request exceeds the configured timeout.
    """

    pass


class ConnectionError(SciBiteError):
    """
    Unable to connect to the server.

    Raised when network connectivity issues prevent reaching the API.
    """

    pass


# ── CENtree-Specific Exceptions ────────────────────────────────────
class OntologyAlreadyExistsError(SciBiteError):
    """
    Ontology already exists and is loaded.

    Raised when attempting to create or load an ontology that already
    exists in CENtree.
    """

    pass


class OntologyNotFoundError(NotFoundError):
    """
    Ontology does not exist or cannot be found.

    Raised when attempting to access an ontology that doesn't exist
    or hasn't been loaded in CENtree.
    """

    pass


# ── TERMite-Specific Exceptions ────────────────────────────────────
class VocabularyNotFoundError(NotFoundError):
    """
    Vocabulary does not exist.

    Raised when attempting to use a vocabulary that isn't available
    on the TERMite instance.
    """

    pass


class AnnotationError(SciBiteError):
    """
    Text annotation failed.

    Raised when TERMite fails to annotate text or a document.
    """

    pass
