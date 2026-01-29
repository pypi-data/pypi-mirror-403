import json

import pytest

from eossr.metadata.codemeta2zenodo.converters import (
    CodeRepositoryConverter,
    CommunityConverter,
    DateConverter,
    IDConverter,
    LicenseConverter,
    OrganizationConverter,
    PersonConverter,
)


@pytest.fixture
def codemeta_test():
    with open("codemeta_test.json") as f:
        return json.load(f)


@pytest.fixture
def zenodo_test():
    with open("zenodo_test.json") as f:
        return json.load(f)


def test_IDConverter_valid_orcid():
    converter = IDConverter("https://orcid.org/0000-0002-1825-0097")
    assert converter.convert() == {"orcid": "https://orcid.org/0000-0002-1825-0097"}


def test_IDConverter_valid_orcid_short():
    converter = IDConverter("0000-0002-1825-0097")
    assert converter.convert() == {"orcid": "0000-0002-1825-0097"}


def test_IDConverter_invalid_orcid():
    converter = IDConverter("https://orcid.org/1234")
    assert converter.convert() == {}


def test_IDConverter_invalid_format():
    converter = IDConverter("not a valid ID")
    assert converter.convert() == {}


def test_IDConverter_invalid_type():
    with pytest.raises(ValueError):
        converter = IDConverter(1234)
        converter.check_type()


def test_organization_converter_dict():
    # Test converting a dictionary with a name key
    org_dict = {"@type": "Organization", "name": "Test Org"}
    expected_output = [{"name": "Test Org"}]
    converter = OrganizationConverter(org_dict)
    assert converter.convert() == expected_output


def test_organization_converter_invalid_type():
    # Test that an error is raised if the value is not a dict or list of dicts
    org_str = "Test Org"
    with pytest.raises(ValueError):
        converter = OrganizationConverter(org_str)
        converter.check_type()


def test_organization_converter_invalid_list_item_type():
    # Test that an error is raised if a list item is not an Organization
    org_list = [
        {"@type": "Organization", "name": "Test Org 1"},
        {"@type": "Person", "name": "Test Person"},
    ]
    with pytest.raises(ValueError):
        converter = OrganizationConverter(org_list)
        converter.check_type()


def test_code_repository_converter():
    url = "https://github.com/myusername/mycode"
    converter = CodeRepositoryConverter(url)
    expected_output = [
        {
            "scheme": "url",
            "identifier": url,
            "relation": "isDerivedFrom",
            "resource_type": "software",
        }
    ]
    assert converter.convert() == expected_output


def test_person_converter_with_valid_input():
    input_data = {
        "@type": "Person",
        "givenName": "John",
        "familyName": "Doe",
        "affiliation": {"@type": "Organization", "name": "University of California"},
        "identifier": "https://orcid.org/0000-0002-1825-0097",
    }
    expected_output = [
        {
            "name": "John Doe",
            "affiliation": "University of California",
            "orcid": "https://orcid.org/0000-0002-1825-0097",
        }
    ]
    converter = PersonConverter(input_data)
    assert converter.convert() == expected_output


def test_person_converter_with_two_affiliations():
    input_data = {
        "@type": "Person",
        "givenName": "John",
        "familyName": "Doe",
        "affiliation": [
            {"@type": "Organization", "name": "University of California"},
            {"@type": "Organization", "name": "University of Annecy"},
        ],
        "identifier": "https://orcid.org/0000-0002-1825-0097",
    }
    expected_output = [
        {
            "name": "John Doe",
            "affiliation": "University of California; University of Annecy",
            "orcid": "https://orcid.org/0000-0002-1825-0097",
        }
    ]
    converter = PersonConverter(input_data)
    assert converter.convert() == expected_output


def test_person_converter_with_missing_given_or_family_name():
    input_data = {
        "@type": "Person",
        "familyName": "Doe",
    }
    excepted_output = [{"name": "Doe"}]
    converter = PersonConverter(input_data)
    assert converter.convert() == excepted_output
    input_data = {
        "@type": "Person",
        "givenName": "Doe",
    }
    excepted_output = [{"name": "Doe"}]
    converter = PersonConverter(input_data)
    assert converter.convert() == excepted_output


def test_person_converter_with_invalid_affiliation():
    input_data = {
        "@type": "Person",
        "givenName": "John",
        "familyName": "Doe",
        "affiliation": "University of California",
        "identifier": "https://orcid.org/0000-0002-1825-0097",
    }
    converter = PersonConverter(input_data)
    with pytest.raises(ValueError):
        converter.convert()


def test_person_converter_with_invalid_orcid():
    input_data = {
        "@type": "Person",
        "givenName": "John",
        "familyName": "Doe",
        "affiliation": {"@type": "Organization", "name": "University of California"},
        "identifier": "https://orcid.org/invalid-orcid",
    }
    converter = PersonConverter(input_data)
    expected_output = [{"name": "John Doe", "affiliation": "University of California"}]
    assert converter.convert() == expected_output


def test_date_converter_valid_date():
    # Test that a valid date is converted correctly
    date_str = "2022-01-01"
    converter = DateConverter(date_str)
    assert converter.convert() == date_str


def test_date_converter_invalid_date():
    # Test that an invalid date raises a ValueError
    date_str = "2022-01-32"
    with pytest.raises(ValueError):
        converter = DateConverter(date_str)
        converter.check_type()


def test_community_converter():
    # Test when community is found
    community_id = "escape2020"
    converter = CommunityConverter(community_id)
    assert converter.convert() == {"identifier": community_id}

    # Test when community is not found
    converter = CommunityConverter("likely-not-a-zenodo-community")
    assert converter.convert() is None


def test_license_converter():
    converter = LicenseConverter("https://spdx.org/licenses/MIT")
    assert converter.convert() == "mit"

    converter = LicenseConverter(["https://spdx.org/licenses/MIT", "https://spdx.org/licenses/BSD-3-Clause"])
    assert converter.convert() == "other-open"


def test_license_converter_invalid_value():
    converter = LicenseConverter("https://spdx.org/licenses/invalid")
    assert converter.convert() == "other-closed"


def test_license_converter_invalid_type():
    with pytest.raises(ValueError):
        converter = LicenseConverter("Apache-2.0")
        converter.convert()
