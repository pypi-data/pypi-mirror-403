#!/usr/bin/env python
# This script is meant to be used by the continuous integration of a git repository to upload its content to the OSSR


import argparse
import json
import tempfile
from copy import deepcopy
from pathlib import Path

from eossr.api.zenodo import Record, SimilarRecordError, ZenodoAPI
from eossr.metadata.codemeta import codemeta_filepath
from eossr.metadata.codemeta2zenodo import codemeta2zenodo
from eossr.metadata.zenodo import add_escape2020_community, add_escape2020_grant, zenodo_filepath
from eossr.utils import zip_repository


def upload(
    zenodo_token,
    sandbox_flag,
    upload_directory,
    archive_name=None,
    record_id=None,
    erase_previous_files=True,
    force_new_record=False,
    publish=True,
    add_escape2020=False,
):
    """
    Zip the content of `upload_directory` and upload it into the OSSR.
    There must be a metadata file `codemeta.json` in the directory to be uploaded.

    The script will search for similar records previously uploaded by the same Zenodo user
    and will raise an error if it finds any and if a `record_id` was not provided or if `force_new_record==False`

    :param zenodo_token: str
        Personal access token to the (sandbox.)zenodo.org/api
    :param sandbox_flag: bold
        Set the Zenodo environment. True to use the sandbox, False to use Zenodo.
    :param upload_directory: str or Path
        Path to the directory whose content will be uploaded to the OSSR.
    :param archive_name: str or None
        Name of the zip archive. If None (default), the name of upload_directory is used.
    :param record_id: int or str
        Zenodo record-id of the record that is going to be updated.
        If no record_id is provided, a new record will be created in the OSSR.
    :param erase_previous_files: bool
        If True (default), it will erase the files of previous versions of the record before creating and updating the
        new version of the record. If False, it will not erase any file and old files will be included in the
        new version.
    :param force_new_record: bool
        If False (default), a new version of the `record_id` record will be created.
        If True, a new record - despite that it might already exists one - will be created.
    :param publish: bool
        If true, publish the record. Otherwise, the record is prepared but publication must be done manually. This
        is useful to check or discard the record before publication.
    :param add_escape2020: bool
        If True, adds ESCAPE project metadata: escape2020 community and ESCAPE grant number.

    :return: The `record_id` of the record created/uploaded
        `ZenodoAPI.upload_dir_content` answer
    """

    zenodo = ZenodoAPI(access_token=zenodo_token, sandbox=sandbox_flag)

    # Loads the metadata files if exists
    path_zenodo_file = zenodo_filepath(upload_directory)
    path_codemeta_file = codemeta_filepath(upload_directory)
    if path_zenodo_file.exists():
        print(f"Record metadata based on zenodo file {zenodo.path_zenodo_file}")
        with open(path_zenodo_file) as file:
            metadata = json.load(file)

    elif path_codemeta_file.exists():
        print(f"Record metadata based on codemeta file {path_codemeta_file}")
        with open(path_codemeta_file) as file:
            codemeta = json.load(file)
        # escape metadata can be added in both cases
        metadata = codemeta2zenodo(codemeta)
    else:
        raise FileNotFoundError("No metadata provided")

    if add_escape2020:
        add_escape2020_community(metadata, sandbox=sandbox_flag)
        add_escape2020_grant(metadata)

    metadata_for_check = {"metadata": deepcopy(metadata), "id": 1}
    metadata_for_check["metadata"]["doi"] = 1  # fake doi to create fake record
    record = Record(metadata_for_check)

    # Searches for similar records
    similar_records = zenodo.find_similar_records(record)
    if similar_records and not force_new_record and not record_id:
        raise SimilarRecordError(
            f"There are similar records in your own records: {similar_records}."
            "If you want to update an existing record, provide its record id to make a new version."
            "If you still want to make a new record, use --force-new-record."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_filename = Path(upload_directory).absolute().name + ".zip" if archive_name is None else archive_name
        zip_repository(upload_directory, zip_filename=Path(tmpdir).joinpath(zip_filename))

        record_id = zenodo.upload_dir_content(
            tmpdir,
            record_id=record_id,
            metadata=metadata,
            erase_previous_files=erase_previous_files,
            publish=publish,
        )

    return record_id


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description="Upload a directory to the OSSR as record. "
        "The directory must include a valid zenodo or codemeta file to be used"
        "as metadata source for the upload. "
        "If not record_id is passed, a new record is created. "
        "Otherwise, a new version of the existing record is created."
    )

    parser.add_argument(
        "--token", "-t", type=str, dest="zenodo_token", help="Personal access token to (sandbox)Zenodo", required=True
    )

    parser.add_argument(
        "--sandbox",
        "-s",
        action="store_true",
        help="Upload to Zenodo sandbox.",
        default=False,
    )

    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        dest="input_directory",
        help="Path to the directory containing the files to upload.All files will be uploaded.",
        required=True,
    )

    parser.add_argument(
        "--archive-name",
        type=str,
        default=None,
        dest="archive_name",
        help="Name of the upload zip archived. Default: name of in the input directory",
    )

    parser.add_argument(
        "--record_id",
        "-id",
        type=str,
        dest="record_id",
        help="record_id of the deposit that is going to be updated by a new version",
        default=None,
        required=False,
    )

    parser.add_argument(
        "--force-new-record",
        action="store_true",
        dest="force_new_record",
        help="Force the upload of a new record in case a similar record is found in the user existing ones",
    )

    parser.add_argument(
        "--no-publish",
        action="store_false",
        dest="publish",
        help="Optional tag to specify if the record will NOT be published. "
        "Useful for checking the record before publication of for CI purposes.",
    )

    parser.add_argument(
        "--add-escape2020",
        action="store_true",
        dest="add_escape2020",
        help="Add ESCAPE2020 community and grant number to the record.",
    )

    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    upload(
        args.zenodo_token,
        args.sandbox,
        args.input_directory,
        archive_name=args.archive_name,
        record_id=args.record_id,
        force_new_record=args.force_new_record,
        publish=args.publish,
        add_escape2020=args.add_escape2020,
    )


if __name__ == "__main__":
    main()
