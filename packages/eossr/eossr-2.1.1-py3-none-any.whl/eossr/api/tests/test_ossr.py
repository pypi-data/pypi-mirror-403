import os

import pytest

from eossr import api
from eossr.api.ossr import get_ossr_pending_requests


def test_search_ossr_records_size():
    ossr_records = api.search_ossr_records(size=27)
    assert len(ossr_records) == 27


def test_search_ossr_records_all_versions():
    ossr_records = api.search_ossr_records(search="eossr", all_versions=True)
    all_ids = [rec.data["id"] for rec in ossr_records]
    assert 5524913 in all_ids  # id of the version v0.2 of the eossr


@pytest.mark.skipif(os.getenv("ZENODO_TOKEN") is None, reason="ZENODO_TOKEN not defined")
def test_get_ossr_pending_requests():
    # Use the actual ZenodoAPI class
    zenodo_token = os.getenv("ZENODO_TOKEN")

    # Call the function with a dummy token
    result = get_ossr_pending_requests(zenodo_token)

    # Assert that the function returns the expected result
    assert isinstance(result, list)
    assert all(isinstance(item, api.zenodo.zenodo.PendingRequest) for item in result)
