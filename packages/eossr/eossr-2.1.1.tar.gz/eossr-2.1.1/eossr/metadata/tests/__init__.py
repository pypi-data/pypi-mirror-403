import json
from pathlib import Path

import pytest

SAMPLES_DIR = Path(__file__).parent.joinpath("samples")
ROOT_DIR = Path("codemeta.json").parent.resolve()
CODEMETA_TEST_FILE = SAMPLES_DIR.joinpath("codemeta_test.json")
ZENODO_TEST_FILE = SAMPLES_DIR.joinpath("zenodo_test.json")


@pytest.fixture
def codemeta_test():
    with open(CODEMETA_TEST_FILE) as f:
        return json.load(f)


@pytest.fixture
def zenodo_test():
    with open(ZENODO_TEST_FILE) as f:
        return json.load(f)


@pytest.fixture
def codemeta_not_valid():
    with open(SAMPLES_DIR.joinpath("codemeta_not_valid.json")) as f:
        return json.load(f)


@pytest.fixture
def codemeta_contributors():
    with open(SAMPLES_DIR.joinpath("codemeta_contributors_sample.json")) as f:
        return json.load(f)
