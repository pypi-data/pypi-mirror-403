# Various tests taken/based from
# https://github.com/cta-observatory/cta-lstchain/blob/master/lstchain/scripts/tests/test_lstchain_scripts.py

import os
import shutil
import subprocess
from os.path import dirname, join, realpath
from pathlib import Path

import pkg_resources
import pytest

from eossr.scripts import eossr_upload_repository

ROOT_DIR = dirname(realpath("codemeta.json"))


def find_entry_points(package_name):
    """from: https://stackoverflow.com/a/47383763/3838691"""
    entrypoints = [
        ep.name for ep in pkg_resources.iter_entry_points("console_scripts") if ep.module_name.startswith(package_name)
    ]
    return entrypoints


ALL_SCRIPTS = find_entry_points("eossr")


def run_script(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8")

    if result.returncode != 0:
        raise ValueError(f"Running {args[0]} failed with return code {result.returncode}, output: \n {result.stdout}")


def test_codemeta2zenodo():
    existing_zenodo_file = Path(ROOT_DIR).joinpath(".zenodo.json")
    if existing_zenodo_file.exists():
        existing_zenodo_file.unlink()

    run_script("eossr-codemeta2zenodo", "-i", join(ROOT_DIR, "codemeta.json"))
    existing_zenodo_file.unlink()


@pytest.mark.parametrize("script", ALL_SCRIPTS)
def test_help_all_scripts(script):
    """Test for all scripts if at least the help works"""
    run_script(script, "--help")


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
def test_eossr_upload_repository(tmpdir):
    path_test_filename = Path(tmpdir).joinpath("test.txt")
    Path(path_test_filename).write_text("Hello World")
    shutil.copy(Path(ROOT_DIR).joinpath("codemeta.json"), tmpdir)
    eossr_upload_repository.upload(
        zenodo_token=os.getenv("SANDBOX_ZENODO_TOKEN"),
        sandbox_flag=True,
        upload_directory=tmpdir,
        force_new_record=True,
        publish=False,
    )


def test_eossr_metadata_validator_valid():
    from eossr.metadata.tests.test_codemeta import SAMPLES_DIR

    path_test_codemeta = SAMPLES_DIR.joinpath("codemeta_valid.json")
    run_script("eossr-metadata-validator", path_test_codemeta)


@pytest.mark.xfail()
def test_eossr_metadata_validator_not_valid():
    from eossr.metadata.tests.test_codemeta import SAMPLES_DIR

    path_test_codemeta = SAMPLES_DIR.joinpath("codemeta_not_valid.json")
    run_script("eossr-metadata-validator", path_test_codemeta)


@pytest.mark.skipif(os.getenv("SANDBOX_ZENODO_TOKEN") is None, reason="SANDBOX_ZENODO_TOKEN not defined")
def test_user_entries_cleanup():
    from eossr.scripts.zenodo_user_entries_cleanup import zenodo_cleanup

    zenodo_cleanup(token=os.getenv("SANDBOX_ZENODO_TOKEN"), sandbox=True)
