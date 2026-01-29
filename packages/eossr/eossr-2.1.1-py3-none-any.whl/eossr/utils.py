import json
import os
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import remotezip
import requests
import urllib3.exceptions
from markdown import markdown

from . import ROOT_DIR

__all__ = [
    "ZipUrl",
    "get_codemeta_from_zipurl",
    "zip_repository",
    "update_codemeta",
]


class ZipUrl(remotezip.RemoteZip, ZipFile):
    def __init__(self, url, initial_buffer_size=48 * 1024, **kwargs):
        # Zenodo imposes a limit on the zipfile to be read.
        # Some tests show that a limit with 48*1024 works fine.
        try:
            super().__init__(url, initial_buffer_size=initial_buffer_size, **kwargs)
        except requests.packages.urllib3.exceptions.ProtocolError as e:
            raise urllib3.exceptions.ProtocolError(
                f"{str(e)}\nTry lowering the initial buffer size for this zipfile"
            ) from e

    def find_files(self, filename):
        """
        return the path of files in the archive matching `filename`

        :param filename: string
        :return: list[str]
        """
        matching_files = [f for f in self.namelist() if Path(f).name == filename]
        if len(matching_files) == 0:
            raise FileNotFoundError(f"No file named {filename} in {self.url}")
        else:
            return matching_files

    def get_codemeta(self):
        codemeta_paths = self.find_files("codemeta.json")
        # if there are more than one codemeta file in the archive, we consider the one in the root directory, hence the
        # one with the shortest path
        codemeta_path = min(codemeta_paths, key=len)
        with self.open(codemeta_path) as file:
            codemeta = json.load(file)
        return codemeta


def get_codemeta_from_zipurl(url, **zipurl_kwargs):
    """
    Extract and reads codemeta metadata from a zip url.
    A codemeta.json file must be present in the zip archive.

    Parameters
    ----------
    url: string
        url to a zip file
    zipurl_kwargs: dictionnary
        metadata in the codemeta.json file in the zip archive

    Returns
    -------
    dict
    """
    zipurl_kwargs.setdefault("initial_buffer_size", 100)
    zipurl = ZipUrl(url, **zipurl_kwargs)
    return zipurl.get_codemeta()


def zip_repository(repository_path, zip_filename=None, overwrite=True):
    """
    Zip the content of `repository_path`
    `.git` subdirectories in the target directory will be excluded

    :param repository_path: str or Path
        Path to the directory to be zipped
    :param zip_filename: str
        Zip filename name, used to name the zip file. If None, the zip will be named as the directory provided.
    :param overwrite: bool
        True to overwrite existing zip archive

    :return: zip_filename: path to the zip archive
    """
    # prepare zip archive
    directory = Path(repository_path).resolve()
    zip_filename = f"{directory.absolute().name}.zip" if zip_filename is None else zip_filename
    if Path(zip_filename).exists() and not overwrite:
        raise FileExistsError(f"{zip_filename} exists. Set overwrite=True")

    print(f" * Zipping the content of {directory.absolute()} into {zip_filename}")

    with ZipFile(zip_filename, "w") as zipObj:
        for folder_name, subfolders, filenames in os.walk(directory):
            # don't zip .git/ content nor the .git dir itself
            if ".git/" in folder_name or folder_name.endswith(".git"):
                continue
            # we want the relative path only inside the archive
            relpath = os.path.relpath(folder_name, directory.parent)
            for filename in filenames:
                abs_file_path = Path(folder_name).joinpath(filename).resolve()
                # avoid archiving the zip file itself
                if abs_file_path == Path(zip_filename).resolve():
                    continue
                rel_file_path = Path(relpath).joinpath(filename)
                zipObj.write(abs_file_path, rel_file_path)

    print(f"Zipping done: {zip_filename}")
    return zip_filename


def markdown_to_html(filepath):
    """
    Read a markdown file and return html transcript
    :param filepath: str or Path
    :return: str
        text in readme converted to html
    """
    html = markdown(open(filepath).read(), extensions=["fenced_code"])
    html = html.replace("\n", "")
    return html


def update_codemeta(
    codemeta_path=Path(ROOT_DIR).joinpath("codemeta.json").as_posix(),
    version=None,
    readme_path=None,
    modification_date=True,
    publication_date=True,
    download_url=None,
    release_notes=None,
    overwrite=True,
):
    """

    :param codemeta_path: Path or str
        path to the codemeta file to update
    :param version: str or None
    :param readme_path:
        Path to readme in markdown. An html transcript of its content will be used to update the `description` value.
    :param modification_date: bool
        If True, updates the modification date with today's
    :param publication_date: bool
        If True, updates the publication date with today's
    :param download_url: str
        Download URL for the software
    :param release_notes: str
        release notes. If None, does not update.
    :param overwrite: bool
        If True, overwrites the codemeta file
    """
    with open(codemeta_path) as file:
        metadata = json.load(file)

    if readme_path is not None:
        metadata["description"] = markdown_to_html(readme_path)

    if modification_date:
        metadata["dateModified"] = f"{date.today()}"

    if publication_date:
        metadata["datePublished"] = f"{date.today()}"

    if download_url is not None:
        metadata["downloadUrl"] = download_url
    if version is not None:
        metadata["version"] = f"v{version}"
        metadata["softwareVersion"] = f"v{version}"

    if release_notes is not None:
        metadata["releaseNotes"] = release_notes

    if overwrite:
        write_json(metadata, codemeta_path, overwrite=overwrite)
    return metadata


def spdx_licenses(open_only=True):
    """
    Get a list of all spdx licenses
    :return: list[str]
    """
    req = requests.get("https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json")
    try:
        req.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise requests.exceptions.HTTPError(f"Error while fetching spdx licenses: {e}") from e

    licenses = req.json()["licenses"]
    if open_only:
        licenses = [lic["licenseId"] for lic in licenses if lic["isOsiApproved"]]
    else:
        licenses = [lic["licenseId"] for lic in licenses if not lic["isOsiApproved"]]
    return licenses


def write_json(data, filename, overwrite=False):
    """
    Write data to a json file
    Parameters
    ----------
    data: dict
    filename: str or Path
    overwrite: bool (default: False)
        If True, overwrites the file if it exists
    """

    if Path(filename).exists() and not overwrite:
        raise FileExistsError(f"{filename} exists. Set overwrite=True")
    with open(filename, "w") as file:
        json.dump(data, file, indent=4)
