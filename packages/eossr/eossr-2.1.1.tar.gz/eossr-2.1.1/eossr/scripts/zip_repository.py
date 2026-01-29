#!/usr/bin/env python

import argparse

from eossr.utils import zip_repository


def build_argparser():
    """
    Construct main argument parser for the ``codemet2zenodo`` script

    :return:
    argparser: `argparse.ArgumentParser`
    """
    parser = argparse.ArgumentParser(
        description="Zip the content of a directory (a git project is expected). "
        "`.git` subdirectories in the target directory will be excluded"
    )

    parser.add_argument(
        "--directory", "-d", type=str, dest="directory", help="Path to the directory to be zipped.", required=True
    )

    parser.add_argument(
        "--name_zip", "-n", type=str, dest="name_zip", help="Zip filename. DEFAULT: directory (basename)", default=None
    )
    return parser


def main():
    parser = build_argparser()
    args = parser.parse_args()
    zip_repository(
        args.directory,
        args.name_zip,
    )


if __name__ == "__main__":
    main()
