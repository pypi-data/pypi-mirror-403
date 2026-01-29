import json

import pytest

from eossr.metadata.codemeta2zenodo import (
    CodeMeta2ZenodoController,
    codemeta2ossr,
    parse_codemeta_and_write_zenodo_metadata_file,
)
from eossr.metadata.tests import CODEMETA_TEST_FILE


@pytest.fixture()
def tmp_dir(tmp_path):
    test_dir = tmp_path
    test_dir.mkdir(exist_ok=True)
    return test_dir


@pytest.fixture
def codemeta_test():
    with open(CODEMETA_TEST_FILE) as f:
        return json.load(f)


def test_Codemeta2ZenodoController(codemeta_test):
    converter = CodeMeta2ZenodoController(codemeta_test)
    assert converter.codemeta_data == codemeta_test
    converter.convert()
    assert converter.zenodo_data != {}
    assert converter.zenodo_data["access_right"] == "open"

    converter.add_escape2020_community()
    assert converter.zenodo_data["communities"] == [{"identifier": "escape2020"}]
    converter.add_escape2020_grant()
    assert converter.zenodo_data["grants"] == [{"id": "10.13039/501100000780::824064"}]


def test_codemeta_license_invalid(codemeta_test):
    converter = CodeMeta2ZenodoController(codemeta_test)
    converter.codemeta_data["license"] = "https://creativecommons.org/licenses/by/4.0/"
    converter.convert()
    assert converter.zenodo_data["license"] == "other-closed"


def test_converter(codemeta_test):
    zenodo = codemeta2ossr(codemeta_test)
    assert zenodo["communities"][0]["identifier"] == "escape2020"


def test_sample_file_conversion(tmp_dir):
    parse_codemeta_and_write_zenodo_metadata_file(CODEMETA_TEST_FILE, tmp_dir)
    with open(tmp_dir.joinpath(".zenodo.json").name) as f:
        zen_meta = json.load(f)
    assert "related_identifiers" in zen_meta
    assert "https://codedoc.com/" in [ri["identifier"] for ri in zen_meta["related_identifiers"]]


def test_root_codemeta_conversion(tmp_dir):
    parse_codemeta_and_write_zenodo_metadata_file(CODEMETA_TEST_FILE, tmp_dir)
    with open(tmp_dir.joinpath(".zenodo.json").name) as f:
        json.load(f)


@pytest.mark.xfail(raises=KeyError)
def test_no_license_in_codemeta(codemeta_test):
    codemeta_dict = codemeta_test.copy()
    codemeta_dict.pop("license")
    converter = CodeMeta2ZenodoController(codemeta_dict=codemeta_dict)
    converter.convert()
