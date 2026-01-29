#!/usr/bin/env python
import argparse
import json
from pathlib import Path

from eossr.metadata import zenodo


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description="Validate a Zenodo metadata file (.zenoodo.json). "
        "Raises warnings for recommended changes "
        "and errors for unvalid entries"
    )

    parser.add_argument("filename", type=Path, help="Path to .zenodo.json")

    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    with open(args.filename) as f:
        metadata = json.load(f)

    zenodo.validate_zenodo_metadata_deposit(metadata)

    print("Valid Zenodo metadata 🚀")


if __name__ == "__main__":
    main()
