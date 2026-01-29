#!/usr/bin/env python
import argparse
from pathlib import Path

from eossr.metadata import codemeta


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description="Validate a codemeta file. Raises warnings for recommended changes and errors for unvalid entries"
    )

    parser.add_argument("filename", type=Path, help="Path to codemeta.json")

    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()

    codemeta_handler = codemeta.Codemeta.from_file(args.filename)

    codemeta_handler.validate()


if __name__ == "__main__":
    main()
