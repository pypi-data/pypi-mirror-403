"""
reader.py

CENtreeReaderClient provides read-only access to ontologies in a CENtree server.
Supports entity lookups, label-based queries, tree navigation, and metadata inspection.
"""

import logging
from logging import NullHandler
from .base import CENtreeClient
from typing import Optional, Union

# ── Logging config ──────────────────────────────────────────
logger = logging.getLogger("scibite_toolkit.centree_clients.reader")
logger.addHandler(NullHandler())
# ────────────────────────────────────────────────────────────


class CENtreeReaderClient(CENtreeClient):
    """
    A client class for read-only operations on CENtree ontologies.
    Provides methods to query ontology metadata, entities, and perform lookups.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: Union[bool, str] = True,
        **kwargs,
    ):
        super().__init__(base_url=base_url, bearer_token=bearer_token, verify=verify, **kwargs)
        logger.debug("Initialized CENtreeReaderClient base_url=%s", self.base_url)

    # ── Search Methods ──────────────────────────────────────────

    def search(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
            boost_priority: Optional[str] = None,
    ) -> dict:
        """
        General search across ontologies.

        Parameters
        ----------
        query : str
            The search query string.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification. Available values : RELEVANCE, ASC
        boost_priority : str, optional
            Boost priority weighting. Available values : PREFIX, FUZZY, EXACT_CASE_INSENSITIVE.
            Default value : FUZZY

        Returns
        -------
        dict
            JSON response with structure: {"from": int, "total": int, "elements": list}

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort
        if boost_priority:
            params["boostPriority"] = boost_priority

        logger.debug("General search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    # Alias for clarity that search() searches classes
    search_classes = search

    def search_exact(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for exact matches across ontologies.

        Parameters
        ----------
        query : str
            The search term for exact match.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/classes/exact"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Exact search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_contains(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for terms containing the query string.

        Parameters
        ----------
        query : str
            The search term to find within labels.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/classes/contains"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Contains search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_starts_with(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for terms starting with the query string.

        Parameters
        ----------
        query : str
            The search term prefix.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/classes/startsWith"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Starts-with search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_ends_with(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for terms ending with the query string.

        Parameters
        ----------
        query : str
            The search term suffix.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/classes/endsWith"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Ends-with search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_instances(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
            boost_priority: Optional[str] = None,
    ) -> dict:
        """
        Search for ontology instances/individuals.

        Parameters
        ----------
        query : str
            The search query string.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.
        boost_priority : str, optional
            Boost priority weighting.

        Returns
        -------
        dict
            JSON response with paginated instance results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/instances"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort
        if boost_priority:
            params["boostPriority"] = boost_priority

        logger.debug("Instance search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_instances_exact(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for instances with exact label/identifier match.

        Parameters
        ----------
        query : str
            The search term for exact match.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated instance results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/instances/exact"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Exact instance search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_properties(
            self,
            query: str,
            property_type: Optional[Union[str, list[str]]] = None,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
            boost_priority: Optional[str] = None,
    ) -> dict:
        """
        Search for ontology properties/relations.

        Parameters
        ----------
        query : str
            The search query string.
        property_type : str or list of str, optional
            Filter by property type (e.g., "annotation", "object", "data").
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.
        boost_priority : str, optional
            Boost priority weighting.

        Returns
        -------
        dict
            JSON response with paginated property results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/properties"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if property_type:
            params["propertyType"] = ([property_type] if isinstance(property_type, str) else property_type)
        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort
        if boost_priority:
            params["boostPriority"] = boost_priority

        logger.debug("Property search query=%r propertyType=%r ontologies=%r",
                     query, params.get("propertyType"), params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_properties_exact(
            self,
            query: str,
            property_type: Optional[Union[str, list[str]]] = None,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for properties with exact match.

        Parameters
        ----------
        query : str
            The search term for exact match.
        property_type : str or list of str, optional
            Filter by property type (e.g., "annotation", "object", "data").
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated property results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/properties/exact"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if property_type:
            params["propertyType"] = ([property_type] if isinstance(property_type, str) else property_type)
        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Exact property search query=%r propertyType=%r ontologies=%r",
                     query, params.get("propertyType"), params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_ontologies(
            self,
            query: Optional[str] = None,
            type_filter: Optional[str] = None,
            page: int = 0,
            size: int = 10,
            sort_by_field: Optional[str] = None,
            sort_order: Optional[str] = None,
    ) -> dict:
        """
        Search for ontologies or list all ontologies.

        Parameters
        ----------
        query : str, optional
            Search query for ontology metadata. If not provided, lists all ontologies.
        type_filter : str, optional
            Filter by ontology type.
        page : int, default 0
            Page number (0-indexed).
        size : int, default 10
            Number of results per page.
        sort_by_field : str, optional
            Field to sort by.
        sort_order : str, optional
            Sort order ("ASC" or "DESC").

        Returns
        -------
        dict
            JSON response with ontology metadata.

        Raises
        ------
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        endpoint = "/api/search/ontologies"
        params: dict[str, Union[str, int]] = {
            "page": page,
            "size": size,
        }

        if query:
            params["q"] = query
        if type_filter:
            params["type"] = type_filter
        if sort_by_field:
            params["sortByField"] = sort_by_field
        if sort_order:
            params["sortOrder"] = sort_order

        logger.debug("Ontology search query=%r type=%r page=%d", query, type_filter, page)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_exact_multiple(
            self,
            ontology_id: str,
            identifiers: list[str],
    ) -> dict:
        """
        Search for multiple identifiers at once within an ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to search within.
        identifiers : list of str
            List of identifiers to look up.

        Returns
        -------
        dict
            JSON response with results for each identifier.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `identifiers` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not identifiers or not isinstance(identifiers, list):
            raise ValueError("identifiers must be a non-empty list")

        endpoint = f"/api/search/{ontology_id}/exactMultiple"
        params = {"identifiers": identifiers}

        logger.debug("Exact multiple search ontology=%r count=%d", ontology_id, len(identifiers))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_obsolete(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for obsolete/deprecated classes.

        Parameters
        ----------
        query : str
            The search query string.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated obsolete class results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/obsolete"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Obsolete search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def search_obsolete_exact(
            self,
            query: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
            from_: int = 0,
            size: int = 10,
            sort: Optional[str] = None,
    ) -> dict:
        """
        Search for obsolete/deprecated classes with exact match.

        Parameters
        ----------
        query : str
            The search term for exact match.
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results per page.
        sort : str, optional
            Sort specification.

        Returns
        -------
        dict
            JSON response with paginated obsolete class results.

        Raises
        ------
        ValueError
            If `query` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not query:
            raise ValueError("query is required")

        endpoint = "/api/search/obsolete/exact"
        params: dict[str, Union[str, int, list[str]]] = {
            "q": query,
            "from": from_,
            "size": size,
        }

        if ontology_list:
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)
        if sort:
            params["sort"] = sort

        logger.debug("Exact obsolete search query=%r ontologies=%r", query, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    # ── Export Methods ──────────────────────────────────────────

    def export_owl(
            self,
            ontology_id: str,
            owl_format: str = "RDFXML",
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in OWL/RDF format (asynchronous).

        This triggers an asynchronous export job. Use the returned job ID to monitor
        progress and retrieve the file once complete.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        owl_format : str, default "RDFXML"
            Export format. Options: "OBO", "RDFXML", "OWLXML", "OWLFUNC", "N3",
            "TURTLE", "JSONLD", "MOS".
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `owl_format` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="...", bearer_token="...")
        >>> job = client.export_owl("efo", owl_format="TURTLE")
        >>> job_id = job["job"]["id"]
        >>> # Poll job status and download when complete
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        valid_formats = {"OBO", "RDFXML", "OWLXML", "OWLFUNC", "N3", "TURTLE", "JSONLD", "MOS"}
        if owl_format not in valid_formats:
            raise ValueError(f"owl_format must be one of {valid_formats}")

        endpoint = f"/api/ontologies/{ontology_id}/export"
        params = {
            "owlFormat": owl_format,
            "withJobDetails": str(with_job_details).lower(),
        }

        logger.debug("Exporting ontology %r in format %r (async)", ontology_id, owl_format)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_owl_sync(
            self,
            ontology_id: str,
            owl_format: str = "RDFXML",
            tag_name: Optional[str] = None,
    ) -> str:
        """
        Export an ontology in OWL/RDF format (synchronous).

        Returns the exported content directly without creating a background job.
        Suitable for smaller ontologies or when immediate response is needed.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        owl_format : str, default "RDFXML"
            Export format. Options: "OBO", "RDFXML", "OWLXML", "OWLFUNC", "N3",
            "TURTLE", "JSONLD", "MOS".
        tag_name : str, optional
            Optional snapshot tag name to export.

        Returns
        -------
        str
            Exported content or file reference.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `owl_format` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        valid_formats = {"OBO", "RDFXML", "OWLXML", "OWLFUNC", "N3", "TURTLE", "JSONLD", "MOS"}
        if owl_format not in valid_formats:
            raise ValueError(f"owl_format must be one of {valid_formats}")

        endpoint = f"/api/ontologies/{ontology_id}/export/sync"
        params = {"owlFormat": owl_format}
        if tag_name:
            params["tagName"] = tag_name

        logger.debug("Exporting ontology %r in format %r (sync)", ontology_id, owl_format)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def export_skos(
            self,
            ontology_id: str,
            skos_format: str = "RDFXML",
            skos_xl: bool = False,
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in SKOS format (asynchronous).

        Converts the ontology to SKOS (Simple Knowledge Organization System) or SKOS-XL
        format and exports it in the specified RDF serialization.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        skos_format : str, default "RDFXML"
            RDF serialization format. Options: "RDFXML", "N3", "NTRIPLES", "TURTLE",
            "RDFXML_ABBREV".
        skos_xl : bool, default False
            Use SKOS-XL (extended label) format instead of simple SKOS.
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `skos_format` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="...", bearer_token="...")
        >>> job = client.export_skos("efo", skos_format="TURTLE", skos_xl=True)
        >>> job_id = job["job"]["id"]
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        valid_formats = {"RDFXML", "N3", "NTRIPLES", "TURTLE", "RDFXML_ABBREV"}
        if skos_format not in valid_formats:
            raise ValueError(f"skos_format must be one of {valid_formats}")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsSkos"
        params = {
            "skosFormat": skos_format,
            "skosXL": str(skos_xl).lower(),
            "withJobDetails": str(with_job_details).lower(),
        }

        logger.debug("Exporting ontology %r as SKOS%s in format %r",
                     ontology_id, "-XL" if skos_xl else "", skos_format)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_qtt(
            self,
            ontology_id: str,
            metadata_columns: list[str],
            qtt_template_export: bool = False,
            generate_ids: bool = False,
            number_of_generated_ids: int = 0,
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in QTT (Quick Term Template) flat file format.

        QTT is a tabular CSV-based format used for bulk ontology operations and
        spreadsheet-based maintenance.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        metadata_columns : list of str
            Array of metadata column IRIs to include in the export.
            Call `get_qtt_column_options()` to retrieve available column options.
        qtt_template_export : bool, default False
            Export an empty template instead of actual data.
        generate_ids : bool, default False
            Generate new IDs for entities.
        number_of_generated_ids : int, default 0
            Number of IDs to generate (if generate_ids is True).
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `metadata_columns` is not a list.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="...", bearer_token="...")
        >>> columns = ["http://www.w3.org/2000/01/rdf-schema#label",
        ...            "http://www.w3.org/2004/02/skos/core#definition"]
        >>> job = client.export_qtt("efo", metadata_columns=columns)
        >>> job_id = job["job"]["id"]
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not isinstance(metadata_columns, list):
            raise ValueError("metadata_columns must be a list")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsQttFlatFile"
        params = {
            "qttTemplateExport": str(qtt_template_export).lower(),
            "generateIds": str(generate_ids).lower(),
            "numberOfGeneratedIds": number_of_generated_ids,
            "withJobDetails": str(with_job_details).lower(),
        }

        logger.debug("Exporting ontology %r as QTT with %d columns",
                     ontology_id, len(metadata_columns))
        resp = self.request("POST", endpoint, params=params, json=metadata_columns)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_termite_aug(
            self,
            ontology_id: str,
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in Termite AUG format.

        Termite AUG format is used with SciBite Termite Named Entity Recognition (NER) engine.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsTermiteAugFile"
        params = {"withJobDetails": str(with_job_details).lower()}

        logger.debug("Exporting ontology %r as Termite AUG", ontology_id)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_termite_vocab(
            self,
            ontology_id: str,
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in Termite VOCAB format.

        Termite VOCAB format is used for text mining and NER applications with SciBite Termite.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsTermiteVocabFile"
        params = {"withJobDetails": str(with_job_details).lower()}

        logger.debug("Exporting ontology %r as Termite VOCAB", ontology_id)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_termite_skos(
            self,
            ontology_id: str,
            include_properties: Optional[list[str]] = None,
            skos_format: str = "TURTLE",
            termite_skos_format: str = "TERMITE_SKOS",
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology in Termite SKOS format.

        Advanced Termite integration with SKOS-based vocabularies, supporting custom
        properties and multiple SKOS variants.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        include_properties : list of str, optional
            Custom property IRIs to include in Termite metadata.
        skos_format : str, default "TURTLE"
            RDF serialization format. Options: "RDFXML", "N3", "NTRIPLES", "TURTLE",
            "RDFXML_ABBREV".
        termite_skos_format : str, default "TERMITE_SKOS"
            Termite SKOS variant. Options: "TERMITE_SKOS_AUG", "TERMITE_SKOS".
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or format options are invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        valid_skos_formats = {"RDFXML", "N3", "NTRIPLES", "TURTLE", "RDFXML_ABBREV"}
        if skos_format not in valid_skos_formats:
            raise ValueError(f"skos_format must be one of {valid_skos_formats}")

        valid_termite_formats = {"TERMITE_SKOS_AUG", "TERMITE_SKOS"}
        if termite_skos_format not in valid_termite_formats:
            raise ValueError(f"termite_skos_format must be one of {valid_termite_formats}")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsTermiteSkos"
        params: dict[str, Union[str, list[str]]] = {
            "skosFormat": skos_format,
            "termiteSkosFormat": termite_skos_format,
            "withJobDetails": str(with_job_details).lower(),
        }

        if include_properties:
            params["includePropertiesForTermite"] = include_properties

        logger.debug("Exporting ontology %r as Termite SKOS (%s)", ontology_id, termite_skos_format)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def export_vocab_flat_file(
            self,
            ontology_id: str,
            file_type: str = "CSV",
            delimiter: str = ",",
            with_job_details: bool = False,
    ) -> dict:
        """
        Export an ontology as a flat CSV or TSV file.

        Exports in a simple spreadsheet-compatible format for quick analysis and sharing.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to export.
        file_type : str, default "CSV"
            File type. Options: "CSV", "TSV", "NOT_SUPPLIED".
        delimiter : str, default ","
            Custom delimiter (e.g., use "\\t" for tab-separated values).
        with_job_details : bool, default False
            Return detailed job information in response.

        Returns
        -------
        dict
            JobSubmitResponse with job details including job ID for monitoring.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `file_type` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> # Export as CSV
        >>> client.export_vocab_flat_file("efo", file_type="CSV")
        >>> # Export as TSV
        >>> client.export_vocab_flat_file("efo", file_type="TSV", delimiter="\\t")
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        valid_types = {"CSV", "TSV", "NOT_SUPPLIED"}
        if file_type not in valid_types:
            raise ValueError(f"file_type must be one of {valid_types}")

        endpoint = f"/api/ontologies/{ontology_id}/exportAsVocabFlatFile"
        params = {
            "fileType": file_type,
            "delimiter": delimiter,
            "withJobDetails": str(with_job_details).lower(),
        }

        logger.debug("Exporting ontology %r as %s flat file", ontology_id, file_type)
        resp = self.request("GET", endpoint, params=params)
        if with_job_details:
            return self.json_or_raise(resp)
        else:
            resp.raise_for_status()
            return {"message": resp.text}

    def download_file(self, file_name: str) -> bytes:
        """
        Download an exported ontology file.

        After an asynchronous export job completes, use this method to retrieve
        the generated file.

        Parameters
        ----------
        file_name : str
            Name of the file to download (typically from job completion response).

        Returns
        -------
        bytes
            Binary file content.

        Raises
        ------
        ValueError
            If `file_name` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="...", bearer_token="...")
        >>> job = client.export_owl("efo", owl_format="TURTLE")
        >>> # Wait for job to complete...
        >>> file_name = job["job"]["completionMessage"]  # or from job status check
        >>> content = client.download_file(file_name)
        >>> with open("efo.ttl", "wb") as f:
        ...     f.write(content)
        """
        if not file_name:
            raise ValueError("file_name is required")

        endpoint = f"/api/ontologies/download/{file_name}"

        logger.debug("Downloading file %r", file_name)
        resp = self.request("GET", endpoint)
        resp.raise_for_status()
        return resp.content

    # ── Other Methods ──────────────────────────────────────────

    def get_loaded_bool(self, ontology_id: str) -> bool:
        """
        Check whether an ontology is loaded.

        Args:
            ontology_id: The ontology identifier.

        Returns:
            True if loaded, False if not.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")

        endpoint = f"/api/ontologies/{ontology_id}/loaded"
        resp = self.request("GET", endpoint)

        text = resp.text.strip().lower()
        if text == "true":
            return True
        elif text == "false":
            return False
        else:
            raise ValueError(f"Unexpected response from {endpoint}: {resp.text!r}")

    def get_classes_by_exact_label(self, ontology_id: str, label: str) -> list[dict]:
        """
        Retrieve ontology classes with an exact label match.

        Parameters
        ----------
        ontology_id : str
            Ontology ID to search within (e.g., "efo").
        label : str
            The exact label to match.

        Returns
        -------
        list[dict]
            List of matching entities (often length 0 or 1).

        Raises
        ------
        ValueError
            If `ontology_id` or `label` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not label:
            raise ValueError("label is required")

        endpoint = f"/api/search/{ontology_id}/exactLabel"
        params = {"label": label}

        logger.debug("Searching for exact label %r in ontology %r", label, ontology_id)
        resp = self.request("GET", endpoint, params=params)
        return self.json_or_raise(resp)

    def get_classes_by_primary_id(
            self,
            class_primary_id: str,
            ontology_list: Optional[Union[str, list[str]]] = None,
    ) -> dict:
        """
        Get classes whose *primary ID* exactly matches the supplied string.

        Parameters
        ----------
        class_primary_id : str
            The primary ID to get (required).
        ontology_list : str or list of str, optional
            One or more ontology IDs to filter on.

        Returns
        -------
        dict
            JSON response from the endpoint.

        Raises
        ------
        ValueError
            If `class_primary_id` is empty.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not class_primary_id:
            raise ValueError("class_primary_id is required")

        endpoint = "/api/search/primaryId"
        params: dict[str, Union[str, list[str]]] = {"q": class_primary_id}

        if ontology_list:
            # Accept a single ontology or a list; requests will encode lists as repeated params
            params["ontology"] = ([ontology_list] if isinstance(ontology_list, str) else ontology_list)

        logger.debug("Primary ID search %r (ontologies=%r)", class_primary_id, params.get("ontology"))
        resp = self.request("GET", endpoint, params=params)  # will raise if raise_for_status=True
        return self.json_or_raise(resp)

    def get_class_details(
            self,
            ontology_id: str,
            class_primary_id: str,
    ) -> Optional[dict]:
        """
        Retrieve detailed information about a specific class by its primary ID.

        This method uses the ``/api/search/{ontology}/primaryIds`` endpoint which
        returns richer information than ``get_classes_by_primary_id``, including
        property values, object property values, annotation properties, and
        relational properties.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to search within (e.g., "MONDO", "DOID", "EFO").
        class_primary_id : str
            The full IRI/URI of the class (e.g., "http://purl.obolibrary.org/obo/MONDO_0005015").
            Use the ``primaryId`` field from search results, not short IDs or internal hashes.

        Returns
        -------
        dict or None
            A dictionary containing detailed class information if found, with keys including:
                - ``id``: Internal CENtree hash ID (for use in edit operations)
                - ``primaryId``: The full IRI of the class
                - ``primaryLabel``: The main label/name
                - ``synonyms``: List of synonyms
                - ``textualDefinitions``: List of definitions
                - ``superClasses``: Parent classes
                - ``shortFormIDs``: Short-form identifiers (CURIEs)
                - ``entityType``: Type of entity
                - ``propertyValues``: List of annotation property values (includes tags)
                - ``objectPropertyValues``: List of object property values (relationships)
                - ``annotationProperties``: Dict of annotation properties
                - ``relationalProperties``: Dict of relational properties
                - ``partOf``, ``derivesFrom``, ``developsFrom``: Relationship lists
                - ``equivalences``, ``mappings``: Equivalence and mapping information

            Returns None if the class is not found.

        Raises
        ------
        ValueError
            If ``ontology_id`` or ``class_primary_id`` is empty.
        requests.HTTPError
            If the HTTP request fails.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="https://centree.example.com", bearer_token="...")
        >>> details = client.get_class_details("MONDO", "http://purl.obolibrary.org/obo/MONDO_0005015")
        >>> if details:
        ...     print(details["primaryLabel"])
        ...     print(details["synonyms"])
        ...     # Access property values with tags for edit operations
        ...     for pv in details.get("propertyValues", []):
        ...         print(pv["iri"], pv["value"], pv.get("tags", []))
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not class_primary_id:
            raise ValueError("class_primary_id is required")

        endpoint = f"/api/search/{ontology_id}/primaryIds"

        logger.debug(
            "Fetching class details for %r in ontology %r",
            class_primary_id, ontology_id
        )
        resp = self.request("POST", endpoint, json=[class_primary_id])
        results = self.json_or_raise(resp)

        # Response is a dict keyed by primary ID
        if not results or class_primary_id not in results:
            logger.debug("Class %r not found in ontology %r", class_primary_id, ontology_id)
            return None

        return results[class_primary_id]

    def get_classes_details(
            self,
            ontology_id: str,
            class_primary_ids: list[str],
    ) -> dict[str, dict]:
        """
        Retrieve detailed information about multiple classes by their primary IDs.

        This method uses the ``/api/search/{ontology}/primaryIds`` endpoint which
        returns richer information than ``get_classes_by_primary_id``, including
        property values, object property values, annotation properties, and
        relational properties.

        Parameters
        ----------
        ontology_id : str
            The ontology ID to search within (e.g., "MONDO", "DOID", "EFO").
        class_primary_ids : list[str]
            List of full IRIs/URIs of the classes to retrieve.

        Returns
        -------
        dict[str, dict]
            A dictionary keyed by primary ID, where each value contains detailed
            class information. Classes not found will not be present in the result.
            See :meth:`get_class_details` for the structure of each class dict.

        Raises
        ------
        ValueError
            If ``ontology_id`` is empty or ``class_primary_ids`` is empty.
        requests.HTTPError
            If the HTTP request fails.

        Examples
        --------
        >>> client = CENtreeReaderClient(base_url="https://centree.example.com", bearer_token="...")
        >>> ids = [
        ...     "http://purl.obolibrary.org/obo/MONDO_0005015",
        ...     "http://purl.obolibrary.org/obo/MONDO_0005148"
        ... ]
        >>> results = client.get_classes_details("MONDO", ids)
        >>> for primary_id, details in results.items():
        ...     print(primary_id, details["primaryLabel"])
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not class_primary_ids:
            raise ValueError("class_primary_ids is required and must not be empty")

        endpoint = f"/api/search/{ontology_id}/primaryIds"

        logger.debug(
            "Fetching details for %d class(es) in ontology %r",
            len(class_primary_ids), ontology_id
        )
        resp = self.request("POST", endpoint, json=class_primary_ids)
        return self.json_or_raise(resp)

    def get_root_entities(
            self,
            ontology_id: str,
            entity_type: str = "classes",
            from_: int = 0,
            size: int = 10,
            transaction_id: Optional[str] = None,
            childcount: bool = False,
            full_response: bool = False,
    ) -> Union[list[dict], dict]:
        """
        Retrieve root entities of a given type in an ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology ID (e.g., "efo").
        entity_type : {"classes","properties","instances"}, default "classes"
            Entity type to fetch roots for.
        from_ : int, default 0
            Pagination offset.
        size : int, default 10
            Number of results to return.
        transaction_id : str, optional
            If provided, include uncommitted changes from this transaction.
        childcount : bool, default False
            Whether to include child-count information in results.
        full_response : bool, default False
            If True, return the full JSON response (with pagination metadata);
            otherwise return a list of entity dicts.

        Returns
        -------
        list[dict] | dict
            Root entity dicts (default) or full JSON if `full_response=True`.

        Raises
        ------
        ValueError
            If `ontology_id` is empty or `entity_type` is invalid.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        allowed = {"classes", "properties", "instances"}
        if entity_type not in allowed:
            raise ValueError(f"entity_type must be one of {sorted(allowed)}")

        endpoint = f"/api/tree/{ontology_id}/{entity_type}/roots"
        params = {
            "from": from_,
            "size": size,
            "childcount": str(childcount).lower(),
        }
        if transaction_id:
            params["transactionId"] = transaction_id

        logger.debug("Fetching root %s from ontology %r (from=%d, size=%d, childcount=%s)",
                     entity_type, ontology_id, from_, size, childcount)

        resp = self.request("GET", endpoint, params=params)
        data = self.json_or_raise(resp)

        if full_response:
            return data
        return [el.get("value", el) for el in data.get("elements", [])]

    def get_paths_from_root(
            self,
            ontology_id: str,
            class_primary_id: str,
            children_relation_max_size: int = 50,
            maximum_number_of_paths: int = 100,
            *,
            as_: str = "ids",  # 'ids' | 'labels' | 'objects'
            include_fake_root: bool = False,
    ) -> list[list[Union[str, dict]]]:
        """
        Return paths from the synthetic 'THING' root to a class.

        Parameters
        ----------
        ontology_id : str
            Ontology ID (e.g., "efo").
        class_primary_id : str
            Primary ID of the target class (e.g., "http://www.ebi.ac.uk/efo/EFO_0000001" or "EFO_0000001").
        children_relation_max_size : int, default 50
            Limit breadth when exploring children.
        maximum_number_of_paths : int, default 100
            Maximum number of distinct paths to return.
        as_ : {'ids','labels','objects'}, default 'ids'
            Shape of each path segment:
              - 'ids'    → use `value.primaryID`.
              - 'labels' → use `value.primaryLabel`.
              - 'objects'→ return the raw `value` dicts.
        include_fake_root : bool, default False
            If False, drop the synthetic 'THING' node from returned paths.

        Returns
        -------
        list[list[Union[str, dict]]]
            A list of root→…→target paths. Each path is a list in the order encountered.

        Raises
        ------
        ValueError
            If required parameters are missing.
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        if not ontology_id:
            raise ValueError("ontology_id is required")
        if not class_primary_id:
            raise ValueError("class_primary_id is required")
        if as_ not in {"ids", "labels", "objects"}:
            raise ValueError("as_ must be one of {'ids','labels','objects'}")

        endpoint = f"/api/ontologies/{ontology_id}/classes/paths-from-root"
        params = {
            "classPrimaryId": class_primary_id,
            "childrenRelationMaxSize": int(children_relation_max_size),
            "maximumNumberOfPaths": int(maximum_number_of_paths),
        }

        resp = self.request("GET", endpoint, params=params)
        tree = self.json_or_raise(resp)  # shape: {"value": {...}, "leaves": [...]}

        def pick(v: Optional[dict], as_: str) -> Optional[Union[str, dict]]:
            if not isinstance(v, dict):  # value may be None
                return None
            if as_ == "objects":
                return v
            if as_ == "labels":
                return v.get("primaryLabel")
            # default 'ids'
            return v.get("primaryID")

        paths: list[list[Union[str, dict]]] = []

        def dfs(node: dict, acc: list[Union[str, dict]]) -> None:
            # Some server versions can return nodes with value=None
            value = node.get("value")
            leaves = node.get("leaves") or []

            added = False
            picked = pick(value, as_)
            if picked is not None:
                acc.append(picked)
                added = True

            if not leaves:
                # Only record a path if we actually added a node
                if added:
                    paths.append(acc.copy())
            else:
                for child in leaves:
                    if isinstance(child, dict):
                        dfs(child, acc)

            if added:
                acc.pop()

        dfs(tree, [])

        if not include_fake_root and paths:
            # drop the first hop (synthetic 'THING') if it’s present
            def drop_fake(p: list[Union[str, dict]]) -> list[Union[str, dict]]:
                return p[1:] if len(p) and (
                            p[0] == "THING" or (isinstance(p[0], dict) and p[0].get("primaryID") == "THING")) else p

            paths = [drop_fake(p) for p in paths]

        return paths
