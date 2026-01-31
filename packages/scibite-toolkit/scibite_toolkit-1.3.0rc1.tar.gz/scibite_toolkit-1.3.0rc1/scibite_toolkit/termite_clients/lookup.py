# scibite_toolkit/termite_clients/lookup.py
"""Client for TERMite vocabulary lookup operations.

This client provides access to the TERMite Vocabulary Service API, which
queries the **compiled vocabulary cache** loaded in TERMite - not the source
ontology. Use this for entity lookups, taxonomy navigation, and autocomplete
against the vocabulary snapshot used at annotation time.

For source ontology operations (editing, full metadata), use the CENtree clients.
"""

from __future__ import annotations

import logging
from logging import NullHandler
from typing import Any, Optional, Union

from scibite_toolkit.termite_clients.base import TermiteClient
from scibite_toolkit.exceptions import ValidationError

logger = logging.getLogger("scibite_toolkit.termite_clients.lookup")
logger.addHandler(NullHandler())


class TermiteLookupClient(TermiteClient):
    """
    Client for TERMite vocabulary lookup operations.

    Provides access to the TERMite Vocabulary Service API for:
    - Entity lookups (get details for an entity ID)
    - Taxonomy navigation (parents, children, paths from root)
    - Autocomplete suggestions

    .. note::
        This queries the **compiled vocabulary cache** in TERMite, which is
        a snapshot of the source ontology. For live ontology operations,
        use the CENtree clients instead.

    This client inherits all authentication and HTTP methods from TermiteClient.

    Examples
    --------
    Look up an entity from annotation results:

    >>> client = TermiteLookupClient(
    ...     base_url="https://termite.example.com",
    ...     token_url="https://auth.example.com"
    ... )
    >>> client.set_oauth2("client_id", "client_secret")
    >>> entity = client.get_entity("DRUG$CHEMBL25")
    >>> print(entity["name"], entity["publicUri"])

    Get autocomplete suggestions:

    >>> suggestions = client.suggest("aspir", vocabularies=["DRUG"])
    >>> for s in suggestions:
    ...     print(s["name"], s["entityId"])
    """

    # Base path for vocabulary service API
    _VOCAB_SERVICE_PATH = "/api/vocabularyservice/v1"

    def _unwrap_data(self, result: Any) -> Any:
        """
        Unwrap 'data' field from API response if present.

        The Vocabulary Service API wraps responses in {"data": ...}.
        """
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result

    # ── Entity Lookup ──────────────────────────────────────────────
    def get_entity(self, entity_id: str) -> dict[str, Any]:
        """
        Get details for an entity by ID.

        Parameters
        ----------
        entity_id : str
            The entity ID in the form ``"VOCAB$CODE"`` (e.g., ``"DRUG$CHEMBL25"``).
            Case-sensitive.

        Returns
        -------
        dict
            Entity details including:
            - ``entityId``: The entity ID
            - ``name``: Preferred name
            - ``description``: Entity description
            - ``publicUri``: External URI
            - ``publicSynonyms``: List of synonyms
            - ``vocabularyId``: Source vocabulary ID
            - ``vocabularyName``: Source vocabulary name

        Raises
        ------
        ValidationError
            If entity_id is empty.
        APIError
            If the entity is not found or request fails.

        Examples
        --------
        >>> entity = client.get_entity("DRUG$CHEMBL25")
        >>> print(f"{entity['name']}: {entity['publicUri']}")
        Aspirin: https://www.ebi.ac.uk/chembl/compound_report_card/CHEMBL25
        """
        if not entity_id:
            raise ValidationError("entity_id is required")

        endpoint = f"{self._VOCAB_SERVICE_PATH}/entity/{entity_id}"

        logger.debug("Fetching entity: %s", entity_id)

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)

        logger.info("Fetched entity %s", entity_id)
        return self._unwrap_data(result)

    # ── Taxonomy Navigation ────────────────────────────────────────
    def get_node(
        self,
        entity_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        Get taxonomy node with parents and children.

        Parameters
        ----------
        entity_id : str
            The entity ID in the form ``"VOCAB$CODE"``. Case-sensitive.
        limit : int, default=50
            Maximum number of children to return.
        offset : int, default=0
            Number of children to skip (for pagination).

        Returns
        -------
        dict
            Node information including:
            - ``entityId``: The entity ID
            - ``name``: Entity name
            - ``parents``: List of parent entities
            - ``children``: List of child entities
            - ``_noOfChildren``: Total number of children

        Raises
        ------
        ValidationError
            If entity_id is empty.

        Examples
        --------
        >>> node = client.get_node("DRUG$CHEMBL25")
        >>> print(f"Parents: {len(node['parents'])}")
        >>> print(f"Children: {node['_noOfChildren']}")
        """
        if not entity_id:
            raise ValidationError("entity_id is required")

        endpoint = f"{self._VOCAB_SERVICE_PATH}/node/{entity_id}"
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        logger.debug("Fetching node: %s", entity_id)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)

        logger.info("Fetched node %s", entity_id)
        return self._unwrap_data(result)

    def get_paths_from_root(self, entity_id: str) -> list[dict[str, Any]]:
        """
        Get all paths from the hierarchy root to an entity.

        Returns the complete taxonomy paths from root nodes down to the
        specified entity. Useful for understanding an entity's position
        in the concept hierarchy.

        Parameters
        ----------
        entity_id : str
            The entity ID in the form ``"VOCAB$CODE"``. Case-sensitive.

        Returns
        -------
        list of dict
            List of path trees, where each tree has:
            - ``entityId``: Node entity ID
            - ``name``: Node name
            - ``_noOfChildren``: Number of children
            - ``children``: Nested child nodes leading to target

        Raises
        ------
        ValidationError
            If entity_id is empty.

        Examples
        --------
        >>> paths = client.get_paths_from_root("DRUG$CHEMBL25")
        >>> for path in paths:
        ...     print(f"Root: {path['name']}")
        """
        if not entity_id:
            raise ValidationError("entity_id is required")

        endpoint = f"{self._VOCAB_SERVICE_PATH}/paths-from-root/{entity_id}"

        logger.debug("Fetching paths from root for: %s", entity_id)

        resp = self.get(endpoint)
        result = self.json_or_raise(resp)

        logger.info("Fetched paths from root for %s", entity_id)
        return self._unwrap_data(result)

    def get_roots(
        self,
        vocabulary_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get root nodes for a vocabulary.

        Returns the top-level concepts (roots) for a vocabulary's taxonomy.

        Parameters
        ----------
        vocabulary_id : str
            The vocabulary ID (e.g., ``"DRUG"``, ``"INDICATION"``).
            Case-sensitive.
        limit : int, default=50
            Maximum number of roots to return.
        offset : int, default=0
            Number of roots to skip (for pagination).

        Returns
        -------
        list of dict
            List of root nodes, each containing:
            - ``entityId``: Root entity ID
            - ``name``: Root name
            - ``_noOfChildren``: Number of children

        Raises
        ------
        ValidationError
            If vocabulary_id is empty.

        Examples
        --------
        >>> roots = client.get_roots("DRUG")
        >>> for root in roots:
        ...     print(f"{root['name']} ({root['_noOfChildren']} children)")
        """
        if not vocabulary_id:
            raise ValidationError("vocabulary_id is required")

        endpoint = f"{self._VOCAB_SERVICE_PATH}/roots/{vocabulary_id}"
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        logger.debug("Fetching roots for vocabulary: %s", vocabulary_id)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)
        data = self._unwrap_data(result)

        logger.info("Fetched %d roots for %s", len(data) if isinstance(data, list) else 0, vocabulary_id)
        return data

    # ── Autocomplete ───────────────────────────────────────────────
    def suggest(
        self,
        prefix: str,
        vocabularies: Optional[Union[str, list[str]]] = None,
        ancestors: Optional[list[str]] = None,
        entity_ids: Optional[list[str]] = None,
        taxonomy_node: Optional[bool] = None,
        include_ignored: Optional[bool] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get autocomplete suggestions for a prefix.

        Provides entity suggestions for building search/typeahead interfaces.

        Parameters
        ----------
        prefix : str
            The prefix to search for (e.g., ``"aspir"`` for Aspirin).
        vocabularies : str or list of str, optional
            Vocabularies to search (e.g., ``["DRUG", "INDICATION"]``).
            If not specified, uses default vocabularies.
        ancestors : list of str, optional
            Only include entities that are descendants of these taxonomy nodes.
        entity_ids : list of str, optional
            Only include suggestions for these specific entity IDs.
        taxonomy_node : bool, optional
            If ``True``, only return entities that are taxonomy nodes
            (i.e., have children).
        include_ignored : bool, optional
            If ``True``, include entities marked as "ignored" (not used for NER).
            Default is ``False``.
        limit : int, default=50
            Maximum number of suggestions to return.

        Returns
        -------
        list of dict
            List of suggestions, each containing:
            - ``entityId``: Entity ID
            - ``name``: Entity name
            - ``vocabularyId``: Source vocabulary ID
            - ``vocabularyName``: Source vocabulary name
            - ``matchingSynonyms``: Synonyms that matched the prefix

        Raises
        ------
        ValidationError
            If prefix is empty.

        Examples
        --------
        >>> suggestions = client.suggest("aspir", vocabularies=["DRUG"])
        >>> for s in suggestions[:5]:
        ...     print(f"{s['name']} ({s['entityId']})")
        Aspirin (DRUG$CHEMBL25)
        Aspirin tablets (DRUG$...)
        ...

        Filter to taxonomy nodes only:

        >>> nodes = client.suggest("cancer", taxonomy_node=True)
        """
        if not prefix:
            raise ValidationError("prefix is required")

        endpoint = f"{self._VOCAB_SERVICE_PATH}/suggestions"
        params: dict[str, Any] = {
            "prefix": prefix,
            "limit": limit,
        }

        # Normalize vocabularies
        if vocabularies is not None:
            if isinstance(vocabularies, str):
                params["vocabularies"] = [v.strip() for v in vocabularies.split(",")]
            else:
                params["vocabularies"] = vocabularies

        if ancestors is not None:
            params["ancestors"] = ancestors
        if entity_ids is not None:
            params["entityIds"] = entity_ids
        if taxonomy_node is not None:
            params["taxonomyNode"] = taxonomy_node
        if include_ignored is not None:
            params["includeIgnored"] = include_ignored

        logger.debug("Fetching suggestions for prefix: %s", prefix)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)
        data = self._unwrap_data(result)

        logger.info("Fetched %d suggestions for '%s'", len(data) if isinstance(data, list) else 0, prefix)
        return data
