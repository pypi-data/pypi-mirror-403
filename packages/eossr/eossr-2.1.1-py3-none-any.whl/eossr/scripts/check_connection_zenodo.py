#!/usr/bin/env python

import argparse

from eossr.api.zenodo import ZenodoAPI
from eossr.metadata.codemeta import codemeta_filepath
from eossr.metadata.codemeta2zenodo import parse_codemeta_and_write_zenodo_metadata_file
from eossr.metadata.zenodo import zenodo_filepath


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(description="Test the connection to zenodo and all the stages of a new upload.")

    parser.add_argument(
        "--token", "-t", type=str, dest="zenodo_token", help="Personal access token to (sandbox)Zenodo", required=True
    )

    parser.add_argument(
        "--sandbox",
        "-s",
        action="store_true",
        help="Use Zenodo sandbox.",
    )

    parser.add_argument(
        "--project_dir",
        "-p",
        action="store",
        dest="project_dir",
        help='Path to the root directory of the directory to be uploaded. DEFAULT; assumed to be on it, i.e., "./"',
        default="./",
    )
    return parser


def main():
    # Required arguments

    args = build_argparser().parse_args()

    # Loads the metadata files if exists
    path_zenodo_file = zenodo_filepath(args.project_dir)
    path_codemeta_file = codemeta_filepath(args.project_dir)

    if not path_zenodo_file.exists() and not path_codemeta_file.exists():
        raise FileNotFoundError("No metadata file provided")
    elif path_zenodo_file.exists():
        print(f"Record metadata based on zenodo file {path_zenodo_file}")
    elif path_codemeta_file.exists() and not path_zenodo_file.exists():
        print(f"Record metadata based on codemeta file {path_codemeta_file}")
        print(f"Created zenodo metadata file {path_zenodo_file}")
        parse_codemeta_and_write_zenodo_metadata_file(path_codemeta_file, args.project_dir, add_escape2020=False)

    zenodo = ZenodoAPI(access_token=args.zenodo_token, sandbox=args.sandbox)
    zenodo.check_upload_to_zenodo(args.project_dir)


if __name__ == "__main__":
    main()
