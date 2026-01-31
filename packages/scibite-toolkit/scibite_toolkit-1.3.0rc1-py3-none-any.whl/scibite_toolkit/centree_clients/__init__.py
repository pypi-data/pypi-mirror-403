"""
__init__.py
Modular CENtree API clients for interacting with ontology services.

Classes:
- CENtreeClient: Base client for configuration, authentication, and shared utilities.
- CENtreeReaderClient: Query ontologies for classes, properties, instances, and tree structure.
- CENtreeEditorClient: Create and edit ontologies, classes, instances, and properties.
- CENtreeSuggestorClient: (planned) Submit transactions as suggestions for review and approval.
- CENtreeSparqlClient: (planned) Execute SPARQL queries against the CENtree triple store.

All clients share a common logging setup and require a bearer token for authentication.
"""

from .base import CENtreeClient
from .reader import CENtreeReaderClient
from .editor import CENtreeEditorClient
from .forms import CENtreeFormsClient
from .sparql import CENtreeSparqlClient
from .exceptions import OntologyAlreadyExistsError, OntologyNotFoundError

__all__ = [
    "CENtreeClient",
    "CENtreeReaderClient",
    "CENtreeEditorClient",
    "CENtreeFormsClient",
    "CENtreeSparqlClient",
    "OntologyAlreadyExistsError",
    "OntologyNotFoundError"
]
