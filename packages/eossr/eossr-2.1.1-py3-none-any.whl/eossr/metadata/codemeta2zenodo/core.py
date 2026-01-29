"""
The converter is based on the crosswalk table defined in the csv file `escape_codemeta_3.0_crosswalk.csv` in the schema folder.
The logic is the following:
- the crosswalk table defines the mapping keys in the Zenodo metadata schema
- the converter classes know the type and structure of the value in the Zenodo metadata schema
- in general, the choice of which converter class should be used is based on the codemeta Type
"""

import datetime
import json
import warnings
from pathlib import Path

from ..codemeta import Codemeta
from ..zenodo import (
    add_escape2020_community,
    add_escape2020_grant,
    validate_zenodo_metadata_deposit,
    write_zenodo_metadata,
)
from .converters import MasterConverter
from .utils import handle_version_type, remove_duplicates


def add_upload_type(codemeta_dict, zenodo_dict):
    if "@type" not in codemeta_dict or codemeta_dict["@type"] == "SoftwareSourceCode":
        zenodo_dict["upload_type"] = "software"
    else:
        raise ValueError(
            f"CodeMeta schema has been developed for software, '@type' key must be 'SoftwareSourceCode' "
            f"but is {codemeta_dict['upload_type']}"
        )


def codemeta2zenodo(codemeta_dict, zenodo_access_right="open"):
    """
    Convert a codemeta dict to a Zenodo dict
    Special cases:
    - access_right: set to 'open' as this is mandatory for Zenodo and not in codemeta. You will have to change it manually if you want it otherwise.

    """
    codemeta_handler = Codemeta(codemeta_dict)
    codemeta_handler.validate()

    crosswalk_table = codemeta_handler.crosswalk_table

    zenodo_dict = {}

    add_upload_type(codemeta_dict, zenodo_dict)

    sub_codemeta_dict = codemeta_dict.copy()
    sub_codemeta_dict.pop("@context", None)
    sub_codemeta_dict.pop("@type", None)

    for codemeta_key, codemeta_value in sub_codemeta_dict.items():
        try:
            index = crosswalk_table.index[crosswalk_table["Property"] == codemeta_key].tolist()[0]
        except IndexError:
            # if the key is not found in the crosswalk table, just don't convert it
            # note: the codemeta schema should have been validated before
            warnings.warn(f"Key '{codemeta_key}' not found in crosswalk table, ignored by converter")
            continue

        zenodo_key = crosswalk_table.loc[index, "Zenodo"]

        # no conversion defined for this key
        if zenodo_key == "":
            continue

        zenodo_keys = zenodo_key.split(".")  # type: ignore
        sub_zenodo_dict = zenodo_dict
        for k in zenodo_keys[:-1]:
            sub_zenodo_dict.setdefault(k, {})
            sub_zenodo_dict = zenodo_dict[k]
        zenodo_key = zenodo_keys[-1]

        codemeta_type = str(crosswalk_table.loc[index, "Type"])
        zenodo_contributor_type = str(crosswalk_table.loc[index, "ZenodoContributorType"])

        if zenodo_key in zenodo_dict:
            # if the key is already in the dict, create a list so it can be appended
            if not isinstance(sub_zenodo_dict[zenodo_key], list):
                zenodo_dict[zenodo_key] = [sub_zenodo_dict[zenodo_key]]

            converted_value = MasterConverter(
                codemeta_value,
                codemeta_type,
                codemeta_key=codemeta_key,
                zenodo_contributor_type=zenodo_contributor_type,
            )
            if converted_value is None:
                pass
            elif isinstance(converted_value, list):
                sub_zenodo_dict[zenodo_key].extend(converted_value)
            else:
                sub_zenodo_dict[zenodo_key].append(converted_value)
        else:
            converted_value = MasterConverter(
                codemeta_value,
                codemeta_type,
                codemeta_key=codemeta_key,
                zenodo_contributor_type=zenodo_contributor_type,
            )
            if converted_value is None:
                pass
            else:
                sub_zenodo_dict[zenodo_key] = converted_value

    if zenodo_access_right not in ["open", "closed", "embargoed", "restricted"]:
        raise ValueError(
            f"Invalid access_right {zenodo_access_right}, must be one of 'open', 'closed', 'embargoed', 'restricted'"
        )
    zenodo_dict["access_right"] = zenodo_access_right

    # Handle the case where version is provided in two places in codemeta, leading to a list of versions, but zenodo only accepts one
    handle_version_type(zenodo_dict)

    for codemeta_key, codemeta_value in zenodo_dict.items():
        if isinstance(codemeta_value, list):
            zenodo_dict[codemeta_key] = remove_duplicates(codemeta_value)

    if "publication_date" not in zenodo_dict:
        zenodo_dict["publication_date"] = datetime.datetime.today().date().isoformat()

    return zenodo_dict


class CodeMeta2ZenodoController:
    """Control the conversion of a codemeta file to a zenodo file"""

    def __init__(self, codemeta_dict):
        assert isinstance(codemeta_dict, dict)
        self.codemeta_data = codemeta_dict
        self.zenodo_data = {}

    @classmethod
    def from_file(cls, codemeta_filename):
        """Load `codemeta_filename` into the converter"""
        with open(codemeta_filename) as infile:
            controller = cls(json.load(infile))
        return controller

    def convert(self, validate=True):
        """Convert data over to zenodo format"""
        self.zenodo_data = codemeta2zenodo(self.codemeta_data)
        if validate:
            self.validate_zenodo()
        return self.zenodo_data

    def validate_zenodo(self):
        """
        Validate the zenodo data.
        """
        validate_zenodo_metadata_deposit(self.zenodo_data)

    def add_escape2020_community(self):
        """
        Add compulsory information to the .zenodo.json file:
         * zenodo community : ESCAPE2020
        """
        add_escape2020_community(self.zenodo_data)

    def add_escape2020_grant(self):
        """
        Add compulsory information to the .zenodo.json file:
         * ESCAPE grant ID (zenodo syntax)
        """
        add_escape2020_grant(self.zenodo_data)

    def write_zenodo(self, zenodo_filename=".zenodo.json", overwrite=False, validate=True):
        """Write `zenodo_filename` after conversion"""
        write_zenodo_metadata(self.zenodo_data, zenodo_filename, overwrite=overwrite, validate=validate)


def codemeta2ossr(codemeta_dict, add_escape_grant=True):
    """
    Convert codemeta metadata into zenodo metadata

    Parameters
    ----------
    codemeta_dict : dict
        A dictionary containing the codemeta metadata.
    add_escape_grant : bool, optional
        If True, add escape2020 community and grant. Default is True.

    Returns
    -------
    dict
        A dictionary containing the zenodo metadata.
    """
    zenodo = codemeta2zenodo(codemeta_dict)
    if add_escape_grant:
        add_escape2020_grant(zenodo)
    return zenodo


def parse_codemeta_and_write_zenodo_metadata_file(codemeta_filename, outdir, add_escape2020=True, overwrite=True):
    """
    Reads the codemeta.json file and creates a new `.zenodo.json` file in outdir.
    This file contains the same information that in the codemeta.json file but following the zenodo metadata schema.

    codemeta_filename: str or Path
        path to the codemeta.json file
    outdir: str or Path
        path to the outdir where the file `.zenodo.json` will be created
    add_escape2020: bool
        adds escape2020 metadata in zenodo metadata file
    overwrite: bool
        overwrite existing `.zendoo.json` file in `outdir`
    """
    meta_converter = CodeMeta2ZenodoController.from_file(codemeta_filename)
    meta_converter.convert()
    if add_escape2020:
        meta_converter.add_escape2020_community()
        meta_converter.add_escape2020_grant()
    outfile = Path(outdir).joinpath(".zenodo.json")
    meta_converter.write_zenodo(outfile.name, overwrite=overwrite)
