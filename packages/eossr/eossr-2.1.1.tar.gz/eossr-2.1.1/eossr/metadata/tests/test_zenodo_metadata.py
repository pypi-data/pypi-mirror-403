from copy import deepcopy

import pytest

from eossr.metadata import zenodo

meta_base = {
    "title": "eOSSR unit test",
    "description": "eOSSR unit tests.",
    "version": "1.7.0",
    "creators": [{"affiliation": "The best affiliation", "name": "Rick"}],
    "access_right": "open",
    "upload_type": "software",
    "license": "mit",
}


def test_zenodo_metadata():
    meta = meta_base
    zenodo.validate_zenodo_metadata_deposit(meta)


def test_zenodo_metadata_publication_type():
    meta = deepcopy(meta_base)
    meta["upload_type"] = "publication"
    for publication_type in [
        "annotationcollection",
        "article",
        "book",
        "section",
        "conferencepaper",
        "datamanagementplan",
        "article",
        "patent",
        "preprint",
        "deliverable",
        "milestone",
        "proposal",
        "report",
        "softwaredocumentation",
        "taxonomictreatment",
        "technicalnote",
        "thesis",
        "workingpaper",
        "other",
    ]:
        meta["publication_type"] = publication_type
        zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_publication_type_fail():
    meta = deepcopy(meta_base)
    meta["upload_type"] = "publication"
    meta["publication_type"] = "invalid"
    zenodo.validate_zenodo_metadata_deposit(meta)


def test_zenodo_metadata_image_type():
    meta = deepcopy(meta_base)
    meta["upload_type"] = "image"
    for publication_type in ["figure", "plot", "drawing", "diagram", "photo", "other"]:
        meta["image_type"] = publication_type
        zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_access_right_fail():
    meta = deepcopy(meta_base)
    meta["access_right"] = "invalid"
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_image_type_fail():
    meta = deepcopy(meta_base)
    meta["upload_type"] = "publication"
    meta["publication_type"] = "invalid"
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_creator_noname():
    meta = deepcopy(meta_base)
    meta["creators"] = [{"affiliation": "The best affiliation"}]
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_access_right_license():
    meta = deepcopy(meta_base)
    meta["access_right"] = "open"
    meta.pop("license")
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_embargo_date():
    meta = deepcopy(meta_base)
    meta["access_right"] = "restricted"
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_access_conditions():
    meta = deepcopy(meta_base)
    meta["access_right"] = "restricted"
    zenodo.validate_zenodo_metadata_deposit(meta)


@pytest.mark.xfail(raises=zenodo.ZenodoMetadataValidationError)
def test_zenodo_metadata_fail():
    meta = deepcopy(meta_base)
    meta.pop("description")
    zenodo.validate_zenodo_metadata_deposit(meta)


def test_add_escape2020_community():
    meta = deepcopy(meta_base)
    zenodo.add_escape2020_community(meta, sandbox=False)
    assert meta["communities"] == [{"identifier": "escape2020"}]

    zenodo.add_escape2020_community(meta)
    assert meta["communities"] == [{"identifier": "escape2020"}]

    meta["communities"] = [{"identifier": "escape2021"}]
    zenodo.add_escape2020_community(meta)
    assert meta["communities"] == [
        {"identifier": "escape2021"},
        {"identifier": "escape2020"},
    ]
    zenodo.validate_zenodo_metadata_deposit(meta)


def test_add_escape2020_grant():
    meta = deepcopy(meta_base)
    zenodo.add_escape2020_grant(meta)
    assert meta["grants"] == [{"id": "10.13039/501100000780::824064"}]

    meta["grants"] = [{"id": "10.13039/501100000780::824064"}]
    zenodo.add_escape2020_grant(meta)
    assert meta["grants"] == [{"id": "10.13039/501100000780::824064"}]

    meta["grants"] = [{"id": "another grant"}]
    zenodo.add_escape2020_grant(meta)
    assert meta["grants"] == [{"id": "another grant"}, {"id": "10.13039/501100000780::824064"}]
    zenodo.validate_zenodo_metadata_deposit(meta)


def test_valid_license():
    assert zenodo.valid_license("mit")
    assert ~zenodo.valid_license("MIT2")
