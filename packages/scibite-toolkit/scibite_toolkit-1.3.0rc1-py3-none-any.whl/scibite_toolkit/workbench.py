import configparser
import requests
import os
import time
import pandas as pd
from io import StringIO


class WorkbenchRequestBuilder:
    """
    Class for creating Workbench Requests
    """

    def __init__(self):
        self.session = requests.Session()
        self.url = ''
        self.file_input = None
        self.headers = {}
        self.verify_request = False
        self.dataset_name = ''
        self.dataset_id = ''
        self.dataset_description = ''
        self.file_ext = ''
        self.user_info = {}
        self.termite_config = ''

    def set_oauth2(self, client_id, username, password, verification=True):
        """
        Pass username and password for the Workbench token api
        It then uses these credentials to generate an access token and adds
        this to the request header.
        We will also gather the user's info to pass to subsequent API calls

        Parameters
        ----------
        client_id : str
            client_id to access the token api
        username : str
            scibite search username
        password : str
            scibite search password for username above
        """
        token_address = self.url + "/auth/realms/Scibite/protocol/openid-connect/token"

        req = requests.post(token_address, data={"grant_type": "password", "client_id": client_id, "username": username,
                                                 "password": password},
                            headers={"Content-Type": "application/x-www-form-urlencoded"})
        access_token = req.json()["access_token"]
        user_info_url = "{}/api/users/me/internal".format(self.url.rstrip("/"))
        self.headers = {"Authorization": "Bearer " + access_token}

        user_info_request = requests.get(user_info_url, headers=self.headers)
        user_info_json = user_info_request.json()
        user_info_json["memberOf"][0]["group"]["userGroup"] = 'true'
        self.user_info = user_info_json
        self.verify_request = verification

    def set_apikey(self, force_regeneration=False, max_age=30):
        """
        Retrieves or generates an API key for the authenticated user. If an API key does not exist
        or force regeneration is requested, a new API key is generated.

        Parameters
        ----------
        force_regeneration : bool, optional
            If set to True, a new API key will be generated regardless of existing keys (default is False).
        max_age : int, optional
            Maximum token validity in days for new API keys (default is 30).

        Raises
        ------
        requests.exceptions.HTTPError
            If the HTTP request returned an unsuccessful status code.
        Exception
            For any other exceptions that occur during the request.

        Examples
        --------
        >>> self.set_apikey(force_regeneration=True, max_age=60)
        """
        get_apikey_endpoint = f"{self.url}/api/users/me/api-key"
        generate_apikey_endpoint = f"{self.url}/api/users/me/api-key?max_age={max_age}"

        try:
            if force_regeneration:
                response = requests.post(generate_apikey_endpoint, headers=self.headers)
                response.raise_for_status()
                api_key = response.json().get('apiKey')
                self.headers.update({"Authorization": f"Bearer {api_key}"})

            # Try to get the existing API key
            response = requests.get(get_apikey_endpoint, headers=self.headers)
            response.raise_for_status()
            api_key = response.json().get('apiKey')

            if not api_key:
                # If no API key exists, generate one
                response = requests.post(generate_apikey_endpoint, headers=self.headers)
                response.raise_for_status()
                api_key = response.json().get('apiKey')

            self.headers.update({"Authorization": f"Bearer {api_key}"})

        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                print("Error: User is not authenticated. Your token may have expired.")
            else:
                print(f"HTTP error occurred: {http_err}")
        except Exception as err:
            print(f"An error occurred: {err}")

    def set_url(self, url):
        """
        Set the URL of the Workbench instance

        Parameters
        ----------
        url : str
            the URL of the Workbench instance to be hit
        """
        self.url = url.rstrip('/')

    def set_file_input(self, input_file_path):
        """
        For annotating file content, send file path string and process file as a binary

        Parameters
        ----------
        input_file_path : str
            file path to the file to be sent to TERMite
        """
        file_obj = open(input_file_path, 'rb')
        file_name = os.path.basename(input_file_path)
        split_tup = os.path.splitext(input_file_path)
        self.file_ext = split_tup[1]
        self.file_input = {"file": (file_name, file_obj)}

    def set_dataset_name(self, name):
        """
        Set the name of the dataset you will create on your instance

        Parameters
        ----------
        name : str
            name of dataset to create
        """
        self.dataset_name = name

    def set_dataset_desc(self, desc):
        """
        Set the desc of the dataset you will create on your instance

        Parameters
        ----------
        desc : str
            description of dataset to create
        """
        self.dataset_description = desc

    def set_dataset_id(self, dataset_id):
        """
        Set the id of the dataset you would like to edit/use.

        Parameters
        ----------
        dataset_id : str
            id of the dataset you would like to edit/use
        """
        self.dataset_description = dataset_id

    def create_dataset(self):
        """
        Given a dataset name, description and owner, this method will attempt
        to create a dataset with those given details.
        """
        endpoint = "{}/api/datasets".format(self.url.rstrip("/"))
        payload = {
            "title": self.dataset_name,
            "description": self.dataset_description,
            "owner": self.user_info
        }
        req = requests.post(endpoint, json=payload, headers=self.headers)
        if req.ok:
            self.dataset_id = req.json()['id']

    def upload_file_to_dataset(self, dataset_id='', first_row_is_header=True):
        """
        Upload file provided to class to dataset - do not pass a dataset_id if you previously created a dataset using
        this class

        Parameters
        ----------
        dataset_id : str, optional
            id of dataset to upload file to - do no pass anything if previously set
        first_row_is_header : bool, optional
            True if first row in file is header row (default), otherwise False
        """
        if dataset_id != "":
            self.dataset_id = dataset_id
        endpoint_options = {
            '.xls': "{}/api/datasets/{}/uploadExcel?firstRowIsAttributes={}".format(self.url.rstrip("/"),
                                                                                    self.dataset_id,
                                                                                    first_row_is_header),
            '.xlsx': "{}/api/datasets/{}/uploadExcel?firstRowIsAttributes={}".format(self.url.rstrip("/"),
                                                                                     self.dataset_id,
                                                                                     first_row_is_header),
            '.csv': "{}/api/datasets/{}/uploadCsv?firstRowIsAttributes={}".format(self.url.rstrip("/"),
                                                                                  self.dataset_id,
                                                                                  first_row_is_header),
            '.tsv': "{}/api/datasets/{}/uploadTsv?firstRowIsAttributes={}".format(self.url.rstrip("/"),
                                                                                  self.dataset_id,
                                                                                  first_row_is_header)
        }
        endpoint = endpoint_options[self.file_ext]
        req = requests.post(endpoint, headers=self.headers, files=self.file_input)
        job_id = req.json()["jobId"]
        while not check_job_status(self.url, self.headers, job_id):
            time.sleep(5)

    def auto_annotate_dataset(self, dataset_id=''):
        """
        Annotate a dataset in Workbench automatically.
        Please call set_termite_config first if you want to customize the VOCabs used and/or the attributes to annotate.
        If you do not set a termite config, the system will annotate each column in the dataset with every VOCab.

        Parameters
        ----------
        dataset_id : str, optional
            id of dataset to annotate - do not pass anything if previously set
        """
        if dataset_id != "":
            self.dataset_id = dataset_id
        annotate_dataset_endpoint = "{}/api/datasets/{}/autoAnnotateWithTermite?exact=false&replace=false".format(
            self.url.rstrip("/"),
            self.dataset_id)
        if self.termite_config == '':
            req = requests.post(annotate_dataset_endpoint, headers=self.headers)
        else:
            req = requests.post(annotate_dataset_endpoint, headers=self.headers, json=self.termite_config)

        job_id = req.json()["jobId"]

        while not check_job_status(self.url, self.headers, job_id):
            time.sleep(5)
        return True

    def set_termite_config(self, dataset_id='', vocabs=None, passed_attrs=None):
        """
        Use this method to set the termite config for the dataset you want to annotate. Please note the following:

        - The vocabs and passed_attrs objects must match in length.
        - You do not need to set a TERMite Config to WB - if you do not, the system will annotate with all VOCabs.
        - If you specify an attribute/column, but pass an empty list of VOCabs,
          the system will annotate that attribute with all VOCabs.

        Here is an example run of this method: wb.set_termite_config('500',[[5],[6]], [2000,2001])
        - The system will annotate dataset 500's, 2000 and 2001 attributes/columns with vocabs 5 and 6 respectively.

        Parameters
        ----------
        dataset_id : str, optional
            id of dataset to annotate - do not pass anything if previously set
        vocabs : list of list of int, optional
            a list of list<int> representing the VOCabs that you want to annotate each attribute/column
        passed_attrs : list of int, optional
            list<int> of attributes/columns you would like to set a TERMite config for.
        """
        if vocabs is None or passed_attrs is None:
            return 0
        elif len(passed_attrs) != len(vocabs):
            return 0
        termite_configs = []
        if dataset_id != "":
            self.dataset_id = dataset_id
        get_attributes_endpoint = "{}/api/datasets/{}/attributes".format(self.url, self.dataset_id)
        attr_resp = requests.get(get_attributes_endpoint, headers=self.headers)
        all_attributes = attr_resp.json()
        attributes = [attr for attr in all_attributes if attr['id'] in passed_attrs]
        for idx, attribute in enumerate(attributes):
            termite_config = {'termiteConfig': attribute['termiteConfig']}
            termite_config['termiteConfig']['vocabIds'] = vocabs[idx]
            termite_config['attributeIds'] = [attribute['id']]
            termite_configs.append(termite_config)
        self.termite_config = termite_configs

    def annotated_df(self, dataset_id=None,
                     filt=None,
                     filter_attributes=None,
                     exact=None,
                     filter_vocab=None,
                     filter_primary_id=None,
                     filter_term=None,
                     filter_annotation_type=None,
                     filter_partial_match=None,
                     exclude_attributes=None,
                     page=None,
                     size=None,
                     sort=None):
        """
        Fetches annotated data from the specified dataset and returns it as a pandas DataFrame.

        Parameters
        ----------
        dataset_id : str, optional
            The ID of the dataset to fetch annotations from. If not provided, uses the instance's dataset_id.
        filt : str, optional
            Select values to view based on this filter
        filter_attributes : list of int, optional
            Only show values for these attribute ids
        exact : bool, optional
            Filter for exact matches only
        filter_vocab : str, optional
            Filter values based on this vocabulary (e.g., ANAT).
        filter_primary_id : str, optional
            Filter values annotated with this primary ID (e.g., U0001723).
        filter_term : str, optional
            Filter values annotated with the term filter in its label or primary ID (e.g., lung or U0001723).
        filter_annotation_type : str, optional
            Filter values with this annotation type (e.g., MANUAL_ANNOTATION, AUTOMATED, INFERRED_FROM_RULE).
        filter_partial_match : bool, optional
            Filter to only show partial annotations where only a part of the term is annotated
        exclude_attributes : list of int, optional
            Hide these attributes from the table
        page : int, optional
            Page number for pagination.
        size : int, optional
            Page size for pagination.
        sort : list of str, optional
            Sorting by value. Default sort order is ascending e.g. To sort descending on label the parameter would be sort=['label,desc'].

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the annotated data. If an error occurs or no annotations are found, an empty DataFrame is returned.

        Examples
        --------
        >>> workbench = WorkbenchRequestBuilder("http://example.com", "12345", {"Authorization": "Bearer your_token"})
        >>> df = workbench.annotated_df(filt="aspirin")
        >>> print(df)
        """
        annotated_endpoint = "{}/api/datasets/{}/annotated".format(self.url, dataset_id or self.dataset_id)
        params = {
            'filter': filt,
            'filter_attributes': filter_attributes,
            'exact': exact,
            'filter_vocab': filter_vocab,
            'filter_primary_id': filter_primary_id,
            'filter_term': filter_term,
            'filter_annotation_type': filter_annotation_type,
            'filter_partial_match': filter_partial_match,
            'exclude_attributes': exclude_attributes,
            'page': page,
            'size': size,
            'sort': sort
        }

        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}

        try:
            response = requests.get(annotated_endpoint, params=params, headers=self.headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_json = response.json()

            # Ensure the expected key exists in the response
            if '_embedded' in response_json and 'annotationByValues' in response_json['_embedded']:
                annotation_by_values = response_json['_embedded']['annotationByValues']
                df = pd.DataFrame(annotation_by_values)
                return df
            else:
                print("No annotations found in the response.")
                return pd.DataFrame()  # Return an empty dataframe
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            return pd.DataFrame()  # Return an empty dataframe on error

    def dataset_to_df(self, dataset_id=None,
                     table_format='ANNOTATED_SHEET',
                     filt=None,
                     export_field_codes=None,
                     filter_attributes=None,
                     exact=None,
                     filter_vocab=None,
                     filter_primary_id=None,
                     filter_term=None,
                     filter_annotation_type=None,
                     exclude_attributes=None):
        """
        Fetches an annotated sheet, annotations list, or unannotated list from the specified dataset and returns it as a pandas DataFrame.

        Parameters
        ----------
        dataset_id : str, optional
            The ID of the dataset to fetch annotations from. If not provided, uses the instance's dataset_id.
        table_format : str, optional
            The table format for exporting the dataset. Available values : ANNOTATED_SHEET, ANNOTATIONS_LIST, UNANNOTATED_LIST
        export_field_codes : list of str, optional
            A list of fields to include with ANNOTATIONS_LIST. Options are:

            - cell_value*
            - term_id*
            - term_label*
            - column_name*
            - term_vocab_id*
            - type*
            - count*
            - end
            - start
            - partial
            - term_description
            - term_synonyms
            - term_uri
            - matched_value

            Fields marked with an asterisk (*) are always exported.

        filt : str, optional
            Select values to view based on this filter.
        filter_attributes : list of int, optional
            Only show values for these attribute IDs.
        exact : bool, optional
            Filter for exact matches only.
        filter_vocab : str, optional
            Filter values based on this vocabulary (e.g., ANAT).
        filter_primary_id : str, optional
            Filter values annotated with this primary ID (e.g., U0001723).
        filter_term : str, optional
            Filter values annotated with the term filter in its label or primary ID (e.g., lung or U0001723).
        filter_annotation_type : str, optional
            Filter values with this annotation type (e.g., MANUAL_ANNOTATION, AUTOMATED, INFERRED_FROM_RULE).
        exclude_attributes : list of int, optional
            Hide these attributes from the table.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the annotated data.

        Raises
        ------
        Exception
            If the export job fails.
        """
        export_dataset_endpoint = "{}/api/datasets/{}/export".format(self.url, dataset_id or self.dataset_id)
        params = [
            ('format', 'CSV'),
            ('tableFormat', table_format),
            ('filter', filt),
            ('filter_attributes', filter_attributes),
            ('exact', exact),
            ('filter_vocab', filter_vocab),
            ('filter_primary_id', filter_primary_id),
            ('filter_term', filter_term),
            ('filter_annotation_type', filter_annotation_type),
            ('exclude_attributes', exclude_attributes)
        ]
        # Add export_field_codes parameters
        if export_field_codes:
            for field_code in export_field_codes:
                params.append(('export_field_codes', field_code))

        # Filter out None values
        params = [(k, v) for k, v in params if v]

        export_job_resp = requests.post(export_dataset_endpoint, params=params, headers=self.headers)
        export_job_resp_json = export_job_resp.json()
        job_id = export_job_resp_json['jobId']
        while check_job_status(self.url, self.headers, job_id) == False:
            print(f"Waiting for job {job_id} to complete...")
            time.sleep(5)

        final_status = check_job_status(self.url, self.headers, job_id)
        if final_status == True:
            print("Dataset export complete")
        else:
            raise Exception(f"Upload failed with status: {final_status}")

        download_link = f"{self.url}/api/datasets/{dataset_id or self.dataset_id}/download/{job_id}"
        export = requests.get(download_link, headers=self.headers)
        export.raise_for_status()

        # Don't save to disk
        csv_content = StringIO(export.text)
        df = pd.read_csv(csv_content)

        return df

    def annotated_list_df(self, dataset_id=None,
                          metadata_to_add=None):
        """
        Fetches annotated data with metadata for a dataset and returns it as a pandas DataFrame.

        Parameters
        ----------
        dataset_id : str, optional
            The ID of the dataset to fetch annotations from. If not provided, uses the instance's dataset_id.
        metadata_to_add : list of str, optional
            A list that can contain:

            - term_label
            - term_description
            - term_synonyms
            - term_uri
            - partial
            - start
            - end
        """
        annotations_list_df = self.dataset_to_df(dataset_id or self.dataset_id)
        annotations_df = self.dataset_to_df(dataset_id or self.dataset_id, table_format='ANNOTATIONS_LIST',
                                           export_field_codes=metadata_to_add)
        columns_annotated = annotations_df['Column Label'].unique().tolist()

        # Function to map IDs to Labels
        def map_ids_to_labels(ids, id_to_label):
            if not isinstance(ids, list):
                return []
            return [id_to_label[id] for id in ids if id in id_to_label]

        # Function to safely join lists
        def safe_join(value):
            if isinstance(value, list):
                return ', '.join(value)
            elif pd.isna(value):
                return ''
            else:
                return str(value)

        # Apply mappings for each unique column label
        for col in columns_annotated:
            annotation_column = f"{col} annotations"
            if annotation_column in annotations_list_df.columns:
                # Split annotations into lists
                annotations_list_df[annotation_column] = annotations_list_df[annotation_column].str.split(',')

                # Create a dictionary for mapping Term IDs to Term Labels for the specific Column Label
                id_to_label = dict(zip(annotations_df[annotations_df['Column Label'] == col]['Term Id'],
                                       annotations_df[annotations_df['Column Label'] == col]['Term Label']))

                # Create new column for term labels
                term_labels_column = annotations_list_df[annotation_column].apply(map_ids_to_labels, args=(id_to_label,))

                # Join the list back into a string for display
                term_labels_column = term_labels_column.apply(safe_join)

                # Insert the new column immediately after the annotation column
                annotations_list_df.insert(annotations_list_df.columns.get_loc(annotation_column) + 1, f"{col} Term Labels",
                                        term_labels_column)

                annotations_list_df[f"{annotation_column}"] = annotations_list_df[f"{annotation_column}"].apply(safe_join)

        # Return the resulting dataframe
        return annotations_list_df


    def export_dataset(self, dataset_id='', form='EXCEL', table_format='GROUPED_ANNOTATIONS', exact='false', filt='',
                       filter_attributes=None, filter_vocab='', filter_primary_id='', filter_annotation_type='',
                       exclude_attributes=None):
        """
        Use this method to export a dataset from WB. We will default to export with all annotations to excel as grouped.

        Parameters
        ----------
        dataset_id : str, optional
            id of dataset to export - do not pass anything if previously set
        form : str, optional
            the file extension of the export - can be 'EXCEL', 'TSV', or 'CSV'
        table_format : str, optional
            format of resulting export - can be 'GROUPED_ANNOTATIONS' or 'FLATTENED_ANNOTATIONS'
        exact : str, optional
            filter for exact matches
        filt : str, optional
            string filter to filter what rows are provided in the export
        filter_attributes : list of int, optional
            provide a list<int> of attributes/columns to include in the export
        filter_vocab : str, optional
            export only annotations made by this VOCab
        filter_primary_id : str, optional
            export only annotations that include this primary id
        filter_annotation_type : str, optional
            export rows according to annotation type - can be 'MANUAL_VERIFIED', 'INFERRED_FROM_RULE', or 'AUTOMATED'.
            defaults to include all annotations.
        exclude_attributes : list of int, optional
            provide a list<int> of attributes/columns to NOT include in the export
        """
        if exclude_attributes is None:
            exclude_attributes = []
        if filter_attributes is None:
            filter_attributes = []
        if dataset_id != "":
            self.dataset_id = dataset_id

        export_dataset_endpoint = "{}/api/datasets/{}/export".format(self.url, self.dataset_id)
        params = {
            'format': form,
            'tableFormat': table_format,
            'exact': exact,
            'filter': filt,
            'filter_attributes': filter_attributes,
            'filter_vocab': filter_vocab,
            'filter_primary_id': filter_primary_id,
            'filter_annotation_type': filter_annotation_type,
            'exclude_attributes': exclude_attributes,
        }

        job_request = requests.post(export_dataset_endpoint, params=params, headers=self.headers)
        json_job_req = job_request.json()
        job_id = json_job_req['jobId']
        while not check_job_status(self.url, self.headers, job_id):
            time.sleep(5)
        download_link = '{}/api/datasets/{}/download/{}'.format(self.url, self.dataset_id, job_id)
        export = requests.get(download_link, headers=self.headers)
        return export.content


def check_job_status(url, headers, job_id):
    """
    Check the status of a job on a workbench server

    Parameters
    ----------
    url : str
        the url of the workbench instance to check
    headers : dict
        the authentication header to send to authenticate with the instance
    job_id : str
        the job_id to check

    Returns
    -------
    bool
        True if job is complete, False otherwise
    """
    job_status_endpoint = "{}/api/jobs/{}".format(url.rstrip("/"), job_id)
    req = requests.get(job_status_endpoint, headers=headers)
    json_req = req.json()
    status = json_req['jobStatus']

    if status == 'COMPLETE':
        return True
    else:
        return False


def upload_and_annotate_directory(input_directory_path, wb_url, username, password, client_id, annotate=False,
                                  vocabs=None, attrs=None):
    """
    Given an input directory, this method will create WB datasets for each applicable file
    (file ext of csv,tsv, xlsx or xls) in the directory and upload the files to WB. It will also annotate each file if
    annotate is set to true according to the vocabs and attrs passed.

    Parameters
    ----------
    input_directory_path : str
        directory of files to upload to WB
    wb_url : str
        url of WB instance to use.
    username : str
        username of user to authenticate with
    password : str
        password of user to authenticate with
    client_id : str
        client_id of instance to authenticate with
    annotate : bool, optional
        boolean - True to annotate each file in directory, false to do nothing. Defaults to false
    vocabs : list of list of int, optional
        a list of list<int> representing the VOCabs that you want to annotate each attribute/column
    attrs : list of int, optional
        list<int> of attributes/columns you would like to set a TERMite config for.
    """
    wb = WorkbenchRequestBuilder()
    wb.set_url(wb_url)
    wb.set_oauth2(client_id, username, password)
    datasets = []
    for path, _, filenames in os.walk(input_directory_path):
        for filename in filenames:
            file_path = os.path.join(path, filename)
            if filename.endswith(".csv") or filename.endswith(".xlsx") \
                    or filename.endswith(".tsv") or filename.endswith(".xls"):
                wb.set_dataset_name(os.path.splitext(filename)[0])
                wb.set_dataset_desc(os.path.splitext(filename)[0])
                wb.create_dataset()
                wb.set_file_input(file_path)
                wb.upload_file_to_dataset()
                if annotate:
                    wb.set_termite_config('', vocabs, attrs)
                    wb.auto_annotate_dataset()
                datasets.append(wb.dataset_id)
    return datasets


def export_datasets(export_directory_path, wb_url, username, password, client_id, datasets, form='EXCEL',
                    table_format='ANNOTATED_SHEET', exact='false', filt='',
                    filter_attributes=None, filter_vocab='', filter_primary_id='', filter_annotation_type='',
                    exclude_attributes=None):
    """
    Given a list of WB datasets, this method with export all of them to a given directory.

    Parameters
    ----------
    export_directory_path : str
        path of where the exports should be saved
    wb_url : str
        url of WB instance to use.
    username : str
        username of user to authenticate with
    password : str
        password of user to authenticate with
    client_id : str
        client_id of instance to authenticate with
    datasets : list of int
        list<int> of datasets to export.
    form : str, optional
        the file extension of the export - can be 'EXCEL', 'TSV', or 'CSV'
    table_format : str, optional
        format of resulting export - can be 'ANNOTATED_SHEET', 'ANNOTATIONS_LIST', or 'UNANNOTATED_LIST' (default is 'ANNOTATED_SHEET')
    exact : str, optional
        filter for exact matches
    filt : str, optional
        string filter to filter what rows are provided in the export
    filter_attributes : list of int, optional
        provide a list<int> of attributes/columns to include in the export
    filter_vocab : str, optional
        export only annotations made by this VOCab
    filter_primary_id : str, optional
        export only annotations that include this primary id
    filter_annotation_type : str, optional
        export rows according to annotation type - can be 'MANUAL_VERIFIED', 'INFERRED_FROM_RULE', or 'AUTOMATED'.
        defaults to include all annotations.
    exclude_attributes : list of int, optional
        provide a list<int> of attributes/columns to NOT include in the export
    """
    wb = WorkbenchRequestBuilder()
    wb.set_url(wb_url)
    wb.set_oauth2(client_id, username, password)
    file_exts = {
        'EXCEL': '.xlsx',
        'CSV': '.csv',
        'TSV': '.tsv'
    }
    file_ext = file_exts[form]
    for dataset in datasets:
        dataset_info_link = '{}/api/datasets/{}'.format(wb.url, dataset)
        file_export = wb.export_dataset(dataset, form, table_format, exact, filt, filter_attributes, filter_vocab,
                                        filter_primary_id, filter_annotation_type, exclude_attributes)
        dataset_info = requests.get(dataset_info_link, headers=wb.headers)
        dataset_name = dataset_info.json()['title']
        filename = dataset_name + file_ext
        with open(os.path.join(export_directory_path, filename), 'wb') as file:
            file.write(file_export)
            file.close()


def get_attributes(columns_to_clean, wb_url, headers, dataset_id):
    """
    Given a list<string> of column names, this method will return a list<int> of attributes (what are called columns
    in Workbench) for a given dataset.
    If the returned list does not have the same length as the inputted list, we will not return it
    and will print an error.

    Parameters
    ----------
    columns_to_clean : list of str
        list<string> of columns to identify by attribute number
    wb_url : str
        url of workbench to connect to
    headers : dict
        the wb object headers attribute
    dataset_id : str
        id of dataset to use.

    Returns
    -------
    list of int
        list<int> of attribute ids that correspond with column names
    """
    attribute_endpoint = '{}/api/datasets/{}/attributes'.format(wb_url.rstrip('/'), dataset_id)
    resp = requests.get(attribute_endpoint, headers=headers)
    all_attrs = resp.json()

    attrs_ids = [next((attr['id'] for attr in all_attrs if attr['name'] == column), None) for column in
                 columns_to_clean]

    if None in attrs_ids:
        print('ERROR: One of the columns inputted was not found.')
        exit(2)

    return attrs_ids

def get_vocabs(vocabs, wb_url, headers):
    """
    Given a list<string> of vocab names, this method will return a list<int> of vocabs by their number ID in Workbench.
    If the returned list does not have the same length as the inputted list, we will not return it
    and will print an error.

    Parameters
    ----------
    vocabs : list of str
        list<string> of vocabs to identify by vocab number
    wb_url : str
        url of workbench to connect to
    headers : dict
        the wb object headers attribute

    Returns
    -------
    dict
        JSON object of two lists, list<int> of vocab ids that correspond with vocab names, list<str> of vocab names that have no correspond ids
    """
    vocab_endpoint = '{}/api/vocabs/active'.format(wb_url.rstrip('/'))
    resp = requests.get(vocab_endpoint, headers=headers)
    all_vocabs = resp.json()

    vocab_ids = [next((vocab['id'] for vocab in all_vocabs if vocab['termiteId'] == vocab_name), None) for vocab_name in
                 vocabs]
    
    non_loaded_vocabs = [vocabs[idx] for idx, vocab_id in enumerate(vocab_ids) if vocab_id is None]

    results_wb_ids = {'vocab_ids':vocab_ids,'non_loaded_vocabs':non_loaded_vocabs }
    return results_wb_ids

def merge_annotations_metadata(dataset_csv, annotations_list_csv, output_filename='merged_data.csv',
                              metadata_to_add=['Term Label', 'Term Id', 'Term URI']):
    """
    take an annotated dataset, an annotations list, and merge them to add a column of metadata

    Parameters
    ----------
    dataset_csv : str
        Path to the annotated dataset CSV file
    annotations_list_csv : str
        Path to the annotations list CSV file
    output_filename : str, optional
        Name of the output file (default is 'merged_data.csv')
    metadata_to_add : list of str, optional
        A list that can contain:

        - term_label
        - term_description
        - term_synonyms
        - term_uri
        - partial
        - start
        - end
    """
    annotations_list_df = pd.read_csv(dataset_csv)
    annotations_df = pd.read_csv(annotations_list_csv)
    columns_annotated = annotations_df['Column Label'].unique().tolist()

    # Function to map IDs to metadata
    def map_ids_to_metadata(ids, id_to_metadata):
        if not isinstance(ids, list):
            return []
        return [id_to_metadata.get(id, '') for id in ids]

    # Function to safely join lists
    def safe_join(value):
        if isinstance(value, list):
            return ', '.join([str(v) for v in value])
        elif pd.isna(value):
            return ''
        else:
            return str(value)

    # Apply mappings for each unique column label
    for col in columns_annotated:
        annotation_column = f"{col} annotations"
        if annotation_column in annotations_list_df.columns:
            # Split annotations into lists
            annotations_list_df[annotation_column] = annotations_list_df[annotation_column].str.split(',')

            for meta_col in metadata_to_add:
                # Map the metadata column name to the actual column in the annotations_df
                # Accept both 'Term Label' and 'term_label' etc.
                possible_colnames = [meta_col, meta_col.replace(' ', '_'), meta_col.lower().replace(' ', '_')]
                meta_colname = next((c for c in possible_colnames if c in annotations_df.columns), None)
                if meta_colname is None:
                    continue

                id_to_metadata = dict(zip(
                    annotations_df[annotations_df['Column Label'] == col]['Term Id'],
                    annotations_df[annotations_df['Column Label'] == col][meta_colname]
                ))

                # Create new column for the metadata
                meta_column = annotations_list_df[annotation_column].apply(map_ids_to_metadata, args=(id_to_metadata,))
                meta_column = meta_column.apply(safe_join)

                # Insert the new column immediately after the annotation column
                insert_loc = annotations_list_df.columns.get_loc(annotation_column) + 1
                annotations_list_df.insert(insert_loc, f"{col} {meta_col}", meta_column)

            # Join the annotation column back into a string for display
            annotations_list_df[f"{annotation_column}"] = annotations_list_df[f"{annotation_column}"].apply(safe_join)

    # Return the resulting dataframe

    return annotations_list_df.to_csv(output_filename, index=False)