"""
editor.py

CENtreeEditorClient: A client for performing ontology editing operations via the CENtree API.

This includes capabilities for creating new ontology classes, instances, and properties,
as well as managing transaction IDs for change tracking.

Classes:
- CENtreeEditorClient: Supports editing operations on ontologies (create, update, transaction management).
"""

import logging
from logging import NullHandler
from typing import Optional, Any, Union
import time
import requests
from .base import CENtreeClient
from .reader import CENtreeReaderClient
from .exceptions import OntologyAlreadyExistsError, OntologyNotFoundError
from .helpers import ontology_exists

# ── Logging config ──────────────────────────────────────────
logger = logging.getLogger("scibite_toolkit.centree_clients.editor")
logger.addHandler(NullHandler())
# ────────────────────────────────────────────────────────────


class CENtreeEditorClient(CENtreeClient):
    """Client for editing ontologies in CENtree.

    Extends the base `CENtreeClient` with capabilities for managing ontology
    transactions, including caching transaction IDs locally for each ontology.

    Note:
        - Transaction ID caching is in-memory only and not persisted.
    """
    def __init__(self, base_url: Optional[str] = None, bearer_token: Optional[str] = None, verify: bool = True, allow_insecure: bool = False):
        super().__init__(base_url=base_url, bearer_token=bearer_token, verify=verify, allow_insecure=allow_insecure)
        self._cached_transaction_ids: dict[str, str] = {}
        logger.debug("Initialized CENtreeEditorClient base_url=%s verify=%s", self.base_url, verify)

    # ---------------------------------- #
    # -------- CACHE MANAGEMENT -------- #
    # ---------------------------------- #

    def get_cached_transaction_id(self, ontology_id: str) -> Optional[str]:
        """Retrieves the cached transaction ID for a given ontology.

        Args:
            ontology_id (str): The ontology identifier.

        Returns:
            Optional[str]: The cached transaction ID, or None if no transaction is cached.

        Raises:
            ValueError: If `ontology_id` is an empty string.

        Logs:
            DEBUG: Whether the transaction cache was a HIT or MISS.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string")
        tx = self._cached_transaction_ids.get(ontology_id)
        logger.debug("Transaction cache %s for ontology=%s", "HIT" if tx else "MISS", ontology_id)
        return tx

    def set_cached_transaction_id(self, ontology_id: str, transaction_id: str):
        """Sets or overwrites the cached transaction ID for a given ontology.

        Args:
            ontology_id (str): The ontology identifier.
            transaction_id (str): The transaction ID to cache.

        Returns:
            Optional[str]: The previous transaction ID, if one existed; otherwise None.

        Raises:
            ValueError: If `ontology_id` or `transaction_id` is an empty string.

        Logs:
            DEBUG: Whether a previous transaction ID existed.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string")
        if not transaction_id:
            raise ValueError("transaction_id must be a non-empty string")
        prev = self._cached_transaction_ids.get(ontology_id)
        self._cached_transaction_ids[ontology_id] = transaction_id
        logger.debug("Cached transaction_id for ontology=%s (had_prev=%s)", ontology_id, prev is not None)
        return prev

    def clear_cached_transaction_id(self, ontology_id: str):
        """Removes the cached transaction ID for a given ontology.

        Args:
            ontology_id (str): The ontology identifier.

        Returns:
            bool: True if a transaction ID was removed; False if none existed.

        Raises:
            ValueError: If `ontology_id` is an empty string.

        Logs:
            DEBUG: Whether a cached ID existed and was cleared.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string")
        removed = self._cached_transaction_ids.pop(ontology_id, None) is not None
        logger.debug("Cleared transaction_id for ontology=%s (existed=%s)", ontology_id, removed)
        return removed

    def clear_all_cached_transaction_ids(self) -> int:
        """Clears all cached transaction IDs across all ontologies.

        Returns:
            int: The number of transaction IDs that were removed.

        Logs:
            DEBUG: Total number of cleared entries.
        """
        n = len(self._cached_transaction_ids)
        self._cached_transaction_ids.clear()
        logger.debug("Cleared all transaction_ids (count=%d)", n)
        return n

    # -------------------------------- #
    # -------- INPUT / OUTPUT -------- #
    # -------------------------------- #

    def upload_file(self, file_path: str) -> dict:
        """
        Upload a source file to CENtree for ontology creation.

        Args:
            file_path (str): Path to the local ontology file to be uploaded.

        Returns:
            dict: The parsed JSON response from the server.

        Raises:
            ValueError: If base_url is not set.
            HTTPError: If the upload fails.
        """
        if not self.base_url:
            raise ValueError("Base URL is not set.")

        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = self.request(
                "POST",
                "/api/ontology/uploadFile",
                files=files
            )

        if response.status_code != 201:
            response.raise_for_status()

        return response.json()

    # ------------------------------------ #
    # -------- ONTOLOGY LIFECYCLE -------- #
    # ------------------------------------ #

    def create_ontology_new(
            self,
            payload: dict,
            wait_until_loaded: bool = False,
            timeout: int = 60
    ) -> Union[dict, str]:
        """
        Create a new ontology in CENtree using the provided payload.

        Args:
            payload (dict): Dictionary representing ontology metadata and configuration.
            wait_until_loaded (bool): Whether to poll until the ontology is fully loaded.
            timeout (int): Max time in seconds to wait for loading confirmation.

        Returns:
            Union[dict, str]: JSON response from the server if successful, or response
                              text if not in JSON. This is only returned if the
                              ontology is created and, if waiting, loads successfully.

        Raises:
            OntologyAlreadyExistsError: If the ontology already exists and is loaded.
            requests.HTTPError: If the initial creation request fails (e.g., non-201 status).
            TimeoutError: If `wait_until_loaded` is True and the ontology
                is not searchable within the `timeout` period.
        """
        if not self.base_url:
            raise ValueError("Base URL is not set.")

        ontology_id = payload.get("ontologyId")
        if not ontology_id:
            raise ValueError("Payload must include 'ontologyId'.")

        existence_url = f"/api/ontologies/{ontology_id}/loaded"
        existence_resp = self.request("GET", existence_url)

        if existence_resp.status_code == 200 and existence_resp.text.strip().lower() == "true":
            logger.info("Ontology '%s' already exists and is loaded. Skipping creation.", ontology_id)
            raise OntologyAlreadyExistsError(f"Ontology '{ontology_id}' already exists and is loaded.")

        logger.info("Creating ontology '%s'…", ontology_id)
        create_resp = self.request("POST", "/api/ontology", json=payload)

        if create_resp.status_code != 201:
            logger.error("Ontology creation failed: %s %s", create_resp.status_code, create_resp.text)
            create_resp.raise_for_status()

        logger.info("Ontology creation request accepted.")

        if wait_until_loaded:
            logger.info("Waiting for ontology '%s' to be fully available (indexed)...", ontology_id)
            start = time.time()
            while time.time() - start < timeout:
                try:
                    check_resp = self.request(
                        "GET",
                        f"/api/search/{ontology_id}/exactLabel",
                        params={"label": "Thing"},
                        suppress_warning=True
                    )
                    if check_resp.status_code == 200:
                        logger.info("Ontology '%s' is now fully available and searchable.", ontology_id)
                        break
                except requests.HTTPError as e:
                    if e.response.status_code == 400:
                        pass  # Search index not ready yet — expected
                    else:
                        logger.warning("Unexpected error during polling: %s", e)
                time.sleep(2)
            else:
                logger.warning("Timeout waiting for ontology '%s' to be indexed in search.", ontology_id)
                raise TimeoutError(
                    f"Timeout waiting for ontology '{ontology_id}' to be indexed after {timeout}s."
                )

        content_type = create_resp.headers.get("Content-Type", "")
        if "application/json" in content_type:
            logger.info("Ontology creation successful with JSON response.")
            return create_resp.json()
        else:
            logger.info("Ontology creation returned non-JSON response.")
            return create_resp.text

    def merge_ontology(
            self,
            ontology_id: str,
            file_url: str,
            *,
            new_version: str = "latestLoadedVersion",
            file_merging_strategy: str = "AS_FILE",
            wait_until_loaded: bool = False,
            timeout: int = 300,
            poll_interval: int = 5
    ) -> Union[dict, str]:
        """
        Merge a new file into an existing ontology and optionally wait for completion.

        Args:
            ontology_id (str): The ontology ID to merge into.
            file_url (str): The URL of the uploaded file to merge.
            new_version (str): The new version identifier.
            file_merging_strategy (str): One of AS_FILE, AS_EDITS_MERGE, AS_EDITS_REPLACE,
                                         AS_EDITS_MERGE_SUGGEST, AS_EDITS_REPLACE_SUGGEST.
            wait_until_loaded (bool): If True, poll until the merge job completes.
            timeout (int): Max total wait time in seconds.
            poll_interval (int): How often to poll job status in seconds.

        Returns:
            dict: If not waiting, the initial job creation response.
                  If waiting, the final job status JSON from the completed job.

        Raises:
            requests.HTTPError: If the initial merge request fails (e.g., non-202 status).
            TimeoutError: If `wait_until_loaded` is True and the merge job
                does not complete within the `timeout` period.
        """
        params = {
            "fileUrl": file_url,
            "newVersion": new_version,
            "fileMergingStrategy": file_merging_strategy,
            "withJobDetails": "true"
        }

        logger.info("Merging file into ontology '%s' with strategy '%s'…", ontology_id, file_merging_strategy)
        response = self.request("POST", f"/api/ontology/{ontology_id}/merge", params=params)

        if response.status_code != 202:
            logger.error("Ontology merge failed: %s %s", response.status_code, response.text)
            response.raise_for_status()

        json_response = response.json()
        job_id = json_response.get("job", {}).get("id")
        logger.info("Ontology merge job accepted: %s", job_id)

        if wait_until_loaded and job_id:
            logger.info("Polling job status for job ID '%s'…", job_id)
            start = time.time()
            while time.time() - start < timeout:
                try:
                    job_status_resp = self.request("GET", f"/api/jobs/{job_id}")
                    if job_status_resp.status_code == 200:
                        job_data = job_status_resp.json()
                        status = job_data.get("status")
                        logger.info("Job status: %s — %s", status, job_data.get("progress", "").strip())

                        if status in ("Succeeded", "Failed", "Cancelled", "Interrupted"):
                            logger.info("Job %s completed with status: %s", job_id, status)
                            return job_data
                    else:
                        logger.warning("Unexpected job status response: %s", job_status_resp.status_code)

                except requests.RequestException as e:
                    logger.warning("Exception while polling job: %s", str(e))

                time.sleep(poll_interval)

            logger.warning("Timeout exceeded while waiting for merge job '%s' to finish", job_id)
            raise TimeoutError(
                f"Timeout waiting for merge job {job_id} to complete after {timeout}s."
            )

        # If not waiting, just return the initial response
        return json_response

    def build_application_ontology(
            self,
            payload: dict,
            wait_until_loaded: bool = False,
            timeout: int = 60
    ) -> dict:
        """
        Build an application ontology in CENtree.

        Args:
            payload (dict): Ontology creation payload. Must include 'ontologyId' and 'sourceOntologySet'.
            wait_until_loaded (bool): If True, poll until the ontology is indexed in search.
            timeout (int): Maximum time in seconds to wait for indexing confirmation.

        Returns:
            dict: JSON response from the server.

        Raises:
            HTTPError: If the request fails.
        """
        if not self.base_url:
            raise ValueError("Base URL is not set.")

        ontology_id = payload.get("ontologyId")
        if not ontology_id:
            raise ValueError("Payload must include 'ontologyId'.")

        logger.info("Initiating build of application ontology '%s' …", ontology_id)
        response = self.request("POST", "/api/ontology/build", json=payload)

        logger.debug("Build request status: %s, body: %s", response.status_code, response.text)

        try:
            build_response = response.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            build_response = {"message": response.text.strip()}

        if wait_until_loaded:
            logger.info("Waiting for ontology '%s' to be fully available (indexed)...", ontology_id)
            start = time.time()
            while time.time() - start < timeout:
                try:
                    check_resp = self.request(
                        "GET",
                        f"/api/search/{ontology_id}/exactLabel",
                        params={"label": "Thing"},
                        suppress_warning=True
                    )
                    if check_resp.status_code == 200:
                        logger.info("Ontology '%s' is now fully available and searchable.", ontology_id)
                        break
                except requests.HTTPError as e:
                    if e.response.status_code == 400:
                        continue  # Index not ready yet — expected
                    else:
                        logger.warning("Unexpected error during polling: %s", e)
                time.sleep(2)
            else:
                logger.warning("Timeout waiting for ontology '%s' to be indexed in search.", ontology_id)

        return build_response

    def cleanup_default_root_class(
            self,
            ontology_id: str,
            reader: Optional[CENtreeReaderClient] = None
    ) -> bool:
        """
        Removes the default root class ('Thing') from the given ontology if it exists.

        Args:
            ontology_id (str): Ontology from which to remove the root class.
            reader (Optional[CENtreeReaderClient]): Reader client to look up entity ID.

        Returns:
            bool: True if the class was found and deleted, False otherwise.

        Raises:
            OntologyNotFoundError: If the ontology is not found.
            Other exceptions from delete_entity() or commit_transaction().
        """
        if reader is None:
            reader = CENtreeReaderClient(
                base_url=self.base_url,
                bearer_token=self.bearer_token,
                verify=self.verify
            )

        try:
            results = reader.get_classes_by_exact_label(ontology_id, "Thing")
        except OntologyNotFoundError as e:
            logger.error("Ontology '%s' not found: %s", ontology_id, e)
            raise
        except Exception as e:
            logger.error("Unexpected error while retrieving class 'Thing': %s", e)
            raise

        if not results:
            logger.info("No default root class 'Thing' found in ontology '%s'.", ontology_id)
            return False

        entity_id = results[0].get("id")
        if not entity_id:
            logger.warning("Entity for 'Thing' has no ID — skipping delete.")
            return False

        logger.info("Deleting default root class 'Thing' with ID %s", entity_id)

        try:
            self.delete_entity(ontology_id=ontology_id, entity_type="classes", entity_id=entity_id)
        except Exception as e:
            logger.error("Failed to delete 'Thing': %s", e)
            raise

        logger.info("Transaction updated: Deleted 'Thing' class from ontology '%s'", ontology_id)

        try:
            self.commit_transaction(ontology_id)
        except Exception as e:
            logger.error("Failed to commit transaction: %s", e)
            raise

        logger.info("Committed deletion of 'Thing'.")

        return True

    def delete_ontology(
            self,
            ontology_id: str,
            *,
            delete_metadata_entry: bool = True,
            delete_stored_files: bool = True,
            wait_until_deleted: bool = False,
            timeout: int = 60
    ) -> dict:
        """
        Delete an ontology from CENtree.

        Args:
            ontology_id (str): The ID of the ontology to delete.
            delete_metadata_entry (bool): Whether to delete the metadata entry.
            delete_stored_files (bool): Whether to delete uploaded source files.
            wait_until_deleted (bool): If True, poll until the ontology is fully removed.
            timeout (int): Maximum time in seconds to wait for confirmation.

        Returns:
            dict: A confirmation message on successful deletion.

        Raises:
            TimeoutError: If `wait_until_deleted` is True and the ontology
                is not confirmed deleted within the `timeout` period.
        """
        if not ontology_exists(self, ontology_id):
            logger.info("Ontology '%s' does not exist. Skipping deletion.", ontology_id)
            return {"message": f"Ontology '{ontology_id}' does not exist."}

        endpoint = f"/api/ontology/{ontology_id}"
        params = {
            "deleteMetadataEntry": str(delete_metadata_entry).lower(),
            "deleteStoredFiles": str(delete_stored_files).lower(),
        }

        logger.info("Deleting ontology '%s'…", ontology_id)
        resp = self.request("DELETE", endpoint, params=params)

        if resp.status_code not in (200, 202):
            logger.error("Ontology deletion failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()

        logger.info("Deletion request accepted for ontology '%s'.", ontology_id)

        if wait_until_deleted:
            logger.info("Waiting for ontology '%s' to be fully deleted …", ontology_id)
            start = time.time()
            while time.time() - start < timeout:
                if not ontology_exists(self, ontology_id):
                    logger.info("Ontology '%s' confirmed deleted.", ontology_id)
                    return {"message": f"Ontology '{ontology_id}' deleted."}
                time.sleep(2)
            else:
                logger.warning("Timeout waiting for ontology '%s' to be fully deleted.", ontology_id)
                # Raise an exception to signal failure
                raise TimeoutError(
                    f"Timeout waiting for ontology '{ontology_id}' to be fully deleted after {timeout}s."
                )
        else:
            return {"message": f"Deletion of '{ontology_id}' initiated"}

    # ---------------------------------- #
    # -------- CLASS OPERATIONS -------- #
    # ---------------------------------- #

    def create_class(
            self,
            ontology_id: str,
            primary_label: str,
            *,
            super_entity: Optional[str] = None,
            primary_id: Optional[str] = None,
            short_ids: Optional[list[str]] = None,
            description: Optional[str] = None,
            transaction_id: Optional[str] = None,
            annotated: bool = False
    ) -> dict[str, Any]:
        """Convenience method for creating a new class entity."""
        return self.create_entity(
            ontology_id=ontology_id,
            entity_type="classes",
            primary_label=primary_label,
            super_entity=super_entity,
            primary_id=primary_id,
            short_ids=short_ids,
            description=description,
            transaction_id=transaction_id,
            annotated=annotated
        )

    def suggest_class(
            self,
            ontology_id: str,
            primary_label: str,
            *,
            super_entity: Optional[str] = None,
            primary_id: Optional[str] = None,
            short_ids: Optional[list[str]] = None,
            description: Optional[str] = None,
            annotated: bool = False,
            clear_transaction: bool = True
    ) -> dict[str, Any]:
        """Create a class and immediately submit the transaction as a suggestion."""
        result = self.create_class(
            ontology_id=ontology_id,
            primary_label=primary_label,
            super_entity=super_entity,
            primary_id=primary_id,
            short_ids=short_ids,
            description=description,
            annotated=annotated
        )
        tx_id = result.get("transactionId")
        return self.suggest_transaction(ontology_id, transaction_id=tx_id, clear_transaction=clear_transaction)

    def commit_class(
            self,
            ontology_id: str,
            primary_label: str,
            *,
            super_entity: Optional[str] = None,
            primary_id: Optional[str] = None,
            short_ids: Optional[list[str]] = None,
            description: Optional[str] = None,
            annotated: bool = False,
            create_reverse_mappings: bool = False,
            validation_checksum: Optional[str] = None,
            clear_transaction: bool = True
    ) -> dict[str, Any]:
        """Create a class and immediately commit the transaction."""
        result = self.create_class(
            ontology_id=ontology_id,
            primary_label=primary_label,
            super_entity=super_entity,
            primary_id=primary_id,
            short_ids=short_ids,
            description=description,
            annotated=annotated
        )
        tx_id = result.get("transactionId")
        return self.commit_transaction(
            ontology_id=ontology_id,
            transaction_id=tx_id,
            create_reverse_mappings=create_reverse_mappings,
            validation_checksum=validation_checksum,
            clear_transaction=clear_transaction
        )

    def bulk_add_classes(self, ontology_id: str, classes: list[dict]) -> dict:
        """
        Add multiple classes to a specified ontology in bulk.

        Args:
            ontology_id (str): The ontology ID to which classes will be added.
            classes (list[dict]): A list of class payloads. Each payload must contain at least 'label'.

        Returns:
            dict: {
                "transactionId": str,
                "createdClasses": list[dict]
            }
        """
        if not self.base_url:
            raise ValueError("Base URL is not set.")

        url = f"{self.base_url}/api/ontologies/{ontology_id}/classes/bulk"
        logger.info("Adding %d class(es) to ontology '%s' …", len(classes), ontology_id)

        try:
            response = self.request("PUT", url, json=classes)
            response.raise_for_status()
        except Exception as e:
            logger.error("Bulk class creation failed: %s", e)
            raise

        data = response.json()
        transaction_id = data[0].get("transactionId") if data else None

        if transaction_id:
            self.set_cached_transaction_id(ontology_id, transaction_id)
            logger.info("Transaction ID '%s' cached for ontology '%s'.", transaction_id, ontology_id)
        else:
            logger.warning("No transaction ID found in response — nothing cached.")

        return {
            "transactionId": transaction_id,
            "createdClasses": data
        }

    # ----------------------------------- #
    # -------- ENTITY OPERATIONS -------- #
    # ----------------------------------- #

    def create_entity(
            self,
            ontology_id: str,
            entity_type: str,  # "classes", "instances", or "properties"
            primary_label: str,
            *,
            super_entity: Optional[str] = None,
            primary_id: Optional[str] = None,
            short_ids: Optional[list[str]] = None,
            description: Optional[str] = None,
            transaction_id: Optional[str] = None,
            property_type: Optional[str] = None,
            annotated: bool = False
    ) -> dict[str, Any]:
        """Create a new entity (class, instance, or property) in the ontology.

            Args:
                ontology_id (str): The ontology ID to add the entity to.
                entity_type (str): One of ``"classes"``, ``"instances"``, or ``"properties"``.
                primary_label (str): The label for the new entity.
                super_entity (Optional[str]): The ``primaryId`` of the parent entity.
                primary_id (Optional[str]): Full URI to use as ``primaryId`` for the new entity.
                short_ids (Optional[list[str]]): Short-form IDs (CURIEs) to associate.
                description (Optional[str]): Description or definition for the entity.
                transaction_id (Optional[str]): Transaction ID to use. If omitted, uses the cached
                    transaction ID for this ontology (if present).
                property_type (Optional[str]): Required when ``entity_type == "properties"``; type of the property.
                annotated (bool): If ``True``, request annotated metadata in the response.

            Returns:
                dict[str, Any]: A dictionary with at least:
                    - ``"transactionId"`` (str or None): Transaction ID returned by the server (and cached if present).
                    - ``"createdEntity"`` (dict): The created entity object if provided by the API, otherwise the raw response.

            Raises:
                ValueError: If required parameters are missing, or if ``entity_type`` is invalid,
                    or if ``property_type`` is missing for a property entity,
                    or if ``short_ids`` are missing when ``primary_id`` is provided.
                Exception: If the HTTP request fails.

            Notes:
                - When the response includes a ``transactionId``, it is cached via
                  :meth:`set_cached_transaction_id`.
                - Logging:
                  * INFO when initiating entity creation and when caching a transaction ID.
                  * WARNING if no transaction ID is present in the response.
                  * ERROR if the request fails.
            """
        if not all([ontology_id, entity_type, primary_label]):
            raise ValueError("ontology_id, entity_type, and primary_label are required.")

        allowed = {"classes", "instances", "properties"}
        if entity_type not in allowed:
            raise ValueError(f"entity_type must be one of {sorted(allowed)}")

        if entity_type == "properties" and not property_type:
            raise ValueError("property_type is required when entity_type == 'properties'.")

        if primary_id and not short_ids:
            raise ValueError("short_ids must be provided when primary_id is specified.")

        # Use cached transaction if one is not explicitly supplied.
        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)

        path = f"/api/ontologies/{ontology_id}/{entity_type}/new"
        params = {"annotated": str(annotated).lower()}
        payload: dict[str, Any] = {
            "primaryLabel": primary_label,
        }

        if transaction_id:
            payload["transactionId"] = transaction_id
        if super_entity:
            payload["superEntity"] = super_entity
        if primary_id:
            payload["primaryId"] = primary_id
        if short_ids:
            payload["shortIds"] = short_ids
        if description:
            payload["description"] = description
        if entity_type == "properties":
            payload["propertyType"] = property_type  # validated above

        logger.debug(
            "Creating new %s '%s' under '%s' in ontology '%s' (annotated=%s)",
            entity_type, primary_label, super_entity, ontology_id, annotated
        )

        try:
            response = self.request("PUT", path, json=payload, params=params)
            response.raise_for_status()
        except Exception as e:
            logger.error("Entity creation failed: %s", e)
            raise

        data = response.json()
        tx = data.get("transactionId")

        if tx:
            self.set_cached_transaction_id(ontology_id, tx)
            logger.debug("Transaction ID %s cached for ontology %s", tx, ontology_id)
        else:
            logger.warning("No transaction ID found in response; nothing cached.")

        return {
            "transactionId": tx,
            "createdEntity": data.get("createdEntity", data),
        }

    def edit_entity(
            self,
            ontology_id: str,
            entity_type: str,
            entity_id: str,
            *,
            new_property_value: Optional[dict] = None,
            old_property_value: Optional[dict] = None,
            transaction_id: Optional[str] = None,
            as_primary_label: bool = False,
            annotated: bool = False,
            message: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Edit a property on a class, instance, or property in the ontology.

        Args:
            ontology_id (str): Ontology ID.
            entity_type (str): One of "classes", "instances", or "properties".
            entity_id (str): The full IRI of the entity being edited.
            new_property_value (dict, optional): New property value to apply.
                To delete a property, set this to None. The dict should contain:
                - ``iri`` (str, required): The property IRI (e.g., "http://www.w3.org/2004/02/skos/core#altLabel").
                - ``value`` (str, required): The property value.
                - ``tags`` (list[dict], optional): List of tag objects for language tags or other metadata.
                  Each tag should have: ``type``, ``value``, ``isLiteral``, ``iri``.
                - ``primaryId`` (str, optional): Primary ID if applicable.
            old_property_value (dict, optional): Old value to replace (None if adding a new property).
                **Important**: When replacing or deleting a property that has tags (e.g., language tags),
                you must include the complete ``tags`` array in ``old_property_value`` to match
                the existing property exactly. Example for a property with a language tag::

                    {
                        "iri": "http://www.w3.org/2004/02/skos/core#altLabel",
                        "value": "precision and recall",
                        "tags": [
                            {
                                "type": "LANG",
                                "value": "en",
                                "isLiteral": True,
                                "iri": "http://www.w3.org/XML/1998/namespace/"
                            }
                        ]
                    }

            transaction_id (str, optional): Transaction ID to use; otherwise, uses cached one.
            as_primary_label (bool): Whether this property becomes the primary label.
            annotated (bool): If True, return annotated metadata.
            message (str, optional): Optional message or reason for the edit.

        Returns:
            dict[str, Any]: JSON response from the server, including transactionId.

        Raises:
            ValueError: If required fields are missing or invalid.
            HTTPError: If the request fails.
        """
        if not all([ontology_id, entity_type, entity_id]):
            raise ValueError("ontology_id, entity_type, and entity_id are required.")

        if entity_type not in {"classes", "instances", "properties"}:
            raise ValueError("entity_type must be one of 'classes', 'instances', or 'properties'.")

        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)

        path = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/editEntity"
        params = {"annotated": str(annotated).lower()}

        payload: dict[str, Any] = {
            "asPrimaryLabel": as_primary_label,
        }

        # Include newPropertyValue explicitly (None means delete the property)
        payload["newPropertyValue"] = new_property_value

        if old_property_value is not None:
            payload["oldPropertyValue"] = old_property_value
        if transaction_id:
            payload["transactionId"] = transaction_id
        if message:
            payload["message"] = message

        logger.debug(
            "Editing %s entity '%s' in ontology '%s' (annotated=%s)",
            entity_type, entity_id, ontology_id, annotated
        )

        try:
            response = self.request("POST", path, json=payload, params=params)
            response.raise_for_status()
        except Exception as e:
            logger.error("Entity edit failed: %s", e)
            raise

        data = response.json()
        tx = data.get("transactionId")

        if tx:
            self.set_cached_transaction_id(ontology_id, tx)
            logger.debug("Transaction ID %s cached for ontology %s", tx, ontology_id)
        else:
            logger.warning("No transaction ID found in response; nothing cached.")

        return data

    def obsolete_entity(
            self,
            ontology_id: str,
            entity_type: str,  # "classes", "instances", or "properties"
            entity_id: str,
            *,
            transaction_id: Optional[str] = None,
            message: Optional[str] = None,
            annotated: bool = False,
    ) -> dict[str, Any]:
        """Obsolete an existing entity (class, instance, or property) in the ontology.

        Args:
            ontology_id (str): The ontology ID containing the entity.
            entity_type (str): One of ``"classes"``, ``"instances"``, or ``"properties"``.
            entity_id (str): The identifier of the entity to obsolete (typically its ``primaryId``).
            transaction_id (Optional[str]): Transaction ID to use. If omitted, uses the cached
                transaction ID for this ontology (if present).
            message (Optional[str]): Message or reason for obsoleting the entity.
            annotated (bool): If ``True``, request annotated metadata in the response.

        Returns:
            dict[str, Any]: A dictionary with at least:
                - ``"transactionId"`` (str or None): Transaction ID returned by the server (and cached if present).
                - ``"obsoletedEntity"`` (dict): The obsoleted entity object if provided by the API, otherwise the raw response.

        Raises:
            ValueError: If required parameters are missing, or if ``entity_type`` is invalid.
            Exception: If the HTTP request fails.

        Notes:
            - When the response includes a ``transactionId``, it is cached via
              :meth:`set_cached_transaction_id`.
            - Logging:
              * INFO when initiating the obsoletion and when caching a transaction ID.
              * WARNING if no transaction ID is present in the response.
              * ERROR if the request fails.
        """
        if not all([ontology_id, entity_type, entity_id]):
            raise ValueError("ontology_id, entity_type, and entity_id are required.")

        allowed = {"classes", "instances", "properties"}
        if entity_type not in allowed:
            raise ValueError(f"entity_type must be one of {sorted(allowed)}")

        # Use cached transaction if one is not explicitly supplied.
        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)

        path = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/obsoleteEntity"
        params = {"annotated": str(annotated).lower()}

        # Build payload only if we have something to send
        payload: dict[str, Any] = {}
        if message:
            payload["message"] = message
        if transaction_id:
            payload["transactionId"] = transaction_id

        logger.debug(
            "Obsoleting %s '%s' in ontology '%s' (annotated=%s)",
            entity_type, entity_id, ontology_id, annotated
        )

        try:
            response = self.request("POST", path, json=(payload or {}), params=params)
            response.raise_for_status()  # API returns 201 on success
        except Exception as e:
            logger.error("Obsolete entity failed: %s", e)
            raise

        data = response.json()
        tx = data.get("transactionId")

        if tx:
            self.set_cached_transaction_id(ontology_id, tx)
            logger.debug("Transaction ID %s cached for ontology %s", tx, ontology_id)
        else:
            logger.warning("No transaction ID found in response; nothing cached.")

        return {
            "transactionId": tx,
            "obsoletedEntity": data.get("obsoletedEntity", data),
        }

    def delete_entity(
            self,
            ontology_id: str,
            entity_type: str,
            entity_id: str,
            transaction_id: Optional[str] = None,
            annotated: bool = False
    ) -> dict:
        """
        Delete an entity (class, instance, or property) in an ontology.

        If no transaction ID is provided and no cached one exists, a new transaction will be created and cached.

        Args:
            ontology_id (str): The ontology ID.
            entity_type (str): The type of the entity ('classes', 'instances', or 'properties').
            entity_id (str): The internal CENtree ID of the entity to delete.
            transaction_id (str, optional): A transaction ID to use.
            annotated (bool): Whether to mark the edit as annotated.

        Returns:
            dict: Response from the API including transaction and confirmation.

        Raises:
            ValueError: If the entity_type is invalid.
            HTTPError: If the API call fails.
        """
        if entity_type not in {"classes", "instances", "properties"}:
            raise ValueError("entity_type must be one of: 'classes', 'instances', or 'properties'")
        if not ontology_id:
            raise ValueError("ontology_id is required.")
        if not entity_id:
            raise ValueError("entity_id is required.")

        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)
        endpoint = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/deleteEntity"
        params = {"annotated": str(annotated).lower()}
        if transaction_id:
            params["transactionId"] = transaction_id

        logger.info(
            "Requesting deletion of %s '%s' from ontology '%s' with params %s",
            entity_type, entity_id, ontology_id, params
        )

        try:
            response = self.request("POST", endpoint, json={}, params=params)
            response.raise_for_status()
        except Exception as e:
            logger.error("Entity deletion failed: %s", e)
            raise

        data = response.json()
        new_tid = data.get("transactionId")
        if new_tid:
            self.set_cached_transaction_id(ontology_id, new_tid)

        logger.info("Successfully submitted deletion for entity '%s'.", entity_id)
        return data

    # ---------------------------------------- #
    # -------- TRANSACTION MANAGEMENT -------- #
    # ---------------------------------------- #

    def suggest_transaction(
            self,
            ontology_id: str,
            transaction_id: Optional[str] = None,
            clear_transaction: bool = True,
            message: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Submit a transaction as a suggestion for review.

        Args:
            ontology_id (str): The ontology ID.
            transaction_id (str, optional): Transaction ID to submit. If not provided, uses cached one.
            clear_transaction (bool): Whether to clear the cached transaction ID after submission. Defaults to True.
            message (str, optional): Optional message to include with the suggestion.

        Returns:
            dict: JSON response from the server.

        Raises:
            ValueError: If no transaction ID is provided or cached.
            HTTPError: If the API request fails.
        """
        if not self.base_url:
            raise ValueError("Base URL is not set.")
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)
        if not transaction_id:
            raise ValueError(f"No transaction ID provided or cached for ontology '{ontology_id}'.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/transactions/{transaction_id}/suggest"
        logger.debug("Submitting suggestion for transaction '%s' in ontology '%s'…", transaction_id, ontology_id)

        payload = {"message": message} if message else None

        try:
            response = self.request("POST", endpoint, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to suggest transaction: %s", e)
            raise

        logger.debug("✓ Transaction '%s' successfully suggested.", transaction_id)

        if clear_transaction:
            self.clear_cached_transaction_id(ontology_id)

        return response.json()

    def commit_transaction(
            self,
            ontology_id: str,
            transaction_id: Optional[str] = None,
            create_reverse_mappings: bool = False,
            validation_checksum: Optional[str] = None,
            clear_transaction: bool = True
    ) -> dict[str, Any]:
        """Commit a transaction for the given ontology.

        Args:
            ontology_id (str): The ontology ID.
            transaction_id (str, optional): The transaction ID to commit. If not provided, uses the cached ID.
            create_reverse_mappings (bool): Whether to automatically create reverse mappings during commit.
            validation_checksum (str, optional): A checksum to validate the transaction state before commit.
            clear_transaction (bool): Whether to clear the cached transaction ID after commit. Defaults to True.

        Returns:
            dict[str, Any]: The response returned by the commit endpoint.

        Raises:
            ValueError: If `ontology_id` is empty or no transaction ID is provided or cached.
            HTTPError: If the commit request fails.

        Notes:
            - If `clear_transaction` is True (default), the transaction will be removed from the in-memory cache after a successful commit.
            - Logging:
                * INFO when committing and when commit is successful.
                * ERROR if the commit fails.
        """
        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)
        if not transaction_id:
            raise ValueError(f"No transaction ID provided or cached for ontology '{ontology_id}'.")
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/transactions/{transaction_id}/commit"
        payload = {"createReverseMappings": create_reverse_mappings}
        if validation_checksum:
            payload["validationChecksum"] = validation_checksum

        logger.info("Committing transaction '%s' for ontology '%s'…", transaction_id, ontology_id)

        try:
            response = self.request("POST", endpoint, json=payload)
            response.raise_for_status()
        except Exception as e:
            logger.error("Failed to commit transaction '%s': %s", transaction_id, e)
            raise

        logger.info("✓ Transaction '%s' committed successfully.", transaction_id)

        if clear_transaction:
            self.clear_cached_transaction_id(ontology_id)

        return response.json()

    def delete_transaction(
            self,
            ontology_id: str,
            transaction_id: Optional[str] = None,
            clear_transaction: bool = True
    ) -> bool:
        """
        Delete a transaction from the ontology.

        Args:
            ontology_id (str): The ontology ID.
            transaction_id (str, optional): The transaction ID to delete. If not provided, uses cached ID.
            clear_transaction (bool): Whether to clear the cached transaction ID after deletion. Defaults to True.

        Returns:
            bool: True if deletion was confirmed by the server, False otherwise.

        Raises:
            ValueError: If no transaction ID is provided or cached.
            HTTPError: If the request fails.
        """
        transaction_id = transaction_id or self.get_cached_transaction_id(ontology_id)
        if not transaction_id:
            raise ValueError(f"No transaction ID provided or cached for ontology '{ontology_id}'.")

        endpoint = f"/api/ontologies/{ontology_id}/transactions/{transaction_id}"

        logger.info("Deleting transaction '%s' from ontology '%s'…", transaction_id, ontology_id)

        try:
            response = self.request("DELETE", endpoint)
            response.raise_for_status()
            response_text = response.text.strip()
            if response.status_code == 200 and response_text == "Successfully discarded local edits":
                logger.info("✓ Transaction '%s' deleted successfully.", transaction_id)
                if clear_transaction:
                    self.clear_cached_transaction_id(ontology_id)
                return True
            else:
                logger.warning(
                    "Unexpected response when deleting transaction: status=%s, text=%r",
                    response.status_code, response_text
                )
                return False
        except Exception as e:
            logger.error("Failed to delete transaction '%s': %s", transaction_id, e)
            raise

    def get_uncommitted_transactions(
            self,
            ontology_id: str,
            user_login: Optional[str] = None,
            from_: int = 0,
            size: int = 100,
            sort: str = "asc",
            stale_transactions_included: bool = True,
            exclude_suggestions: bool = True
    ) -> dict[str, Any]:
        """
        Retrieve uncommitted transactions for a given ontology and user.

        Args:
            ontology_id (str): The ontology ID to query.
            user_login (str, optional): User login to query transactions for.
                If not provided, the authenticated user's login is used.
            from_ (int): Pagination start index (default: 0).
            size (int): Number of transactions to retrieve (default: 100).
            sort (str): 'asc' or 'desc' based on transaction date (default: 'asc').
            stale_transactions_included (bool): Whether to include stale transactions (default: True).
            exclude_suggestions (bool): Whether to exclude suggested transactions (default: True).

        Returns:
            dict[str, Any]: A dictionary containing total, from, and elements (transactions).

        Raises:
            HTTPError: If the request fails.
            ValueError: If ontology_id is not provided or invalid.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be provided.")

        user_login = user_login or self.get_username()
        endpoint = f"/api/ontologies/{ontology_id}/transactions/{user_login}/uncommitted"

        params = {
            "from": from_,
            "size": size,
            "sort": sort,
            "staleTransactionsIncluded": str(stale_transactions_included).lower(),
            "excludeSuggestions": str(exclude_suggestions).lower(),
        }

        logger.info(
            "Fetching uncommitted transactions for ontology='%s', user='%s', from=%d, size=%d, sort=%s",
            ontology_id, user_login, from_, size, sort
        )

        try:
            response = self.request("GET", endpoint, params=params)
            response.raise_for_status()
            logger.info("✓ Uncommitted transactions retrieved successfully.")
            return response.json()
        except Exception as e:
            logger.error("Failed to retrieve uncommitted transactions: %s", e)
            raise

    # -------------------------------- #
    # -------- EDIT HISTORY ---------- #
    # -------------------------------- #

    def get_edits(
            self,
            ontology_id: str,
            from_date: Optional[str] = None,
            page: int = 0,
            size: int = 100
    ) -> dict[str, Any]:
        """
        Get all edits for an ontology.

        Returns paginated edit history for the entire ontology, including
        classes, properties, and instances.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        from_date : str, optional
            Filter edits from this date (ISO 8601 format, e.g., '2020-01-01T00:00:00Z').
            Without this parameter, only recent edits may be returned.
        page : int, optional
            Page number (0-indexed). Default is 0.
        size : int, optional
            Number of results per page. Default is 100.

        Returns
        -------
        dict
            Paginated response containing:
            - content: List of edit records
            - totalElements: Total number of edits
            - totalPages: Total number of pages
            - number: Current page number

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.

        Examples
        --------
        >>> edits = client.get_edits("my_ontology", from_date="2024-01-01T00:00:00Z")
        >>> for edit in edits["content"]:
        ...     print(edit["id"], edit["ontologyEditActionSet"])
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits"
        params = {"page": page, "size": size}
        if from_date:
            params["fromDate"] = from_date

        logger.debug("Fetching edits for ontology='%s', page=%d, size=%d", ontology_id, page, size)

        response = self.request("GET", endpoint, params=params)
        response.raise_for_status()

        logger.debug("✓ Retrieved edits for ontology '%s'.", ontology_id)
        return response.json()

    def get_committed_edits(
            self,
            ontology_id: str,
            from_date: Optional[str] = None,
            page: int = 0,
            size: int = 100
    ) -> dict[str, Any]:
        """
        Get committed edits for an ontology.

        Returns only committed (not pending) edits, useful for audit trails.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        from_date : str, optional
            Filter edits from this date (ISO 8601 format).
        page : int, optional
            Page number (0-indexed). Default is 0.
        size : int, optional
            Number of results per page. Default is 100.

        Returns
        -------
        dict
            Paginated response containing committed edit records.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/committed"
        params = {"page": page, "size": size}
        if from_date:
            params["fromDate"] = from_date

        logger.debug("Fetching committed edits for ontology='%s'", ontology_id)

        response = self.request("GET", endpoint, params=params)
        response.raise_for_status()

        logger.debug("✓ Retrieved committed edits for ontology '%s'.", ontology_id)
        return response.json()

    def get_entity_edits(
            self,
            ontology_id: str,
            entity_type: str,
            entity_id: str
    ) -> dict[str, Any]:
        """
        Get edit history for a specific entity.

        Returns the complete edit history for a class, property, or instance.
        The entity_id must be the internal hash ID, not the short form ID.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        entity_type : str
            One of: 'classes', 'properties', 'instances'.
        entity_id : str
            The internal hash ID of the entity (e.g., '5313c7b729e9...').

        Returns
        -------
        dict
            Edit history containing:
            - editsHistory: List of committed edits (most recent first)
            - currentEdits: List of pending/uncommitted edits
            - newClass: Present if this is a newly created entity

        Raises
        ------
        ValueError
            If any required parameter is empty or entity_type is invalid.
        requests.HTTPError
            If the API request fails.

        Examples
        --------
        >>> history = client.get_entity_edits("my_ontology", "classes", "5313c7b729e9...")
        >>> for edit in history["editsHistory"]:
        ...     print(f"Edit {edit['id']}: {edit['ontologyEditActionSet']}")
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not entity_id:
            raise ValueError("entity_id must be a non-empty string.")
        if entity_type not in ("classes", "properties", "instances"):
            raise ValueError("entity_type must be one of: 'classes', 'properties', 'instances'.")

        endpoint = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/edits"

        logger.debug("Fetching edit history for %s/%s in ontology='%s'", entity_type, entity_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        logger.debug("✓ Retrieved edit history for entity '%s'.", entity_id)
        return response.json()

    def get_class_edits(self, ontology_id: str, class_id: str) -> dict[str, Any]:
        """
        Get edit history for a specific class.

        Convenience method that calls get_entity_edits with entity_type='classes'.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        class_id : str
            The internal hash ID of the class.

        Returns
        -------
        dict
            Edit history for the class.

        See Also
        --------
        get_entity_edits : Generic method for any entity type.
        """
        return self.get_entity_edits(ontology_id, "classes", class_id)

    def get_edit(self, ontology_id: str, edit_id: int) -> dict[str, Any]:
        """
        Get details for a specific edit.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        edit_id : int
            The unique edit identifier.

        Returns
        -------
        dict
            The edit record containing full details of the change.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails or edit not found.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/{edit_id}"

        logger.debug("Fetching edit %d for ontology='%s'", edit_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        logger.debug("✓ Retrieved edit %d.", edit_id)
        return response.json()

    def get_transaction_edits(self, transaction_id: str) -> list[dict[str, Any]]:
        """
        Get all edits belonging to a specific transaction.

        Parameters
        ----------
        transaction_id : str
            The transaction UUID.

        Returns
        -------
        list[dict]
            List of edit records in the transaction.

        Raises
        ------
        ValueError
            If transaction_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not transaction_id:
            raise ValueError("transaction_id must be a non-empty string.")

        endpoint = f"/api/ontologies/edits/transactions/{transaction_id}"

        logger.debug("Fetching edits for transaction='%s'", transaction_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        logger.debug("✓ Retrieved edits for transaction '%s'.", transaction_id)
        return response.json()

    # -------------------------------- #
    # -------- EDIT COMPARISON ------- #
    # -------------------------------- #

    def compare_edit_with_previous(self, ontology_id: str, edit_id: int) -> dict[str, Any]:
        """
        Compare an edit with the previous version of the entity.

        Shows what changed in this edit compared to the previous state.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        edit_id : int
            The edit identifier to compare.

        Returns
        -------
        dict
            Comparison result showing differences.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/{edit_id}/compareWithPrevious"

        logger.debug("Comparing edit %d with previous for ontology='%s'", edit_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        return response.json()

    def compare_edit_with_current(self, ontology_id: str, edit_id: int) -> dict[str, Any]:
        """
        Compare an edit with the current state of the entity.

        Useful for seeing how much has changed since a particular edit.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        edit_id : int
            The edit identifier to compare.

        Returns
        -------
        dict
            Comparison result showing differences from current state.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/{edit_id}/compareWithCurrent"

        logger.debug("Comparing edit %d with current for ontology='%s'", edit_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        return response.json()

    def compare_edit_with_original(self, ontology_id: str, edit_id: int) -> dict[str, Any]:
        """
        Compare an edit with the original state of the entity.

        Shows all changes since the entity was created.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        edit_id : int
            The edit identifier to compare.

        Returns
        -------
        dict
            Comparison result showing differences from original state.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/{edit_id}/compareWithOriginal"

        logger.debug("Comparing edit %d with original for ontology='%s'", edit_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        return response.json()

    def compare_edit_with_previous_commit(self, ontology_id: str, edit_id: int) -> dict[str, Any]:
        """
        Compare an edit with the previous committed version.

        Useful when reviewing uncommitted changes.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        edit_id : int
            The edit identifier to compare.

        Returns
        -------
        dict
            Comparison result showing differences from last commit.

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/{edit_id}/compareWithPreviousCommit"

        logger.debug("Comparing edit %d with previous commit for ontology='%s'", edit_id, ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        return response.json()

    # -------------------------------- #
    # -------- UNDO / RESTORE -------- #
    # -------------------------------- #

    def undo_transaction(
            self,
            ontology_id: str,
            transaction_id: str,
            commit: bool = True,
            annotated: bool = False
    ) -> list[dict[str, Any]]:
        """
        Undo an entire transaction.

        Reverts all changes made in the specified transaction.

        .. warning::

            Transaction undo only works if ALL entities in the transaction are
            at their most recent version. If any entity has been modified since,
            the undo will fail with a versioning conflict.

            For entity creation transactions, the API records the undo but the
            entities are NOT actually removed. Use ``undo_entity_creation()``
            instead to delete newly created entities.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        transaction_id : str
            The transaction UUID to undo.
        commit : bool, optional
            Whether to immediately commit the undo. Default is True.
        annotated : bool, optional
            Include edit annotations in response. Default is False.

        Returns
        -------
        list[dict]
            List of edit records created by the undo operation.

        Raises
        ------
        ValueError
            If ontology_id or transaction_id is empty.
        requests.HTTPError
            If the API request fails (e.g., versioning conflict).

        See Also
        --------
        restore_entity_version : Restore a specific entity to any previous state.
        undo_entity_creation : Delete a newly created entity.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not transaction_id:
            raise ValueError("transaction_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/transactions/{transaction_id}/undo"
        params = {
            "commit": str(commit).lower(),
            "annotated": str(annotated).lower()
        }

        logger.info("Undoing transaction '%s' for ontology='%s' (commit=%s)", transaction_id, ontology_id, commit)

        response = self.request("POST", endpoint, params=params)
        response.raise_for_status()

        logger.info("✓ Transaction '%s' undone successfully.", transaction_id)
        return response.json()

    def restore_entity_version(
            self,
            ontology_id: str,
            entity_type: str,
            entity_id: str,
            edit_id: int
    ) -> dict[str, Any]:
        """
        Restore an entity to a previous version.

        This is the recommended way to revert an entity to any previous state.
        Unlike transaction undo, this can jump to any editId in the entity's
        history, regardless of how many changes have been made since.

        The restore creates and commits a new transaction automatically.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        entity_type : str
            One of: 'classes', 'properties', 'instances'.
        entity_id : str
            The internal hash ID of the entity.
        edit_id : int
            The edit ID to restore to (from edit history).

        Returns
        -------
        dict
            The edit record for the restore operation.

        Raises
        ------
        ValueError
            If any required parameter is empty or entity_type is invalid.
        requests.HTTPError
            If the API request fails.

        Examples
        --------
        >>> # Get edit history to find the editId to restore to
        >>> history = client.get_class_edits("my_ontology", "abc123...")
        >>> target_edit_id = history["editsHistory"][2]["id"]  # e.g., third-oldest edit
        >>> client.restore_entity_version("my_ontology", "classes", "abc123...", target_edit_id)

        See Also
        --------
        get_entity_edits : Get edit history to find the edit_id.
        undo_transaction : Undo an entire transaction (more restrictive).
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not entity_id:
            raise ValueError("entity_id must be a non-empty string.")
        if entity_type not in ("classes", "properties", "instances"):
            raise ValueError("entity_type must be one of: 'classes', 'properties', 'instances'.")

        endpoint = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/edits/{edit_id}/restore"

        logger.info(
            "Restoring %s/%s to edit %d in ontology='%s'",
            entity_type, entity_id, edit_id, ontology_id
        )

        response = self.request("POST", endpoint)
        response.raise_for_status()

        logger.info("✓ Entity restored to edit %d.", edit_id)
        return response.json()

    def restore_class_version(
            self,
            ontology_id: str,
            class_id: str,
            edit_id: int
    ) -> dict[str, Any]:
        """
        Restore a class to a previous version.

        Convenience method that calls restore_entity_version with entity_type='classes'.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        class_id : str
            The internal hash ID of the class.
        edit_id : int
            The edit ID to restore to.

        Returns
        -------
        dict
            The edit record for the restore operation.

        See Also
        --------
        restore_entity_version : Generic method for any entity type.
        """
        return self.restore_entity_version(ontology_id, "classes", class_id, edit_id)

    def undo_entity_creation(
            self,
            ontology_id: str,
            entity_type: str,
            entity_id: str
    ) -> dict[str, Any]:
        """
        Delete a newly created entity.

        This is the correct endpoint to fully delete a newly created entity.
        Unlike transaction undo, this actually removes the entity from the ontology.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        entity_type : str
            One of: 'classes', 'properties', 'instances'.
        entity_id : str
            The internal hash ID of the entity.

        Returns
        -------
        dict
            The edit record confirming the deletion (includes UNDO_COMMIT,
            DELETE, and COMMIT actions).

        Raises
        ------
        ValueError
            If any required parameter is empty or entity_type is invalid.
        requests.HTTPError
            If the API request fails.

        See Also
        --------
        undo_class_creation : Convenience method for classes.
        delete_entity : Delete an entity (adds to transaction, needs commit).
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not entity_id:
            raise ValueError("entity_id must be a non-empty string.")
        if entity_type not in ("classes", "properties", "instances"):
            raise ValueError("entity_type must be one of: 'classes', 'properties', 'instances'.")

        endpoint = f"/api/ontologies/{ontology_id}/{entity_type}/{entity_id}/undoCreationOfEntity"

        logger.info("Undoing creation of %s/%s in ontology='%s'", entity_type, entity_id, ontology_id)

        response = self.request("POST", endpoint)
        response.raise_for_status()

        logger.info("✓ Entity creation undone (entity deleted).")
        return response.json()

    def undo_class_creation(self, ontology_id: str, class_id: str) -> dict[str, Any]:
        """
        Delete a newly created class.

        Convenience method that calls undo_entity_creation with entity_type='classes'.
        This is the correct way to fully remove a class that was created via the API.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        class_id : str
            The internal hash ID of the class.

        Returns
        -------
        dict
            The edit record confirming the deletion.

        See Also
        --------
        undo_entity_creation : Generic method for any entity type.
        """
        return self.undo_entity_creation(ontology_id, "classes", class_id)

    # -------------------------------- #
    # ----- SUGGESTION WORKFLOW ------ #
    # -------------------------------- #

    def reject_suggestion(
            self,
            ontology_id: str,
            transaction_id: str,
            message: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Reject a suggested transaction.

        Only available to users with approval permissions.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        transaction_id : str
            The transaction UUID of the suggestion.
        message : str, optional
            Reason for rejection.

        Returns
        -------
        list[dict]
            List of edit records for the rejected suggestion.

        Raises
        ------
        ValueError
            If ontology_id or transaction_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not transaction_id:
            raise ValueError("transaction_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/transactions/{transaction_id}/reject"
        payload = {"message": message} if message else None

        logger.info("Rejecting suggestion '%s' for ontology='%s'", transaction_id, ontology_id)

        response = self.request("POST", endpoint, json=payload)
        response.raise_for_status()

        logger.info("✓ Suggestion '%s' rejected.", transaction_id)
        return response.json()

    def cancel_suggestion(
            self,
            ontology_id: str,
            transaction_id: str,
            message: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """
        Cancel/discard a pending suggestion.

        Can be done by the original submitter or an approver.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.
        transaction_id : str
            The transaction UUID of the suggestion.
        message : str, optional
            Optional cancellation message.

        Returns
        -------
        list[dict]
            List of edit records for the cancelled suggestion.

        Raises
        ------
        ValueError
            If ontology_id or transaction_id is empty.
        requests.HTTPError
            If the API request fails.
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")
        if not transaction_id:
            raise ValueError("transaction_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/edits/transactions/{transaction_id}/cancel"
        payload = {"message": message} if message else None

        logger.info("Cancelling suggestion '%s' for ontology='%s'", transaction_id, ontology_id)

        response = self.request("POST", endpoint, json=payload)
        response.raise_for_status()

        logger.info("✓ Suggestion '%s' cancelled.", transaction_id)
        return response.json()

    # -------------------------------- #
    # -------- EDIT EXPORT ----------- #
    # -------------------------------- #

    def export_edits_owl(self, ontology_id: str) -> str:
        """
        Export all edits as an OWL file (ZIP).

        Returns a filename that can be downloaded via the download endpoint.
        The OWL export contains the current state of all entities in RDF/XML format.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.

        Returns
        -------
        str
            The filename of the generated ZIP file (use download_file() to retrieve).

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.

        Examples
        --------
        >>> filename = client.export_edits_owl("my_ontology")
        >>> client.download_file(filename, "/path/to/save/edits.zip")
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/exportEdits"

        logger.info("Exporting edits as OWL for ontology='%s'", ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        filename = response.text.strip()
        logger.info("✓ Edits exported to: %s", filename)
        return filename

    def export_edits_json(self, ontology_id: str) -> str:
        """
        Export all edits as a JSON file (ZIP).

        Returns a download path for the generated ZIP file.
        The JSON export contains the full version history of all entities.

        Parameters
        ----------
        ontology_id : str
            The ontology identifier.

        Returns
        -------
        str
            The download path for the ZIP file (use download_file() to retrieve).

        Raises
        ------
        ValueError
            If ontology_id is empty.
        requests.HTTPError
            If the API request fails.

        Examples
        --------
        >>> download_path = client.export_edits_json("my_ontology")
        >>> # download_path is like '/api/ontologies/download/my_ontology-edits-json....zip'
        >>> filename = download_path.split('/')[-1]
        >>> client.download_file(filename, "/path/to/save/edits.zip")
        """
        if not ontology_id:
            raise ValueError("ontology_id must be a non-empty string.")

        endpoint = f"/api/ontologies/{ontology_id}/exportEditsAsJsonFile"

        logger.info("Exporting edits as JSON for ontology='%s'", ontology_id)

        response = self.request("GET", endpoint)
        response.raise_for_status()

        download_path = response.text.strip()
        logger.info("✓ Edits exported to: %s", download_path)
        return download_path
