import tempfile
from os import path
from pathlib import Path

import pytest

from eossr.metadata import codemeta
from eossr.metadata.tests import codemeta_not_valid, codemeta_test


SAMPLES_DIR = Path(path.join(path.dirname(path.realpath(__file__)), "samples"))


def test_samples_dir():
    assert SAMPLES_DIR.exists()


def test_codemeta():
    meta = codemeta.schema()
    assert meta["@context"]["codemeta"] == "https://codemeta.github.io/terms/"


def test_codemeta_valid(codemeta_test):
    codemeta_handler = codemeta.Codemeta(codemeta_test)
    codemeta_handler.validate()


@pytest.mark.xfail(raises=codemeta.CodemetaRequiredError)
def test_codemeta_not_valid(codemeta_not_valid):
    codemeta_handler = codemeta.Codemeta(codemeta_not_valid)
    codemeta_handler.validate()


def test_read_codemeta_crosswalk():
    cw = codemeta.codemeta_crosswalk()
    assert set(cw["OSSR Requirement Level"].values) == {"required", "recommended", ""}


def test_codemeta_write():
    metadata = {"name": "Rick", "version": "v10"}
    codemeta_handler = codemeta.Codemeta(metadata)
    with tempfile.TemporaryDirectory() as tmpdirname:
        filename = Path(tmpdirname, "codemeta.json")
        codemeta_handler.write(filename)
        new_codemeta = codemeta.Codemeta.from_file(filename)
        assert new_codemeta.metadata == metadata
