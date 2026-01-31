import requests
import logging
from logging import NullHandler
import pandas as pd
import re
import os
from requests import exceptions as reqexc
from datetime import datetime, timezone
import time

# Configure logging
logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())

class Termite7RequestBuilder:
    """
    Class for creating TERMite 7 Requests
    """

    def __init__(self, timeout: int = 60, log_level: str = 'WARNING'):
        """
        Initialize the Termite7RequestBuilder.

        Parameters
        ----------
        timeout : int, optional
            The timeout for HTTP requests in seconds (default is 60 seconds).
        log_level : str, optional
            The logging level to use (default is 'WARNING').
            Accepts: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
        """
        self.session = requests.Session()
        self.url = ''
        self.file_input = None
        self.headers = {}
        self.verify_request = False
        self.timeout = timeout
        self.settings = {}
        self.token_url = None
        self._open_file = None  # Track open file handle for cleanup

        level = getattr(logging, log_level.upper(), logging.WARNING)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures file cleanup."""
        self.close()
        return False

    def close(self):
        """Close any open file handles and cleanup resources."""
        if self._open_file is not None:
            try:
                self._open_file.close()
                self.logger.debug("Closed open file handle")
            except Exception as e:
                self.logger.debug("Error closing file handle: %s", e)
            finally:
                self._open_file = None
                if 'file' in self.settings:
                    del self.settings['file']

    def set_token_url(self, token_url):
        """Set the URL for the token API.

        Parameters
        ----------
        token_url : str
            URL for the token API
        """
        self.token_url = token_url.rstrip('/')

    def set_oauth2(self, client_id, client_secret):
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

        Raises
        ------
        ValueError
            If token_url is not set, or if client_id/client_secret are invalid.
        """
        # Validate token_url is set
        if not self.token_url:
            self.logger.error("token_url not set; call set_token_url() first")
            raise ValueError("token_url must be set before calling set_oauth2()")

        # Validate input parameters
        if not client_id or not isinstance(client_id, str):
            self.logger.error("Invalid client_id: must be a non-empty string")
            raise ValueError("client_id must be a non-empty string")

        if not client_secret or not isinstance(client_secret, str):
            self.logger.error("Invalid client_secret: must be a non-empty string")
            raise ValueError("client_secret must be a non-empty string")

        token_address = f"{self.token_url}/auth/realms/Scibite/protocol/openid-connect/token"

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = self.session.post(
                token_address,
                data=payload,
                headers=headers,
                verify=True,
                timeout=self.timeout,
            )
            resp.raise_for_status()

            try:
                body = resp.json()
            except ValueError as e:
                self.logger.warning("OAuth2 response is not valid JSON: %s", e)
                return False

            access_token = body.get("access_token")
            if not access_token:
                self.logger.warning("Access token missing in OAuth2 response")
                return False

            self.headers = {"Authorization": f"Bearer {access_token}"}

            expires_in = int(body.get("expires_in", 0))
            if expires_in:
                utc_when = datetime.fromtimestamp(
                    time.time() + expires_in, tz=timezone.utc
                ).isoformat()
                self.logger.info(
                    "OAuth2 token acquired; expires in ~%ds (at %s)",
                    expires_in,
                    utc_when,
                )
            else:
                self.logger.info("OAuth2 token acquired; 'expires_in' not provided")

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
            self.logger.warning("OAuth2 HTTP error (%s) at %s; body: %s", code, token_address, snippet)
            return False

        except reqexc.SSLError as e:
            self.logger.warning("OAuth2 TLS/SSL error at %s: %s (verify=%s)", token_address, e, 'True')
            return False

        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            self.logger.warning("OAuth2 network error at %s: %s", token_address, e)
            return False

        except Exception as e:
            self.logger.warning("OAuth2 authentication failed: %s", e)
            return False

    def set_oauth2_legacy(self, client_id, username, password, verification=True):
        """
        Passes username and password for the TERMite 7 token API to generate an access token
        and adds it to the request header.

        This method uses the OAuth2 password grant flow (legacy/deprecated flow). For new
        implementations, prefer set_oauth2() with client credentials flow.

        Parameters
        ----------
        client_id : str
            The client ID to access the token API.
        username : str
            The TERMite 7 username.
        password : str
            The TERMite 7 password for the provided username.
        verification : bool, optional
            Whether to verify SSL certificate (default is True).

        Returns
        -------
        bool
            True if authentication was successful, False otherwise.

        Raises
        ------
        ValueError
            If url is not set, or if client_id/username/password are invalid.
        """
        # Validate url is set (legacy uses main TERMite URL, not separate token URL)
        if not self.url:
            self.logger.error("url not set; call set_url() first")
            raise ValueError("url must be set before calling set_oauth2_legacy()")

        # Validate input parameters
        if not client_id or not isinstance(client_id, str):
            self.logger.error("Invalid client_id: must be a non-empty string")
            raise ValueError("client_id must be a non-empty string")

        if not username or not isinstance(username, str):
            self.logger.error("Invalid username: must be a non-empty string")
            raise ValueError("username must be a non-empty string")

        if not password or not isinstance(password, str):
            self.logger.error("Invalid password: must be a non-empty string")
            raise ValueError("password must be a non-empty string")

        token_address = f"{self.url}/auth/realms/Scibite/protocol/openid-connect/token"

        # Log the token request details
        self.logger.debug("Authenticating to %s with client_id=%s (verify=%s)", token_address, client_id, verification)

        try:
            req = self.session.post(token_address,
                                    data={
                                        "grant_type": "password",
                                        "client_id": client_id,
                                        "username": username,
                                        "password": password
                                    },
                                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                                    timeout=self.timeout,  # Use instance timeout
                                    verify=verification)  # Use the verification flag

            req.raise_for_status()  # Raise an HTTPError if the response was unsuccessful

            # Log the successful request
            self.logger.debug("Token request succeeded with status %s", req.status_code)

            try:
                body = req.json()
            except ValueError as e:
                self.logger.warning("OAuth2 legacy response is not valid JSON: %s", e)
                return False

            access_token = body.get("access_token")
            if not access_token:
                self.logger.warning("Access token missing in OAuth2 legacy response")
                return False

            # Set headers and verification flag
            self.headers = {"Authorization": f"Bearer {access_token}"}
            self.verify_request = verification

            # Log token reception
            self.logger.info("TERMite authentication successful; access token set")
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
            self.logger.warning("OAuth2 legacy HTTP error (%s) at %s; body: %s", code, token_address, snippet)
            return False

        except reqexc.SSLError as e:
            self.logger.warning("OAuth2 legacy TLS/SSL error at %s: %s (verify=%s)", token_address, e, verification)
            return False

        except (reqexc.ConnectionError, reqexc.Timeout) as e:
            self.logger.warning("OAuth2 legacy network error at %s: %s", token_address, e)
            return False

        except Exception as e:
            self.logger.warning("OAuth2 legacy authentication failed: %s", e)
            return False

    def set_url(self, url):
        """
        Set the URL of the TERMite 7 instance.

        Parameters
        ----------
        url : str
            The URL of the TERMite 7 instance to be hit.
        """
        if not isinstance(url, str) or not url.strip():
            self.logger.error("Invalid URL: value must be a non-empty string")
            raise ValueError("URL must be a non-empty string")

        # Log the URL being set
        self.logger.debug("Received TERMite URL input: %r", url)

        # Remove any trailing slash from the URL and set it
        self.url = url.rstrip('/')

        # High-level success without echoing the URL
        self.logger.info("TERMite URL configured")
        # Detailed value at DEBUG only
        self.logger.debug("TERMite URL set to %r", self.url)

    def set_text(self, text):
        """
        Set the text to be annotated.

        Parameters
        ----------
        text : str or list of str
            The text or list of text to annotate.

        Raises
        ------
        ValueError
            If the input is not a string or a list of strings.

        Notes
        -----
        If a single string is provided, it will be wrapped in a list.
        If a list of strings is provided, it will be used as-is.
        """
        if isinstance(text, str):
            self.settings["text"] = [text]
            self.logger.debug("Set text: 1 item")
        elif isinstance(text, list) and all(isinstance(item, str) for item in text):
            self.logger.info("Received a list of strings.")
            self.settings["text"] = text
            self.logger.debug("Set text: %d items", len(text))
        else:
            self.logger.error("Invalid input: 'text' should be a string or a list of strings.")
            raise ValueError("Input should be a string or a list of strings.")

    def set_subsume(self, subsume):
        """
        Set the subsume option for entity annotation.

        This method determines whether to prioritize and return the longest entity match
        when an entity is recognized against multiple vocabularies (VOCabs). Enabling this
        option ensures that if an entity has overlapping matches in different vocabularies,
        only the longest match is returned.

        Parameters
        ----------
        subsume : bool, int, or str
            The subsume option:
            - If True (or equivalent input), the longest entity match is taken when an entity matches more than one vocabulary.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_subsume(True)
        Enables subsume, so the longest entity match is selected.

        >>> set_subsume(0)
        Disables subsume using an integer input.

        >>> set_subsume("true")
        Enables subsume using a string input.
        """
        original = subsume
        value: bool

        # Coerce input to boolean
        if isinstance(subsume, bool):
            value = subsume

        elif isinstance(subsume, int) and subsume in (0, 1):
            value = bool(subsume)
            self.logger.debug("Coerced int %r to bool %r for subsume", original, value)

        elif isinstance(subsume, str):
            s = subsume.strip().lower()
            if s in ("true", "t", "1", "yes", "on"):
                value = True
            elif s in ("false", "f", "0", "no", "off"):
                value = False
            else:
                self.logger.error("Invalid string for subsume: %r", subsume)
                raise ValueError("Invalid input for subsume: expected True/False or 'true'/'false' (case-insensitive).")

        else:
            # Log invalid input before raising an exception
            self.logger.error("Invalid type for subsume: %s", type(subsume).__name__)
            raise ValueError("Invalid input for subsume: expected bool, 0/1, or 'true'/'false'.")

        # Set the value in settings
        self.settings["subsume"] = value

        # Log the change
        self.logger.info("Subsume %s", "enabled" if value else "disabled")
        self.logger.debug("Subsume set (input=%r -> value=%r)", original, value)

    def set_entities(self, vocabulary):
        """
        Limit the types of entities to be annotated by specifying vocabularies (VOCabs).

        This method restricts the annotations to a subset of entities based on the provided
        vocabularies (VOCabs). The input is a comma-separated string of entity types, which
        will be converted into a list of uppercase VOCab IDs. Each entity type is validated
        against the pattern [A-Z0-9_]. If any entity does not match the valid pattern, a
        warning is logged.

        Parameters
        ----------
        vocabulary : str
            A comma-separated string of entity types to limit annotations to, e.g., 'DRUG,INDICATION'.
            Each entity type will be stripped of extra spaces and converted to uppercase.

        Raises
        ------
        ValueError
            If the input is not a string or is empty.

        Notes
        -----
        - Valid VOCab IDs must match the pattern [A-Z0-9_].
        - Invalid VOCab IDs will not be included in the final list, and a warning will be logged.

        Examples
        --------
        >>> set_entities('DRUG, INDICATION')
        Restricts the annotation to the entities 'DRUG' and 'INDICATION'.

        >>> set_entities('DRUG,Invalid!Entity')
        Logs a warning for 'Invalid!Entity' and only 'DRUG' will be used.
        """
        if not isinstance(vocabulary, str) or not vocabulary.strip():
            self.logger.error("Invalid vocabulary input: must be a non-empty string")
            raise ValueError("vocabulary must be a non-empty comma-separated string")

        self.logger.debug("set_entities called with %r", vocabulary)

        valid_pattern = re.compile(r'^[A-Z0-9_]+$')
        entities = [v.strip().upper() for v in vocabulary.split(",") if v.strip()]

        # Validate each entity and log a warning if the pattern is not matched
        valid_entities, invalid_entities = [], []
        for entity in entities:
            if valid_pattern.match(entity):
                valid_entities.append(entity)
                self.logger.debug("Valid vocabulary: %s", entity)
            else:
                invalid_entities.append(entity)
                # invalid vocab = non-fatal but noteworthy
                self.logger.warning("Invalid vocabulary: %r (must match [A-Z0-9_])", entity)

        self.settings["vocabulary"] = valid_entities

        if valid_entities:
            self.logger.info(
                "Vocabulary restriction applied (%d valid, %d invalid)",
                len(valid_entities),
                len(invalid_entities),
            )
        else:
            self.logger.warning("No valid vocabularies provided; annotation will not be restricted")

        self.logger.debug("Final valid vocabularies: %s", valid_entities)

    def set_case_match(self, case_match):
        """
        Set the case_match option to enforce case-sensitive entity matching.

        This method determines whether entities must match case exactly during annotation.
        Enabling this option will ensure that synonym matches are case-sensitive, meaning
        entities will only be recognized if the case of the input text matches exactly.
        This option is optional and defaults to False.

        Parameters
        ----------
        case_match : bool, int, or str
            The case_match option:
            - If True (or equivalent input), entities must match case exactly.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_case_match(True)
        Enables case-sensitive matching for entity synonyms.

        >>> set_case_match(0)
        Disables case-sensitive matching using an integer input.

        >>> set_case_match("true")
        Enables case-sensitive matching using a string input.
        """
        original = case_match
        value: bool

        # Coerce input to boolean
        if isinstance(case_match, bool):
            value = case_match

        elif isinstance(case_match, int) and case_match in (0, 1):
            value = bool(case_match)
            self.logger.debug("Coerced int %r to bool %r for case_match", original, value)

        elif isinstance(case_match, str):
            s = case_match.strip().lower()
            if s in ("true", "t", "1", "yes", "on"):
                value = True
            elif s in ("false", "f", "0", "no", "off"):
                value = False
            else:
                self.logger.error("Invalid string for case_match: %r", case_match)
                raise ValueError("Invalid input for case_match: expected True/False or 'true'/'false' (case-insensitive).")

        else:
            # Log invalid input before raising an exception
            self.logger.error("Invalid type for case_match: %s", type(case_match).__name__)
            raise ValueError("Invalid input for case_match: expected bool, 0/1, or 'true'/'false'.")

        # Set the value in settings
        self.settings["caseMatch"] = value

        # Log the change
        self.logger.info("caseMatch %s", "enabled" if value else "disabled")
        self.logger.debug("caseMatch set (input=%r -> value=%r)", original, value)

    def set_reject_ambig(self, reject_ambig):
        """
        Set the rejectAmbig option to handle ambiguous entity matches.

        This method determines whether entities that have ambiguous hits should be rejected
        during annotation. Enabling this option can help filter out potentially inaccurate
        annotations by excluding ambiguous entity matches. This option is optional and
        defaults to False.

        Parameters
        ----------
        rejectAmbig : bool, int, or str
            The rejectAmbig option:
            - If True (or equivalent input), ambiguous entity hits are rejected.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_reject_ambig(True)
        Enables rejection of ambiguous entity matches.

        >>> set_reject_ambig(1)
        Enables rejection using an integer input.

        >>> set_reject_ambig("false")
        Disables rejection using a string input.
        """
        original = reject_ambig
        value: bool

        # Coerce input to boolean
        if isinstance(reject_ambig, bool):
            value = reject_ambig

        elif isinstance(reject_ambig, int) and reject_ambig in (0, 1):
            value = bool(reject_ambig)
            self.logger.debug("Coerced int %r to bool %r for reject_ambig", original, value)

        elif isinstance(reject_ambig, str):
            s = reject_ambig.strip().lower()
            if s in ("true", "t", "1", "yes", "on"):
                value = True
            elif s in ("false", "f", "0", "no", "off"):
                value = False
            else:
                self.logger.error("Invalid string for reject_ambig: %r", reject_ambig)
                raise ValueError(
                    "Invalid input for reject_ambig: expected True/False or 'true'/'false' (case-insensitive).")

        else:
            # Log invalid input before raising an exception
            self.logger.error("Invalid type for reject_ambig: %s", type(reject_ambig).__name__)
            raise ValueError("Invalid input for reject_ambig: expected bool, 0/1, or 'true'/'false'.")

        # Set the value in settings
        self.settings["rejectAmbig"] = value

        # Log the change
        self.logger.info("rejectAmbig %s", "enabled" if value else "disabled")
        self.logger.debug("rejectAmbig set (input=%r -> value=%r)", original, value)

    def set_boost(self, boost):
        """
        Set the boost option to modify ambiguity and subsyn behavior.

        This method enables or disables the boost option, which determines whether
        any ambiguity and subsyn settings are switched off, treating them as full hits.
        This can be useful when more aggressive matching is desired.

        Parameters
        ----------
        boost : bool, int, or str
            The boost option:
            - If True (or equivalent input), subsyns are recognized as full hits.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Examples
        --------
        >>> set_boost(True)
        Enables boost, treating subsyns as full hits.

        >>> set_boost(1)
        Enables boost with an integer input.

        >>> set_boost("false")
        Disables boost using a string input.
        """
        original = boost
        value: bool

        # Coerce input to boolean
        if isinstance(boost, bool):
            value = boost

        elif isinstance(boost, int) and boost in (0, 1):
            value = bool(boost)
            self.logger.debug("Coerced int %r to bool %r for boost", original, value)

        elif isinstance(boost, str):
            s = boost.strip().lower()
            if s in ("true", "t", "1", "yes", "on"):
                value = True
            elif s in ("false", "f", "0", "no", "off"):
                value = False
            else:
                self.logger.error("Invalid string for boost: %r", boost)
                raise ValueError(
                    "Invalid input for boost: expected True/False or 'true'/'false' (case-insensitive).")

        else:
            # Log invalid input before raising an exception
            self.logger.error("Invalid type for boost: %s", type(boost).__name__)
            raise ValueError("Invalid input for boost: expected bool, 0/1, or 'true'/'false'.")

        # Set the value in settings
        self.settings["boost"] = value

        # Log the change
        self.logger.info("boost %s", "enabled" if value else "disabled")
        self.logger.debug("boost set (input=%r -> value=%r)", original, value)

    def set_entityIds(self, entityIds):
        """
        Set the entityIds option to filter annotations by Entity IDs.

        This method filters results to only include annotations that belong to the
        provided list of Entity IDs.

        Parameters
        ----------
        entityIds : list of str
            A list of Entity IDs to filter annotations. Each element in the list must be a string.
            - If an empty list is provided, no filtering will be applied (all annotations will be included).

        Raises
        ------
        ValueError
            If the input is not a list or if any element in the list is not a string.

        Examples
        --------
        >>> set_entityIds(["D006801", "U0002048"])
        Sets the entityIds to ["D006801", "U0002048"] to filter annotations by those IDs.

        >>> set_entityIds([])
        Sets an empty list, meaning no filtering will be applied.
        """
        self.logger.debug("set_entityIds called with %r", entityIds)

        # Validate input
        if not isinstance(entityIds, list):
            self.logger.error("Invalid input: expected list, got %s", type(entityIds).__name__)
            raise ValueError("entityIds must be a list of strings")

        if not all(isinstance(i, str) for i in entityIds):
            self.logger.error("Invalid input: all entityIds must be strings. Input=%r", entityIds)
            raise ValueError("All entityIds must be strings")

        if not entityIds:  # Optional: Handle empty list case
            self.logger.info("entityIds list empty — no filtering will be applied")

        else:
            self.logger.info("entityIds filter applied (%d IDs)", len(entityIds))
            self.logger.debug("entityIds set to: %s", entityIds)

        self.settings["entityIds"] = entityIds

    def set_ancestors(self, ancestors):
        """
        Set the ancestors option for filtering annotations.

        This method filters results to only include annotations for entities that are
        descendants of one of the specified taxonomy nodes.

        Parameters
        ----------
        ancestors : list of str
            A list of entity IDs representing taxonomy nodes to filter annotations.
            Each element in the list must be a string.
            - If an empty list is provided, no filtering will be applied (all annotations included).

        Raises
        ------
        ValueError
            If the input is not a list or if any element in the list is not a string.

        Examples
        --------
        >>> set_ancestors(["NCIT$NCIT_C8278", "HGNCGENE$GROUP397"])
        Sets the ancestors to ["NCIT$NCIT_C8278", "HGNCGENE$GROUP397"].

        >>> set_ancestors([])
        Sets an empty list, meaning no filtering will be applied.
        """
        self.logger.debug("set_ancestors called with %r", ancestors)

        # Validate input
        if not isinstance(ancestors, list):
            self.logger.error("Invalid input: expected list, got %s", type(ancestors).__name__)
            raise ValueError("ancestors must be a list of strings")

        if not all(isinstance(i, str) for i in ancestors):
            self.logger.error("Invalid input: all ancestors must be strings. Input=%r", ancestors)
            raise ValueError("All ancestors must be strings")

        if not ancestors:  # Optional: Handle empty list case
            self.logger.info("Ancestors list empty — no ancestor filtering will be applied")
        else:
            self.logger.info("Ancestor filter applied (%d IDs)", len(ancestors))
            self.logger.debug("Ancestors set to: %s", ancestors)

        self.settings["ancestors"] = ancestors

    def set_byte_positions(self, byte_positions):
        """
        Set the byte_positions option to include byte offsets for entity locations.

        This method determines whether byte positions (in addition to character positions)
        for entity mentions should be included in the results. Enabling this option allows
        the system to return both character and byte offsets, but it may incur a performance
        penalty due to the additional computation required to calculate byte positions.

        Parameters
        ----------
        byte_positions : bool, int, or str
            The byte_positions option:
            - If True (or equivalent input), byte positions are included.
            - Accepts:
              - Boolean values: True or False.
              - Integer values: 1 (equivalent to True) or 0 (equivalent to False).
              - Strings: 'true' (equivalent to True) or 'false' (equivalent to False).

        Raises
        ------
        ValueError
            If the input is not a boolean, an integer (0 or 1), or a string ('true' or 'false').

        Notes
        -----
        Enabling byte positions may affect performance, as additional processing is required
        to compute byte offsets. Consider whether byte positions are necessary for your use case.

        Examples
        --------
        >>> set_byte_positions(True)
        Enables byte positions for entity mentions.

        >>> set_byte_positions(0)
        Disables byte positions using an integer input.

        >>> set_byte_positions("true")
        Enables byte positions using a string input.
        """
        self.logger.debug("set_byte_positions called with %r (%s)", byte_positions, type(byte_positions).__name__)

        original = byte_positions
        value: bool

        # Coerce input to boolean
        if isinstance(byte_positions, bool):
            value = byte_positions
        elif isinstance(byte_positions, int) and byte_positions in (0, 1):
            value = bool(byte_positions)
            self.logger.debug("Coerced int %r to bool %r", original, value)
        elif isinstance(byte_positions, str):
            s = byte_positions.strip().lower()
            if s in ("true", "t", "1", "yes", "on"):
                value = True
            elif s in ("false", "f", "0", "no", "off"):
                value = False
            else:
                self.logger.error("Invalid string for byte_positions: %r", byte_positions)
                raise ValueError("Invalid input for byte_positions: expected True/False or 'true'/'false'.")
        else:
            self.logger.error("Invalid type for byte_positions: %s", type(byte_positions).__name__)
            raise ValueError("Invalid input for byte_positions: expected bool, 0/1, or 'true'/'false'.")

        self.settings["bytePositions"] = value

        # Log the change
        self.logger.info("Byte positions %s", "enabled" if value else "disabled")
        self.logger.debug("bytePositions set (input=%r -> value=%r)", original, value)

    def annotate_text(self, **kwargs):
        """
        Sends an array of text strings or a single string to the TERMite /v1/annotate API and returns the resulting JSON.

        Parameters
        ----------
        text : str or list of str, optional
            A single string or an array of strings to be annotated. If not provided, falls back to `self.settings['text']`.
        vocabulary : str, optional
            Vocabulary or set of terms to use for the annotation. If not provided, defaults to `self.settings['vocabulary']`.
        case_match : bool, optional
            Whether to enforce case sensitivity when matching terms. If not provided, defaults to `self.settings['caseMatch']`.
        reject_ambig : bool, optional
            Whether to reject ambiguous matches (if a term has multiple meanings). Defaults to `self.settings['rejectAmbig']`.
        boost : str, optional
            Boost specific entities in the annotation results. Defaults to `self.settings['boost']`.
        entity_ids : list of str, optional
            Specific entity IDs to be boosted or used for annotations. Defaults to `self.settings['entityIds']`.
        ancestors : bool, optional
            Whether to include ancestors of the matched entities in the result. Defaults to `self.settings['ancestors']`.
        subsume : bool, optional
            Whether to allow larger terms to subsume smaller ones during matching. Defaults to `self.settings['subsume']`.
        byte_positions : bool, optional
            If True, returns the byte positions of the matched entities in the original text. Defaults to `self.settings['bytePositions']`.

        Returns
        -------
        dict or None
            The JSON response from the TERMite API if the request is successful. If the request fails, returns None.

        Raises
        ------
        ValueError
            If no text is provided and `self.settings['text']` is also not set.

        Examples
        --------
        Annotate a single string:
        >>> annotate_text(text="COVID-19 is a disease caused by SARS-CoV-2.")

        Annotate multiple strings:
        >>> annotate_text(text=["COVID-19 is caused by SARS-CoV-2.", "Influenza is caused by the flu virus."],
                          vocabulary="INDICATION",
                          caseMatch=True)

        Notes
        -----
        The method logs and handles HTTP and request errors, such as timeouts or invalid responses. Be sure to configure
        `self.settings` appropriately for defaults.
        """
        # ---- Pull kwargs with fallbacks from settings ----
        text = kwargs.get("text", self.settings.get("text"))
        vocabulary = kwargs.get("vocabulary", self.settings.get("vocabulary"))
        case_match = kwargs.get("case_match", self.settings.get("caseMatch"))
        reject_ambig = kwargs.get("reject_ambig", self.settings.get("rejectAmbig"))
        boost = kwargs.get("boost", self.settings.get("boost"))
        entity_ids = kwargs.get("entity_ids", self.settings.get("entityIds"))
        ancestors = kwargs.get("ancestors", self.settings.get("ancestors"))
        subsume = kwargs.get("subsume", self.settings.get("subsume"))
        byte_positions = kwargs.get("byte_positions", self.settings.get("bytePositions"))

        # ---- Validate URL + text presence ----
        if not getattr(self, "url", None):
            self.logger.error("annotate_text called before URL was configured")
            return None

        if text is None:
            raise ValueError("No text provided, and self.settings['text'] is not set.")

        # ---- Normalize text to list[str] ----
        if isinstance(text, str):
            text = [text]
            self.logger.debug("Single string received; wrapped in a list")

        if not isinstance(text, list) or not all(isinstance(item, str) for item in text):
            self.logger.error("Invalid 'text' input: must be a string or a list of strings")
            return None

        # ---- Build request ----
        annotate_endpoint = f"{self.url}/api/termite/v1/annotate"
        params = {"text": text}

        if vocabulary is not None: params["vocabulary"] = vocabulary
        if case_match is not None: params["caseMatch"] = case_match
        if reject_ambig is not None: params["rejectAmbig"] = reject_ambig
        if boost is not None: params["boost"] = boost
        if entity_ids is not None: params["entityIds"] = entity_ids
        if ancestors is not None: params["ancestors"] = ancestors
        if subsume is not None: params["subsume"] = subsume
        if byte_positions is not None: params["bytePositions"] = byte_positions

        # ---- Send request with timing ----
        try:
            # Make the GET request
            req = self.session.get(annotate_endpoint, params=params, headers=self.headers, timeout=self.timeout)
            req.raise_for_status()  # Raise an error for bad status codes (4xx, 5xx)

            # Log successful request
            self.logger.info("Text annotation request successful")

            # Return the raw JSON response
            return req.json()

        except requests.exceptions.Timeout:
            self.logger.error("Annotation timed out after %ss (endpoint=%s)",self.timeout, annotate_endpoint)
        except requests.exceptions.HTTPError as http_err:
            status = getattr(http_err.response, "status_code", "unknown")
            self.logger.error("HTTP error during annotation: status=%s, err=%s",status, http_err)
        except requests.exceptions.RequestException as req_err:
            self.logger.error("Request error during annotation: %s", req_err)
        except ValueError:
            self.logger.error("Failed to parse response as JSON")

        return None

    def set_file(self, input_file_path):
        """
        Set the file to be annotated by TERMite.

        This method sets a file for annotation by specifying its file path. The file is opened
        in binary mode and stored in the settings. If multiple files of the same type need to
        be annotated at once, they should be placed in a zip archive and specified as the input.

        Any previously opened file will be closed automatically.

        Parameters
        ----------
        input_file_path : str
            The file path to the file that will be sent to TERMite for annotation.
            This can also be a zip archive if multiple files are to be scanned.

        Raises
        ------
        FileNotFoundError
            If the specified file path does not exist or cannot be opened.

        Examples
        --------
        >>> set_file("/path/to/file.txt")
        Prepares the specified file for TERMite annotation.

        >>> set_file("/path/to/files.zip")
        Prepares a zip archive of files for TERMite annotation.
        """
        self.logger.debug("set_file called with path=%r", input_file_path)

        if not isinstance(input_file_path, str):
            self.logger.error("Invalid input type for input_file_path: %s", type(input_file_path).__name__)
            raise ValueError("input_file_path must be a string")

        if not os.path.exists(input_file_path):
            self.logger.error("File not found: %s", input_file_path)
            raise FileNotFoundError(f"File not found: {input_file_path}")

        # Close any previously opened file
        self.close()

        file_name = os.path.basename(input_file_path)

        try:
            file_obj = open(input_file_path, "rb")
        except OSError as e:
            self.logger.error("Unable to open file %s: %s", input_file_path, e)
            raise

        # Store the open file object in settings and track it
        self._open_file = file_obj
        self.settings['file'] = {"file": (file_name, file_obj)}

        # Log the file setting
        self.logger.info("File '%s' prepared for annotation", file_name)
        self.logger.debug("File object stored in settings['file'] with size=%d bytes", os.path.getsize(input_file_path))

    def set_parser_id(self, parser_id):
        """
        Set the parser to use when annotating documents with TERMite 7.

        Parameters
        ----------
        parser_id : str
            The ID of the parser to use, e.g. 'generic', or 'xml'.
        """
        self.logger.debug("set_parser_id called with %r", parser_id)

        if not isinstance(parser_id, str) or not parser_id.strip():
            self.logger.error("Invalid parser_id: expected non-empty string, got %r", parser_id)
            raise ValueError("parser_id must be a non-empty string")

        self.settings["parserId"] = parser_id.strip()
        self.logger.info("Parser ID set to '%s'", self.settings["parserId"])

    def annotate_document(self, **kwargs):
        """
        Sends a document or collection of documents to the TERMite /v1/annotate API and returns the resulting JSON.

        Parameters
        ----------
        input_file_path : binary
            A document or zip archive of documents. If not provided, falls back to `self.settings['file']`.
        parser_id : str, optional
            The ID of the parser to use. Default is 'generic'.
        vocabulary : str, optional
            Vocabulary or set of terms to use for the annotation. If not provided, defaults to `self.settings['vocabulary']`.
        case_match : bool, optional
            Whether to enforce case sensitivity when matching terms. If not provided, defaults to `self.settings['caseMatch']`.
        reject_ambig : bool, optional
            Whether to reject ambiguous matches (if a term has multiple meanings). Defaults to `self.settings['rejectAmbig']`.
        boost : str, optional
            Boost specific entities in the annotation results. Defaults to `self.settings['boost']`.
        entity_ids : list of str, optional
            Specific entity IDs to be boosted or used for annotations. Defaults to `self.settings['entityIds']`.
        ancestors : bool, optional
            Whether to include ancestors of the matched entities in the result. Defaults to `self.settings['ancestors']`.
        subsume : bool, optional
            Whether to allow larger terms to subsume smaller ones during matching. Defaults to `self.settings['subsume']`.
        byte_positions : bool, optional
            If True, returns the byte positions of the matched entities in the original text. Defaults to `self.settings['bytePositions']`.

        Returns
        -------
        dict or None
            The JSON response from the TERMite API if the request is successful. If the request fails, returns None.

        Raises
        ------
        ValueError
            If no text is provided and `self.settings['file']` is also not set.

        Examples
        --------
        Annotate a single document:
        >>> annotate_document(file="")

        Annotate multiple strings:
        >>> annotate_text(text=["COVID-19 is caused by SARS-CoV-2.", "Influenza is caused by the flu virus."],
                          vocabulary="INDICATION",
                          caseMatch=True)

        Notes
        -----
        The method logs and handles HTTP and request errors, such as timeouts or invalid responses. Be sure to configure
        `self.settings` appropriately for defaults.
        """
        # ---- Pull kwargs with fallbacks from settings ----
        input_file_path = kwargs.get("input_file_path", None)
        parser_id = kwargs.get("parser_id", self.settings.get("parserId"))
        vocabulary = kwargs.get("vocabulary", self.settings.get("vocabulary"))
        case_match = kwargs.get("case_match", self.settings.get("caseMatch"))
        reject_ambig = kwargs.get("reject_ambig", self.settings.get("rejectAmbig"))
        boost = kwargs.get("boost", self.settings.get("boost"))
        entity_ids = kwargs.get("entity_ids", self.settings.get("entityIds"))
        ancestors = kwargs.get("ancestors", self.settings.get("ancestors"))
        subsume = kwargs.get("subsume", self.settings.get("subsume"))
        byte_positions = kwargs.get("byte_positions", self.settings.get("bytePositions"))

        # ---- Validate URL + text presence ----
        if not getattr(self, "url", None):
            self.logger.error("annotate_document called before URL was configured")
            return None

        # ---- Determine file handle strategy ----
        opened_here = False
        using_prepped_file = False

        if input_file_path:
            # Use a fresh path -> open here, and close here
            if not isinstance(input_file_path, str):
                self.logger.error("Invalid input type for input_file_path: %s", type(input_file_path).__name__)
                raise ValueError("input_file_path must be a string")

            if not os.path.exists(input_file_path):
                self.logger.error("File not found: %s", input_file_path)
                raise FileNotFoundError(f"File not found: {input_file_path}")

            file_name = os.path.basename(input_file_path)
            try:
                file_obj = open(input_file_path, "rb")
                opened_here = True
            except OSError as e:
                self.logger.error("Unable to open file %s: %s", input_file_path, e)
                raise

            files_arg = {"file": (file_name, file_obj)}
            file_size = os.path.getsize(input_file_path)
            self.logger.debug("Prepared file from path: name=%s size=%d bytes", file_name, file_size)

        else:
            # Fall back to pre-opened handle stored by set_file()
            prepped = self.settings.get("file")
            if not prepped or not isinstance(prepped, dict) or "file" not in prepped:
                raise ValueError("No file provided and no prepared file found in self.settings['file']")
            # prepped is expected to be {"file": (filename, file_obj)}
            files_arg = prepped
            using_prepped_file = True
            # Best-effort name/size for logs
            try:
                fname = files_arg["file"][0]
                self.logger.debug("Using prepped file from settings: name=%s", fname)
            except Exception:
                self.logger.debug("Using prepped file from settings")

        # ---- Build request ----
        annotate_endpoint = f"{self.url}/api/termite/v1/annotate"

        params = {}
        if parser_id is not None: params["parserId"] = parser_id
        if vocabulary is not None: params["vocabulary"] = vocabulary
        if case_match is not None: params["caseMatch"] = case_match
        if reject_ambig is not None: params["rejectAmbig"] = reject_ambig
        if boost is not None: params["boost"] = boost
        if entity_ids is not None: params["entityIds"] = entity_ids
        if ancestors is not None: params["ancestors"] = ancestors
        if subsume is not None: params["subsume"] = subsume
        if byte_positions is not None: params["bytePositions"] = byte_positions

        safe_params = {k: v for k, v in params.items()}
        self.logger.debug("Annotate document -> endpoint=%s, params=%r", annotate_endpoint, safe_params)

        # ---- Send request ----
        try:
            req = self.session.post(
                annotate_endpoint,
                params=params,
                files=files_arg,
                headers=self.headers,
                timeout=self.timeout
            )

            req.raise_for_status()

            self.logger.info(
                "Document annotation succeeded: %s",
                req.status_code
            )

            self.logger.debug(
                "Response ok (bytes=%d, content-type=%s)",
                len(req.content or b""),
                req.headers.get("Content-Type")
            )

            return req.json()

        except requests.exceptions.Timeout:
            self.logger.error("Annotation timed out after %ss (endpoint=%s)", self.timeout, annotate_endpoint)
        except requests.exceptions.HTTPError as http_err:
            status = getattr(http_err.response, "status_code", "unknown")
            self.logger.error("HTTP error during document annotation: status=%s, err=%s", status, http_err)
        except requests.exceptions.RequestException as req_err:
            self.logger.error("Request error during document annotation: %s", req_err)
        except ValueError:
            self.logger.error("Failed to parse response as JSON")
        finally:
            # Close only if we opened it here
            if opened_here:
                try:
                    file_obj.close()
                except Exception:
                    # Don't raise; just log at debug
                    self.logger.debug("Failed to close file object opened in annotate_document")
            # If we used a pre-opened file, close it now (file has been consumed)
            elif using_prepped_file:
                self.close()

        return None

def get_system_status(url, headers, fields='*', logger=None):
    """
    Fetches system Status from the TERMite API.

    Parameters
    ----------
    url : str
        Base URL of the TERMite service (e.g. "https://termite.server.com").
    headers : dict
        HTTP headers including authentication info.
    fields : str, optional
        Comma-separated list of fields to return (default '*').
    logger : logging.Logger, optional
        Logger to use instead of the root logger.

    Returns
    -------
    dict or None
        Parsed JSON response if successful; None otherwise.
    """
    log = logger or logging.getLogger(__name__)
    status_endpoint = f"{url}/api/termite/v1/status?fields={fields}"

    timeout = 4
    log.debug("Fetching TERMite status: endpoint=%s, timeout=%ss", status_endpoint, timeout)

    try:
        req = requests.get(status_endpoint, headers=headers, timeout=timeout)
        req.raise_for_status()
        log.info("TERMite system status fetched successfully")
        return req.json()

    except requests.exceptions.Timeout:
        log.error("Request to %s timed out after %ss", status_endpoint, timeout)
    except requests.exceptions.HTTPError as http_err:
        log.error("HTTP error while fetching system status: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        log.error("Network error while fetching system status: %s", req_err)
    except ValueError:
        log.error("Failed to parse system status response as JSON")

    return None

def get_vocabs(url, headers, logger=None):
    """
    Fetch available vocabularies from the TERMite API.

    Parameters
    ----------
    url : str
        Base URL of the TERMite service (e.g., "https://termite.server.com").
    headers : dict
        HTTP headers including authentication info.
    logger : logging.Logger, optional
        Logger to use instead of the root logger.

    Returns
    -------
    dict or None
        Parsed JSON response containing vocabularies if successful; None otherwise.
    """
    log = logger or logging.getLogger(__name__)
    vocabs_endpoint = f"{url.rstrip('/')}/api/termite/v1/vocabularies?hasCurrentVocabularyFile=true"

    timeout = 4
    log.debug("Fetching vocabularies from %s", vocabs_endpoint)

    try:
        resp = requests.get(vocabs_endpoint, headers=headers, timeout=timeout)
        resp.raise_for_status()
        log.info("Fetched TERMite vocabularies successfully (status=%s)", resp.status_code)
        return resp.json()

    except requests.exceptions.Timeout:
        log.error("Request to %s timed out after %ss", vocabs_endpoint, timeout)
    except requests.exceptions.HTTPError as http_err:
        log.error("HTTP error while fetching vocabularies: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        log.error("Network error while fetching vocabularies: %s", req_err)
    except ValueError:
        log.error("Failed to parse vocabularies response as JSON")

    return None

def get_parsers(url, headers, logger=None):
    """
    Fetch available parsers from the TERMite API.

    Parameters
    ----------
    url : str
        Base URL of the TERMite service (e.g., "https://termite.server.com").
    headers : dict
        HTTP headers including authentication info.
    logger : logging.Logger, optional
        Logger to use instead of the root logger.

    Returns
    -------
    dict or None
        Parsed JSON response containing available parsers if successful; None otherwise.
    """
    log = logger or logging.getLogger(__name__)
    parsers_endpoint = f"{url.rstrip('/')}/api/termite/v1/parsers"

    timeout = 4
    log.debug("Fetching parsers from %s (timeout=%ss)", parsers_endpoint)

    try:
        resp = requests.get(parsers_endpoint, headers=headers, timeout=timeout)
        resp.raise_for_status()
        log.info("Fetched TERMite parsers successfully (status=%s)", resp.status_code)
        return resp.json()

    except requests.exceptions.Timeout:
        log.error("Request to %s timed out after %ss", parsers_endpoint, timeout)
    except requests.exceptions.HTTPError as http_err:
        log.error("HTTP error while fetching parsers: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        log.error("Network error while fetching parsers: %s", req_err)
    except ValueError:
        log.error("Failed to parse parsers response as JSON")

    return None

def process_annotation_output(annotation_output, logger=None):
    """
    Processes the annotation output and returns a pandas DataFrame with the entity id, name, publicUri, and number of occurrences.

    Parameters
    ----------
    annotation_output : dict
        The output from the TERMite annotation API.
    logger : logging.Logger, optional
        Logger to use instead of the root logger.

    Returns
    -------
    pd.DataFrame
        A DataFrame with columns:
        ["Entity ID", "Name", "Public URI", "Occurrences", "FirstStartChar", "FirstStartByte"].
    """
    log = logger or logging.getLogger(__name__)

    if not isinstance(annotation_output, dict):
        log.error("Invalid input: expected dict, got %s", type(annotation_output).__name__)
        raise ValueError("annotation_output must be a dictionary")

    included_entities = annotation_output.get("included", [])
    if not included_entities:
        log.warning("No 'included' entities found in annotation output")
        return pd.DataFrame(
            columns=["Entity ID", "Name", "Public URI", "Occurrences", "FirstStartChar", "FirstStartByte"])

    data = []

    for entity_group in included_entities:
        entities = entity_group.get("entities", [])
        for entity in entities:
            occurrences = entity.get("occurrences", [])
            first_occ = occurrences[0] if occurrences else {}

            data.append({
                "Entity ID": entity.get("id", "N/A"),
                "Name": entity.get("name", "N/A"),
                "Public URI": entity.get("publicUri", "N/A"),
                "Occurrences": len(occurrences),
                "FirstStartChar": first_occ.get("startChar"),
                "FirstStartByte": first_occ.get("startByte"),
            })

    df = pd.DataFrame(data, columns=[
        "Entity ID", "Name", "Public URI", "Occurrences", "FirstStartChar", "FirstStartByte"
    ])

    log.info("Processed %d entities into DataFrame", len(df))

    return df

def get_runtime_options(url, headers, logger=None):
    """
    Fetch runtime options from the TERMite API.

    Parameters
    ----------
    url : str
        Base URL of the TERMite service (e.g., "https://termite.server.com").
    headers : dict
        HTTP headers including authentication info.
    logger : logging.Logger, optional
        Logger to use instead of the root logger.

    Returns
    -------
    dict or None
        Parsed JSON response containing runtime options if successful; None otherwise.
    """
    log = logger or logging.getLogger(__name__)
    endpoint = f"{url.rstrip('/')}/api/termite/v1/runtime-options"

    timeout = 4
    log.debug("Fetching runtime options from %s (timeout=%ss)", endpoint, timeout)

    try:
        resp = requests.get(endpoint, headers=headers)
        resp.raise_for_status()
        log.info("Fetched TERMite runtime options successfully (status=%s)", resp.status_code)
        return resp.json()

    except requests.exceptions.Timeout:
        log.error("Request to %s timed out after %ss", endpoint, timeout)
    except requests.exceptions.HTTPError as http_err:
        log.error("HTTP error while fetching runtime options: %s", http_err)
    except requests.exceptions.RequestException as req_err:
        log.error("Network error while fetching runtime options: %s", req_err)
    except ValueError:
        log.error("Failed to parse runtime options response as JSON")

    return None
