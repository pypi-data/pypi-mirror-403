import json
from pathlib import Path
from warnings import warn

import numpy as np
import pandas as pd
import pkg_resources
import requests

from ..utils import write_json
from . import valid_semver

__all__ = [
    "schema",
    "codemeta_crosswalk",
    "Codemeta",
]


CODEMETA_VERSIONS_CONTEXTS = {
    "https://raw.githubusercontent.com/codemeta/codemeta/3.0/codemeta.jsonld": "3.0",
    "https://raw.githubusercontent.com/codemeta/codemeta/2.0/codemeta.jsonld": "2.0",
    "https://raw.githubusercontent.com/codemeta/codemeta/1.0/codemeta.jsonld": "1.0",
    "https://doi.org/10.5063/schema/codemeta-2.0": "2.0",
    "https://doi.org/10.5063/schema/codemeta-1.0": "1.0",
    # "https://doi.org/10.5063/schema/codemeta-3.0": "3.0",
}


def codemeta_filepath(directory):
    """
    Return the path to the CodeMeta file in `directory`
    """
    return Path(directory).joinpath("codemeta.json")


def schema(codemeta_version="2.0"):
    """
    Load the CodeMeta schema from the CodeMeta repository.

    Parameters
    ----------
    codemeta_version : str, optional
        The version of the CodeMeta schema to load. Default is '2.0'.

    Returns
    -------
    dict
        The CodeMeta schema as a JSON object.

    Raises
    ------
    requests.exceptions.HTTPError
        If the request to the CodeMeta repository fails.

    """
    url = f"https://raw.githubusercontent.com/codemeta/codemeta/{codemeta_version}/codemeta.jsonld"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def codemeta_version_from_context(context):
    if context not in CODEMETA_VERSIONS_CONTEXTS:
        raise ValueError(
            f"Unknown @context {context}, supported contexts are {list(CODEMETA_VERSIONS_CONTEXTS.keys())}"
        )
    return CODEMETA_VERSIONS_CONTEXTS[context]


def codemeta_crosswalk(codemeta_version="2.0"):
    if codemeta_version not in CODEMETA_VERSIONS_CONTEXTS.values():
        raise ValueError(
            f"CodeMeta version {codemeta_version} not supported. Supported versions are {CODEMETA_VERSIONS_CONTEXTS.values()}"
        )
    df = pd.read_csv(
        pkg_resources.resource_stream(__name__, "schema/escape_codemeta_crosswalk.csv"),
        comment="#",
        delimiter=";",
    )
    df.fillna("", inplace=True)

    df["Property"] = df[f"codemeta-{codemeta_version}"]

    return df


class CodemetaRequiredError(KeyError):
    counter = 0

    def __init__(self, message):
        CodemetaRequiredError.counter += 1


class CodemetaRecommendedWarning(Warning):
    counter = 0

    def __init__(self, message):
        CodemetaRecommendedWarning.counter += 1


class Codemeta:
    _crosswalk_table = None
    _codemeta_version = None

    def __init__(self, metadata: dict):
        """
        The CodeMeta version and corresponding crosswalk table are inferred from the @context key in the metadata
        """
        self.metadata = metadata

    @classmethod
    def from_file(cls, codemeta_filename):
        """Load `codemeta_filename` into the validator"""
        with open(codemeta_filename) as infile:
            controller = cls(json.load(infile))
        return controller

    @property
    def schema(self):
        return schema()

    @property
    def codemeta_version(self):
        if self._codemeta_version is None:
            if "@context" not in self.metadata:
                raise KeyError("Missing @context key in provided codemeta, could not guess codemeta version")
            else:
                self._codemeta_version = codemeta_version_from_context(self.metadata["@context"])
        return self._codemeta_version

    @property
    def crosswalk_table(self):
        if self._crosswalk_table is None:
            if "@context" not in self.metadata:
                raise KeyError("Missing @context key in provided codemeta, could not guess codemeta version")
            else:
                self._codemeta_version = codemeta_version_from_context(self.metadata["@context"])
                self._crosswalk_table = codemeta_crosswalk(self._codemeta_version)
        return self._crosswalk_table

    def missing_keys(self, level="required"):
        """
        Return the list of keys that are required but not present in the metadata
        level: str
            'required' or 'recommended'
        """
        required_mask = self.crosswalk_table["OSSR Requirement Level"] == level
        keys = np.array(list(self.metadata.keys()))
        required_keys = self.crosswalk_table["Property"][required_mask].values
        missing_keys = required_keys[np.in1d(required_keys, keys, invert=True)]
        return missing_keys

    def validate(self):
        """Validate the metadata against the OSSR CodeMeta schema
        Raises errors for required keys and warnings for recommended keys
        """
        codemeta_dict = self.metadata.copy()
        if codemeta_dict["@type"] != "SoftwareSourceCode":
            raise ValueError(f"Invalid @type {codemeta_dict['@type']}")

        if "@context" not in codemeta_dict:
            raise ValueError("No @context key in provided codemeta")

        if codemeta_dict["@context"] not in CODEMETA_VERSIONS_CONTEXTS:
            raise ValueError(
                f"Invalid @context {codemeta_dict['@context']}, must be one of {list(CODEMETA_VERSIONS_CONTEXTS.keys())}"
            )
        self._codemeta_version = codemeta_version_from_context(codemeta_dict["@context"])

        codemeta_dict.pop("@context")
        codemeta_dict.pop("@type")
        for key in codemeta_dict.keys():
            if key not in list(self.crosswalk_table["Property"]):
                raise ValueError(f"Unknown codemeta key {key}")

        if self.missing_keys("required").size > 0:
            raise CodemetaRequiredError(
                f"Missing {self.missing_keys('required').size} required keys: {self.missing_keys('required')}"
            )
        elif self.missing_keys("recommended").size > 0:
            warn(
                f"Missing {self.missing_keys('recommended').size} recommended keys: {self.missing_keys('recommended')}",
                CodemetaRecommendedWarning,
            )
            return False
        elif "version" in self.metadata and not valid_semver(self.metadata["version"]):
            warn(f"Version {self.metadata['version']} does not follow the recommended format from semver.org.")
            return False
        elif "softwareVersion" in self.metadata and not valid_semver(self.metadata["softwareVersion"]):
            warn(f"Version {self.metadata['softwareVersion']} does not follow the recommended format from semver.org.")
            return False
        else:
            print("CodeMeta is valid")
            return True

    def write(self, path="codemeta.json", overwrite=False):
        """Write the CodeMeta file to `path`"""
        write_json(self.metadata, path, overwrite=overwrite)
