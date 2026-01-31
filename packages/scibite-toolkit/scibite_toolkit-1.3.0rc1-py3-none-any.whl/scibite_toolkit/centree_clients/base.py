# scibite_toolkit/centree_clients/base.py
import logging
from logging import NullHandler
from typing import Optional, Union, Any
from urllib.parse import urlparse
import warnings
import requests
from datetime import datetime, timezone
import time
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from requests import exceptions as reqexc

# Module-level alias for typing
JSON = Union[dict[str, Any], list, None]

logger = logging.getLogger("scibite_toolkit.centree_clients.base")
logger.addHandler(NullHandler())

class CENtreeClient:
    """
    Base client for CENtree API interactions.

    Holds configuration, session, authentication headers, retries, and request helpers
    shared by all CENtree sub-clients (reader, editor, SPARQL, etc.).

    Parameters
    ----------
    base_url : str, optional
        Base URL for the CENtree API (e.g. ``"https://centree.example.com/api"``).
        Trailing slash is automatically removed.
    bearer_token : str, optional
        Bearer token for authentication. Required for most API calls.
    verify : bool or str, default=True
        SSL certificate verification. If ``True`` (default), certificates are verified
        against the system's trust store. If a string, treated as a path to a CA bundle
        file or directory. ``False`` is blocked unless ``allow_insecure=True`` is set.
    timeout : float or (float, float) or None, default=(3.0, None)
        Timeout for requests. If a single float, applies to both the connection and
        read phases. If a tuple ``(connect_timeout, read_timeout)``, sets each phase
        separately. Use ``None`` for no timeout in that phase. For example,
        ``(3.0, None)`` means fail quickly if the server cannot be reached within
        3 seconds, but allow unlimited time for reading the response once connected.
    allow_insecure : bool, default=False
        If ``True``, allows ``verify=False`` to skip TLS certificate verification.
        **Not recommended** except in development with self-signed certificates.
    session : requests.Session, optional
        A pre-configured requests session to use. If not provided, a new session is created.
    retry : urllib3.util.retry.Retry, optional
        Retry policy to use. If not provided, a default policy is applied.

    Notes
    -----
    - `requests.Session` is **not** thread-safe. Create one client instance per thread.
    - For long-running operations such as merging large ontologies, set
      ``timeout=None`` or ``timeout=(3.0, None)`` to avoid premature read timeouts.

    Examples
    --------
    Create a client and perform a GET request::

        from scibite_toolkit.centree.base import CENtreeClient

        client = CENtreeClient(
            base_url="https://centree.example.com/api",
            bearer_token="mytoken",
            timeout=(3.0, None)  # Quick connect timeout, no read limit
        )
        resp = client.get("/ontologies")
        data = resp.json()

    Use as a context manager::

        with CENtreeClient(base_url="...", bearer_token="...") as client:
            resp = client.get("/status")
            print(resp.json())
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: Union[bool, str] = True,
        timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]] = (3.0, None),
        allow_insecure: bool = False,
        retry: Optional[Retry] = None,
        session: Optional[requests.Session] = None,
        **_,
    ):
        self.base_url = base_url.rstrip("/") if base_url else None
        self.bearer_token = bearer_token
        self.allow_insecure = allow_insecure
        self.verify = self._normalize_verify(verify)
        self.timeout = self._normalize_timeout(timeout)
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry or Retry(total=5, backoff_factor=0.5,
                                 status_forcelist=(429,500,502,503,504),
                                 allowed_methods=frozenset(["GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"])))
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        logger.debug("CENtreeClient init base_url=%s verify=%s timeout=%s", self.base_url, self.verify, self.timeout)

    # ── Setters ─────────────────────────────────────────────
    def set_url(self, url: str) -> "CENtreeClient":
        self.base_url = url.rstrip("/")
        return self

    def set_auth(self, token: str) -> "CENtreeClient":
        self.bearer_token = token
        return self

    def set_verify(self, verify: Union[bool, str]) -> "CENtreeClient":
        self.verify = self._normalize_verify(verify)
        return self

    def set_timeout(self, timeout: Optional[Union[float, tuple[float, float]]]) -> "CENtreeClient":
        self.timeout = self._normalize_timeout(timeout)
        return self

    # ── Helpers ────────────────────────────────────────────
    def _normalize_verify(self, verify: Union[bool, str]) -> Union[bool, str]:
        if verify is False:
            if not self.allow_insecure:
                raise ValueError(
                    "Insecure TLS disabled. Pass allow_insecure=True if you really want verify=False (not recommended)."
                )
            warnings.warn("TLS certificate verification disabled (verify=False). This is insecure.", UserWarning)
        return verify

    def _normalize_timeout(self, timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]]):
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
        if not self.bearer_token:
            raise ValueError("Bearer token is not set.")
        return {"Authorization": f"Bearer {self.bearer_token}"}

    def _build_url(self, endpoint: str) -> str:
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"
        if urlparse(url).scheme != "https":
            raise ValueError(f"Non-HTTPS URL rejected: {url}")
        return url

    def set_oauth2(self, client_id: str, client_secret: str) -> bool:
        """
        Authenticate using OAuth2 client credentials flow and set the bearer token.

        Parameters
        ----------
        client_id : str
            The client ID for OAuth2 authentication.
        client_secret : str
            The client secret for OAuth2 authentication.

        Returns
        -------
        bool
            True if authentication was successful, False otherwise.
        """
        token_url = f"{self.base_url}/auth/realms/Scibite/protocol/openid-connect/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = self.session.post(
                token_url,
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

            self.set_auth(access_token)

            expires_in = int(body.get("expires_in", 0))
            if expires_in:
                utc_when = datetime.fromtimestamp(
                    time.time() + expires_in, tz=timezone.utc
                ).isoformat()
                logger.info(
                    "OAuth2 token acquired; expires in ~%ds (at %s)",
                    expires_in,
                    utc_when,
                )
            else:
                logger.info("OAuth2 token acquired; 'expires_in' not provided")

            return True
        except reqexc.HTTPError as e:
            r = getattr(e, "response", None)
            code = getattr(r, "status_code", "unknown")
            snippet = ""
            try:
                # avoid huge logs
                snippet = (r.text or "")[:300] if r is not None else ""
            except Exception:
                pass
            logger.warning("OAuth2 HTTP error (%s) at %s; body: %s", code, token_url, snippet)
            return False

        except reqexc.SSLError as e:
            logger.warning("OAuth2 TLS/SSL error at %s: %s (verify=%s)", token_url, e, self.verify)
            return False

        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            logger.warning("OAuth2 network error at %s: %s", token_url, e)
            return False

        except Exception as e:
            logger.warning("OAuth2 authentication failed: %s", e)
            return False

    def refresh_token(self) -> bool:
        """
        Attempt to refresh the bearer token using the current token.

        Returns
        -------
        bool
            True if a new token was received and set, False otherwise.
        """
        if not self.bearer_token:
            logger.warning("Cannot refresh token: no bearer_token set")
            return False

        url = f"{self.base_url}/api/authenticate/token/refresh"
        payload = {"rememberMe": True, "id_token": self.bearer_token}

        try:
            resp = self.session.post(
                url,
                json=payload,
                verify=self.verify,
                timeout=self.timeout
            )
            resp.raise_for_status()

            body = resp.json()
            new_token = body.get("id_token")
            if new_token:
                self.set_auth(new_token)
                logger.info("Bearer token refreshed successfully.")
                return True

            logger.warning("Token refresh response missing 'id_token'")
            return False

        except reqexc.HTTPError as e:
            r = getattr(e, "response", None)
            code = getattr(r, "status_code", "unknown")
            snippet = ""
            try:
                snippet = (r.text or "")[:300] if r is not None else ""
            except Exception:
                pass
            logger.warning("Token refresh HTTP error (%s) at %s; body: %s", code, url, snippet)
            return False

        except reqexc.SSLError as e:
            logger.warning("Token refresh TLS/SSL error at %s: %s (verify=%s)", url, e, self.verify)
            return False

        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            logger.warning("Token refresh network error at %s: %s", url, e)
            return False

        except Exception as e:
            logger.warning("Token refresh failed: %s", e)
            return False

    def request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        json: JSON = None,
        headers: Optional[dict[str, str]] = None,
        raise_for_status: bool = True,
        timeout: Optional[Union[float, tuple[Optional[float], Optional[float]]]] = None,
        suppress_warning: bool = False,
        **kwargs: Any,
    ) -> requests.Response:
        """
        Send an HTTP request to the configured CENtree API endpoint.

        Parameters
        ----------
        method : str
            HTTP method to use, e.g., 'GET', 'POST', 'PUT', etc.
        endpoint : str
            API endpoint path relative to the base URL (e.g. '/api/ontologies/all')
            or an absolute URL (overrides base_url).
        params : dict, optional
            Query parameters to include in the request URL.
        json : dict or list, optional
            JSON payload to include in the request body (for POST, PUT, etc.).
        headers : dict, optional
            Additional HTTP headers to include in the request. These will be merged
            with the authorization headers.
        raise_for_status : bool, default=True
            If True, raise an HTTPError for 4xx/5xx responses. If False, return
            the response object even on failure.
        timeout : float or (float, float), optional
            Timeout for the request. Can be a single float (total timeout),
            or a tuple (connect timeout, read timeout). If not provided, uses
            the default timeout configured on the client. Use 0 or None to disable timeout.
        suppress_warning : bool, default=False
            If True, suppress the warning log message for failed requests.
            Useful during polling operations where failures are expected (e.g.,
            waiting for an ontology to finish loading).
        **kwargs : any
            Additional arguments passed directly to `requests.Session.request()`.

        Returns
        -------
        requests.Response
            The raw response object from the HTTP request.

        Raises
        ------
        ValueError
            If no base URL is set and the endpoint is relative.
        requests.HTTPError
            If `raise_for_status` is True and the response is unsuccessful.
        """
        if not endpoint.startswith("http") and not self.base_url:
            raise ValueError("Base URL is not set and endpoint is relative.")

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
            logger.debug("Request JSON payload (keys/type): %s",
                         list(json.keys()) if isinstance(json, dict) else type(json))

        resp = self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            headers=req_headers,
            verify=self.verify,
            timeout=eff_timeout,
            **kwargs,
        )

        if raise_for_status and not resp.ok:
            if not suppress_warning:
                logger.warning("Request failed %s %s -> %s", method.upper(), url, resp.status_code)
            resp.raise_for_status()

        return resp

    def get_account_details(self) -> dict[str, Any]:
        """
        Retrieve details about the authenticated user.

        Returns:
            dict[str, Any]: Dictionary containing user details and permission sets.

        Raises:
            HTTPError: If the request fails or returns an unexpected response.
        """
        endpoint = "/api/account"
        logger.info("Fetching account details from %s", endpoint)

        try:
            response = self.request("GET", endpoint)
            response.raise_for_status()
            logger.info("✓ Successfully retrieved account details for user.")
            return response.json()
        except Exception as e:
            logger.error("Failed to retrieve account details: %s", e)
            raise

    def get_username(self) -> str:
        """
        Retrieve the login username of the authenticated user.

        Returns:
            str: The user's login name.

        Raises:
            KeyError: If the 'login' field is missing from the response.
            HTTPError: If the account details request fails.
        """
        account = self.get_account_details()
        try:
            return account["login"]
        except KeyError:
            logger.error("Account details response is missing 'login' field: %s", account)
            raise

    # ── Convenience wrappers ─────────────────────────────────────────
    def get(self, endpoint: str, **kw: Any) -> requests.Response:
        return self.request("GET", endpoint, **kw)

    def post(self, endpoint: str, **kw: Any) -> requests.Response:
        return self.request("POST", endpoint, **kw)

    def put(self, endpoint: str, **kw: Any) -> requests.Response:
        return self.request("PUT", endpoint, **kw)

    def patch(self, endpoint: str, **kw: Any) -> requests.Response:
        return self.request("PATCH", endpoint, **kw)

    def delete(self, endpoint: str, **kw: Any) -> requests.Response:
        return self.request("DELETE", endpoint, **kw)

    # ── JSON helper ──────────────────────────────────────────────────
    def json_or_raise(self, resp: requests.Response) -> Any:
        try:
            return resp.json()
        except ValueError as e:
            logger.warning("Response is not valid JSON: %s", e)
            resp.raise_for_status()
            raise

    # ── Cleanup ──────────────────────────────────────────────────────
    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> "CENtreeClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


