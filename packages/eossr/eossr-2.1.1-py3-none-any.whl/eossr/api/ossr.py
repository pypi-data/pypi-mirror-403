#!/usr/bin/env python

from .zenodo import PendingRequest, Record, ZenodoAPI, query_records, search_records

__all__ = [
    "search_ossr_records",
    "get_ossr_records",
    "get_ossr_pending_requests",
]

escape_community = "escape2020"
sandbox_escape_community = "escape2020"


def search_ossr_records(search="", sandbox=False, **kwargs) -> list[Record]:
    """
    Search the OSSR for records whose names or descriptions include the provided string `search`.
    The default record type is 'software' or 'record'.
    If `size` is not specified or is larger than 25, pagination is used to retrieve all matching records.

    :param search: string
        A string to refine the search in the OSSR. The default will search for all records in the OSSR.
    :param sandbox: bool
        Indicates the use of sandbox zenodo or not.
    :param kwargs: Zenodo query arguments.
        For an exhaustive list, see the query arguments at https://developers.zenodo.org/#list36
        Common arguments are:
        - size: int
        Number of results to return. Default = 25
        - all_versions: int
        Show (1) or hide (0) all versions of records
        - type: string or list[string]
        Default: ['software', 'dataset']
        Records of the specified type (Publication, Poster, Presentation, Software, ...).
        A logical OR is applied in case of a list
        - subject: string or list[string]
        Records with the specified keywords. A logical OR is applied in case of a list
        - file_type: string or list[string]
        Records from the specified file_type. A logical OR is applied in case of a list

    :return: [Record]
    """

    # if another community is specified, a logical OR is applied by zenodo API,
    # thus potentially finding entries that are not part of escape2020
    # ruling out that possibility at the moment
    if "communities" in kwargs and kwargs["communities"] != escape_community:
        raise NotImplementedError(
            "Searching in another community will search outside of the OSSR. Use `eossr.api.zenodo.search_records` to do so"
        )

    # OSSR is limited to software and datasets
    kwargs.setdefault("type", ["software", "dataset"])
    kwargs["communities"] = escape_community

    page_size = 25  # Zenodo's limit per page
    if "size" in kwargs and kwargs["size"] <= page_size:
        return search_records(search, sandbox=sandbox, **kwargs)
    else:
        # Paginate through results
        return _paginate_ossr_records(search, sandbox=sandbox, page_size=page_size, **kwargs)


def _paginate_ossr_records(search, sandbox=False, page_size=25, **kwargs) -> list[Record]:
    """
    Paginate through OSSR records to retrieve all records matching the search criteria.
    :param search: string
        A string to refine the search in the OSSR.
    :param sandbox: bool
        Indicates the use of sandbox zenodo or not.
    :param page_size: int
        Number of results per page.
    :param kwargs: Zenodo query arguments.
    :return: [Record]
    """
    # Get the total number of OSSR records
    params = kwargs.copy()
    params["size"] = 1  # Only need 1 result to get the total count
    response = query_records(search, sandbox=sandbox, **params)
    number_of_ossr_entries = response.json()["aggregations"]["access_status"]["buckets"][0]["doc_count"]

    # Determine how many records to retrieve
    requested_size = kwargs.get("size", number_of_ossr_entries)
    total_to_fetch = min(requested_size, number_of_ossr_entries)

    # Paginate through all records
    all_records = []
    page = 1
    remaining = total_to_fetch

    while remaining > 0:
        current_page_size = min(page_size, remaining)
        kwargs["size"] = current_page_size
        kwargs["page"] = page

        records = search_records(search, sandbox=sandbox, **kwargs)

        if not records:
            break

        all_records.extend(records)
        remaining -= len(records)
        page += 1

        # If we got fewer records than requested, we've reached the end
        if len(records) < current_page_size:
            break

    return all_records


def get_ossr_pending_requests(zenodo_token, **params) -> list[PendingRequest]:
    """
    Get a list of records that have been requested to be added to the OSSR.

    :param zenodo_token: str
        The Zenodo API token.
    :param params: dict
        Parameters for the request. Override the class parameters.
    :return: [eossr.api.zenodo.zenodo.PendingRequest]
    """
    zen = ZenodoAPI(access_token=zenodo_token)
    return zen.get_community_pending_requests(escape_community, **params)


def get_ossr_records(sandbox=False, **kwargs) -> list[Record]:
    """
    Get a list of records that have been added to the OSSR.

    :return:
    """
    return search_ossr_records("", sandbox=sandbox, **kwargs)
