# scibite_toolkit/termite_clients/metadata.py
"""Client for TERMite metadata operations."""

from __future__ import annotations

import logging
from logging import NullHandler
from typing import Any, Optional, Union

from scibite_toolkit.termite_clients.base import TermiteClient
from scibite_toolkit.exceptions import APIError, ValidationError

logger = logging.getLogger("scibite_toolkit.termite_clients.metadata")
logger.addHandler(NullHandler())


class TermiteMetadataClient(TermiteClient):
    """
    Client for TERMite metadata operations.

    Provides methods for retrieving information about the TERMite instance,
    including system status, available vocabularies, parsers, and runtime options.

    This client inherits all authentication and HTTP methods from TermiteClient.

    Examples
    --------
    Get system status:

    >>> client = TermiteMetadataClient(
    ...     base_url="https://termite.example.com",
    ...     token_url="https://auth.example.com"
    ... )
    >>> client.set_oauth2("client_id", "client_secret")
    >>> status = client.get_status()
    >>> print(status["version"])

    List available vocabularies:

    >>> vocabs = client.get_vocabularies()
    >>> for v in vocabs:
    ...     print(v["name"], v["version"])

    Get runtime options:

    >>> options = client.get_runtime_options()
    >>> for opt in options:
    ...     print(opt["name"], opt["defaultValue"])
    """

    def _unwrap_data(self, result: Any) -> Any:
        """
        Unwrap 'data' field from API response if present.

        TERMite API typically wraps responses in {"data": ...}.
        This helper extracts the data field for cleaner return values.
        """
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result

    # ── Status ─────────────────────────────────────────────────────
    def get_status(self, fields: str = "*") -> dict[str, Any]:
        """
        Fetch system status from TERMite.

        Parameters
        ----------
        fields : str, default="*"
            Comma-separated list of fields to return, or ``"*"`` for all fields.
            Available fields include: version, uptime, memory, vocabularies.

        Returns
        -------
        dict
            System status information.

        Raises
        ------
        APIError
            If the request fails.

        Examples
        --------
        >>> status = client.get_status()
        >>> print(f"TERMite version: {status['version']}")

        Get specific fields only:

        >>> status = client.get_status(fields="version,uptime")
        """
        endpoint = "/api/termite/v1/status"
        params = {"fields": fields}

        logger.debug("Fetching TERMite status: fields=%s", fields)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)

        logger.info("TERMite status fetched successfully")
        return self._unwrap_data(result)

    # ── Vocabularies ───────────────────────────────────────────────
    def get_vocabularies(
        self, has_current_vocabulary_file: bool = True
    ) -> list[dict[str, Any]]:
        """
        Fetch available vocabularies from TERMite.

        Parameters
        ----------
        has_current_vocabulary_file : bool, default=True
            If ``True``, only return vocabularies that have a current
            vocabulary file loaded. Set to ``False`` to include all
            configured vocabularies.

        Returns
        -------
        list of dict
            List of vocabulary objects, each containing name, version,
            entity count, and other metadata.

        Raises
        ------
        APIError
            If the request fails.

        Examples
        --------
        >>> vocabs = client.get_vocabularies()
        >>> for v in vocabs:
        ...     print(f"{v['name']}: {v['entityCount']} entities")

        Include vocabularies without loaded files:

        >>> all_vocabs = client.get_vocabularies(has_current_vocabulary_file=False)
        """
        endpoint = "/api/termite/v1/vocabularies"
        params = {
            "hasCurrentVocabularyFile": "true" if has_current_vocabulary_file else "false"
        }

        logger.debug("Fetching vocabularies: hasCurrentVocabularyFile=%s", has_current_vocabulary_file)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)
        data = self._unwrap_data(result)

        logger.info("Fetched %d vocabularies", len(data) if isinstance(data, list) else 0)
        return data

    def get_vocabulary(self, vocab_name: str) -> dict[str, Any]:
        """
        Fetch details for a specific vocabulary.

        Parameters
        ----------
        vocab_name : str
            The vocabulary name/ID (e.g., ``"DRUG"``, ``"INDICATION"``).

        Returns
        -------
        dict
            Vocabulary details including name, version, entity count.

        Raises
        ------
        ValidationError
            If vocab_name is empty.
        APIError
            If the vocabulary is not found or request fails.

        Examples
        --------
        >>> drug_vocab = client.get_vocabulary("DRUG")
        >>> print(f"Version: {drug_vocab['version']}")
        """
        if not vocab_name:
            raise ValidationError("vocab_name is required")

        endpoint = f"/api/termite/v1/vocabularies/{vocab_name}"

        logger.debug("Fetching vocabulary: %s", vocab_name)

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)

        logger.info("Fetched vocabulary %s", vocab_name)
        return self._unwrap_data(result)

    # ── Parsers ────────────────────────────────────────────────────
    def get_parsers(self) -> list[dict[str, Any]]:
        """
        Fetch available document parsers from TERMite.

        Returns
        -------
        list of dict
            List of parser objects, each containing parser ID, supported
            file types, and configuration options.

        Raises
        ------
        APIError
            If the request fails.

        Examples
        --------
        >>> parsers = client.get_parsers()
        >>> for p in parsers:
        ...     print(f"{p['id']}: {p['description']}")
        """
        endpoint = "/api/termite/v1/parsers"

        logger.debug("Fetching parsers")

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)
        data = self._unwrap_data(result)

        logger.info("Fetched %d parsers", len(data) if isinstance(data, list) else 0)
        return data

    def get_parser(self, parser_id: str) -> dict[str, Any]:
        """
        Fetch details for a specific parser.

        Parameters
        ----------
        parser_id : str
            The parser ID (e.g., ``"pdf"``, ``"txt"``, ``"xml"``).

        Returns
        -------
        dict
            Parser details including supported options and file types.

        Raises
        ------
        ValidationError
            If parser_id is empty.
        APIError
            If the parser is not found or request fails.

        Examples
        --------
        >>> pdf_parser = client.get_parser("pdf")
        >>> print(pdf_parser["supportedExtensions"])
        """
        if not parser_id:
            raise ValidationError("parser_id is required")

        endpoint = f"/api/termite/v1/parsers/{parser_id}"

        logger.debug("Fetching parser: %s", parser_id)

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)

        logger.info("Fetched parser %s", parser_id)
        return self._unwrap_data(result)

    # ── Runtime Options ────────────────────────────────────────────
    def get_runtime_options(self) -> list[dict[str, Any]]:
        """
        Fetch available runtime options from TERMite.

        Runtime options control annotation behavior (e.g., subsumption,
        boosting, case matching).

        Returns
        -------
        list of dict
            List of runtime option objects, each containing name,
            description, default value, and allowed values.

        Raises
        ------
        APIError
            If the request fails.

        Examples
        --------
        >>> options = client.get_runtime_options()
        >>> for opt in options:
        ...     print(f"{opt['name']}: {opt['defaultValue']}")
        """
        endpoint = "/api/termite/v1/runtime-options"

        logger.debug("Fetching runtime options")

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)
        data = self._unwrap_data(result)

        logger.info("Fetched %d runtime options", len(data) if isinstance(data, list) else 0)
        return data

    def get_runtime_option(self, option_name: str) -> dict[str, Any]:
        """
        Fetch details for a specific runtime option.

        Parameters
        ----------
        option_name : str
            The option name (e.g., ``"subsume"``, ``"boost"``, ``"caseMatch"``).

        Returns
        -------
        dict
            Runtime option details including description, default value,
            and allowed values.

        Raises
        ------
        ValidationError
            If option_name is empty.
        APIError
            If the option is not found or request fails.

        Examples
        --------
        >>> subsume = client.get_runtime_option("subsume")
        >>> print(f"Default: {subsume['defaultValue']}")
        >>> print(f"Allowed values: {subsume['allowedValues']}")
        """
        if not option_name:
            raise ValidationError("option_name is required")

        endpoint = f"/api/termite/v1/runtime-options/{option_name}"

        logger.debug("Fetching runtime option: %s", option_name)

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)

        logger.info("Fetched runtime option %s", option_name)
        return self._unwrap_data(result)
