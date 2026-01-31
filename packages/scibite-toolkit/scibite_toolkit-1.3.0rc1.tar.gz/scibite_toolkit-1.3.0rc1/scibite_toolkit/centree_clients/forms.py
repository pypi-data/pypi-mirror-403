"""
forms.py

CENtreeFormsClient provides access to CENtree Forms indexes for ontology search and navigation.
Forms are optimized JSON representations of ontology entities enabling fast search and retrieval.
"""

import logging
from logging import NullHandler
from .base import CENtreeClient
from typing import Optional, Union

# ── Logging config ──────────────────────────────────────────
logger = logging.getLogger("scibite_toolkit.centree_clients.forms")
logger.addHandler(NullHandler())
# ────────────────────────────────────────────────────────────


class CENtreeFormsClient(CENtreeClient):
    """
    A client class for CENtree Forms operations.

    Forms are optimized JSON indexes of ontology entities that enable fast search
    and efficient navigation. This client provides methods to search forms indexes,
    query descendants, and manage forms index creation/deletion.

    Forms indexes must be created for an ontology before they can be searched.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: Union[bool, str] = True,
        **kwargs,
    ):
        super().__init__(base_url=base_url, bearer_token=bearer_token, verify=verify, **kwargs)
        logger.debug("Initialized CENtreeFormsClient base_url=%s", self.base_url)

    # ── Search Methods ──────────────────────────────────────────

    def search(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            from_: int = 0,
            size: int = 10,
    ) -> dict:
        """
        General string search across ontology forms indexes.

        Parameters
        ----------
        query : str
            Search query string.
        ontology_list : str or list of str, optional
            Filter results to specific ontologies.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results when using children_of.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.

        Returns
        -------
        dict
            PageOntologyJSONFormBean with structure:
            {"from": int, "total": int, "elements": [OntologyJSONFormBean, ...]}

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeFormsClient(base_url="...", bearer_token="...")
        >>> results = client.search("lung cancer", ontology_list=["efo"])
        >>> print(f"Found {results['total']} results")
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/forms/search"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
            "includeSelf": include_self,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_direct(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            from_: int = 0,
            size: int = 10,
    ) -> dict:
        """
        Direct branch search across ontology forms.

        Performs a direct search within specific ontology branches.

        Parameters
        ----------
        query : str
            Search query string.
        ontology_list : str or list of str, optional
            Filter results to specific ontologies.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results when using children_of.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.

        Returns
        -------
        dict
            PageOntologyJSONFormBean with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/forms/search/direct"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
            "includeSelf": include_self,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms direct search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_exact(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            from_: int = 0,
            size: int = 10,
    ) -> dict:
        """
        Exact string match search across ontology forms.

        Parameters
        ----------
        query : str
            Exact search term.
        ontology_list : str or list of str, optional
            Filter results to specific ontologies.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results when using children_of.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.

        Returns
        -------
        dict
            PageOntologyJSONFormBean with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/forms/search/exact"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
            "includeSelf": include_self,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms exact search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_ranked(
            self,
            query: str,
            ontology_ranking: Optional[list[str]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            from_: int = 0,
            size: int = 10,
    ) -> dict:
        """
        String search with ontology ranking preference.

        Results are ranked by preferred ontology order.

        Parameters
        ----------
        query : str
            Search query string.
        ontology_ranking : list of str, optional
            Preferred ontology order (e.g., ["GO", "CHEBI"]).
            Results from higher-ranked ontologies appear first.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results when using children_of.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.

        Returns
        -------
        dict
            PageOntologyJSONFormBean with ranked results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> # Prefer GO over CHEBI results
        >>> results = client.search_ranked("protein", ontology_ranking=["GO", "CHEBI"])
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/forms/search/ranked"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
            "includeSelf": include_self,
        }

        if ontology_ranking:
            params["ontologyRanking"] = ontology_ranking
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms ranked search query=%r ranking=%r", query, ontology_ranking)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_exact_multiple(
            self,
            ontology_id: str,
            identifiers: Optional[list[str]] = None,
    ) -> dict:
        """
        Batch exact search by primaryId, shortFormId, or primaryLabel.

        Searches for multiple identifiers at once within a single ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to search within.
        identifiers : list of str, optional
            List of identifiers to search (primaryId, shortFormId, or primaryLabel).

        Returns
        -------
        dict
            ExactMultipleFormSearchResult with structure:
            {"resultList": [OntologyJSONFormBean, ...]}

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> ids = ["GO:0008150", "GO:0008152"]
        >>> results = client.search_exact_multiple("go", identifiers=ids)
        >>> print(f"Found {len(results['resultList'])} matches")
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/forms/search/{ontology_id}/exactMultiple"
        params = {}
        if identifiers:
            params["identifiers"] = identifiers

        logger.debug("Forms exact multiple search ontology=%r count=%d",
                     ontology_id, len(identifiers) if identifiers else 0)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_descendants(
            self,
            ontology_list: Optional[Union[str, list[str]]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            from_: int = 0,
            size: int = 10,
    ) -> dict:
        """
        Search descendants with pagination.

        **Note:** Limited to max 20,000 descendants. Use search_descendants_scroll()
        for larger result sets.

        Parameters
        ----------
        ontology_list : str or list of str, optional
            Filter results to specific ontologies.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page (max 20,000 total).

        Returns
        -------
        dict
            PageOntologyJSONFormBean with paginated descendants.

        Raises
        ------
        requests.HTTPError
            If the HTTP request is unsuccessful or if result set exceeds 20,000.

        Examples
        --------
        >>> # Get all descendants of a GO term
        >>> results = client.search_descendants(
        ...     ontology_list=["go"],
        ...     children_of=["GO:0008150"],
        ...     size=100
        ... )
        """
        endpoint = "/api/forms/search/descendants"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "from": from_,
            "size": size,
            "includeSelf": include_self,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms descendants search childrenOf=%r", children_of)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_descendants_scroll(
            self,
            scroll_id: Optional[str] = None,
            ontology_list: Optional[Union[str, list[str]]] = None,
            children_of: Optional[Union[str, list[str]]] = None,
            include_self: bool = False,
            size: int = 1000,
    ) -> dict:
        """
        Search descendants with scroll mechanism for large result sets.

        Use this method for descendant queries exceeding 20,000 results.
        First call: omit scroll_id. Subsequent calls: use scrollId from previous response.

        Parameters
        ----------
        scroll_id : str, optional
            Scroll ID from previous response (omit for first request).
        ontology_list : str or list of str, optional
            Filter results to specific ontologies.
        children_of : str or list of str, optional
            Limit results to children of specified entities.
        include_self : bool, default False
            Include the parent entity in results.
        size : int, default 1000
            Number of results per scroll batch (max 20,000).

        Returns
        -------
        dict
            ScrollOntologyJSONFormBean with structure:
            {"total": int, "scrollId": str, "elements": [OntologyJSONFormBean, ...]}
            Use the returned scrollId for the next request.

        Raises
        ------
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> # First request
        >>> batch1 = client.search_descendants_scroll(
        ...     ontology_list=["go"],
        ...     children_of=["GO:0008150"],
        ...     size=1000
        ... )
        >>> print(f"Total: {batch1['total']}, got {len(batch1['elements'])}")
        >>>
        >>> # Subsequent requests
        >>> batch2 = client.search_descendants_scroll(scroll_id=batch1['scrollId'])
        >>> # Continue until elements is empty
        """
        endpoint = "/api/forms/search/descendants/scroll"
        params: dict[str, Union[str, int, bool, list[str]]] = {
            "size": size,
            "includeSelf": include_self,
        }

        if scroll_id:
            params["scrollId"] = scroll_id
        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if children_of:
            params["childrenOf"] = ([children_of] if isinstance(children_of, str) else children_of)

        logger.debug("Forms descendants scroll scrollId=%r childrenOf=%r", scroll_id, children_of)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    # ── Management Methods ──────────────────────────────────────

    def create_forms_index(
            self,
            ontology_id: str,
            relationships: Optional[list[str]] = None,
            with_job_details: bool = False,
    ) -> dict:
        """
        Create a forms index for an ontology.

        Forms indexes enable fast search and navigation. This operation is asynchronous
        and returns job details for monitoring progress.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to create the forms index for.
        relationships : list of str, optional
            Relationship types to include in the index.
            Default: ["subClassOf"]
            Allowed: "subClassOf", "partOf", "derivesFrom", "developsFrom", "equivalence"
        with_job_details : bool, default False
            Include full job details in response.

        Returns
        -------
        dict
            JobSubmitResponse with structure:
            {"message": str, "job": JobJson (if with_job_details=True)}

        Raises
        ------
        ValueError
            If `ontology_id` is empty or relationships contains invalid values.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> # Create index with default relationships
        >>> job = client.create_forms_index("efo")
        >>> print(job["message"])
        >>>
        >>> # Create index with custom relationships
        >>> job = client.create_forms_index(
        ...     "go",
        ...     relationships=["subClassOf", "partOf"],
        ...     with_job_details=True
        ... )
        >>> job_id = job["job"]["id"]
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        allowed_relationships = {"subClassOf", "partOf", "derivesFrom", "developsFrom", "equivalence"}
        if relationships:
            invalid = set(relationships) - allowed_relationships
            if invalid:
                raise ValueError(f"Invalid relationships: {invalid}. "
                                 f"Allowed: {allowed_relationships}")

        endpoint = f"/api/ontology/{ontology_id}/forms"
        params = {"withJobDetails": str(with_job_details).lower()}

        if relationships:
            params["relationships"] = relationships

        logger.debug("Creating forms index for ontology %r with relationships %r",
                     ontology_id, relationships or ["subClassOf"])
        resp = self.request("POST", endpoint, params=params)
        # Handle text response when with_job_details=False
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def delete_forms_index(
            self,
            ontology_id: str,
            with_job_details: bool = False,
    ) -> dict:
        """
        Delete a forms index for an ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to delete the forms index for.
        with_job_details : bool, default False
            Include full job details in response.

        Returns
        -------
        dict
            JobSubmitResponse with structure:
            {"message": str, "job": JobJson (if with_job_details=True)}

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> result = client.delete_forms_index("efo")
        >>> print(result["message"])
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/ontology/{ontology_id}/forms"
        params = {"withJobDetails": str(with_job_details).lower()}

        logger.debug("Deleting forms index for ontology %r", ontology_id)
        resp = self.request("DELETE", endpoint, params=params)
        # Handle text response when with_job_details=False
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def forms_index_status(self, ontology_id: str) -> dict:
        """
        Get forms index status for an ontology.

        Retrieves metadata about the ontology and its forms index status,
        including version, modification dates, and whether a forms index exists.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to check status for.

        Returns
        -------
        dict
            Dictionary with forms index status containing:
            - version: str - Ontology version
            - lastModified: str - Last modification timestamp
            - hasFormsIndex: bool - Whether a forms index exists
            - formsIndexLastModified: str - Forms index last modification timestamp
            - formsIndexLastModifiedBy: str - User who last modified the forms index

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> status = client.forms_index_status("efo")
        >>> print(f"Has forms index: {status['hasFormsIndex']}")
        >>> if status['hasFormsIndex']:
        ...     print(f"Last modified: {status['formsIndexLastModified']}")
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/ontologies/{ontology_id}/ontologyMetadataSummary"

        logger.debug("Fetching forms index status for ontology %r", ontology_id)
        resp = self.request("GET", endpoint)
        data = self.json_or_raise(resp)

        return {
            "version": data.get("version"),
            "lastModified": data.get("lastModified"),
            "lastModifiedBy": data.get("lastModifiedBy"),
            "hasFormsIndex": data.get("hasFormsIndex"),
            "formsIndexLastModified": data.get("formsIndexLastModified"),
            "formsIndexLastModifiedBy": data.get("formsIndexLastModifiedBy"),
        }

    def has_forms_index(self, ontology_id: str) -> bool:
        """
        Check if an ontology has a forms index.

        This is a convenience method that wraps forms_index_status() to provide
        a simple boolean check.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to check.

        Returns
        -------
        bool
            True if the ontology has a forms index, False otherwise.

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeFormsClient(base_url="...", bearer_token="...")
        >>> if client.has_forms_index("efo"):
        ...     print("EFO has a forms index")
        >>> else:
        ...     print("Creating forms index for EFO...")
        ...     client.create_forms_index("efo")
        """
        status = self.forms_index_status(ontology_id)
        return status.get("hasFormsIndex", False)

    def batch_forms_index_status(self, ontology_ids: list[str]) -> dict[str, dict]:
        """
        Get forms index status for multiple ontologies.

        This method fetches status for multiple ontologies in sequence and returns
        a dictionary mapping ontology IDs to their status information.

        Parameters
        ----------
        ontology_ids : list of str
            List of ontology IDs to check status for.

        Returns
        -------
        dict of str to dict
            Dictionary mapping ontology ID to status dictionary.
            Each status dictionary contains the same fields as forms_index_status().
            If an ontology status check fails, it will not be included in the result.

        Examples
        --------
        >>> client = CENtreeFormsClient(base_url="...", bearer_token="...")
        >>> statuses = client.batch_forms_index_status(["efo", "go", "mondo"])
        >>> for onto_id, status in statuses.items():
        ...     if status["hasFormsIndex"]:
        ...         print(f"{onto_id}: has index (modified {status['formsIndexLastModified']})")
        ...     else:
        ...         print(f"{onto_id}: no index")
        """
        results = {}
        for ontology_id in ontology_ids:
            try:
                status = self.forms_index_status(ontology_id)
                results[ontology_id] = status
                logger.debug("Retrieved status for ontology %r", ontology_id)
            except Exception as e:
                logger.warning("Failed to get status for ontology %r: %s", ontology_id, e)
                # Skip this ontology and continue with the rest
                continue
        return results