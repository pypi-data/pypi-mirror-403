# scibite_toolkit/termite_clients/base.py
"""Base client for TERMite API interactions."""

from __future__ import annotations

import logging
import time
import warnings
from datetime import datetime, timezone
from logging import NullHandler
from typing import Any, Optional, Union
from urllib.parse import urlparse

import requests
from requests import exceptions as reqexc
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scibite_toolkit.exceptions import (
    AuthenticationError,
    APIError,
    ValidationError,
)

# Module-level alias for typing
JSON = Union[dict[str, Any], list, None]

logger = logging.getLogger("scibite_toolkit.termite_clients.base")
logger.addHandler(NullHandler())


class TermiteClient:
    """
    Base client for TERMite API interactions.

    Provides authentication, session management, retries, and HTTP request
    handling. Use as a base for specialized clients or standalone for
    low-level API access.

    TERMite 7 uses OAuth2 client credentials for authentication. Tokens are
    short-lived (~300 seconds) and the client will automatically refresh
    them when they expire.

    Parameters
    ----------
    base_url : str, optional
        Base URL of the TERMite instance (e.g., ``"https://termite.example.com"``).
        Trailing slash is automatically removed.
    token_url : str, optional
        OAuth2 token endpoint URL (e.g., ``"https://auth.example.com"``).
        Required for SaaS deployments where auth is on a separate server.
        If not provided, ``base_url`` is used for OAuth2 authentication.
    verify : bool or str, default=True
        SSL certificate verification. If ``True``, certificates are verified.
        If a string, treated as a path to a CA bundle. ``False`` is blocked
        unless ``allow_insecure=True``.
    timeout : float or (float, float) or None, default=(3.0, None)
        Request timeout. Single float applies to both connect and read.
        Tuple ``(connect_timeout, read_timeout)`` sets each separately.
        ``None`` disables timeout.
    allow_insecure : bool, default=False
        If ``True``, allows ``verify=False``. **Not recommended** except for
        development with self-signed certificates.
    retry : urllib3.util.retry.Retry, optional
        Custom retry policy. Defaults to 5 retries with exponential backoff.
    session : requests.Session, optional
        Pre-configured session. If not provided, a new session is created.

    Notes
    -----
    - ``requests.Session`` is **not** thread-safe. Create one client per thread.
    - For large document annotation, use ``timeout=(3.0, None)`` to avoid
      premature read timeouts.
    - Tokens are automatically refreshed when they expire (with a 30-second buffer).

    Examples
    --------
    OAuth2 client credentials (SaaS with separate auth server):

    >>> client = TermiteClient(
    ...     base_url="https://termite.example.com",
    ...     token_url="https://auth.example.com"
    ... )
    >>> client.set_oauth2("client_id", "client_secret")

    OAuth2 client credentials (on-prem, auth on same server):

    >>> client = TermiteClient(base_url="https://termite.example.com")
    >>> client.set_oauth2("client_id", "client_secret")

    Context manager:

    >>> with TermiteClient(base_url="...") as client:
    ...     client.set_oauth2("id", "secret")
    ...     # Use client...
    """

    # Buffer time (seconds) before token expiry to trigger refresh
    _TOKEN_REFRESH_BUFFER = 30

    def __init__(
        self,
        base_url: Optional[str] = None,
        token_url: Optional[str] = None,
        verify: Union[bool, str] = True,
        timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]] = (
            3.0,
            None,
        ),
        allow_insecure: bool = False,
        retry: Optional[Retry] = None,
        session: Optional[requests.Session] = None,
        **_,
    ):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.token_url = token_url.rstrip("/") if token_url else None
        self.allow_insecure = allow_insecure
        self.verify = self._normalize_verify(verify)
        self.timeout = self._normalize_timeout(timeout)

        # Token state (internal)
        self._bearer_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None  # Unix timestamp

        # Stored credentials for auto-refresh
        self._client_id: Optional[str] = None
        self._client_secret: Optional[str] = None

        # Initialize session with retry configuration
        if session:
            self.session = session
        else:
            self.session = requests.Session()
            adapter = HTTPAdapter(
                max_retries=retry
                or Retry(
                    total=5,
                    backoff_factor=0.5,
                    status_forcelist=(429, 500, 502, 503, 504),
                    allowed_methods=frozenset(
                        ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
                    ),
                )
            )
            self.session.mount("http://", adapter)
            self.session.mount("https://", adapter)

        logger.debug(
            "TermiteClient init base_url=%s token_url=%s verify=%s timeout=%s",
            self.base_url,
            self.token_url,
            self.verify,
            self.timeout,
        )

    # ── Context manager ────────────────────────────────────────────
    def __enter__(self) -> "TermiteClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Close session and release resources."""
        if self.session:
            self.session.close()
            logger.debug("Session closed")

    # ── Setters (fluent interface) ─────────────────────────────────
    def set_url(self, url: str) -> "TermiteClient":
        """
        Set the base URL of the TERMite instance.

        Parameters
        ----------
        url : str
            TERMite instance URL.

        Returns
        -------
        TermiteClient
            Self, for method chaining.
        """
        self.base_url = url.rstrip("/")
        return self

    def set_token_url(self, token_url: str) -> "TermiteClient":
        """
        Set the OAuth2 token endpoint URL.

        Parameters
        ----------
        token_url : str
            Auth server URL (e.g., ``"https://auth.example.com"``).

        Returns
        -------
        TermiteClient
            Self, for method chaining.
        """
        self.token_url = token_url.rstrip("/")
        return self

    def _set_auth(self, token: str, expires_in: Optional[int] = None) -> None:
        """
        Set the bearer token (internal use only).

        Parameters
        ----------
        token : str
            Bearer token for API authentication.
        expires_in : int, optional
            Token lifetime in seconds. If provided, used for auto-refresh timing.
        """
        self._bearer_token = token
        if expires_in:
            self._token_expires_at = time.time() + expires_in
        else:
            self._token_expires_at = None

    def set_verify(self, verify: Union[bool, str]) -> "TermiteClient":
        """
        Set SSL certificate verification.

        Parameters
        ----------
        verify : bool or str
            ``True`` to verify, ``False`` to skip (requires ``allow_insecure``),
            or path to CA bundle.

        Returns
        -------
        TermiteClient
            Self, for method chaining.
        """
        self.verify = self._normalize_verify(verify)
        return self

    def set_timeout(
        self, timeout: Optional[Union[float, tuple[float, float]]]
    ) -> "TermiteClient":
        """
        Set request timeout.

        Parameters
        ----------
        timeout : float or (float, float) or None
            Connect timeout, or tuple of (connect, read) timeouts.

        Returns
        -------
        TermiteClient
            Self, for method chaining.
        """
        self.timeout = self._normalize_timeout(timeout)
        return self

    # ── Normalization helpers ──────────────────────────────────────
    def _normalize_verify(self, verify: Union[bool, str]) -> Union[bool, str]:
        if verify is False:
            if not self.allow_insecure:
                raise ValueError(
                    "Insecure TLS disabled. Pass allow_insecure=True if you really "
                    "want verify=False (not recommended)."
                )
            warnings.warn(
                "TLS certificate verification disabled (verify=False). This is insecure.",
                UserWarning,
            )
        return verify

    def _normalize_timeout(
        self,
        timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]],
    ) -> Optional[Union[float, tuple[Optional[float], Optional[float]]]]:
        # Accept 0 as "no timeout"; translate to None
        if timeout == 0:
            return None
        if isinstance(timeout, tuple):
            ct, rt = timeout
            ct = None if ct == 0 else ct
            rt = None if rt == 0 else rt
            return (ct, rt)
        return timeout

    def _headers(self) -> dict[str, str]:
        """Build authorization headers, refreshing token if needed."""
        self._ensure_valid_token()
        if not self._bearer_token:
            raise AuthenticationError(
                "Not authenticated. Call set_oauth2() first."
            )
        return {"Authorization": f"Bearer {self._bearer_token}"}

    def _ensure_valid_token(self) -> None:
        """Check token validity and refresh if expired or expiring soon."""
        if not self._bearer_token:
            return  # No token yet, will fail in _headers

        if not self._token_expires_at:
            return  # No expiry info, assume valid

        # Check if token is expired or expiring within buffer
        if time.time() >= (self._token_expires_at - self._TOKEN_REFRESH_BUFFER):
            if self._client_id and self._client_secret:
                logger.info("Token expired or expiring soon, refreshing...")
                if not self._refresh_token():
                    logger.warning("Token refresh failed")
            else:
                logger.warning(
                    "Token expired but no credentials stored for refresh"
                )

    def _refresh_token(self) -> bool:
        """Refresh the OAuth2 token using stored credentials."""
        if not self._client_id or not self._client_secret:
            return False

        # Re-authenticate using stored credentials
        return self._do_oauth2_auth(self._client_id, self._client_secret)

    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint, validating HTTPS."""
        if endpoint.startswith("http"):
            url = endpoint
        else:
            if not self.base_url:
                raise ValueError("Base URL is not set and endpoint is relative.")
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

        parsed = urlparse(url)
        if parsed.scheme != "https":
            raise ValueError(f"Non-HTTPS URL rejected: {url}")
        return url

    # ── OAuth2 Authentication ──────────────────────────────────────
    def set_oauth2(self, client_id: str, client_secret: str) -> bool:
        """
        Authenticate using OAuth2 client credentials flow.

        Credentials are stored for automatic token refresh when the token
        expires (tokens are typically short-lived, ~300 seconds).

        Uses ``token_url`` if set, otherwise falls back to ``base_url``.

        Parameters
        ----------
        client_id : str
            OAuth2 client ID.
        client_secret : str
            OAuth2 client secret.

        Returns
        -------
        bool
            ``True`` if authentication succeeded, ``False`` otherwise.

        Raises
        ------
        ValueError
            If neither ``token_url`` nor ``base_url`` is set.
        """
        # Store credentials for auto-refresh
        self._client_id = client_id
        self._client_secret = client_secret

        return self._do_oauth2_auth(client_id, client_secret)

    def _do_oauth2_auth(self, client_id: str, client_secret: str) -> bool:
        """Perform OAuth2 client credentials authentication."""
        auth_base = self.token_url or self.base_url
        if not auth_base:
            raise ValueError(
                "Neither token_url nor base_url is set. Call set_token_url() or set_url() first."
            )

        token_endpoint = f"{auth_base}/auth/realms/Scibite/protocol/openid-connect/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = self.session.post(
                token_endpoint,
                data=payload,
                headers=headers,
                verify=self.verify,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            body = resp.json()

            access_token = body.get("access_token")
            if not access_token:
                logger.warning("Access token missing in OAuth2 response")
                return False

            expires_in = int(body.get("expires_in", 0)) or None
            self._set_auth(access_token, expires_in)
            self._log_token_expiry(body)
            return True

        except reqexc.HTTPError as e:
            self._log_http_error("OAuth2", token_endpoint, e)
            return False
        except reqexc.SSLError as e:
            logger.warning("OAuth2 TLS/SSL error at %s: %s", token_endpoint, e)
            return False
        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            logger.warning("OAuth2 network error at %s: %s", token_endpoint, e)
            return False
        except Exception as e:
            logger.warning("OAuth2 authentication failed: %s", e)
            return False

    def set_oauth2_password(
        self,
        client_id: str,
        username: str,
        password: str,
    ) -> bool:
        """
        Authenticate using OAuth2 password grant flow.

        .. deprecated::
            Password grant is deprecated. Use ``set_oauth2()`` with client
            credentials instead. Create a client in the TERMite UI to get
            a client ID and secret.

        This is the legacy flow used by older on-prem TERMite deployments.

        Uses ``token_url`` if set, otherwise falls back to ``base_url``.

        Parameters
        ----------
        client_id : str
            OAuth2 client ID (typically ``"termite-ui"`` for on-prem).
        username : str
            TERMite username.
        password : str
            TERMite password.

        Returns
        -------
        bool
            ``True`` if authentication succeeded, ``False`` otherwise.

        Raises
        ------
        ValueError
            If neither ``token_url`` nor ``base_url`` is set.
        """
        warnings.warn(
            "set_oauth2_password() is deprecated. Use set_oauth2() with client "
            "credentials instead. Create a client in the TERMite UI to get a "
            "client ID and secret.",
            DeprecationWarning,
            stacklevel=2,
        )

        auth_base = self.token_url or self.base_url
        if not auth_base:
            raise ValueError(
                "Neither token_url nor base_url is set. Call set_token_url() or set_url() first."
            )

        token_endpoint = f"{auth_base}/auth/realms/Scibite/protocol/openid-connect/token"

        payload = {
            "grant_type": "password",
            "client_id": client_id,
            "username": username,
            "password": password,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = self.session.post(
                token_endpoint,
                data=payload,
                headers=headers,
                verify=self.verify,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            body = resp.json()

            access_token = body.get("access_token")
            if not access_token:
                logger.warning("Access token missing in OAuth2 password response")
                return False

            expires_in = int(body.get("expires_in", 0)) or None
            self._set_auth(access_token, expires_in)
            self._log_token_expiry(body)
            return True

        except reqexc.HTTPError as e:
            self._log_http_error("OAuth2 password", token_endpoint, e)
            return False
        except reqexc.SSLError as e:
            logger.warning("OAuth2 password TLS/SSL error at %s: %s", token_endpoint, e)
            return False
        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            logger.warning("OAuth2 password network error at %s: %s", token_endpoint, e)
            return False
        except Exception as e:
            logger.warning("OAuth2 password authentication failed: %s", e)
            return False

    def _log_token_expiry(self, body: dict) -> None:
        """Log token expiry information."""
        expires_in = int(body.get("expires_in", 0))
        if expires_in:
            utc_when = datetime.fromtimestamp(
                time.time() + expires_in, tz=timezone.utc
            ).isoformat()
            logger.info(
                "Token acquired; expires in ~%ds (at %s)", expires_in, utc_when
            )
        else:
            logger.info("Token acquired; 'expires_in' not provided")

    def _log_http_error(self, context: str, url: str, e: reqexc.HTTPError) -> None:
        """Log HTTP error details."""
        r = getattr(e, "response", None)
        code = getattr(r, "status_code", "unknown")
        snippet = ""
        try:
            snippet = (r.text or "")[:300] if r is not None else ""
        except Exception:
            pass
        logger.warning("%s HTTP error (%s) at %s; body: %s", context, code, url, snippet)

    # ── HTTP Request Methods ───────────────────────────────────────
    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: JSON = None,
        data: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, str]] = None,
        raise_for_status: bool = True,
        timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]] = None,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send an HTTP request to the TERMite API.

        Parameters
        ----------
        method : str
            HTTP method (e.g., ``'GET'``, ``'POST'``).
        endpoint : str
            API endpoint relative to base URL, or absolute URL.
        params : dict, optional
            Query parameters.
        json : dict or list, optional
            JSON payload for request body.
        data : dict, optional
            Form data for request body.
        files : dict, optional
            Files for multipart upload.
        headers : dict, optional
            Additional headers (merged with auth headers).
        raise_for_status : bool, default=True
            If ``True``, raise ``HTTPError`` on 4xx/5xx responses.
        timeout : float or (float, float), optional
            Override default timeout for this request.
        **kwargs
            Additional arguments passed to ``requests.Session.request()``.

        Returns
        -------
        requests.Response
            The HTTP response object.

        Raises
        ------
        ValueError
            If base URL is not set and endpoint is relative.
        requests.HTTPError
            If ``raise_for_status`` is ``True`` and response is unsuccessful.
        """
        url = self._build_url(endpoint)
        req_headers = self._headers()
        if headers:
            req_headers.update(headers)

        eff_timeout = self._normalize_timeout(timeout)
        if eff_timeout is None:
            eff_timeout = self.timeout

        if params:
            logger.debug("Request params: %s", params)
        if json is not None:
            logger.debug(
                "Request JSON payload (keys/type): %s",
                list(json.keys()) if isinstance(json, dict) else type(json),
            )

        resp = self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            data=data,
            files=files,
            headers=req_headers,
            verify=self.verify,
            timeout=eff_timeout,
            **kwargs,
        )

        if raise_for_status and not resp.ok:
            logger.warning(
                "Request failed %s %s -> %s", method.upper(), url, resp.status_code
            )
            resp.raise_for_status()

        return resp

    # ── Convenience wrappers ───────────────────────────────────────
    def get(self, endpoint: str, **kw: Any) -> requests.Response:
        """Send a GET request."""
        return self.request("GET", endpoint, **kw)

    def post(self, endpoint: str, **kw: Any) -> requests.Response:
        """Send a POST request."""
        return self.request("POST", endpoint, **kw)

    def put(self, endpoint: str, **kw: Any) -> requests.Response:
        """Send a PUT request."""
        return self.request("PUT", endpoint, **kw)

    def patch(self, endpoint: str, **kw: Any) -> requests.Response:
        """Send a PATCH request."""
        return self.request("PATCH", endpoint, **kw)

    def delete(self, endpoint: str, **kw: Any) -> requests.Response:
        """Send a DELETE request."""
        return self.request("DELETE", endpoint, **kw)

    # ── Response helpers ───────────────────────────────────────────
    def json_or_raise(self, resp: requests.Response) -> Any:
        """
        Extract JSON from response or raise an exception.

        Parameters
        ----------
        resp : requests.Response
            HTTP response object.

        Returns
        -------
        Any
            Parsed JSON data.

        Raises
        ------
        ValueError
            If response is not valid JSON.
        requests.HTTPError
            If response status indicates an error.
        """
        try:
            return resp.json()
        except ValueError as e:
            logger.warning("Response is not valid JSON: %s", e)
            resp.raise_for_status()
            raise
