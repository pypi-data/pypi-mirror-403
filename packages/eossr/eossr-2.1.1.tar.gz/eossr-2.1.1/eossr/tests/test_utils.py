import os
import tempfile
from pathlib import Path
from zipfile import ZipFile

import pytest
import urllib3

from eossr import utils as eutils

_testurl = "https://zenodo.org/record/5592584/files/eossr.zip"
_testurl_buffer = "https://zenodo.org/record/5524913/files/eossr-v0.2.zip"


def test_ZipUrl():
    zipurl = eutils.ZipUrl(_testurl)
    codemeta_paths = zipurl.find_files("codemeta.json")

    assert "eossr/codemeta.json" in codemeta_paths
    assert "eossr/eossr/metadata/schema/codemeta.json" in codemeta_paths
    zipurl.extract("eossr/codemeta.json")
    assert Path("eossr/codemeta.json").exists()


@pytest.mark.xfail(urllib3.exceptions.ProtocolError)
def test_ZipUrl_buffer_fail():
    eutils.ZipUrl(_testurl_buffer, initial_buffer_size=64 * 1024)


def test_ZipUrl_buffer_success():
    zipurl = eutils.ZipUrl(_testurl_buffer)
    zipurl.extract("eossr-v0.2/codemeta.json")
    assert Path("eossr-v0.2/codemeta.json").exists()


def test_get_codemeta_from_zipurl():
    codemeta = eutils.get_codemeta_from_zipurl(_testurl, timeout=10, initial_buffer_size=100)
    assert codemeta["name"] == "eossr"


def test_zip_repository():
    from eossr import ROOT_DIR
    from eossr.utils import zip_repository

    zip_file = zip_repository(ROOT_DIR, "test_zipping_v0.1.zip")
    assert Path(zip_file).exists()
    with ZipFile(zip_file) as zo:
        for file in zo.namelist():
            assert ".git/" not in file
    Path(zip_file).unlink()

    with tempfile.TemporaryDirectory() as tmpdir:
        subtmpdir = tempfile.mkdtemp(dir=tmpdir)
        _, tmpfile = tempfile.mkstemp(dir=subtmpdir)
        Path(tmpfile).write_text("Hello World")
        zip_filename = Path(subtmpdir).joinpath("test_zip_repo.zip").as_posix()
        zip_repository(tmpdir, zip_filename=zip_filename)
        with ZipFile(zip_filename) as zo:
            assert "test_zip_repo.zip" not in [Path(f).name for f in zo.namelist()]
            assert (
                os.path.join(
                    os.path.join(os.path.basename(tmpdir), os.path.basename(subtmpdir)), os.path.basename(tmpfile)
                )
                in zo.namelist()
            )


def test_markdown_to_html():
    _, tmpfile = tempfile.mkstemp()
    Path(tmpfile).write_text("# Hello Markdown")
    html = eutils.markdown_to_html(tmpfile)
    assert html == "<h1>Hello Markdown</h1>"


def test_update_codemeta():
    # do not update main codemeta.json in unit test
    eutils.update_codemeta(overwrite=False)


def test_spdx():
    assert "MIT" in eutils.spdx_licenses()
    assert "dummy" not in eutils.spdx_licenses()
