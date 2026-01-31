# Re-export from shared exceptions module for backwards compatibility
from scibite_toolkit.exceptions import (
    OntologyAlreadyExistsError,
    OntologyNotFoundError,
)

__all__ = [
    "OntologyAlreadyExistsError",
    "OntologyNotFoundError",
]
