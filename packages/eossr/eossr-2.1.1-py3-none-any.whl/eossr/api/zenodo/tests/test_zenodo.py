#!/usr/bin/env python
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import pytest
import requests
from bs4 import BeautifulSoup

from eossr.api.ossr import sandbox_escape_community
from eossr.api.zenodo import (
    Record,
    ZenodoAPI,
    get_community,
    get_deposit,
    get_funder,
    get_license,
    get_record,
    query_deposits,
    search_records,
    zenodo,
    zenodo_url,
)
from eossr.api.zenodo.http_status import HTTPStatusError
from eossr.api.zenodo.zenodo import PendingRequest, is_live, query_records
from eossr.metadata.tests import ZENODO_TEST_FILE

# test deactivated at the moment
test_record_sandbox = 28069  # test library in sandbox (owner: eossr)
test_record_sandbox_draft = 778  # test draft record (owner: eossr)
test_pending_request_sandbox = 821
eossr_record_id = 7940962
tests_default_timeout = 30


def test_is_live():
    assert is_live(sandbox=False)
    assert is_live(sandbox=True)


@pytest.fixture
def temp_dir_with_file():
    with tempfile.TemporaryDirectory() as tmpdirname:
        print(f"tmpdir {tmpdirname}")
        shutil.copy(ZENODO_TEST_FILE, Path(tmpdirname, ".zenodo.json"))

        _, filename = tempfile.mkstemp(dir=tmpdirname)
        Path(filename).write_text("Hello from eossr unit tests")

        yield tmpdirname, filename


class TestZenodoApiSandbox(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestZenodoApiSandbox, self).__init__(*args, **kwargs)
        self.token = "FakeToken"
        self.zenodo = ZenodoAPI(access_token=self.token, sandbox=True)

        # Note: Zenodo API limits page size to 25 for unauthenticated and 100 for authenticated requests
        self.zenodo.parameters["size"] = 25
        self.zenodo.parameters["all_versions"] = True

    def test_initialization_sandbox(self):
        from eossr.api.zenodo import zenodo_sandbox_api_base_url

        assert isinstance(self.zenodo, ZenodoAPI)
        assert self.zenodo.api_base_url == zenodo_sandbox_api_base_url
        assert self.zenodo.access_token == self.token

    def test_query_community_entries(self):
        community_entries = self.zenodo.query_community_records("escape2020")
        assert isinstance(community_entries, requests.models.Response)


class TestZenodoAPINoToken(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestZenodoAPINoToken, self).__init__(*args, **kwargs)
        self.token = ""
        self.zenodo = ZenodoAPI(access_token=self.token, sandbox=False)

    def test_initialization(self):
        from eossr.api.zenodo import zenodo_api_base_url

        assert isinstance(self.zenodo, ZenodoAPI)
        assert self.zenodo.api_base_url == zenodo_api_base_url
        assert self.zenodo.access_token == self.token

    @pytest.mark.xfail(raises=ValueError)
    def test_raise_token_status(self):
        # A value error should be raised as no valid token was provided
        self.zenodo._raise_token_status()


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
class TestZenodoAPITokenSandbox(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestZenodoAPITokenSandbox, self).__init__(*args, **kwargs)
        self.token = os.getenv("SANDBOX_ZENODO_TOKEN")
        self.zenodo = ZenodoAPI(access_token=self.token, sandbox=True)

    def test_init(self):
        assert self.zenodo.access_token == os.getenv("SANDBOX_ZENODO_TOKEN")

    def test_raise_token_status(self):
        self.zenodo._raise_token_status()

    def test_query_user_deposits(self):
        self.zenodo.query_user_deposits()

    def test_create_erase_new_deposit(self):
        create_new_deposit = self.zenodo.create_new_deposit()
        assert isinstance(create_new_deposit, requests.models.Response)
        record_id = create_new_deposit.json()["id"]
        erase_deposit = self.zenodo.erase_deposit(record_id)
        assert isinstance(erase_deposit, requests.models.Response)

    def test_pending_request(self):
        z = self.zenodo
        pending_requests = z.get_community_pending_requests(sandbox_escape_community)
        requests_ids = [rec.data["id"] for rec in pending_requests]
        # pending request in escape2020 sandbox community - 2023-11-13
        assert "6eaf34cf-f63d-4604-8b43-a6198bfdaa5d" in requests_ids

    def test_find_similar_records_sandbox(self):
        self.zenodo.parameters.update({"size": 100})
        existing_record = Record.from_id(test_record_sandbox, sandbox=True)
        assert len(self.zenodo.find_similar_records(existing_record)) > 0

    def test_get_user_records(self):
        records = self.zenodo.get_user_records()
        assert isinstance(records[0], Record)


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
def test_upload_package(temp_dir_with_file):
    tmpdirname, _ = temp_dir_with_file
    zenodo = ZenodoAPI(access_token=os.getenv("SANDBOX_ZENODO_TOKEN"), sandbox=True)
    # create new record
    deposit_id = zenodo.upload_dir_content(tmpdirname, publish=True)
    print(f"{deposit_id} created")

    # update existing record
    _, filename = tempfile.mkstemp(dir=tmpdirname)
    Path(filename).write_text("2nd upload from eossr unit tests")
    new_deposit_id = zenodo.upload_dir_content(tmpdirname, record_id=deposit_id, publish=False)
    zenodo.erase_deposit(new_deposit_id)
    print(f"{new_deposit_id} created and deleted")


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
def test_check_upload_to_zenodo(temp_dir_with_file):
    tmpdirname, _ = temp_dir_with_file

    zenodo = ZenodoAPI(access_token=os.getenv("SANDBOX_ZENODO_TOKEN"), sandbox=True)
    # 1 - Test connection
    test_connection = zenodo.query_user_deposits()
    assert test_connection.status_code == 200

    # 2 - Test new entry
    new_deposit = zenodo.create_new_deposit()
    assert new_deposit.status_code == 201

    # 3 - Test upload metadata
    test_deposit_id = new_deposit.json()["id"]
    with open(zenodo.path_zenodo_file(tmpdirname)) as file:
        metadata_entry = json.load(file)
    updated_metadata = zenodo.set_deposit_metadata(test_deposit_id, json_metadata=metadata_entry)
    assert updated_metadata.status_code == 200

    # 4 - Test delete entry
    delete_test_entry = zenodo.erase_deposit(test_deposit_id)
    assert delete_test_entry.status_code == 204

    # 2023-15-11 - not working at the moment with Zenodo API
    # def test_accept_community_request(self):
    #     zen = self.zenodo
    #     record_id = test_record_sandbox
    #     # Add to escape2020 community and test request
    #     meta = {'communities': [{'identifier': sandbox_escape_community}]}
    #     try:
    #         zen.update_record_metadata(record_id, meta)
    #     except (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError):
    #         # 2023-11-13: Zenodo Sandbox API returns 504 (Gateway Time-out) instead of 204
    #         # Deleting a record in sandbox takes a long time... passing atm
    #         return None
    #     # Give some time to zenodo to process the request and update its database
    #     # time.sleep(10)
    #     records = zen.get_community_pending_requests(sandbox_escape_community)
    #     assert record_id in [rec['id'] for rec in records]
    #     # Accept request
    #     zen.answer_to_pending_request(
    #         sandbox_escape_community, record_id, 'accept')
    #     records = zen.get_community_pending_requests(sandbox_escape_community)
    #     assert record_id not in [rec['id'] for rec in records]
    #     # Remove from community
    #     meta = {'communities': []}
    #     try:
    #         zen.update_record_metadata(record_id, meta)
    #     except (requests.exceptions.ReadTimeout, requests.exceptions.HTTPError):
    #         # 2023-11-13: Zenodo Sandbox API returns 504 (Gateway Time-out) instead of 204
    #         # Deleting a record in sandbox takes a long time... passing atm
    #         pass


@pytest.mark.skipif(os.getenv("ZENODO_TOKEN") is None, reason="ZENODO_TOKEN not defined")
class TestZenodoAPIToken(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestZenodoAPIToken, self).__init__(*args, **kwargs)
        self.token = os.getenv("ZENODO_TOKEN")
        self.zenodo = ZenodoAPI(access_token=self.token, sandbox=False)

    def test_query_user(self):
        self.zenodo.query_user_deposits()


def test_search_records():
    zenodo_records = search_records(
        "ESCAPE template project",
        all_versions=True,
        timeout=tests_default_timeout,
    )
    assert len(zenodo_records) > 1
    all_dois = [r.data["doi"] for r in zenodo_records]
    assert "10.5281/zenodo.4923992" in all_dois


@pytest.mark.xfail(raises=HTTPStatusError)
def test_get_record_42():
    get_record(42)


def test_query_record_10005007():
    answer = query_records("eossr", sandbox=True)
    assert answer.status_code == 200
    assert len(answer.json()["hits"]["hits"]) >= 1


@pytest.fixture
def record_4923992():
    return get_record(4923992)


def test_record(record_4923992):
    assert record_4923992.data["conceptdoi"] == "10.5281/zenodo.3572654"
    record_4923992.print_info()
    codemeta = record_4923992.get_codemeta()
    assert isinstance(codemeta, dict)
    assert codemeta["name"] == "ESCAPE template project"
    record_4923992.get_mybinder_url()


def test_web_url(record_4923992):
    """
    Unit test for the web_url property.
    """
    # Test for production URL (record_4923992 is from production)
    expected_prod_url = f"{zenodo_url}/records/4923992"
    assert record_4923992.web_url == expected_prod_url, (
        f"Expected {expected_prod_url}, but got {record_4923992.web_url}"
    )
    assert requests.get(record_4923992.web_url, timeout=10).status_code == 200


def test_get_record_sandbox():
    record = get_record(test_record_sandbox, sandbox=True)
    assert record.data["doi"] == f"10.5072/zenodo.{test_record_sandbox}"


def test_write_record_zenodo(record_4923992, tmpdir):
    record_4923992._write_zenodo_deposit(filename=tmpdir / ".zenodo.json", validate=False)
    with open(tmpdir / ".zenodo.json") as file:
        json_dict = json.load(file)
    assert json_dict["title"] == "ESCAPE template project"
    assert json_dict["version"] == "v2.2"


def test_search_funders():
    funders = zenodo.search_funders("European Commission", timeout=tests_default_timeout)
    assert len(funders) >= 1


# def test_search_grants():
#     grants = zenodo.search_grants('code:824064')
#     assert len(grants) == 1
#     assert grants[0]['metadata']['acronym'] == 'ESCAPE'


def test_search_license():
    licenses = zenodo.search_licenses("MIT", timeout=tests_default_timeout)
    assert licenses[0]["title"] == {"en": "MIT License"}


def test_search_communities():
    communities = zenodo.search_communities(
        "id:8b951469-55d0-44f2-bb91-b541501c9c8e",
        timeout=tests_default_timeout,
    )
    assert communities[0]["slug"] == "escape2020"


def test_get_associated_versions():
    # ZenodoCI deprecated lib. A single version
    record = Record.from_id(4786641)
    versions = record.get_associated_versions()
    assert len(versions) == 1
    assert list(versions)[0] == record.id  # itself
    eossr_record = Record.from_id(6352039)
    eossr_record_versions = eossr_record.get_associated_versions()
    # Seven versions, to date 21/03/2022
    assert len(eossr_record_versions) >= 7
    for recid in eossr_record_versions.keys():
        assert eossr_record.data["conceptrecid"] == Record.from_id(recid).data["conceptrecid"]
    assert eossr_record_versions[5524913] == "v0.2"  # ID of eOSSR version v0.2


@pytest.mark.xfail(raises=FileNotFoundError)
def test_get_codemeta_fail():
    record = Record.from_id(3734091)
    record.get_codemeta()


def test_get_supported_licenses():
    zenodo_licenses = zenodo.get_supported_licenses()
    assert isinstance(zenodo_licenses, list)
    assert "mit" in zenodo_licenses
    assert "apache-2.0" in zenodo_licenses
    assert "apache-license-x." not in zenodo_licenses


def test_download_record():
    with tempfile.TemporaryDirectory() as tmpdir:
        record = Record.from_id(3743490)
        record.download(tmpdir)
        assert os.path.exists(f"{tmpdir}/template_project_escape-v1.1.zip")


def test_get_funder():
    funder_id = "00k4n6c32"  # European Commission
    funder = get_funder(funder_id, sandbox=True)
    assert isinstance(funder, dict)
    assert funder["id"] == funder_id
    assert funder["name"] == "European Commission"


def test_get_license():
    license_id = "mit"
    license = get_license(license_id, sandbox=True)
    assert isinstance(license, dict)
    assert license["id"] == license_id


def test_get_community():
    community_slug = sandbox_escape_community
    community = get_community(community_slug, sandbox=True)
    assert isinstance(community, dict)
    assert community["slug"] == community_slug
    assert community["id"] == "012c7725-ee21-4603-855d-e675842b4f7b"


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
def test_query_deposits():
    search = "eossr"
    access_token = os.getenv("SANDBOX_ZENODO_TOKEN")
    sandbox = True
    deposits = query_deposits(search, access_token, sandbox=sandbox, timeout=tests_default_timeout)
    assert isinstance(deposits, requests.Response)
    assert len(deposits.json()) > 0


@pytest.mark.skipif(os.getenv("EOSSR_SANDBOX_ZENODO_TOKEN") is None, reason="EOSSR_SANDBOX_ZENODO_TOKEN not defined")
def test_get_deposit():
    deposit = get_deposit(test_record_sandbox, sandbox=True, access_token=os.getenv("EOSSR_SANDBOX_ZENODO_TOKEN"))
    assert isinstance(deposit, dict)
    assert deposit["conceptdoi"] == f"10.5072/zenodo.{test_record_sandbox - 1}"


@pytest.mark.skipif(os.getenv("EOSSR_SANDBOX_ZENODO_TOKEN") is None, reason="EOSSR_SANDBOX_ZENODO_TOKEN not defined")
def test_post_message():
    request_data = {
        "id": "6eaf34cf-f63d-4604-8b43-a6198bfdaa5d",
        "links": {
            "timeline": "https://sandbox.zenodo.org/api/requests/6eaf34cf-f63d-4604-8b43-a6198bfdaa5d/timeline",
            "comments": "https://sandbox.zenodo.org/api/requests/6eaf34cf-f63d-4604-8b43-a6198bfdaa5d/comments",
        },
        "receiver": {"community": "012c7725-ee21-4603-855d-e675842b4f7b"},
        "topic": {"record": "27635"},
    }
    pending_request = PendingRequest(request_data, access_token=os.getenv("SANDBOX_ZENODO_TOKEN"))

    message = "Test message"
    response = pending_request.post_message(message)
    assert response is True

    time.sleep(1)

    timeline = pending_request.get_timeline(force_refresh=True, sort="newest")["hits"]["hits"]
    last_comment = timeline[0]
    assert last_comment["type"] == "C"
    assert BeautifulSoup(last_comment["payload"]["content"], "html.parser").get_text() == message

    delete_url = last_comment["links"]["self"]
    response = requests.delete(delete_url, params=pending_request.parameters, timeout=10)
    response.raise_for_status()

    assert response.status_code == 204
