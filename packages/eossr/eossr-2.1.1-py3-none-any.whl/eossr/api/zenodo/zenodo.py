#!/usr/bin/env python
"""
Zenodo API
----------

This module provides a Python interface to the Zenodo REST API.
The Zenodo REST API is documented at https://developers.zenodo.org/.

The main class is `ZenodoAPI`, which allows to perform tasks within the (sandbox.)zenodo api environment.

Note the following nomeclature:
- queries: GET methods to {api_url}, returns requests.response objects
- search: general text-based searches. Returns JSON dicts or custom classes with the information of the query
- get: targeted query. returns JSON dicts or custom classes with the information of the query

- deposit: a deposit is a single entry, published or not published, in Zenodo.
- record: a record is a published entry in Zenodo. It can be a software, a dataset, a publication, etc.

"""

import concurrent.futures
import json
import os
import pprint
import re
import sys
import textwrap
import warnings
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Union
from urllib.request import urlopen

import requests
from bs4 import BeautifulSoup

from ...metadata.zenodo import write_zenodo_metadata, zenodo_filepath
from ...utils import get_codemeta_from_zipurl, write_json
from . import http_status

__all__ = [
    "zenodo_url",
    "zenodo_sandbox_url",
    "zenodo_api_base_url",
    "zenodo_sandbox_api_base_url",
    "ZenodoAPI",
    "SimilarRecordError",  # noqa
    "Record",
    "search_records",
    "query_records",
    "get_record",
    "get_supported_licenses",
    "search_records",
    "search_funders",
    # 'search_grants',
    "search_communities",
    "search_licenses",
    "is_live",
    "get_community",
    "get_license",
    "get_funder",
    "query_deposits",
    "query_deposit",
    "get_deposit",
    "PendingRequest",
]


zenodo_url = "https://zenodo.org"
zenodo_api_base_url = f"{zenodo_url}/api/"
zenodo_sandbox_url = "https://sandbox.zenodo.org"
zenodo_sandbox_api_base_url = f"{zenodo_sandbox_url}/api/"

# Default page size for queries (25 is the max for unauthenticated requests)
_default_size_query = 25
_default_timeout = 35


class ZenodoAPI:
    def __init__(self, access_token=None, sandbox=False):
        """
        Manages the communication with the (sandbox.)zenodo REST API through the Python request library.
        The client would allow to perform the following tasks within the (sandbox.)zenodo api environment:

          - Fetches a user's published entries,
          - Creates a new deposit,
          - Fetches any published record,
          - Creates a new version of an existing deposit,
          - Uploads files to a specific Zenodo deposit,
          - Erases a non-published deposit / new version draft,
          - Erases (old version) files from an deposit (when creating a new_version deposit and uploading
            new_version files),
          - Uploads information to the deposit (Zenodo compulsory deposit information),
          - Publishes an deposit
          - Finds all the published community entries
            * per title
            * per deposit_id
          - Finds all the records of a user (defined by the zenodo token)
          - Searches for similar records within all records associated to a user.

          Please note that every request.json() answer has been limited to 50 elements. You can set this value
          as follows (once ZenodoAPI has been initialised, for example):
          z = ZenodoApi(token)
          z.parameters.update({'size': INTEGER_NUMBER)

        Parameters
        ----------
        access_token : str, optional
            Personal access token to (sandbox.)zenodo.org/api.
        sandbox : bool, optional
            If True, communicates with the sandbox.zenodo API. If False, communicates with the zenodo API.
        """

        self.sandbox = sandbox
        self.api_base_url = zenodo_sandbox_api_base_url if sandbox else zenodo_api_base_url
        if access_token is None:
            warnings.warn("No access token provided, limited functionalities")
        self.access_token = access_token
        self.parameters = {"access_token": self.access_token}
        self.parameters.setdefault("size", _default_size_query)

    def _raise_token_status(self):
        """
        private method to check if a valid token has been provided, called in methods requiring a token
        :return:
        """
        if self.access_token is None or self.access_token == "":
            raise ValueError("No access token was provided. This method requires one.")

    def query_user_deposits(self):
        """
        Fetch the published and unpublished deposits to which an user has access.

        :return: request.response
        """
        self._raise_token_status()
        response = query_deposits("", sandbox=self.sandbox, **self.parameters)
        http_status.ZenodoHTTPStatus(response)
        return response

    def query_deposit(self, deposit_id):
        """
        Queries an existing Zenodo deposit from its ID.

        Parameters
        ----------
        deposit_id : str or int
            The deposition ID of the Zenodo deposit.

        Returns
        -------
        request.response
            The response from the query.

        Raises
        ------
        TokenStatusError
            If the access token is not provided or is invalid.
        """
        self._raise_token_status()
        return query_deposit(deposit_id, self.access_token, sandbox=self.sandbox)

    def create_new_deposit(self):
        """
        Create a new deposit in (sandbox.)zenodo

        Parameters
        ----------
        None

        Returns
        -------
        requests.Response
            The response object representing the HTTP response.

        Raises
        ------
        ZenodoTokenError
            If the access token is invalid or expired.

        Notes
        -----
        This method sends a POST request to the Zenodo API to create a new deposit.
        The request is made to the endpoint {api_url}/deposit/depositions.
        The request body is empty, and the request headers include the content type as "application/json".
        The request parameters are taken from the `parameters` attribute of the Zenodo object.
        The request timeout is set to the default timeout value.

        The method returns the response object representing the HTTP response.
        If the response status code is not successful, an exception of type ZenodoHTTPStatus is raised.

        Example
        -------
        >>> zenodo = Zenodo(access_token=os.getenv('SANDBOX_ZENODO_TOKEN'), sandbox=True)
        >>> response = zenodo.create_new_deposit()
        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions"
        headers = {"Content-Type": "application/json"}
        req = requests.post(url, json={}, headers=headers, params=self.parameters, timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(req)
        return req

    def upload_file_deposit(self, deposit_id, name_file, path_file):
        """
        Upload a file to a Zenodo deposit.

        Parameters
        ----------
        deposit_id : str
            Deposition ID of the Zenodo deposit.
        name_file : str
            File name of the file when uploaded.
        path_file : str
            Path to the file to be uploaded.

        Returns
        -------
        request.response
            The response from the upload request.
        """
        self._raise_token_status()
        # 1 - Retrieve and recover information of a record that is in process of being published
        response = self.query_deposit(deposit_id)

        # 2 - Upload the files
        # full url is recovered from previous GET method
        bucket_url = response.json()["links"]["bucket"]
        url = f"{bucket_url}/{name_file}"

        with open(path_file, "rb") as upload_file:
            upload = requests.put(url, data=upload_file, params=self.parameters, timeout=_default_timeout)

        http_status.ZenodoHTTPStatus(upload)
        return upload

    def set_deposit_metadata(self, deposit_id, json_metadata):
        """
        Set a deposit metadata.

        Parameters
        ----------
        deposit_id : str
            Deposition ID of the Zenodo deposit.
        json_metadata : object
            JSON object containing the metadata (compulsory fields) that are enclosed when a new deposit is created.

        Returns
        -------
        request.response
            The response from the PUT request to update the deposit metadata.
        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions/{deposit_id}"
        headers = {"Content-Type": "application/json"}

        # The metadata field is already created, just need to be updated.
        # Thus, the root 'metadata' key need to be kept, to indicate the field to be updated.
        data = {"metadata": json_metadata}
        req = requests.put(
            url, data=json.dumps(data), headers=headers, params=self.parameters, timeout=_default_timeout
        )
        http_status.ZenodoHTTPStatus(req)
        return req

    def update_deposit_metadata(self, deposit_it, metadata):
        """
        Update the deposit metadata with only the one provided.

        Parameters
        ----------
        deposit_it: str or int
        metadata: dict
            The metadata to be updated.
        """
        req = self.query_deposit(deposit_it)
        data = req.json()
        data["metadata"].update(metadata)
        req = self.set_deposit_metadata(deposit_it, data["metadata"])
        return req

    def erase_deposit(self, deposit_id):
        """
        Erase a deposit (that has not been published yet).
        Any new upload/version will be first saved as 'draft' and not published until confirmation (i.e, requests.post)

        Parameters
        ----------
        deposit_id : str or int
            Deposition ID of the Zenodo deposit to be erased

        Returns
        -------
        request.response
            The response object from the DELETE request

        Raises
        ------
        ZenodoHTTPStatus
            If the HTTP status code is not 204 or 410
        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions/{deposit_id}"
        req = requests.delete(url, params=self.parameters, timeout=_default_timeout)
        if req.status_code == 204:
            print("The deposit has been deleted")
            return req
        elif req.status_code == 410:  # Not raising an error in this case is OK
            warnings.warn("The deposit already was deleted")
        else:
            try:
                http_status.ZenodoHTTPStatus(req)
            except (requests.exceptions.JSONDecodeError, ValueError):
                req.raise_for_status()
        return req

    def erase_file_deposit(self, deposit_id, file_id):
        """
        Erase a file from a deposit (that has not been published yet).
        This method is intended to be used for substitution of files (deletion) within a deposit by their correspondent
        new versions.

        Parameters
        ----------
        deposit_id : str
            deposition_id of the Zenodo deposit
        file_id : str
            ID of the files stored in Zenodo

        Returns
        -------
        requests.response
            The response object from the DELETE request to Zenodo API.
        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions/{deposit_id}/files/{file_id}"
        req = requests.delete(url, params=self.parameters, timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(req)
        return req

    def publish_deposit(self, deposit_id):
        """
        Publishes a deposit in (sandbox.)zenodo

        Parameters
        ----------
        deposit_id : str
            deposition_id of the Zenodo entry

        Returns
        -------
        requests.response
            The response object from the POST request to publish the deposit.
        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions/{deposit_id}/actions/publish"
        req = requests.post(url, params=self.parameters, timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(req)
        return req

    def new_version_deposit(self, record_id):
        """
        Creates a new version of an existing record.

        Parameters
        ----------
        record_id : str or int
            The ID of the existing record.

        Returns
        -------
        requests.response
            The response object from the POST request.

        Raises
        ------
        ZenodoHTTPStatus
            If there is an error in the HTTP request.

        """
        self._raise_token_status()
        url = f"{self.api_base_url}/deposit/depositions/{record_id}/actions/newversion"
        parameters = {"access_token": self.access_token}
        req = requests.post(url, params=parameters, timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(req)
        return req

    def query_community_records(self, community_name="escape2020", **kwargs):
        """
        Query the records within a community.

        Parameters
        ----------
        community_name : str, optional
            Community name. Default is 'escape2020'.
        **kwargs : dict
            Parameters for `query_records`

        Returns
        -------
        requests.models.Response
            The response object from the API request.
        """
        # https://developers.zenodo.org/#list36
        parameters = deepcopy(self.parameters)
        parameters.update(kwargs)
        parameters["communities"] = str(community_name)
        return query_records("", sandbox=self.sandbox, **parameters)

    @staticmethod
    def path_zenodo_file(root_dir):
        return zenodo_filepath(root_dir)

    def upload_dir_content(self, directory, record_id=None, metadata=None, erase_previous_files=True, publish=True):
        """
        Package the project root directory as a zip archive and upload it to Zenodo.

        Parameters
        ----------
        directory : str or Path
            Path to the directory to upload.
        record_id : str or int or None, optional
            If a record_id is provided, a new version of the record will be created.
            Otherwise, a new record is created.
        metadata : dict or None, optional
            Dictionary of Zenodo metadata. If None, the metadata will be read from a `.zenodo.json` file
            or a `codemeta.json` file in `self.root_dir`.
        erase_previous_files : bool, optional
            In case of making a new version of an existing record (`record_id` not None), erase files from the previous version.
        publish : bool, optional
            If True, publish the record. Otherwise, the record is prepared but publication must be done manually.
            This is useful to check or discard the record before publication.

        Returns
        -------
        str
            The ID of the newly created or updated record.
        """
        self._raise_token_status()

        # prepare new record version
        if record_id is not None:
            new_deposit = self.new_version_deposit(record_id)
            new_deposit_id = new_deposit.json()["links"]["latest_draft"].rsplit("/")[-1]
            print(f" * Preparing a new version of record {record_id}")
            # TODO: log
            if erase_previous_files:
                old_files_ids = [file["id"] for file in new_deposit.json()["files"]]
                for file_id in old_files_ids:
                    self.erase_file_deposit(new_deposit_id, file_id)
                    print(f"   - file {file_id} erased")
        else:
            new_deposit = self.create_new_deposit()
            new_deposit_id = new_deposit.json()["id"]
            print(" * Preparing a new record")

        print(f" * New record id: {new_deposit_id}")

        # get metadata
        path_zenodo_file = self.path_zenodo_file(directory)
        if metadata is not None:
            print(f" * Record metadata based on provided metadata: {metadata}")
        elif path_zenodo_file.exists():
            print(f"   - Record metadata based on zenodo file {path_zenodo_file}")
            with open(path_zenodo_file) as file:
                metadata = json.load(file)
        else:
            raise FileNotFoundError(" ! No metadata file provided")

        # upload files
        dir_to_upload = Path(directory)
        for file in dir_to_upload.iterdir():
            self.upload_file_deposit(deposit_id=new_deposit_id, name_file=file.name, path_file=file)
            print(f" * {file.name} uploaded")

        # and update metadata
        self.set_deposit_metadata(new_deposit_id, json_metadata=metadata)
        print(" * Metadata updated successfully")

        # publish new record
        if publish:
            self.publish_deposit(new_deposit_id)
            if record_id:
                print(f" * New version of {record_id} published at {new_deposit_id} !")
            else:
                print(f" * Record {new_deposit_id} published")
            print(f" * The new doi should be 10.5281/{new_deposit_id}")

        print(f" * Check the upload at {self.api_base_url[:-4]}/deposit/{new_deposit_id} *")

        return new_deposit_id

    def check_upload_to_zenodo(self, directory):
        """
        `Tests` the different stages of the GitLab-Zenodo connection and that the status_code returned by every
        stage is the correct one.

        Checks:
         - The existence of a `.zenodo.json` file in the ROOT dir of the project

         - The communication with Zenodo through its API to verify that:
            - You can fetch a user entries
            - You can create a new entry
            - The provided zenodo metadata can be digested, and not errors appear
            - Finally erases the test entry - because IT HAS NOT BEEN PUBLISHED !
        """
        self._raise_token_status()
        path_zenodo_file = self.path_zenodo_file(directory)
        if not path_zenodo_file.exists():
            raise FileNotFoundError(f"No {path_zenodo_file} file.")

        print(f"\n * Using {path_zenodo_file} file to simulate a new upload to Zenodo... \n")

        # 1 - Test connection
        print("1 --> Testing communication with Zenodo...")

        test_connection = self.query_user_deposits()

        http_status.ZenodoHTTPStatus(test_connection)
        print("  * Test connection status OK !")

        # 2 - Test new entry
        print("2 --> Testing the creation of a dummy entry to (sandbox)Zenodo...")

        new_deposit = self.create_new_deposit()

        http_status.ZenodoHTTPStatus(new_deposit)
        print("  * Test new deposit status OK !")

        # 3 - Test upload metadata
        print("3 --> Testing the ingestion of the Zenodo metadata...")

        test_deposit_id = new_deposit.json()["id"]
        with open(path_zenodo_file) as file:
            metadata_entry = json.load(file)
        updated_metadata = self.set_deposit_metadata(test_deposit_id, json_metadata=metadata_entry)

        try:
            http_status.ZenodoHTTPStatus(updated_metadata)
            print("  * Metadata deposit status OK !")
            pprint.pprint(metadata_entry)
        except http_status.HTTPStatusError:
            print("  ! ERROR while testing update of metadata\n", updated_metadata.json())
            print("  ! The deposit will be deleted")

        # 4 - Test delete entry
        print("4 --> Deleting the dummy entry...")
        delete_test_entry = self.erase_deposit(test_deposit_id)
        try:
            http_status.ZenodoHTTPStatus(delete_test_entry)
        except http_status.HTTPStatusError:
            print(f" !! ERROR erasing dummy test entry: {delete_test_entry.json()}")
            print(f"Please erase it manually at {self.api_base_url[:-4]}/deposit")
            sys.exit(-1)

        print("  * Delete test entry status OK !")

        print(
            "\n\tYAY ! Successful testing of the connection to Zenodo ! \n\n"
            "You should not face any trouble when uploading a project to Zenodo"
        )

    def get_user_records(self):
        """
        Finds all the records associated with a user (defined by the zenodo token).

        Returns:
            list: A list of Record objects representing the user's records.
        """
        request = self.query_user_deposits()

        return [Record(hit) for hit in request.json() if hit["state"] == "done"]

    def find_similar_records(self, record):
        """
        Find similar records in the owner records.

        Parameters
        ----------
        record : eossr.api.zenodo.Record
            The record to compare with.

        Returns
        -------
        list[Record]
            List of similar records.
        """
        similar_records = []
        user_records = self.get_user_records()
        for user_rec in user_records:
            if user_rec.title == record.title:
                similar_records.append(user_rec)

            if "related_identifiers" in user_rec.data["metadata"] and "related_identifiers" in record.data["metadata"]:
                relid1 = [r["identifier"] for r in user_rec.data["metadata"]["related_identifiers"]]
                relid2 = [r["identifier"] for r in record.data["metadata"]["related_identifiers"]]

                if set(relid1).intersection(relid2):
                    similar_records.append(user_rec)

        return similar_records

    def get_community_pending_requests(self, community, **params):
        """
        Get a list of records that have been requested to be added to a community.

        Parameters
        ----------
        community : str
            Name of the community.
        params : dict
            Parameters for the request. Override the class parameters.

        Returns
        -------
        list
            A list of records.

        """
        self._raise_token_status()
        community_json = get_community(community, sandbox=self.sandbox, token=self.access_token)
        community_requests_url = community_json["links"]["requests"]
        parameters = deepcopy(self.parameters)
        parameters.update(params)
        response = requests.get(community_requests_url, params=parameters, timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(response)
        response_json = response.json()["hits"]["hits"]
        response_json = [
            PendingRequest(hit, sandbox=self.sandbox, access_token=self.access_token)
            for hit in response_json
            if hit["is_open"]
        ]
        return response_json

    def answer_to_pending_request(self, community: str, record_id: Union[str, int], accept: bool):
        """
        Answer to a pending request into a community.

        Parameters
        ----------
        community : str
            The name of the community. The community must be owned by the token owner.
        record_id : str or int
            The ID of the record.
        accept : bool
            Whether to accept or decline the request.

        Raises
        ------
        ValueError
            If the record is not in the pending requests.
        HTTPStatusError
            If the request is not successful.


        """
        self._raise_token_status()
        # check that the record is in the pending requests
        pending_requests = self.get_community_pending_requests(community)
        pending_record = None
        for req in pending_requests:
            if req["topic"]["record"] == record_id:
                if accept:
                    req.accept()
                else:
                    req.decline()
        if pending_record is None:
            raise ValueError(f"Record {record_id} is not in the pending requests of community {community}")

    def update_record_metadata(self, record_id, metadata):
        """
        Update a published record metadata

        Parameters
        ----------
        record_id : int
            The ID of the record to update.
        metadata : dict
            The updated metadata for the record.

        Returns
        -------
        requests.response
            The response from the API call.
        """
        self._raise_token_status()
        req = requests.post(
            f"{self.api_base_url}/deposit/depositions/{record_id}/actions/edit",
            params={"access_token": self.access_token},
            timeout=_default_timeout,
        )
        if req.status_code == 403:
            # In this case it is fine to continue editing the record metadata
            warnings.warn("The record was already open for edition")
        else:
            http_status.ZenodoHTTPStatus(req)

        record = get_record(record_id, sandbox=self.sandbox)
        record_metadata = record.data["metadata"]
        record_metadata["upload_type"] = record_metadata["resource_type"]["type"]
        if "access_right_category" in record_metadata:
            record_metadata.pop("access_right_category")
        if "related_identifiers" in record_metadata:
            record_metadata.pop("related_identifiers")
        record_metadata.pop("relations")
        record_metadata.pop("resource_type")
        record_metadata.update(metadata)
        self.set_deposit_metadata(record_id, json_metadata=record_metadata)
        req = self.publish_deposit(record_id)
        return req


class SimilarRecordError(Exception):
    pass


class Record:
    """
    Basic class object to handle Zenodo records
    """

    def __init__(self, data: dict):
        for k in ["id", "metadata"]:
            if k not in data.keys():
                raise ValueError(f"key {k} not present in data")
        # list of keys mandatory to create a Zenodo entry.
        # Other keys are either optional, or can be hidden in case of Closed Access entries.
        for meta_key in ["title", "doi"]:
            if meta_key not in data["metadata"].keys():
                raise ValueError(f"Mandatory key {meta_key} not in data['metadata']")
        self.data = data

    def __str__(self):
        return f"Record #{self.id} : {self.title}"

    def __repr__(self):
        return f"Record({self.id})"

    def _write_zenodo_deposit(self, filename=".zenodo.json", overwrite=False, validate=True):
        """
        Write the zenodo metadata to a `.zenodo.json` file, so it can be used to create a new deposit.
        The created file is not guaranteed to be valid, but it is a good starting point.

        Parameters
        ----------
        filename : str, optional
            Path to the file to write. Default is '.zenodo.json'.
        overwrite : bool, optional
            True to overwrite an existing file. Default is False.
        validate : bool, optional
            True to validate the metadata before writing the file. Default is True.
        """
        # Transform metadata from record to deposit first
        metadata = deepcopy(self.data["metadata"])
        metadata["upload_type"] = metadata["resource_type"]["type"]
        metadata.pop("resource_type")
        if "access_right_category" in metadata:
            metadata.pop("access_right_category")
        if "relations" in metadata:
            metadata.pop("relations")
        if "communities" in metadata:
            metadata["communities"] = [{"identifier": c["id"]} for c in metadata["communities"]]
        if "zenodo" in metadata["doi"]:
            metadata.pop("doi")
        metadata["license"] = metadata["license"]["id"]

        write_zenodo_metadata(metadata, filename=filename, overwrite=overwrite, validate=validate)

    def write_metadata(self, filename, overwrite=False):
        """
        Write the metadata to a json file.

        Parameters
        ----------
        filename: str
        overwrite: bool
            True to overwrite existing file
        """
        write_json(self.data["metadata"], filename=filename, overwrite=overwrite)

    @property
    def id(self):
        return self.data["id"]

    @property
    def title(self):
        return self.data["metadata"]["title"]

    @property
    def metadata(self):
        return self.data["metadata"]

    @property
    def filelist(self):
        """
        Return the list of files in the record

        :return: [str]
        """
        return [f["links"]["self"] for f in self.data["files"]]

    def get_last_version(self, token=None):
        """
        Return the last version of the record.
        If there is only one version, or if this is already the last version, return itself.

        Parameters
        ----------
        token : str, optional
            The access token for authentication. Default is None.

        Returns
        -------
        eossr.api.zenodo.Record
            The last version of the record.
        """
        if "relations" not in self.data["metadata"] or self.data["metadata"]["relations"]["version"][0]["is_last"]:
            return self
        else:
            conceptrecid = self.data["conceptrecid"]
            return get_record(conceptrecid, sandbox=self.from_sandbox, token=token)

    @property
    def from_sandbox(self):
        """
        Is the record from sandbox?
        :return: bool
        """
        if "sandbox" in self.data["links"]["self"]:
            return True
        else:
            return False

    def get_associated_versions(self, size=_default_size_query, **kwargs):
        """
        Returns a dictionary of all the versions of the current record

        Parameters
        ----------
        size : int, optional
            Number of results to return per page. Default is 25 (`_default_size_query`).
            Pagination is automatic, so all versions will be fetched regardless of this value.
        **kwargs : dict
            Zenodo query arguments. For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36

        Returns
        -------
        dict
            A dictionary of `{record_id: record_version}`
        """
        conceptrecid = self.data["conceptrecid"]
        params = {"all_versions": True, **kwargs}
        params.setdefault("size", size)

        versions = {}
        for record in search_records(f"conceptrecid:{conceptrecid}", sandbox=self.from_sandbox, **params):
            if "version" in record.metadata:
                versions[record.id] = record.metadata["version"]
            else:
                versions[record.id] = None
        return versions

    def _summary(self, linebreak="\n"):
        """
        Generate a summary of the record information.

        The information includes the record id, title, version, DOI, URL and description.
        If certain information is unavailable, it defaults to 'Unknown'.
        HTML tags in the description are stripped before being included in the summary.

        Parameters
        ----------
        linebreak : str, optional
            Line break character. Default is '\n'.

        Returns
        -------
        str
            The summary string.
        """
        lines = [f"=== Record #{self.id} ===", f"Title: {self.title}"]
        version = self.metadata.get("version", "Unknown")
        lines.append(f"Version: {version}")
        lines.append(f"DOI: {self.data.get('doi', 'Unknown')}")

        links = self.data.get("links", {})
        if "html" in links:
            lines.append(f"URL: {links['html']}")

        description = self.metadata.get("description", "")
        # Replace paragraph tags with newlines
        description = re.sub("<p>", linebreak, re.sub("</p>", linebreak, description))
        # Then strip the remaining HTML tags
        stripped_description = re.sub("<[^<]+?>", "", description)

        # Wrap description text to 70 characters wide
        wrapped_description = textwrap.fill(stripped_description, width=70)
        lines.append(wrapped_description)

        descrp = linebreak.join(lines)
        return descrp

    def print_info(self, linebreak="\n", file=sys.stdout):
        """
        Print the summary of the record information to a stream, or to `sys.stdout` by default.

        Parameters
        ----------
        linebreak : str, optional
            Line break character. Default is '\n'.
        file : file-like object, optional
            A file-like object (stream). Defaults to the current sys.stdout.

        Returns
        -------
        None
        """
        print(self._summary(linebreak=linebreak), file=file)

    @classmethod
    def from_id(cls, record_id, sandbox=False):
        """
        Retrieve a record from its record id.

        Parameters
        ----------
        record_id : int
            The id of the record to retrieve.
        sandbox : bool, optional
            True to use Zenodo's sandbox.

        Returns
        -------
        eossr.api.zenodo.Record
            The retrieved record.
        """
        record = get_record(record_id, sandbox=sandbox)
        return record

    def get_codemeta(self, **zipurl_kwargs):
        """
        Get codemeta metadata from the record (can also be in a zip archive).
        Raises an error if no `codemeta.json` file is found.

        Parameters
        ----------
        zipurl_kwargs : dict
            kwargs for `eossr.utils.ZipUrl`

        Returns
        -------
        dict
            codemeta metadata
        Raises
        ------
        FileNotFoundError
            If no `codemeta.json` file is found in the record.
        """
        if "files" not in self.data:
            raise FileNotFoundError(f"The record {self.id} does not contain any file")

        codemeta_paths = [s for s in self.filelist if Path(s.rsplit("/content", maxsplit=1)[0]).name == "codemeta.json"]
        ziparchives = [s for s in self.filelist if s.endswith(".zip/content")]
        if len(codemeta_paths) >= 1:
            # if there are more than one codemeta file in the repository, we consider the one in the root directory,
            # hence the one with the shortest path
            chosen_codemeta = min(codemeta_paths, key=len)
            return json.loads(urlopen(chosen_codemeta).read())
        elif len(ziparchives) > 0:
            for zipurl in ziparchives:
                try:
                    return get_codemeta_from_zipurl(zipurl, **zipurl_kwargs)
                except FileNotFoundError:
                    pass
            raise FileNotFoundError(f"No `codemeta.json` file found in record {self.id}")
        else:
            raise FileNotFoundError(f"No `codemeta.json` file found in record {self.id}")

    @property
    def doi(self):
        if "doi" not in self.data:
            raise KeyError(f"Record {self.id} does not have a doi")
        return self.data["doi"]

    @property
    def web_url(self):
        """
        Get the web URL of the record.

        Returns
        -------
        str
            The web URL of the record.
        """
        base_url = zenodo_sandbox_url if self.from_sandbox else zenodo_url
        return f"{base_url}/records/{self.id}"

    def get_mybinder_url(self):
        """
        Returns a URL to a mybinder instance of that record

        :return: str
        """
        binder_zenodo_url = "https://mybinder.org/v2/zenodo/"
        doi = self.doi
        return binder_zenodo_url + doi

    def download(self, directory=".", max_workers=None):
        """
        Download the record to a directory.

        Parameters
        ----------
        directory: str or Path
            Directory where to download the record content
        max_workers: int or None
            Number of workers to use for the download. If None, use all available workers.
        """
        # Create the directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)

        def download_file(url, path):
            response = requests.get(url, stream=True, timeout=_default_timeout)
            if response.status_code == 200:
                with open(path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                raise Exception(f"Failed to download file from {url}")

        def remove_trailing_content(url):
            return url.rsplit("/content", maxsplit=1)[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(
                    download_file, url, f"{directory}/{os.path.basename(remove_trailing_content(url))}"
                ): url
                for url in self.filelist
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    future.result()
                    print(f"{url} : Download complete")
                except Exception as exc:
                    print(f"{url} generated an exception: {exc}")


def query_records(search, sandbox=False, **kwargs):
    """
    Query Zenodo for a record whose name or description includes the provided string `search`.

    Parameters
    ----------
    search : str
        The string to search for in the name or description of the record.
    sandbox : bool, optional
        True to search in the sandbox, False to search in the production environment.
        Default is False.
    **kwargs : dict
        Additional query arguments for Zenodo.
        For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36.
        Common arguments are:
            - size : int
                Number of results to return. Default is 100.
            - all_versions : int
                Show (1) or hide (0) all versions of records.
            - type : str or list[str]
                Records of the specified type (Publication, Poster, Presentation, Software, ...).
                A logical OR is applied in case of a list.
            - subject : str or list[str]
                Records with the specified keywords or subjects (case sensitive).
                A logical OR is applied in case of a list.
            - communities : str or list[str]
                Records from the specified communities.
                A logical OR is applied in case of a list.
            - file_type : str or list[str]
                Records from the specified file_type.
                A logical OR is applied in case of a list.

    Returns
    -------
    requests.response
        The response from the Zenodo API.
    """
    return _query("records", search=search, sandbox=sandbox, **kwargs)


def _zenodo_get_factory(endpoint):
    """
    Factory (internal) method for creating functions that get something on Zenodo from its ID.

    Parameters
    ----------
    endpoint : str
        The Zenodo API endpoint to use (e.g., "records", "communities").

    Returns
    -------
    function
        A function that takes an ID and optional parameters and returns the corresponding Zenodo record.

    Raises
    ------
    HTTPError
        If the GET request to the Zenodo API returns an error status code.

    Examples
    --------
    To create a function that retrieves a Zenodo record by its ID, use the following code:

    >>> get_record = zenodo_get_factory("records")
    >>> record = get_record(1234)

    This will retrieve the Zenodo record with ID 1234.
    """

    def api_function(id, sandbox=False, token=None):
        base_url = zenodo_sandbox_api_base_url if sandbox else zenodo_api_base_url
        url = f"{base_url}{endpoint}/{id}"
        # Make a GET request to the Zenodo API
        params = {"access_token": token} if token else {}
        response = requests.get(url, params=params, timeout=_default_timeout)

        # if response.status_code == 200:
        #     return response.json()
        # else:
        #     http_status.ZenodoHTTPStatus(response)
        http_status.ZenodoHTTPStatus(response)
        return response.json()

    api_function.__doc__ = f"Get an object from its ID in {endpoint}"
    return api_function


def get_record(record_id, sandbox=False, token=None) -> Record:
    """
    Get a Zenodo record from its ID.

    Parameters
    ----------
    record_id : int
        The ID of the Zenodo record to retrieve.
    sandbox : bool, optional
        Whether to use the Zenodo sandbox API or not. Default is False.
    token : str, optional
        The Zenodo API token to use for authentication. Only necessary for private records.

    Returns
    -------
    record : Record
        The Zenodo record corresponding to the given ID.

    Raises
    ------
    HTTPError
        If the GET request to the Zenodo API returns an error status code.

    Examples
    --------
    >>> record = get_record(54354)
    """
    return Record(_zenodo_get_factory("records")(record_id, sandbox=sandbox, token=token))


def get_community(community_id, sandbox=False, token=None) -> dict:
    """
    Get a Zenodo community from its ID.

    Parameters
    ----------
    community_id : int
        The ID of the Zenodo community to retrieve.
    sandbox : bool, optional
        Whether to use the Zenodo sandbox API or not. Default is False.
    token : str, optional
        The Zenodo API token to use for authentication. Only necessary for private communities.

    Returns
    -------
    dict
        The Zenodo community corresponding to the given ID.

    Raises
    ------
    HTTPError
        If the GET request to the Zenodo API returns an error status code.
    """
    return _zenodo_get_factory("communities")(community_id, sandbox=sandbox, token=token)


def get_license(license_id, sandbox=False, token=None) -> dict:
    """
    Get a Zenodo license from its ID.

    Parameters
    ----------
    license_id : str
        The ID of the Zenodo license to retrieve.
    sandbox : bool, optional
        Whether to use the Zenodo sandbox API or not. Default is False.
    token : str, optional
        The Zenodo API token to use for authentication. Only necessary for private licenses.

    Returns
    -------
    dict
        The Zenodo license corresponding to the given ID.

    Raises
    ------
    HTTPError
        If the GET request to the Zenodo API returns an error status code.
    """
    return _zenodo_get_factory("vocabularies/licenses")(license_id, sandbox=sandbox, token=token)


def get_funder(funder_id, sandbox=False, token=None) -> dict:
    """
    Get a Zenodo funder from its ID.

    Parameters
    ----------
    funder_id : int
        The ID of the Zenodo funder to retrieve.
    sandbox : bool, optional
        Whether to use the Zenodo sandbox API or not. Default is False.
    token : str, optional
        The Zenodo API token to use for authentication. Only necessary for private funders.

    Returns
    -------
    dict
        The Zenodo funder corresponding to the given ID.

    Raises
    ------
    HTTPError
        If the GET request to the Zenodo API returns an error status code.
    """
    return _zenodo_get_factory("funders")(funder_id, sandbox=sandbox, token=token)


def get_supported_licenses() -> list[str]:
    """
    Recovers the list of Zenodo supported license IDs.
    Makes a request.get() call to Zenodo.

    Returns
    -------
    list
        A list of license IDs for all Zenodo supported licenses
    """
    licenses = search_licenses()
    return [license["id"] for license in licenses]


def _query(field, search="", sandbox=False, request_params=None, **zenodo_kwargs):
    """
    Query Zenodo API to search for records, funders, grants, communities, or licenses.

    Parameters
    ----------
    field : str
        Where to search: 'records', 'funders', 'grants', 'communities', 'licenses'.
    search : str, optional
        The search query string.
    sandbox : bool, optional
        True to search in the sandbox, False to search in the production environment.
    request_params : dict, optional
        Parameters for the `requests.get` function. Override the class parameters.
        e.g. {'timeout': 10}.
    **zenodo_kwargs : dict
        Zenodo query arguments and common requests arguments.
        For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36.
        Common arguments are:
            - access_token : str
                Zenodo access token. May be necessary for private queries.
            - size : int
                Number of results to return. Default is 100.
            - all_versions : int
                Show (1) or hide (0) all versions of records.
            - type : str or list[str]
                Records of the specified type (Publication, Poster, Presentation, Software, ...).
                A logical OR is applied in case of a list.
            - subject : str or list[str]
                Records with the specified keywords or subjects (case sensitive).
                A logical OR is applied in case of a list.
            - communities : str or list[str]
                Query in the specified communities.
                A logical OR is applied in case of a list.
            - file_type : str or list[str]
                Records with the specified file_type.
                A logical OR is applied in case of a list.

    Returns
    -------
    requests.response
        The response object from the Zenodo API.

    Raises
    ------
    ZenodoHTTPStatus
        If the response from the Zenodo API is not successful.

    Notes
    -----
    This function queries the Zenodo API to search for records, funders, grants, communities, or licenses.
    The `field` parameter specifies where to search, and the `search` parameter allows for a specific search query.
    Additional query arguments can be passed as keyword arguments (`**zenodo_kwargs`).

    Examples
    --------
    >>> response = _query('records', search='data science', size=10)
    >>> print(response.json())
    """

    def lowercase(param):
        if isinstance(param, str):
            param = param.lower()
        if isinstance(param, list):
            param = [char.lower() for char in param]
        return param

    if request_params is None:
        request_params = {}
    request_params.setdefault("timeout", _default_timeout)

    # zenodo can't handle '/' in search query
    search = search.replace("/", " ")

    params = {"q": search, **zenodo_kwargs}

    for param_name in ["communities", "type", "file_type"]:
        if param_name in zenodo_kwargs:
            params[param_name] = lowercase(zenodo_kwargs[param_name])

    api_url = zenodo_api_base_url if not sandbox else zenodo_sandbox_api_base_url
    url = api_url + f"/{field}?"
    response = requests.get(url, params=params, **request_params)
    http_status.ZenodoHTTPStatus(response)
    return response


def _search(field, search="", sandbox=False, **kwargs) -> list[dict]:
    """
    Text based search base function with automatic pagination.
    Returns all matching results as a list of hits (JSON dict containing the object metadata).

    Parameters
    ----------
    field : str
        Where to search: 'records', 'funders', 'grants', 'communities', 'licenses'
    search : str, optional
        The search query, by default ''
    sandbox : bool, optional
        True to search in the sandbox, by default False
    **kwargs
        Zenodo query arguments and common requests arguments.
        For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36
        Common arguments are:
            - access_token : str
                Zenodo access token
                May be necessary for private queries
            - size : int
                Number of results to return per page.
                Default = 25 (max for unauthenticated requests).
            - all_versions : int
                Show (1) or hide (0) all versions of records
            - type : str or list[str]
                Records of the specified type (Publication, Poster, Presentation, Software, ...)
                A logical OR is applied in case of a list
            - subject : str or list[str]
                Records with the specified keywords or subjects (case sensitive)
                A logical OR is applied in case of a list
            - communities : str or list[str]
                Query in the specified communities
                A logical OR is applied in case of a list
            - file_type : str or list[str]
                Records with the specified file_type
                A logical OR is applied in case of a list

    Returns
    -------
    list[dict]
        A list of matching hits (JSON dict containing the object metadata).
    """
    query = _query(field, search=search, sandbox=sandbox, **kwargs)
    http_status.ZenodoHTTPStatus(query)

    hits = [hit for hit in query.json()["hits"]["hits"]]
    return hits


def search_records(search="", sandbox=False, **kwargs) -> list[Record]:
    """
    Text based search of records.
    Returns a list of Record objects.

    Parameters
    ----------
    search : str, optional
        The search query. (default is '')
    sandbox : bool, optional
        True to search in the sandbox. (default is False)
    **kwargs : dict
        Additional keyword arguments for Zenodo query and common requests arguments.

    Returns
    -------
    list
        A list of Record objects.

    Notes
    -----
    For an exhaustive list of query arguments, see the query arguments at https://developers.zenodo.org/#list36.

    Examples
    --------
    >>> search_records('data science', sandbox=True)
    """
    hits = _search("records", search=search, sandbox=sandbox, **kwargs)
    return [Record(hit) for hit in hits]


def search_funders(search="", sandbox=False, **kwargs):
    """
    Text based search of funders. Returns all matching funders.

    Parameters
    ----------
    search : str
        The search query.
    sandbox : bool, optional
        True to search in the sandbox, False otherwise.
    **kwargs : dict
        Additional Zenodo query arguments. For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36.

    Returns
    -------
    list of dict
        A list of all funders matching the search query.

    Examples
    --------
    >>> search_funders('European Commission')
    [{'id': '...', 'name': 'European Commission'}, ...]
    """
    hits = _search("funders", search=search, sandbox=sandbox, **kwargs)
    return hits


# 2023-11-14: Does not work anymore with invenio rdm backend
# def search_grants(search='', sandbox=False, **kwargs):
#     """
#     https://help.zenodo.org/guides/search/

#     :param search: str
#     :param sandbox: boolean
#         True to search in the sandbox
#     :param kwargs: Zenodo query arguments.
#         For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36
#         Common arguments are:
#             - size: int
#                 Number of results to return
#                 Default = 5
#     :return: [dict]
#     """
#     kwargs.setdefault('size', 5)
#     hits = _search('grants', search=search, sandbox=sandbox, **kwargs)
#     return hits


def search_communities(search="", sandbox=False, **kwargs):
    """
    Text based search of communities. Returns all matching communities.

    Parameters
    ----------
    search : str
        The search query.
    sandbox : bool, optional
        True to search in the sandbox, False otherwise.
    **kwargs : dict
        Additional query arguments. For an exhaustive list, see the query arguments at
        https://developers.zenodo.org/#list36.

    Returns
    -------
    list of dict
        A list of all communities matching the search query.
    """
    hits = _search("communities", search=search, sandbox=sandbox, **kwargs)
    return hits


def search_licenses(search="", sandbox=False, **kwargs):
    """
    Text based search of licenses. Returns all matching licenses.

    Parameters
    ----------
    search : str
        The search query for licenses.
    sandbox : bool, optional
        True to search in the sandbox, False otherwise.
    **kwargs : dict
        Additional query arguments for Zenodo search.

    Returns
    -------
    list of dict
        A list of dictionaries representing all matching licenses.

    Notes
    -----
    For an exhaustive list of query arguments, see the Zenodo API documentation:
    https://developers.zenodo.org/#list36
    """
    kwargs.setdefault("size", 1000)
    hits = _search("licenses", search=search, sandbox=sandbox, **kwargs)
    return hits


def is_live(sandbox=False):
    """
    Check if Zenodo website is live

    Parameters
    ----------
    sandbox : bool, optional
        True to test sandbox instead

    Returns
    -------
    bool
        True if live
    """
    url = zenodo_sandbox_api_base_url if sandbox else zenodo_api_base_url
    req = requests.get(url + "/records?size=1", timeout=_default_timeout)
    return req.status_code == 200


def query_deposit(deposit_id, access_token, sandbox=False):
    """
    Query a deposit based on its ID.

    Parameters
    ----------
    deposit_id : str or int
        The ID of the deposit to query.
    access_token : str
        The access token for authentication.
    sandbox : bool, optional
        Whether to use the sandbox environment. Defaults to False.

    Returns
    -------
    requests.response
        The query result.
    """
    return _query(f"deposit/depositions/{deposit_id}", "", sandbox=sandbox, access_token=access_token)


def query_deposits(search, access_token, sandbox=False, **kwargs):
    """
    Query Zenodo for deposits based on the given search criteria.

    Parameters
    ----------
    search : str
        The search criteria to query Zenodo.
    access_token : str
        Zenodo access token. May be necessary for private queries.
    sandbox : bool, optional
        True to search in the sandbox, False otherwise. Default is False.
    **kwargs : dict
        Additional Zenodo query arguments and common requests arguments.

    Returns
    -------
    requests.response
        The response from the Zenodo API.

    Notes
    -----
    For an exhaustive list of query arguments, see the Zenodo API documentation:
    https://developers.zenodo.org/#list36

    Common arguments include:
    - size : int
        Number of results to return. Default is 100.
    - all_versions : int
        Show (1) or hide (0) all versions of records.
    - type : str or list[str]
        Records of the specified type (Publication, Poster, Presentation, Software, ...).
        A logical OR is applied in case of a list.
    - subject : str or list[str]
        Records with the specified keywords or subjects (case sensitive).
        A logical OR is applied in case of a list.
    - communities : str or list[str]
        Query in the specified communities.
        A logical OR is applied in case of a list.
    - file_type : str or list[str]
        Records with the specified file_type.
        A logical OR is applied in case of a list.
    """
    field = "deposit/depositions"
    kwargs.setdefault("access_token", access_token)
    return _query(field, search=search, sandbox=sandbox, **kwargs)


def get_deposit(deposit_id, access_token, sandbox=False):
    """
    Get a deposit from its ID.

    Parameters
    ----------
    deposit_id : str or int
        The ID of the deposit to retrieve.

    access_token : str
        The access token for authentication.

    sandbox : bool, optional
        Whether to use the sandbox environment. Defaults to False.

    Returns
    -------
    dict
        The deposit corresponding to the given ID.
    """
    return _zenodo_get_factory("deposit/depositions")(deposit_id, sandbox=sandbox, token=access_token)


class PendingRequest:
    def __init__(self, request_data, sandbox=False, access_token=None):
        """
        Initialize a Zenodo object.

        Args:
            request_data (dict): The request data.
            sandbox (bool, optional): Whether to use the Zenodo sandbox. Defaults to False.
            access_token (str, optional): The access token for authentication. Defaults to None.
        """
        self.data = request_data.copy()
        self.access_token = access_token
        self.sandbox = sandbox
        self._record = None
        self._timeline = None

    @property
    def url(self):
        """
        Get the URL for this request
        """
        community_id = self.data.get("receiver", {}).get("community", None)
        if not community_id:
            raise KeyError("No community id found, can't reconstruct url")
        else:
            return (
                self.data.get("links", {})
                .get("self_html", "")
                .replace("requests", f"communities/{community_id}/requests")
            )

    @property
    def parameters(self):
        """
        Returns the parameters required for the Zenodo API.

        Returns:
            dict: A dictionary containing the access token.
        """
        return {"access_token": self.access_token}

    @property
    def record(self):
        """
        Get the Zenodo record associated with this object.

        Returns:
            Record: The Zenodo record object.
        """
        if self._record is None and self.record_id is not None:
            self._record = Record.from_id(self.record_id, sandbox=self.sandbox)
        return self._record

    @property
    def id(self):
        return self.data.get("id")

    @property
    def title(self):
        return self.data.get("title", None)

    @property
    def status(self):
        return self.data.get("status", None)

    @property
    def is_open(self):
        return self.data.get("is_open", None)

    @property
    def record_id(self):
        return self.data.get("topic", {}).get("record", None)

    def get_timeline(self, force_refresh=False, expand=False, **parameters):
        """
        Retrieves the timeline data for the Zenodo API.

        Args:
            force_refresh (bool, optional): If True, forces a refresh of the timeline data. Defaults to False.
            expand (bool, optional): If True, expands the timeline data. Defaults to False.
            **parameters: Additional parameters to be passed in the request.

        Returns:
            dict: The timeline data in JSON format.
        """
        params = self.parameters.copy()
        params.update(parameters)
        if self._timeline is None or force_refresh:
            if "links" not in self.data and "timeline" not in self.data.get("links"):
                raise KeyError(f"No timeline link found in pending request {self.id}")
            url = self.data.get("links").get("timeline")
            if expand:
                url += "?expand=true"
            self._timeline = requests.get(url, params=params).json()
        return self._timeline

    def display_discussion(self):
        """
        Retrieves the discussion timeline and displays the content of each hit.
        """
        timeline = self.get_timeline()
        for hit in timeline["hits"]["hits"]:
            if hit["type"] == "C":
                created_by = hit["created_by"]["user"]
                updated = datetime.fromisoformat(hit["updated"])
                content = BeautifulSoup(hit["payload"]["content"], "html.parser").get_text()
                print(f"User {created_by} ({updated.strftime('%Y-%m-%d %H:%M:%S')}): {content}")

    def __str__(self):
        return f"Record ID: {self.record_id}\nTitle: {self.title}\nStatus: {self.status}\n"

    def __repr__(self):
        return f"<PendingRequest {self.id}>"

    def accept(self):
        """
        Accepts the request by sending a POST request to the accept URL.
        Raises:
            KeyError: if no accept URL is found for the request.
        """
        accept_url = self.data.get("links", {}).get("actions", {}).get("accept")
        if accept_url:
            response = requests.post(accept_url, params=self.parameters)
            response.raise_for_status()
            if response.status_code == 200:
                print("Request accepted successfully.")
        else:
            raise KeyError("No accept URL found for this request.")

    def decline(self):
        """
        Declines the request by sending a POST request to the decline URL.

        Raises:
            KeyError: If no decline URL is found for this request.
        """
        decline_url = self.data.get("links", {}).get("actions", {}).get("decline")
        if decline_url:
            response = requests.post(decline_url, params=self.parameters)
            response.raise_for_status()
            if response.status_code == 200:
                print("Request declined successfully.")
        else:
            raise KeyError("No decline URL found for this request.")

    def post_message(self, message):
        """
        Posts a message to the Zenodo comments section.

        Args:
            message (str): The message to be posted.

        Returns:
            bool: True if the message was successfully posted, raises an HTTPStatusError otherwise.
        """
        comments_url = self.data["links"]["comments"] + "?expand=1"
        data = {
            "payload": {
                "content": f"<p>{message}</p>",
                "format": "html",
            }
        }
        response = requests.post(comments_url, params=self.parameters, data=json.dumps(data), timeout=_default_timeout)
        http_status.ZenodoHTTPStatus(response)
        if response.status_code == 201:
            return True
        else:
            return False
