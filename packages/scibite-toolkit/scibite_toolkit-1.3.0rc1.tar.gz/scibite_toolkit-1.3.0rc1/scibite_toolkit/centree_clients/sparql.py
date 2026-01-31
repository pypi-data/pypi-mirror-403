"""
sparql.py

CENtreeSparqlClient provides SPARQL query functionality for CENtree ontologies.
Supports listing available SPARQL-indexed ontologies and executing SPARQL queries.
"""

import logging
from logging import NullHandler
from .base import CENtreeClient
from typing import Optional, Union, Dict, Any

# ── Logging config ──────────────────────────────────────────
logger = logging.getLogger("scibite_toolkit.centree_clients.sparql")
logger.addHandler(NullHandler())
# ────────────────────────────────────────────────────────────


class CENtreeSparqlClient(CENtreeClient):
    """
    A client class for SPARQL operations on CENtree ontologies.
    Provides methods to list SPARQL-indexed ontologies and execute SPARQL queries.
    """
    def __init__(
        self,
        base_url: Optional[str] = None,
        bearer_token: Optional[str] = None,
        verify: Union[bool, str] = True,
        **kwargs,
    ):
        super().__init__(base_url=base_url, bearer_token=bearer_token, verify=verify, **kwargs)
        logger.debug("Initialized CENtreeSparqlClient base_url=%s", self.base_url)

    def get_sparql_ontologies(self) -> list[dict]:
        """
        Retrieve a list of ontologies that have SPARQL indexes available.

        Returns
        -------
        list[dict]
            List of ontologies with SPARQL indexes. Each dict typically contains
            metadata about the ontology such as ID, name, and indexing status.

        Raises
        ------
        requests.HTTPError
            If the HTTP request is unsuccessful.
        """
        endpoint = "/api/sparql/ontologies"
        logger.debug("Fetching list of SPARQL-indexed ontologies")
        resp = self.get(endpoint)
        return self.json_or_raise(resp)

    def query_sparql(
        self,
        query: str,
        ontology_id: str,
        method: str = "POST",
        format: str = "json",
        **kwargs: Any,
    ) -> Any:
        """
        Execute a SPARQL query against a specified ontology.

        Parameters
        ----------
        query : str
            The SPARQL query string to execute.
        ontology_id : str
            The ID of the ontology to query against. This is passed in the request header.
        method : {"GET", "POST"}, default "POST"
            HTTP method to use for the query. Both GET and POST are supported.
        format : {"json", "xml", "csv", "tsv"}, default "json"
            Output format for query results.

        Returns
        -------
        Any
            The JSON response from the SPARQL endpoint, typically containing query results.

        Raises
        ------
        ValueError
            If `query` or `ontology_id` is empty, or if an invalid method is specified.
        requests.HTTPError
            If the HTTP request is unsuccessful.

        Examples
        --------
        Execute a simple SPARQL query::

            client = CENtreeSparqlClient(
            base_url="https://centree.example.com",
            bearer_token="mytoken"
            )

            query = '''
            SELECT ?subject ?predicate ?object
            WHERE {
            ?subject ?predicate ?object
            }
            LIMIT 10
            '''

            # Get JSON results (default)
            results = client.query_sparql(query, ontology_id="efo")

            # Get XML results
            results = client.query_sparql(query, ontology_id="efo", format="xml")

            # Get TSV results
            results = client.query_sparql(query, ontology_id="efo", format="tsv")
        """
        if not query:
            raise ValueError("query is required")
        if not ontology_id:
            raise ValueError("ontology_id is required")

        method = method.upper()
        if method not in ("GET", "POST"):
            raise ValueError("method must be 'GET' or 'POST'")

        # Map format to Accept header
        format_map = {
            "json": "application/sparql-results+json",
            "xml": "application/sparql-results+xml",
            "csv": "text/csv",
            "tsv": "text/tab-separated-values",
        }

        format = format.lower()
        if format not in format_map:
            raise ValueError(f"format must be one of {list(format_map.keys())}")

        endpoint = "/api/sparql"
        headers = {
            'ontologyId': ontology_id,
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8',
            'Accept': format_map[format]
        }
        logger.debug("Executing SPARQL query via %s for ontology %r", method, ontology_id)
        logger.debug("Query: %s", query[:200] + "..." if len(query) > 200 else query)

        data = {'query': query}

        if method == "POST":
            # For POST, send the query in the request body
            resp = self.post(endpoint, headers=headers, data=data, **kwargs)
        else:
            # For GET, send the query as a URL parameter
            resp = self.get(endpoint, headers=headers, params=data, **kwargs)

            # Return parsed JSON for json format, raw response for others
        if format == "json":
            return self.json_or_raise(resp)
        else:
            return resp.text