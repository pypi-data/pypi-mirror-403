#!/usr/bin/env python

import argparse
import sys
from pathlib import Path

from eossr.metadata.codemeta2zenodo import parse_codemeta_and_write_zenodo_metadata_file


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description="Converts a metadata descriptive files from the the CodeMeta to the Zenodo schema. "
        "Creates a .zenodo.json file from a codemeta.json file."
    )

    parser.add_argument(
        "--input_codemeta_file",
        "-i",
        type=str,
        dest="codemeta_file",
        help="Path to a codemeta.json file",
        required=True,
    )
    parser.add_argument("--overwrite", action="store_true", help="Use to overwrite an existing `.zenodo.json` file")

    return parser


def main():
    """
    Check files exist and run codemeta2zenodo
    """

    parser = build_argparser()
    args = parser.parse_args()

    codemeta_file = Path(args.codemeta_file)

    # Check if file exists and it is named as it should
    if not codemeta_file.exists():
        raise FileNotFoundError(f"Codemeta file {codemeta_file} not found")
        sys.exit(-1)

    if not codemeta_file.name.startswith("codemeta") or not codemeta_file.name.endswith(".json"):
        raise ValueError(
            f"\n\t{codemeta_file.name} either does not start with the `codemeta` prefix or "
            f"does not finishes with a `.json` suffix. Exiting"
        )
        sys.exit(-1)

    directory_codemeta = codemeta_file.parent.absolute()
    zenodo_metadata_file = directory_codemeta / ".zenodo.json"

    # Check overwrite zenodo file if exists
    if zenodo_metadata_file.exists() and not args.overwrite:
        raise FileExistsError(f"File {zenodo_metadata_file} exists. Use --overwrite to overwrite file")
    else:
        # Parse the codemeta.json file and create the .zenodo.json file
        parse_codemeta_and_write_zenodo_metadata_file(
            codemeta_file, outdir=directory_codemeta, overwrite=args.overwrite
        )
    print("\nConversion codemeta2zenodo done.\n")


if __name__ == "__main__":
    main()
