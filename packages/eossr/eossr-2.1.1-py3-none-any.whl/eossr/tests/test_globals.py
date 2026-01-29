import os
from pathlib import Path

import eossr
from eossr.metadata import codemeta


def test_eossr_codemeta():
    eossr_codemeta_file = Path(__file__).parent.joinpath("../../codemeta.json").resolve()
    codemeta_handler = codemeta.Codemeta.from_file(eossr_codemeta_file)
    codemeta_handler.validate()


def test_version():
    print("HEREEEEEE", os.getenv("SANDBOX_ZENODO_TOKEN"))
    assert eossr.__version__ != "0.0.0"
