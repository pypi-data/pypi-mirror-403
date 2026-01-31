import requests
import os
import pandas as pd
import json
import base64
from bs4 import BeautifulSoup
import itertools
import copy

"""TERMite module from scibite-toolkit .

This module contains functionality to interact with the API from TERMite 6.x
both on local/on-prem setups and on SaaS instances.
It allows for the creation of TERMite requests, setting of various options,
and processing of responses to extract relevant information.
"""


class TermiteRequestBuilder():
    """
    Class for creating TERMite requests
    """

    def __init__(self):
        self.login_url = None
        self.session = requests.Session()
        self.url = 'http://localhost:9090/termite'
        self.input_file_path = ''
        self.payload = {"output": "json"}
        self.options = {}
        self.binary_content = None
        self.basic_auth = ()
        self.headers = {}
        self.verify_request = True

    def set_basic_auth(self, username='', password='', verification=True):
        """
        Pass basic authentication credentials.

        Parameters
        ----------
        username : str, optional
            Username to be used for basic authentication.
        password : str, optional
            Password to be used for basic authentication.
        verification : bool or str, optional
            How to perform verification on the requests that the TermiteRequestBuilder object will raise.
            If True, verify the SSL certificate using default paths.
            If str, use as the path to a CA_BUNDLE file or directory with certificates of trusted CAs.
            Cannot be set to False, as this would disable SSL verification and be insecure.

        """
        if verification is False:
            raise ValueError("SSL verification cannot be set to False for security reasons.")
        self.basic_auth = (username, password)
        self.verify_request = verification

    def set_oauth2(self, token_user, token_pw, verification=True,
                   token_address="https://api.healthcare.elsevier.com:443/token"):
        """Pass username and password for the Elsevier token API to generate an access token and add it to the request header.

        Parameters
        ----------
        token_user : str
            Username to access Elsevier token API. Specific to the hosting website.
        token_pw : str
            Password to access Elsevier token API. Specific to the hosting website.
        verification : bool or str, optional
            How to perform verification on the requests that the TermiteRequestBuilder object will raise.
            If True, verify the SSL certificate using default paths.
            If str, use as the path to a CA_BUNDLE file or directory with certificates of trusted CAs.
            Cannot be set to False, as this would disable SSL verification and be insecure.
        token_address : str, optional
            Address of the token API. Defaults to "https://api.healthcare.elsevier.com:443/token".
        """
        if verification is False:
            raise ValueError("SSL verification cannot be set to False for security reasons.")
        auth64 = base64.b64encode(bytearray(token_user + ":" + token_pw, 'utf8'))  # base64 encoded Username+password
        auth64 = auth64.decode('utf8')
        token_address = token_address or "https://api.healthcare.elsevier.com:443/token"
        req = self.session.post(token_address, data={"grant_type": "client_credentials"},
                                headers={"Authorization": "Basic " + auth64,
                                         "Content-Type": "application/x-www-form-urlencoded"})
        access_token = req.json()['access_token']
        self.headers = {"Authorization": "Bearer " + access_token}
        self.verify_request = verification

    def set_auth_saas(self, username, password, verification=True):
        """
        Authenticate with the SaaS API using a username and password.

        This method performs authentication against the SaaS server using credentials provided by the user.
        It executes the necessary authentication steps and stores the session information for subsequent API calls.

        Parameters
        ----------
        username : str
            Username to be used for SaaS authentication.
        password : str
            Password to be used for SaaS authentication.
        verification : bool or str, optional
            True by default, can also be a path to a CA bundle to use for verification. False is not allowed for security reasons

        Raises
        ------
        ValueError
            If verification is set to False.
        Exception
            If login_url is not set or is empty.

        Notes
        -----
        The authentication process involves multiple steps, including parsing the login response and handling redirects.
        The session information is saved for use in subsequent API requests.
        """
        if verification is False:
            raise ValueError("SSL verification cannot be set to False for security reasons.")
        # first login via username and password
        if self.login_url is None or self.login_url == "":
            raise Exception("Please set your provided login_url. If you do not know this URL, please reach out your "
                            "SciBite contacts.")
        login_resp = self.session.post(self.login_url,
                                       data={"grant_type": "password", "credentialId": "", "username": username,
                                             "password": password},
                                       headers={"Content-Type": "application/x-www-form-urlencoded"})
        # parse login response to find correct URL and then login again
        soup = BeautifulSoup(login_resp.text, "html.parser")
        form_data = soup.find('form')
        action_url = form_data['action']
        form_resp = self.session.post(action_url,
                                      data={"credentialId": "", "username": username, "password": password},
                                      headers={"Content-Type": "application/x-www-form-urlencoded"},
                                      allow_redirects=False
                                      )
        # get final authentication
        url3 = form_resp.headers.get("Location")
        resp = self.session.get(url3,
                                data={"credentialId": "", "username": username, "password": password},
                                headers={"Content-Type": "application/x-www-form-urlencoded"},
                                allow_redirects=False
                                )
        self.verify_request = verification

    def set_saas_login_url(self, login_url):
        """
        Set the SaaS login URL of the TERMite instance.

        Parameters
        ----------
        login_url : str
            The URL of the TERMite SaaS login endpoint.
        """
        self.login_url = login_url.rstrip("/")

    def set_url(self, url):
        """
        Set the URL of the TERMite instance.

        Parameters
        ----------
        url : str
            The URL of the TERMite instance to be used (e.g., 'http://localhost:9090/termite').

        """
        self.url = url.rstrip('/')

    def set_username(self, username):
        """
        Set the username for the user making the current termite request.

        Parameters
        ----------
        username : str
            Username of the user making the current termite request.
        """
        self.payload["username"] = username

    def set_usertoken(self, usertoken):
        """
        Set the usertoken for the user making the current termite request.

        Parameters
        ----------
        usertoken : str
            The usertoken of the user making the current termite request.
        """
        self.payload["usertoken"] = usertoken

    def set_bgjob(self, bgjob):
        """
        Set if a TERMite job should be handled as a background process.

        Parameters
        ----------
        bgjob : bool
            Specify if the TERMite job should be done in the background.
        """
        self.payload["bgjob"] = bgjob

    def set_bginfo(self, bginfo):
        """
        Set any information associated with the background task.

        Parameters
        ----------
        bginfo : str
            Information about the background task to be included in the payload.
        """
        self.payload["bginfo"] = bginfo

    def set_binary_content(self, input_file_path):
        """
        Set binary content for annotating file content.

        Parameters
        ----------
        input_file_path : str
            File path to the file to be sent to TERMite. Multiple files of the same type can be scanned at once if placed in a zip archive.
        """
        file_obj = open(input_file_path, 'rb')
        file_name = os.path.basename(input_file_path)
        self.binary_content = {"binary": (file_name, file_obj)}

    def set_text(self, string):
        """
        Set raw text for tagging.

        Parameters
        ----------
        string : str
            Text to be sent to TERMite, e.g., if looping through some file content.
        """
        self.payload["text"] = string

    def set_bundle(self, string):
        """
        Specify a TEXPress/TERMite bundle to use.

        Parameters
        ----------
        string : str
            Bundle name.
        """
        self.payload["bundle"] = string

    def set_df(self, dataframe):
        """
        Use this for tagging pandas dataframes.

        Parameters
        ----------
        dataframe : pandas.DataFrame
            The dataframe to be tagged.

        Notes
        -----
        The dataframe is transposed and converted to a dictionary, then formatted
        as TERMite input for annotation. Each row is treated as a document with
        sections corresponding to columns.

        Sets the payload 'text' and 'format' for TERMite API.
        """
        dataframe = dataframe.T
        df_dict = dataframe.to_dict()
        termite_input = []
        for row in df_dict:
            dic = {"sections": [], "uid": "Row_" + str(row)}
            for column in df_dict[row]:
                mini_dic = {"body": df_dict[row][column], "header": "", "partName": column}
                dic["sections"] += [mini_dic]
            termite_input += [dic]
        self.payload["text"] = json.dumps(termite_input)
        self.payload["format"] = "jsonc"

    def set_options(self, options_dict):
        """
        Bulk set multiple TERMite API options in a single call.

        Parameters
        ----------
        options_dict : dict
            Dictionary of options to be passed to TERMite.

        Notes
        -----
        If 'output' is present in `options_dict`, it will be set directly in the payload.
        All other options are concatenated into a single string and added to the 'opts' field.
        """
        if 'output' in options_dict:
            self.payload['output'] = options_dict['output']

        options = []
        for k, v in options_dict.items():
            options.append(k + "=" + str(v))
        option_string = '&'.join(options)
        if "opts" in self.payload:
            self.payload["opts"] = option_string + "&" + self.payload["opts"]
        else:
            self.payload["opts"] = option_string

    #######
    # individual options for applying the major TERMite settings
    #######

    def set_fuzzy(self, bool):
        """
        Enable fuzzy matching.

        Parameters
        ----------
        bool : bool
            Set to True to enable fuzzy matching.

        Notes
        -----
        Adds the 'fzy.promote' option to the TERMite request payload.
        """
        input = bool_to_string(bool)
        if "opts" in self.payload:
            self.payload["opts"] = "fzy.promote=" + input + "&" + self.payload["opts"]
        else:
            self.payload["opts"] = "fzy.promote=" + input

        self.payload["fuzzy"] = input

    def set_subsume(self, bool):
        """
        Set the 'subsume' option in the payload to control entity subsumption behavior.

        When enabled, only the longest entity hit is retained if an entity matches more than one dictionary.

        Parameters
        ----------
        bool : bool
            If True, enables subsume mode; otherwise disables it.
        """
        input = bool_to_string(bool)
        self.payload["subsume"] = input

    def set_entities(self, string):
        """
        Limit the type of entities to be annotated.

        Parameters
        ----------
        string : str
            Comma-separated string of entity types (VOCabs) to annotate, e.g., 'DRUG,GENE'.

        Notes
        -----
        This sets the 'entities' field in the TERMite request payload, restricting annotation
        to only the specified entity types. If not set, TERMite will annotate with all active VOCabs.
        """
        self.payload["entities"] = string

    def set_input_format(self, string):
        """
        Set the input format for TERMite annotation.

        Parameters
        ----------
        string : str
            The input format to be used, e.g., 'txt', 'medline.xml', 'node.xml', 'pdf', 'xlsx'.
        """
        self.payload["format"] = string

    def set_output_format(self, string):
        """
        Set the output format for TERMite annotation.

        Parameters
        ----------
        string : str
            Output format to be used, e.g., 'tsv', 'json', 'doc.json', 'doc.jsonx'.
        """
        self.payload["output"] = string

    def set_reject_minor_hits(self, bool):
        """
        Reject highly suspicious hits.

        Parameters
        ----------
        bool : bool
            If True, rejects hits flagged as highly suspicious (recommended).
        """
        input = bool_to_string(bool)
        if "opts" in self.payload:
            self.payload["opts"] = self.payload["opts"] + "&rejectMinorHits=" + input
        else:
            self.payload["opts"] = "rejectMinorHits=" + input

    def set_reject_ambiguous(self, bool):
        """
        Sets the option to automatically reject any hits flagged as ambiguous.

        This method updates the 'opts' field in the payload to include or modify the
        'rejectAmbig' parameter, which controls whether ambiguous hits are rejected.

        Parameters
        ----------
        bool : bool
            If True, ambiguous hits will be rejected. If False, ambiguous hits will not be rejected.
        """
        input = bool_to_string(bool)
        if "opts" in self.payload:
            self.payload["opts"] = self.payload["opts"] + "&rejectAmbig=" + input
        else:
            self.payload["opts"] = "rejectAmbig=" + input

    def set_max_docs(self, integer):
        """
        Set the maximum number of documents to scan when tagging.

        Limits the number of documents processed when tagging a zip file containing multiple documents,
        or when multiple document records are present in a single XML file (e.g., from a Medline XML export).

        Parameters
        ----------
        integer : int
            The maximum number of documents to annotate.
        """
        self.payload["maxDocs"] = integer

    def set_no_empty(self, bool):
        """
        Reject all documents where there were no hits.

        Parameters
        ----------
        bool : bool
            If True, do not return any documents with no hits.

        Notes
        -----
        This sets the 'noEmpty' option in the TERMite request payload, which filters out documents that do not contain any entity hits.
        """
        input = bool_to_string(bool)
        self.payload["noEmpty"] = input

    def execute(self, display_request=False, return_text=False):
        """
        Submit the configured request to the TERMite RESTful API.

        Parameters
        ----------
        display_request : bool, optional
            If True, prints the request URL and payload before submission.
        return_text : bool, optional
            If True, returns the raw response text instead of parsing JSON.

        Returns
        -------
        dict or str
            Parsed JSON response if output format is 'json', 'doc.json', or 'doc.jsonx' and `return_text` is False.
            Otherwise, returns the raw response text.

        Raises
        ------
        Exception
            If the request fails or the response status code is not 200.

        Notes
        -----
        - If `binary_content` is set, the request will include file data.
        - For non-binary requests, the payload is sent as form data.
        - Handles TERMite output formats and error reporting.
        """
        if display_request:
            print("REQUEST: ", self.url, self.payload)
        try:
            if self.binary_content:
                response = self.session.post(self.url, data=self.payload, files=self.binary_content, verify=self.verify_request)
            else:
                response = self.session.post(self.url, data=self.payload,
                                             headers={'content-type': 'application/x-www-form'
                                                                      '-urlencoded; '
                                                                      'charset=UTF-8'}, verify=self.verify_request)
        except Exception as e:
            return print(
                "Failed with the following error {}\n\nPlease check that TERMite can be accessed via the following URL {}\nAnd that the necessary credentials have been provided (done so using the set_basic_auth() function)".format(
                    e, self.url))

        if self.payload["output"] in ["json", "doc.json", "doc.jsonx"] and not return_text:
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(response.json()['RESP_META']['ERR_TRACE'])
        else:
            return response.text


def bool_to_string(bool):
    """
    Convert a boolean value to its lowercase string representation.

    Parameters
    ----------
    bool : bool
        Boolean value to be converted.

    Returns
    -------
    string : str
        Lowercase string representation of the boolean value.

    Notes
    -----
    This function is useful for preparing boolean values for APIs or configuration files
    that expect string inputs such as 'true' or 'false'.
    """
    string = str(bool)
    string = string.lower()

    return string


def annotate_files(url, input_file_path, options_dict):
    """
    Annotate files using a TERMite request.

    This function wraps the TERMite API to annotate individual files or a zip archive with specified options.

    Parameters
    ----------
    url : str
        URL of the TERMite instance.
    input_file_path : str
        Path to the file or zip archive to be annotated.
    options_dict : dict
        Dictionary of options to be used during annotation.

    Returns
    -------
    result : object
        Result of the TERMite annotation request. The type depends on the implementation of `TermiteRequestBuilder.execute()`.
    """
    t = TermiteRequestBuilder()
    t.set_url(url)
    t.set_binary_content(input_file_path)
    t.set_options(options_dict)
    result = t.execute()

    return result


def annotate_text(url, text, options_dict):
    """
    Annotate a string of text using a TERMite instance.

    Parameters
    ----------
    url : str
        The URL of the TERMite instance to send the annotation request to.
    text : str
        The text to be annotated.
    options_dict : dict
        Dictionary of options to configure the annotation request.

    Returns
    -------
    dict
        The result of the annotation request
    """
    t = TermiteRequestBuilder()
    t.set_url(url)
    t.set_text(text)
    t.set_options(options_dict)
    result = t.execute()

    return result


def process_payload(filtered_hits, response_payload, filter_entity_types, doc_id='', reject_ambig=True, score_cutoff=0,
                    remove_subsumed=True):
    """
    Filter and aggregate TERMite entity hits from a response payload.

    Parameters
    ----------
    filtered_hits : dict
        Dictionary to accumulate filtered entity hits.
    response_payload : dict
        TERMite JSON response payload containing entity hits.
    filter_entity_types : list or set
        Entity types to include in the output.
    doc_id : str, optional
        Document identifier for the current payload.
    reject_ambig : bool, optional
        If True, exclude ambiguous hits (where 'nonambigsyns' == 0).
    score_cutoff : int or float, optional
        Minimum relevance score required for a hit to be included.
    remove_subsumed : bool, optional
        If True, exclude subsumed hits.

    Returns
    -------
    dict
        Dictionary of filtered entity hits, aggregated by entity type and ID.

    Notes
    -----
    - Aggregates hit counts and document occurrences for each entity.
    - Updates maximum relevance score for repeated entities.
    - Only entities matching `filter_entity_types` are included.
    - Handles both ambiguous and subsumed hit filtering.
    """
    for entity_type, entity_hits in response_payload.items():
        if entity_type in filter_entity_types:
            for entity_hit in entity_hits:
                nonambigsyns = entity_hit["nonambigsyns"]
                entity_score = entity_hit["score"]
                if reject_ambig == True:
                    if nonambigsyns == 0:
                        continue
                if "subsume" in entity_hit and remove_subsumed == True:
                    if True in entity_hit["subsume"]:
                        continue
                if entity_hit["score"] >= score_cutoff:
                    hit_id = entity_hit["hitID"]
                    entity_id = entity_type + '$' + hit_id
                    entity_name = entity_hit["name"]
                    hit_count = entity_hit["hitCount"]
                    if entity_id in filtered_hits:
                        filtered_hits[entity_id]["hit_count"] += hit_count
                        filtered_hits[entity_id]["doc_count"] += 1
                        filtered_hits[entity_id]["doc_id"].append(doc_id)
                        if entity_score > filtered_hits[entity_id]["max_relevance_score"]:
                            filtered_hits[entity_id]["max_relevance_score"] = entity_score
                    else:
                        filtered_hits[entity_id] = {"id": hit_id, "type": entity_type, "name": entity_name,
                                                    "hit_count": hit_count, "max_relevance_score": entity_score,
                                                    "doc_id": [doc_id], "doc_count": 1}

    return filtered_hits


def get_entity_hits_from_json(termite_json_response, filter_entity_types, reject_ambig=True, score_cutoff=0):
    """
    Extract entity hits from TERMite JSON response.

    Parameters
    ----------
    termite_json_response : dict
        JSON object returned from TERMite containing entity hits.
    filter_entity_types : list or set
        List or set of entity types to filter (e.g., ['GENE', 'DRUG']).
    reject_ambig : bool, optional
        If True, exclude ambiguous hits (default is True).
    score_cutoff : int or float, optional
        Minimum relevance score required for a hit to be included (default is 0).

    Returns
    -------
    filtered_hits : dict
        Dictionary of filtered entity hits aggregated by entity type and ID.

    Notes
    -----
    - Handles both single-document and multi-document TERMite JSON responses.
    - Aggregates hit counts and document occurrences for each entity.
    - Only entities matching `filter_entity_types` are included.
    - Uses `process_payload` for filtering and aggregation.
    """
    filtered_hits = {}
    if "RESP_MULTIDOC_PAYLOAD" in termite_json_response:
        doc_results = termite_json_response["RESP_MULTIDOC_PAYLOAD"]
        for doc_id, response_payload in doc_results.items():
            filtered_hits = process_payload(filtered_hits, response_payload, filter_entity_types,
                                            reject_ambig=reject_ambig, score_cutoff=score_cutoff, doc_id=doc_id)

    elif "RESP_PAYLOAD" in termite_json_response:
        response_payload = termite_json_response["RESP_PAYLOAD"]
        filtered_hits = process_payload(filtered_hits, response_payload, filter_entity_types, reject_ambig=reject_ambig,
                                        score_cutoff=score_cutoff)

    return filtered_hits


def docjsonx_payload_records(docjsonx_response_payload, reject_ambig=True, score_cutoff=0, remove_subsumed=True):
    """
    Parse TERMite doc.JSONx payload into records, with filtering options.

    Parameters
    ----------
    docjsonx_response_payload : list of dict
        List of document records from doc.JSONx TERMite response.
    reject_ambig : bool, optional
        If True, exclude ambiguous hits (where 'nonambigsyns' == 0). Default is True.
    score_cutoff : int or float, optional
        Minimum relevance score required for a hit to be included. Default is 0.
    remove_subsumed : bool, optional
        If True, exclude subsumed hits. Default is True.

    Returns
    -------
    payload : list of dict
        List of entity hit records, each merged with its document metadata.

    """
    payload = []
    for doc in docjsonx_response_payload:
        if 'termiteTags' in doc.keys():
            for entity_hit in doc['termiteTags']:
                # update document record with entity hit record
                entity_hit.update(doc)
                del entity_hit['termiteTags']

                # filtering
                if reject_ambig is True and entity_hit['nonambigsyns'] == 0:
                    continue
                if "subsume" in entity_hit and remove_subsumed is True:
                    if True in entity_hit['subsume']:
                        continue
                if entity_hit['score'] >= score_cutoff:
                    payload.append(entity_hit)

    return (payload)


def json_payload_records(response_payload, reject_ambig=True, score_cutoff=0, remove_subsumed=True):
    """
    Parse TERMite JSON payload into a list of entity hit records, with filtering options.

    Parameters
    ----------
    response_payload : dict
        Dictionary containing entity types and their corresponding hits from a TERMite JSON response.
    reject_ambig : bool, optional
        If True, exclude ambiguous hits (where 'nonambigsyns' == 0). Default is True.
    score_cutoff : int or float, optional
        Minimum relevance score required for a hit to be included. Default is 0.
    remove_subsumed : bool, optional
        If True, exclude subsumed hits. Default is True.

    Returns
    -------
    payload : list of dict
        List of entity hit records that passed the filtering criteria.
    """
    payload = []
    for entity_type, entity_hits in response_payload.items():
        for entity_hit in entity_hits:
            if reject_ambig is True and entity_hit['nonambigsyns'] == 0:
                continue
            if "subsume" in entity_hit and remove_subsumed is True:
                if True in entity_hit['subsume']:
                    continue
            if entity_hit['score'] >= score_cutoff:
                payload.append(entity_hit)

    return (payload)


def payload_records(termiteResponse, reject_ambig=True, score_cutoff=0, remove_subsumed=True):
    """
    Parse TERMite JSON or doc.JSONx output into a list of entity hit records.

    Parameters
    ----------
    termiteResponse : dict or list
        TERMite response in JSON or doc.JSONx format.
    reject_ambig : bool, optional
        If True, exclude ambiguous hits (where 'nonambigsyns' == 0). Default is True.
    score_cutoff : int or float, optional
        Minimum relevance score required for a hit to be included. Default is 0.
    remove_subsumed : bool, optional
        If True, exclude subsumed hits. Default is True.

    Returns
    -------
    payload : list of dict
        List of entity hit records extracted from the TERMite response.
    """
    payload = []

    if "RESP_MULTIDOC_PAYLOAD" in termiteResponse:
        for docID, termite_hits in termiteResponse['RESP_MULTIDOC_PAYLOAD'].items():
            payload = payload + json_payload_records(
                termite_hits,
                reject_ambig=reject_ambig,
                score_cutoff=score_cutoff,
                remove_subsumed=remove_subsumed
            )
    elif "RESP_PAYLOAD" in termiteResponse:
        payload = payload + json_payload_records(termiteResponse['RESP_PAYLOAD'], reject_ambig=reject_ambig,
                                                 score_cutoff=score_cutoff, remove_subsumed=remove_subsumed)

    else:
        payload = docjsonx_payload_records(termiteResponse, reject_ambig=reject_ambig,
                                           score_cutoff=score_cutoff, remove_subsumed=remove_subsumed)

    return (payload)


def get_termite_dataframe(termiteResponse, cols_to_add="", reject_ambig=True, score_cutoff=0,
                          remove_subsumed=True):
    """
    Parse TERMite JSON or doc.JSONx response into a pandas DataFrame of entity hits.

    Parameters
    ----------
    termiteResponse : dict or list
        JSON or doc.JSONx response from TERMite.
    cols_to_add : str, optional
        Comma-separated list of additional fields to include in the output DataFrame.
    reject_ambig : bool, default True
        If True, exclude ambiguous hits (where 'nonambigsyns' == 0).
    score_cutoff : int or float, default 0
        Minimum relevance score required for a hit to be included.
    remove_subsumed : bool, default True
        If True, exclude subsumed hits.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing TERMite hits with columns:
        ['docID', 'entityType', 'hitID', 'name', 'score', 'realSynList', 'totnosyns',
         'nonambigsyns', 'frag_vector_array', 'hitCount'] plus any additional columns specified.

    Notes
    -----
    - If no hits are found, returns an empty DataFrame with the specified columns.
    - Additional columns must exist in the TERMite response payload; otherwise, a KeyError is printed.
    - Filtering is applied for ambiguous, subsumed, and low-relevance hits according to the parameters.
    """
    payload = payload_records(termiteResponse, reject_ambig=reject_ambig,
                              score_cutoff=score_cutoff, remove_subsumed=remove_subsumed)

    df = pd.DataFrame(payload)

    cols = ["docID", "entityType", "hitID", "name", "score", "realSynList", "totnosyns", "nonambigsyns",
            "frag_vector_array", "hitCount"]

    if cols_to_add:
        cols_to_add = cols_to_add.replace(" ", "").split(",")
        try:
            cols = cols + cols_to_add
            if df.empty:
                return pd.DataFrame(columns=cols)
            return (df[cols])
        except KeyError as e:
            print("Invalid column selection.", e)
    else:
        if df.empty:
            return pd.DataFrame(columns=cols)
        return (df[cols])


def get_entity_hits_from_docjsonx(termite_response, filter_entity_types):
    """
    Extract filtered entity hits from a TERMite doc.JSONx response.

    Parameters
    ----------
    termite_response : list of dict
        TERMite doc.JSONx response payload, typically a list of document records.
    filter_entity_types : list or set
        List or set of entity types (VOCabs) to include in the output.

    Returns
    -------
    dict
        Dictionary of filtered entity hits, aggregated by entity type and ID.
        Each key is of the form 'entityType$hitID', and each value is a dict with:
        - id : str
            The hit ID.
        - type : str
            The entity type (VOCab).
        - name : str
            The preferred entity name.
        - hit_count : int
            Total number of hits for this entity.
        - max_relevance_score : float
            Maximum relevance score observed for this entity.
        - doc_id : list of str
            List of document IDs where the entity was found.
        - doc_count : int
            Number of unique documents containing the entity.

    Notes
    -----
    - Aggregates hit counts and document occurrences for each entity.
    - Only entities matching `filter_entity_types` are included.
    - Handles multi-document doc.JSONx responses.
    """
    processed = docjsonx_payload_records(termite_response)

    filtered_hits = {}
    for entity_hit in processed:
        hit_id = entity_hit['hitID']
        entityType = entity_hit['entityType']
        entity_id = entityType + '$' + hit_id
        entity_name = entity_hit['name']
        hit_count = entity_hit['hitCount']
        entity_score = entity_hit['score']
        doc_id = entity_hit['docID']

        if entityType in filter_entity_types:
            if entity_id in filtered_hits:
                filtered_hits[entity_id]['hit_count'] += hit_count
                if entity_score > filtered_hits[entity_id]['max_relevance_score']:
                    filtered_hits[entity_id]['max_relevance_score'] = entity_score
                if doc_id not in filtered_hits[entity_id]['doc_id']:
                    filtered_hits[entity_id]['doc_id'].append(doc_id)
                    filtered_hits[entity_id]['doc_count'] += 1
            else:
                filtered_hits[entity_id] = {"id": hit_id, "type": entityType, "name": entity_name,
                                            "hit_count": hit_count,
                                            "max_relevance_score": entity_score, "doc_id": [doc_id], "doc_count": 1}

    return (filtered_hits)


def termite_entity_hits_df(termite_response, filter_entity_types):
    """
    Parse TERMite JSON or doc.JSONx response and return a summary DataFrame of entity hits.

    Parameters
    ----------
    termite_response : dict or list
        TERMite response in JSON or doc.JSONx format.
    filter_entity_types : list of str
        List of entity types (VOCabs) to include as columns in the output DataFrame.

    Returns
    -------
    pandas.DataFrame
        DataFrame where each row corresponds to a hit, with columns for 'docID', each entity type, and its ID.

    Notes
    -----
    - The DataFrame columns are: 'docID', <entityType>, <entityType>_ID for each entity in `filter_entity_types`.
    - Only hits matching the specified entity types are included.
    - If no hits are found, returns an empty DataFrame with the specified columns.
    """
    payload = payload_records(termite_response)

    # Magic formula that adds vocab ID header right after each vocab
    entitieswid = ['docID',
                   *sum(zip(filter_entity_types, [entity_type + '_ID' for entity_type in filter_entity_types]), ())]
    # Initiate empty list that will be populated with one dictionary/row
    df_list = []

    # Loop through hits
    for hit in payload:
        # Populate dictionary with relevant entity hits
        dic = {header: '' for header in entitieswid}
        if hit['entityType'] in filter_entity_types:
            dic['docID'] = hit['docID']
            dic[hit['entityType']] = hit['name']
            dic[hit['entityType'] + '_ID'] = hit['hitID']
            df_list += [dic]

    df = pd.DataFrame(df_list, columns=entitieswid)
    return df


def all_entities(termite_response):
    """
    Parses a TERMite response and returns a list of unique VOCabs with hits.

    Parameters
    ----------
    termite_response : dict or list
        TERMite response in JSON or doc.JSONx format.

    Returns
    -------
    list of str
        List of unique VOCabs found in the TERMite response.

    Notes
    -----
    The function relies on `payload_records(termite_response)` to extract entity hits.
    Only unique VOCabs are included in the returned list.
    """
    payload = payload_records(termite_response)

    entities_used = []
    for entity_hit in payload:
        if entity_hit['entityType'] not in entities_used:
            entities_used.append(entity_hit['entityType'])

    return (entities_used)


def all_entities_df(termite_response):
    """
    Parse TERMite JSON or doc.JSONx response into a summary DataFrame of VOCabs.

    Parameters
    ----------
    termite_response : dict or list
        TERMite response in JSON or doc.JSONx format.

    Returns
    -------
    pandas.DataFrame
        DataFrame summarizing all agregated hits, with each row representing a unique VOCab.
    """
    # identify all entity hit types in the text
    entities_used = all_entities(termite_response)
    entities_string = (',').join(entities_used)

    if "RESP_MULTIDOC_PAYLOAD" in termite_response or "RESP_PAYLOAD" in termite_response:
        filtered_hits = get_entity_hits_from_json(termite_response, entities_string)
    else:
        filtered_hits = get_entity_hits_from_docjsonx(termite_response, entities_string)

    df = pd.DataFrame(filtered_hits).T

    return (df)


def entity_freq(termite_response):
    """
    Parse TERMite JSON or doc.JSONx response and return a DataFrame of entity type frequencies.

    Parameters
    ----------
    termite_response : dict or list
        TERMite response in JSON or doc.JSONx format.

    Returns
    -------
    pandas.DataFrame
        DataFrame with entity types as the index and their frequency counts as values.

    Notes
    -----
    - The function counts occurrences of each entity type found in the TERMite response.
    - If no hits are found, returns an empty DataFrame.
    """
    df = get_termite_dataframe(termite_response)

    values = pd.value_counts(df['entityType'])
    values = pd.DataFrame(values)
    return (values)


def top_hits_df(termite_response, selection=10, entity_subset=None, include_docs=False):
    """
    Return a DataFrame of the most frequent entity hits from a TERMite response.

    Parameters
    ----------
    termite_response : dict or list
        JSON or doc.JSONx TERMite response.
    selection : int, optional
        Number of top hits to return (default is 10).
    entity_subset : str or None, optional
        Comma-separated list of entity types (VOCabs) to include. If None, all are included.
    include_docs : bool, optional
        If True, include document information in the output DataFrame.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the most frequent entity hits, sorted by hit count.

    Notes
    -----
    - For multi-document responses, document IDs can be included if `include_docs` is True.
    - The columns returned depend on the value of `include_docs`.
    - Filtering by entity type is performed if `entity_subset` is provided.
    """
    # get entity hits and sort by hit_count
    df = get_termite_dataframe(termite_response)
    df.sort_values(by=['hitCount'], ascending=False, inplace=True)
    df2 = df.copy()

    # select relevant columns and filtering
    if include_docs is True:
        columns = [3, 5, 6, 2, 1]
    else:
        columns = [3, 5, 6, 2]
    if entity_subset is not None:
        entity_subset = entity_subset.replace(" ", "").split(",")
        criteria = df2['entityType'].isin(entity_subset)
        return (df2[criteria].iloc[0:selection, columns])
    else:
        return (df2.iloc[0:selection, columns])


def markup(
        docjsonx,
        normalisation='id',
        substitute=True,
        wrap=False,
        wrapChars=('{!', '!}'),
        vocabs=None,
        labels=None,
        replacementDict=None
):
    """
    Process TERMite docjsonx output and normalise identified entity hits in the original text.

    Parameters
    ----------
    docjsonx : str or list of dict
        JSON string or object generated by TERMite (must be docjsonx format).
    normalisation : {'id', 'type', 'name', 'typeplusname', 'typeplusid'}, optional
        Type of normalisation to substitute/add for each entity hit.
    substitute : bool, optional
        If True, replace the found term with the normalised value; if False, add normalisation alongside.
    wrap : bool, optional
        If True, wrap found hits with specified bookend characters.
    wrapChars : tuple of str, optional
        Tuple of length 2 containing strings to insert at start/end of found hits.
    vocabs : list of str, optional
        List of vocabularies to be substituted, ordered by priority. If None, all found vocabs are used.
    labels : {'word', 'char'}, optional
        If specified, controls labelling granularity for markup (word or character).
    replacementDict : dict, optional
        Dictionary mapping <VOCAB> to replacement string. Supports '~ID~', '~TYPE~', and '~NAME~' placeholders.
        Example: {'GENE': 'ENTITY_~TYPE~_~ID~'} results in BRCA1 -> ENTITY_GENE_BRCA1.
        If provided, supersedes normalisation.

    Returns
    -------
    dict
        Dictionary mapping document indices to their processed text under the key 'termited_text'.

    Notes
    -----
    - Only valid normalisation types are accepted.
    - If `vocabs` is provided, it determines substitution priority in case of overlapping hits.
    - If `replacementDict` is used, it overrides the normalisation parameter.
    - The function supports both string and object docjsonx input.
    - If no hits are found, the original text is returned.
    """

    results = {}

    validTypes = ['id', 'type', 'name', 'typeplusname', 'typeplusid']
    if normalisation not in validTypes:
        raise ValueError(
            'Invalid normalisation requested. Valid options are \'id\', \'name\', \'type\', \'typeplusname\' and \'tyeplusid\'.'
        )

    if len(wrapChars) != 2 or not all(isinstance(wrapping, str) for wrapping in wrapChars):
        raise ValueError('wrapChars must be a tuple of length 2, containing strings.')

    if labels:
        if labels not in ['word', 'char']:
            raise ValueError('labels, if specified, must be either \'word\' or \'char\'')

    hierarchy = {}
    if vocabs:
        for idx, vocab in enumerate(vocabs):
            hierarchy[vocab] = idx

    if isinstance(docjsonx, str):
        json_docs = json.loads(docjsonx)
    else:
        json_docs = docjsonx

    for doc_idx, doc in enumerate(json_docs):
        text = doc['body']

        try:
            substitutions = get_hits(doc['termiteTags'], hierarchy=hierarchy, vocabs=vocabs)
        except KeyError:
            results[doc_idx] = {'termited_text': text}
            continue

        if len(substitutions) > 0:
            substitutions.sort(key=lambda x: x['startLoc'])
            substitutions = reversed(substitutions)

        if wrap:
            prefix = wrapChars[0]
            postfix = wrapChars[1]
        else:
            prefix, postfix = '', ''

        for sub in substitutions:
            subtext = ''
            if replacementDict:
                subtext = replacementDict[sub['entityType']].replace(
                    '~TYPE~', sub['entityType']
                ).replace(
                    '~ID~', sub['entityID']
                ).replace(
                    '~NAME~', sub['entityName']
                )
            elif normalisation == 'id':
                subtext = '_'.join([sub['entityType'], sub['entityID']])
                if not substitute:
                    subtext += ' %s' % text[sub['startLoc']:sub['endLoc']]
            elif normalisation == 'type':
                subtext = sub['entityType']
                if not substitute:
                    subtext += ' %s' % text[sub['startLoc']:sub['endLoc']]
            elif normalisation == 'name':
                subtext = sub['entityName']
                if not substitute:
                    subtext += ' %s' % text[sub['startLoc']:sub['endLoc']]
            elif normalisation == 'typeplusname':
                subtext = '%s %s' % (sub['entityType'], sub['entityName'])
                if not substitute:
                    subtext += ' %s' % text[sub['startLoc']:sub['endLoc']]
            elif normalisation == 'typeplusid':
                subtext = '%s %s' % (
                    sub['entityType'],
                    '_'.join([sub['entityType'], sub['entityID']])
                )

                if not substitute:
                    subtext += ' %s' % text[sub['startLoc']:sub['endLoc']]

            text = text[:sub['startLoc']] + prefix + subtext + postfix + text[sub['endLoc']:]

        results[doc_idx] = {'termited_text': text}

    return results


def pairwise_markup(
        docjsonx,
        pairwise_types_a,
        pairwise_types_b,
        normalisation='id',
        wrap=False,
        wrapChars=('{!', '!}'),
        substitute=True,
        replacementDict=None
):
    '''
    Receives TERMite docjsonx, returns a dictionary with pairwise TERMited substitutions.

    :param docjsonx: JSON string generated by TERMite. Must be docjsonx.
    :param array(str) pairwise_types_a: list of VOCABs to be found on one side of the pairwise relationships
    :param array(str) pairwise_types_b: list of VOCABS to be found on the other side of the pairwise relationships
    :param str normalisation: Type of normalisation to substitute/add (must be 'id', 'type', 'name', 'typeplusname' or 'typeplusid')
    :param bool substitute: Whether to replace the found term (or add normalisation alongside)
    :param bool wrap: Whether to wrap found hits with 'bookends'
    :param tuple(str) wrapChars: Tuple of length 2, containing strings to insert at start/end of found hits
    :param dict replacementDict: Dictionary with <VOCAB>:<string_to_replace_hits_in_vocab>. '~ID~' will be replaced with the entity id,
    and '~TYPE~' will be replaced with the vocab name. Example: {'GENE':'ENTITY_~TYPE~_~ID~'} would result in BRCA1 -> ENTITY_GENE_BRCA1
    replacementDict supercedes normalisation. ~NAME~ can also be used to get the preferred name.
    :return dict: a dictionary containing entity combinations to their respective masked sentences
    '''

    output = {}
    ent_id_to_hit_json = {}
    pairwise_ids_a = []
    pairwise_ids_b = []
    try:
        for hit in docjsonx[0]['termiteTags']:
            if hit['entityType'] in pairwise_types_a:
                pairwise_ids_a.append(hit['hitID'])
            elif hit['entityType'] in pairwise_types_b:
                pairwise_ids_b.append(hit['hitID'])
            else:
                continue

            ent_id_to_hit_json[hit['hitID']] = hit

    except TypeError:
        raise('Error retrieving results from TERMite')

    except KeyError:
        pass

    combos = itertools.product(pairwise_ids_a, pairwise_ids_b)

    for combo in combos:
        termiteTags = [ent_id_to_hit_json[combo[0]], ent_id_to_hit_json[combo[1]]]
        docjsonx[0]['termiteTags'] = termiteTags
        output[combo] = markup(
            docjsonx,
            vocabs=pairwise_types_a+pairwise_types_b,
            normalisation=normalisation,
            wrap=wrap,
            wrapChars=wrapChars,
            substitute=substitute,
            replacementDict=replacementDict
        )[0]['termited_text']
    return output


def text_markup(
        text,
        termiteAddr='http://localhost:9090/termite',
        vocabs=['GENE', 'INDICATION', 'DRUG'],
        normalisation='id',
        wrap=False,
        wrapChars=('{!', '!}'),
        substitute=True,
        replacementDict=None,
        termite_http_user=None,
        termite_http_pass=None,
        include_json=False
):
    '''
    Receives plain text, returns text with TERMited substitutions.

    :param str text: Text in which to markup entities
    :param str normalisation: Type of normalisation to substitute/add (must be 'id', 'type', 'name', 'typeplusname' or 'typeplusid')
    :param bool substitute: Whether to replace the found term (or add normalisation alongside)
    :param bool wrap: Whether to wrap found hits with 'bookends'
    :param tuple(str) wrapChars: Tuple of length 2, containing strings to insert at start/end of found hits
    :param array(str) vocabs: List of vocabs to be substituted, ordered by priority. These vocabs MUST be in the TERMite results. If left
    empty, all vocabs found will be used with random priority where overlaps are found.
    :param dict replacementDict: Dictionary with <VOCAB>:<string_to_replace_hits_in_vocab>. '~ID~' will be replaced with the entity id,
    and '~TYPE~' will be replaced with the vocab name. Example: {'GENE':'ENTITY_~TYPE~_~ID~'} would result in BRCA1 -> ENTITY_GENE_BRCA1
    replacementDict supercedes normalisation. ~NAME~ can also be used to get the preferred name.
    :return str:
    '''

    termite_handle = TermiteRequestBuilder()
    termite_handle.set_url(termiteAddr)
    termite_handle.set_text(text)
    termite_handle.set_entities(','.join(vocabs))
    termite_handle.set_subsume(True)
    termite_handle.set_input_format("txt")
    termite_handle.set_output_format("doc.jsonx")

    if termite_http_pass:
        termite_handle.set_basic_auth(
            termite_http_user,
            termite_http_pass,
            verification=False
        )

    docjsonx = termite_handle.execute()
    # print(docjsonx)

    if include_json:
        return markup(
            docjsonx,
            vocabs=vocabs,
            normalisation=normalisation,
            wrap=wrap,
            wrapChars=wrapChars,
            substitute=substitute,
            replacementDict=replacementDict
        )[0]['termited_text'], docjsonx

    return markup(
        docjsonx,
        vocabs=vocabs,
        normalisation=normalisation,
        wrap=wrap,
        wrapChars=wrapChars,
        substitute=substitute,
        replacementDict=replacementDict
    )[0]['termited_text']


def pairwise_text_markup(
        text,
        pairwise_types_a,
        pairwise_types_b,
        termiteAddr='http://localhost:9090/termite',
        normalisation='id',
        wrap=False,
        wrapChars=('{!', '!}'),
        substitute=True,
        replacementDict=None,
        termite_http_user=None,
        termite_http_pass=None,
        include_json=False
):
    '''
    Receives plain text, returns a dictionary with pairwise TERMited substitutions.

    :param str text: Text in which to markup entities
    :param array(str) pairwise_types_a: list of VOCABs to be found on one side of the pairwise relationships
    :param array(str) pairwise_types_b: list of VOCABS to be found on the other side of the pairwise relationships
    :param str normalisation: Type of normalisation to substitute/add (must be 'id', 'type', 'name', 'typeplusname' or 'typeplusid')
    :param bool substitute: Whether to replace the found term (or add normalisation alongside)
    :param bool wrap: Whether to wrap found hits with 'bookends'
    :param tuple(str) wrapChars: Tuple of length 2, containing strings to insert at start/end of found hits
    :param dict replacementDict: Dictionary with <VOCAB>:<string_to_replace_hits_in_vocab>. '~ID~' will be replaced with the entity id,
    and '~TYPE~' will be replaced with the vocab name. Example: {'GENE':'ENTITY_~TYPE~_~ID~'} would result in BRCA1 -> ENTITY_GENE_BRCA1
    replacementDict supercedes normalisation. ~NAME~ can also be used to get the preferred name.
    :return dict: a dictionary containing entity combinations to their respective masked sentences
    '''
    t = TermiteRequestBuilder()
    t.set_url(termiteAddr)
    t.set_text(text)
    t.set_entities(','.join(pairwise_types_a+pairwise_types_b))
    t.set_subsume(True)
    t.set_input_format("txt")
    t.set_output_format("doc.jsonx")
    if termite_http_pass:
        t.set_basic_auth(termite_http_user, termite_http_pass, verification=False)
    docjsonx = t.execute()

    if include_json:
        return pairwise_markup(
            docjsonx,
            pairwise_types_a=pairwise_types_a,
            pairwise_types_b=pairwise_types_b,
            normalisation=normalisation,
            wrap=wrap,
            wrapChars=wrapChars,
            substitute=substitute,
            replacementDict=replacementDict
        ), docjsonx

    return pairwise_markup(
        docjsonx,
        pairwise_types_a=pairwise_types_a,
        pairwise_types_b=pairwise_types_b,
        normalisation=normalisation,
        wrap=wrap,
        wrapChars=wrapChars,
        substitute=substitute,
        replacementDict=replacementDict
    )

def get_hits(termiteTags, hierarchy=None, vocabs=None):
    """
    Collects non-overlapping TERMite entity hits, prioritizing by vocabulary hierarchy.

    Parameters
    ----------
    termiteTags : list of dict
        List of TERMite hit records, each containing entity information and location data.
    hierarchy : dict, optional
        Dictionary mapping entity types (VOCabs) to their priority order. Used to resolve overlapping hits.
        If not provided, hierarchy is built from the order of appearance in `termiteTags`.
    vocabs : list of str, optional
        List of VOCabs to include, ordered by substitution priority. If None, all found VOCabs are used.

    Returns
    -------
    hits : list of dict
        List of non-overlapping entity hit dictionaries, each containing:
        - 'entityType': str, the VOCab type
        - 'entityID': str, the entity identifier
        - 'entityName': str, the preferred entity name
        - 'startLoc': int, start character index of the hit
        - 'endLoc': int, end character index of the hit

    Notes
    -----
    - Overlapping hits are resolved by VOCab priority: only the highest-priority hit is retained.
    - Handles both TERMite 6.3 and 6.4 output formats for hit location data.
    - Subsumed hits are excluded.
    - If `vocabs` is provided, only hits matching those VOCabs are considered.
    """
    hits = []
    for hit in termiteTags:
        if not vocabs:
            if hit['entityType'] not in hierarchy:
                hierarchy[hit['entityType']] = len(hierarchy)
        else:
            if hit['entityType'] not in vocabs:
                continue

        if 'fls' in hit['exact_array'][0]: #TERMite 6.3...
            hitLocs, subsumeStates = hit['exact_array'], hit['subsume']
        else: #TERMite 6.4...
            hitLocs = []
            subsumeStates = []
            for hit_array in hit['exact_array']:
                hitLocs.append({'fls': [hit_array['sentence'], hit_array['start'], hit_array['end']]})
                subsumeStates.append(hit_array['subsumed'])

        assert len(hitLocs) == len(subsumeStates)

        for idx, hitLoc in enumerate(hitLocs):
            if hitLoc['fls'][0] < 1:
                continue
            hitInfo = {}
            hitInfo['entityType'], hitInfo['entityID'], hitInfo['entityName'] = hit['entityType'], hit['hitID'], hit[
                'name']
            breakBool = False
            hitInfo['startLoc'], hitInfo['endLoc'] = hitLoc['fls'][1], hitLoc['fls'][2]
            if subsumeStates[idx] == False:  # If hit is not subsumed...
                for hitIdx, hit_ in enumerate(hits):
                    # Compare to already found hits to check there's no conflict
                    if ((hit_['endLoc'] >= hitInfo['startLoc'] and hit_['endLoc'] <= hitInfo['endLoc']) or
                            (hit_['startLoc'] >= hitInfo['startLoc'] and hit_['startLoc'] <= hitInfo['endLoc'])):
                        # If they overlap, check their position in the hierarchy
                        if hierarchy[hit_['entityType']] >= hierarchy[hitInfo['entityType']]:
                            del hits[hitIdx]
                            break
                        else:
                            breakBool = True
                            break
            if not breakBool:
                hits.append(hitInfo)
    return hits
