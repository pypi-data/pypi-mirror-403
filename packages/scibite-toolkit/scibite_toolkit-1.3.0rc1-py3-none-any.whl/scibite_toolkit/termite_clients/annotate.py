# scibite_toolkit/termite_clients/annotate.py
"""Client for TERMite annotation operations."""

from __future__ import annotations

import io
import json
import logging
import os
from logging import NullHandler
from typing import Any, Optional, Union

from scibite_toolkit.termite_clients.base import TermiteClient
from scibite_toolkit.exceptions import ValidationError, AnnotationError

logger = logging.getLogger("scibite_toolkit.termite_clients.annotate")
logger.addHandler(NullHandler())

# Maximum URL-safe text length for GET requests (conservative limit)
# Most servers support 2KB-8KB URLs, but we use a conservative threshold
_MAX_GET_TEXT_LENGTH = 2000


class TermiteAnnotateClient(TermiteClient):
    """
    Client for TERMite annotation operations.

    Provides methods for annotating text and documents with TERMite,
    including configuration options for controlling annotation behavior.

    This client inherits all authentication and HTTP methods from TermiteClient.

    Examples
    --------
    Annotate text:

    >>> client = TermiteAnnotateClient(
    ...     base_url="https://termite.example.com",
    ...     token_url="https://auth.example.com"
    ... )
    >>> client.set_oauth2("client_id", "client_secret")
    >>> result = client.annotate_text(
    ...     text="COVID-19 is caused by SARS-CoV-2.",
    ...     vocabulary=["INDICATION", "SPECIES"]
    ... )

    Annotate a document:

    >>> result = client.annotate_document(
    ...     file_path="/path/to/document.pdf",
    ...     parser_id="pdf",
    ...     vocabulary=["DRUG"]
    ... )
    """

    # ── Text Annotation ────────────────────────────────────────────
    def annotate_text(
        self,
        text: Union[str, list[str]],
        vocabulary: Optional[Union[str, list[str]]] = None,
        case_match: Optional[bool] = None,
        reject_ambig: Optional[bool] = None,
        boost: Optional[bool] = None,
        subsume: Optional[bool] = None,
        byte_positions: Optional[bool] = None,
        entity_ids: Optional[list[str]] = None,
        ancestors: Optional[list[str]] = None,
        force_post: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Annotate text strings with TERMite.

        For large texts, this method automatically switches from GET to POST
        to avoid URL length limits. You can control this behavior with
        ``force_post``.

        Parameters
        ----------
        text : str or list of str
            Text to annotate. Can be a single string or list of strings.
        vocabulary : str or list of str, optional
            Vocabularies to use (e.g., ``"DRUG"`` or ``["DRUG", "INDICATION"]``).
            If a string, can be comma-separated. If not specified, all
            available vocabularies are used.
        case_match : bool, optional
            If ``True``, enforce case-sensitive matching.
        reject_ambig : bool, optional
            If ``True``, reject ambiguous matches.
        boost : bool, optional
            If ``True``, treat sub-synonyms as full hits.
        subsume : bool, optional
            If ``True``, take the longest entity match when overlapping.
        byte_positions : bool, optional
            If ``True``, include byte positions in results.
        entity_ids : list of str, optional
            Filter to specific entity IDs.
        ancestors : list of str, optional
            Filter to descendants of these taxonomy nodes.
        force_post : bool, optional
            If ``True``, always use POST via multipart upload (useful for
            very large texts). If ``False``, always use GET (may fail for
            large texts). If ``None`` (default), automatically switch to POST
            when text exceeds 2000 characters.

        Returns
        -------
        dict
            Annotation results containing matched entities and their positions.

        Raises
        ------
        ValidationError
            If text is empty or invalid.
        AnnotationError
            If annotation fails.

        Examples
        --------
        >>> result = client.annotate_text("Aspirin treats headaches")
        >>> for entity in result.get("included", []):
        ...     print(entity)

        Annotate multiple texts:

        >>> result = client.annotate_text(
        ...     ["First sentence.", "Second sentence."],
        ...     vocabulary="DRUG,INDICATION"
        ... )

        Force POST for large text:

        >>> result = client.annotate_text(large_text, force_post=True)
        """
        # Validate and normalize text
        if not text:
            raise ValidationError("text is required")

        if isinstance(text, str):
            text_list = [text]
        elif isinstance(text, list):
            if not all(isinstance(t, str) for t in text):
                raise ValidationError("text must be a string or list of strings")
            text_list = text
        else:
            raise ValidationError("text must be a string or list of strings")

        # Normalize vocabulary
        vocab_list = self._normalize_vocabulary(vocabulary)

        # Calculate total text length for auto-POST decision
        total_text_length = sum(len(t) for t in text_list)

        # Determine whether to use POST or GET
        use_post = force_post
        if use_post is None:
            # Auto-detect: use POST for large texts
            use_post = total_text_length > _MAX_GET_TEXT_LENGTH

        if use_post:
            return self._annotate_text_post(
                text_list=text_list,
                vocab_list=vocab_list,
                case_match=case_match,
                reject_ambig=reject_ambig,
                boost=boost,
                subsume=subsume,
                byte_positions=byte_positions,
                entity_ids=entity_ids,
                ancestors=ancestors,
            )
        else:
            return self._annotate_text_get(
                text_list=text_list,
                vocab_list=vocab_list,
                case_match=case_match,
                reject_ambig=reject_ambig,
                boost=boost,
                subsume=subsume,
                byte_positions=byte_positions,
                entity_ids=entity_ids,
                ancestors=ancestors,
            )

    def _annotate_text_get(
        self,
        text_list: list[str],
        vocab_list: Optional[list[str]],
        case_match: Optional[bool],
        reject_ambig: Optional[bool],
        boost: Optional[bool],
        subsume: Optional[bool],
        byte_positions: Optional[bool],
        entity_ids: Optional[list[str]],
        ancestors: Optional[list[str]],
    ) -> dict[str, Any]:
        """Annotate text via GET request (for small texts)."""
        endpoint = "/api/termite/v1/annotate"
        params: dict[str, Any] = {"text": text_list}

        if vocab_list is not None:
            params["vocabulary"] = vocab_list
        if case_match is not None:
            params["caseMatch"] = case_match
        if reject_ambig is not None:
            params["rejectAmbig"] = reject_ambig
        if boost is not None:
            params["boost"] = boost
        if subsume is not None:
            params["subsume"] = subsume
        if byte_positions is not None:
            params["bytePositions"] = byte_positions
        if entity_ids is not None:
            params["entityIds"] = entity_ids
        if ancestors is not None:
            params["ancestors"] = ancestors

        logger.debug("Annotating %d text(s) via GET with params: %s", len(text_list), params)

        resp = self.get(endpoint, params=params)
        result = self.json_or_raise(resp)

        logger.info("Text annotation (GET) successful")
        return result

    def _annotate_text_post(
        self,
        text_list: list[str],
        vocab_list: Optional[list[str]],
        case_match: Optional[bool],
        reject_ambig: Optional[bool],
        boost: Optional[bool],
        subsume: Optional[bool],
        byte_positions: Optional[bool],
        entity_ids: Optional[list[str]],
        ancestors: Optional[list[str]],
    ) -> dict[str, Any]:
        """Annotate text via POST multipart upload (for large texts)."""
        endpoint = "/api/termite/v1/annotate"
        params: dict[str, Any] = {"parserId": "generic"}

        if vocab_list is not None:
            params["vocabulary"] = vocab_list
        if case_match is not None:
            params["caseMatch"] = case_match
        if reject_ambig is not None:
            params["rejectAmbig"] = reject_ambig
        if boost is not None:
            params["boost"] = boost
        if subsume is not None:
            params["subsume"] = subsume
        if byte_positions is not None:
            params["bytePositions"] = byte_positions
        if entity_ids is not None:
            params["entityIds"] = entity_ids
        if ancestors is not None:
            params["ancestors"] = ancestors

        # Combine text list into single content for multipart upload
        combined_text = "\n".join(text_list)
        content = combined_text.encode("utf-8")

        logger.debug(
            "Annotating %d text(s) via POST multipart (total %d bytes)",
            len(text_list), len(content)
        )

        files = {"file": ("text.txt", io.BytesIO(content), "text/plain")}
        resp = self.post(endpoint, params=params, files=files)
        result = self.json_or_raise(resp)

        logger.info("Text annotation (POST) successful")
        return result

    # ── Document Annotation ────────────────────────────────────────
    def annotate_document(
        self,
        file_path: str,
        parser_id: str = "generic",
        vocabulary: Optional[Union[str, list[str]]] = None,
        case_match: Optional[bool] = None,
        reject_ambig: Optional[bool] = None,
        boost: Optional[bool] = None,
        subsume: Optional[bool] = None,
        byte_positions: Optional[bool] = None,
        entity_ids: Optional[list[str]] = None,
        ancestors: Optional[list[str]] = None,
        fields: Optional[list[dict[str, Any]]] = None,
        parser_config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Annotate a document with TERMite.

        Parameters
        ----------
        file_path : str
            Path to the file to annotate (PDF, TXT, XML, etc.).
        parser_id : str, default="generic"
            Parser to use (e.g., ``"pdf"``, ``"txt"``, ``"xml"``, ``"generic"``).
        vocabulary : str or list of str, optional
            Vocabularies to use for annotation.
        case_match : bool, optional
            If ``True``, enforce case-sensitive matching.
        reject_ambig : bool, optional
            If ``True``, reject ambiguous matches.
        boost : bool, optional
            If ``True``, treat sub-synonyms as full hits.
        subsume : bool, optional
            If ``True``, take the longest entity match when overlapping.
        byte_positions : bool, optional
            If ``True``, include byte positions in results.
        entity_ids : list of str, optional
            Filter to specific entity IDs.
        ancestors : list of str, optional
            Filter to descendants of these taxonomy nodes.
        fields : list of dict, optional
            Per-field TERMite configurations. Each dict should contain
            ``"id"`` and ``"termiteConfig"`` keys.
        parser_config : dict, optional
            Parser-specific configuration settings.

        Returns
        -------
        dict
            Annotation results containing matched entities and positions.

        Raises
        ------
        ValidationError
            If file_path is invalid.
        FileNotFoundError
            If the file does not exist.
        AnnotationError
            If annotation fails.

        Examples
        --------
        >>> result = client.annotate_document(
        ...     "/path/to/paper.pdf",
        ...     parser_id="pdf",
        ...     vocabulary=["DRUG", "INDICATION"]
        ... )
        """
        # Validate file path
        if not file_path:
            raise ValidationError("file_path is required")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Normalize vocabulary
        vocab_list = self._normalize_vocabulary(vocabulary)

        # Build request parameters
        endpoint = "/api/termite/v1/annotate"
        params: dict[str, Any] = {"parserId": parser_id}

        if vocab_list is not None:
            params["vocabulary"] = vocab_list
        if case_match is not None:
            params["caseMatch"] = case_match
        if reject_ambig is not None:
            params["rejectAmbig"] = reject_ambig
        if boost is not None:
            params["boost"] = boost
        if subsume is not None:
            params["subsume"] = subsume
        if byte_positions is not None:
            params["bytePositions"] = byte_positions
        if entity_ids is not None:
            params["entityIds"] = entity_ids
        if ancestors is not None:
            params["ancestors"] = ancestors

        # Build form data for fields and parser config
        data: dict[str, str] = {}
        if fields is not None:
            data["fields"] = json.dumps(fields)
        if parser_config is not None:
            data["parserConfig"] = json.dumps(parser_config)

        # Prepare file upload
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        logger.debug(
            "Annotating document: file=%s size=%d parser=%s",
            file_name, file_size, parser_id
        )

        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            resp = self.post(
                endpoint,
                params=params,
                files=files,
                data=data if data else None,
            )

        result = self.json_or_raise(resp)

        logger.info("Document annotation successful: %s", file_name)
        return result

    # ── Bytes Annotation ───────────────────────────────────────────
    def annotate_bytes(
        self,
        content: bytes,
        filename: str,
        parser_id: str = "generic",
        vocabulary: Optional[Union[str, list[str]]] = None,
        case_match: Optional[bool] = None,
        reject_ambig: Optional[bool] = None,
        boost: Optional[bool] = None,
        subsume: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Annotate in-memory bytes content with TERMite.

        Useful when you have document content in memory and don't want
        to write it to disk first.

        Parameters
        ----------
        content : bytes
            The document content as bytes.
        filename : str
            Filename to send (used for parser detection, e.g., ``"doc.pdf"``).
        parser_id : str, default="generic"
            Parser to use.
        vocabulary : str or list of str, optional
            Vocabularies to use for annotation.
        case_match : bool, optional
            If ``True``, enforce case-sensitive matching.
        reject_ambig : bool, optional
            If ``True``, reject ambiguous matches.
        boost : bool, optional
            If ``True``, treat sub-synonyms as full hits.
        subsume : bool, optional
            If ``True``, take the longest entity match.

        Returns
        -------
        dict
            Annotation results.

        Raises
        ------
        ValidationError
            If content or filename is empty.

        Examples
        --------
        >>> with open("document.pdf", "rb") as f:
        ...     content = f.read()
        >>> result = client.annotate_bytes(content, "document.pdf")
        """
        if not content:
            raise ValidationError("content is required")
        if not filename:
            raise ValidationError("filename is required")

        vocab_list = self._normalize_vocabulary(vocabulary)

        endpoint = "/api/termite/v1/annotate"
        params: dict[str, Any] = {"parserId": parser_id}

        if vocab_list is not None:
            params["vocabulary"] = vocab_list
        if case_match is not None:
            params["caseMatch"] = case_match
        if reject_ambig is not None:
            params["rejectAmbig"] = reject_ambig
        if boost is not None:
            params["boost"] = boost
        if subsume is not None:
            params["subsume"] = subsume

        logger.debug("Annotating bytes: filename=%s size=%d", filename, len(content))

        files = {"file": (filename, content)}
        resp = self.post(endpoint, params=params, files=files)
        result = self.json_or_raise(resp)

        logger.info("Bytes annotation successful: %s", filename)
        return result

    # ── Helper Methods ─────────────────────────────────────────────
    def _normalize_vocabulary(
        self, vocabulary: Optional[Union[str, list[str]]]
    ) -> Optional[list[str]]:
        """Normalize vocabulary parameter to list of uppercase strings."""
        if vocabulary is None:
            return None

        if isinstance(vocabulary, str):
            # Split by comma and uppercase
            return [v.strip().upper() for v in vocabulary.split(",") if v.strip()]
        elif isinstance(vocabulary, list):
            return [v.upper() if isinstance(v, str) else v for v in vocabulary]
        else:
            raise ValidationError("vocabulary must be a string or list of strings")

    @staticmethod
    def extract_entities(annotation_result: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract entities from annotation result.

        Parameters
        ----------
        annotation_result : dict
            The annotation result from TERMite.

        Returns
        -------
        list of dict
            Flattened list of entity dictionaries with id, name, and occurrences.

        Examples
        --------
        >>> result = client.annotate_text("Aspirin treats pain")
        >>> entities = TermiteAnnotateClient.extract_entities(result)
        >>> for e in entities:
        ...     print(f"{e['id']}: {e['name']} ({e['occurrence_count']} hits)")
        """
        entities = []
        for group in annotation_result.get("included", []):
            for entity in group.get("entities", []):
                occurrences = entity.get("occurrences", [])
                entity_id = entity.get("id", "")
                # Get vocabulary from entity-level field (per API spec),
                # falling back to parsing from entity ID (format: VOCAB$ID)
                vocabulary = entity.get("vocabularyId")
                if not vocabulary and "$" in entity_id:
                    vocabulary = entity_id.split("$")[0]
                entities.append({
                    "id": entity_id,
                    "name": entity.get("name"),
                    "public_uri": entity.get("publicUri"),
                    "vocabulary": vocabulary,
                    "vocabulary_name": entity.get("vocabularyName"),
                    "occurrence_count": len(occurrences),
                    "occurrences": occurrences,
                })
        return entities
