import datetime
import re
import warnings
from typing import Any, Dict, List
from urllib.parse import urlparse

import numpy as np

from ...api.zenodo import search_communities, search_licenses
from ...utils import spdx_licenses
from ..codemeta import codemeta_crosswalk

CROSSWALK_TABLE = codemeta_crosswalk()
__filtered_table__ = CROSSWALK_TABLE.query("Type.str.contains('Organization') or Type.str.contains('Person')")
CODEMETA_ROLES = __filtered_table__["Property"].values
CODEMETA_CONTRIBUTORS_ROLES = __filtered_table__.loc[__filtered_table__["Zenodo"] == "contributors", "Property"].values
CODEMETA_CREATORS_ROLES = __filtered_table__.loc[__filtered_table__["Zenodo"] == "creators", "Property"].values


__CONVERTER_MAPPING__ = {
    "Text or URL": lambda x: TextOrUrlConverter(x).convert(),
    "Number or Text": lambda x: NumberOrTextConverter(x).convert(),
    "Text": lambda x: TextConverter(x).convert(),
    "URL": lambda x: URLConverter(x).convert(),
    "Person": lambda x: PersonConverter(x).convert(),
    "Organization": lambda x: OrganizationConverter(x).convert(),
    "Boolean": lambda x: BooleanConverter(x).convert(),
    "PropertyValue or URL": lambda x: URLConverter(x).convert(),
    "Number": lambda x: NumberConverter(x).convert(),
    "Date": lambda x: DateConverter(x).convert(),
    "ComputerLanguage": lambda x: ComputerLanguageConverter(x).convert(),
    "SoftwareSourceCode": lambda x: SoftwareSourceCodeConverter(x).convert(),
    "CreativeWork": lambda x: CreativeWorkConverter(x).convert(),
    "DataFeed": lambda x: DataFeedConverter(x).convert(),
    "ScholarlyArticle": lambda x: ScholarlyArticleConverter(x).convert(),
    "MediaObject": lambda x: MediaObjectConverter(x).convert(),
    "Review": lambda x: TextConverter(x).convert(),
    "CodeRepository": lambda x: CodeRepositoryConverter(x).convert(),
    "Readme": lambda x: ReadmeConverter(x).convert(),
    "Integer or Text": lambda x: NumberOrTextConverter(x).convert(),
    "CreativeWork or URL": lambda x: URLConverter(x).convert(),
}


def MasterConverter(codemeta_value: Any, codemeta_type: str, codemeta_key=None, zenodo_contributor_type=None):
    """
    Converts a given value to a Zenodo-compatible format based on the provided codemeta info.

    Args:
        codemeta_value (Any): The value to be converted.
        codemeta_type (str): The CodeMeta type of the key for the value from the crosswalk table.
        codemeta_key (str, optional): The CodeMeta key for the value. Defaults to None.

    Returns:
        Any: The converted value.

    Raises:
        ValueError: If the key type is unknown or if the @type for an Organization or Person is unknown.
    """
    # handling lists
    if isinstance(codemeta_value, list):
        converted_values = []
        for item in codemeta_value:
            converted_value = MasterConverter(
                item, codemeta_type, codemeta_key=codemeta_key, zenodo_contributor_type=zenodo_contributor_type
            )
            if converted_value is not None:
                if isinstance(converted_value, list):
                    converted_values.extend(converted_value)
                else:
                    converted_values.append(converted_value)
        return converted_values if converted_values else None

    # handling special cases first
    if codemeta_key == "codeRepository":
        return CodeRepositoryConverter(codemeta_value).convert()
    if codemeta_key == "readme":
        return ReadmeConverter(codemeta_value).convert()
    if codemeta_key == "applicationCategory":
        return CommunityConverter(codemeta_value).convert()
    if codemeta_key in CODEMETA_CONTRIBUTORS_ROLES:
        return ContributorConverter(codemeta_value, zenodo_contributor_type).convert()
    if codemeta_key == "license":
        return LicenseConverter(codemeta_value).convert()
    if codemeta_key == "citation":
        return ReferencesConverter(codemeta_value).convert()

    if codemeta_type == "Organization or Person":
        if codemeta_value.get("@type", None) == "Person":
            return PersonConverter(codemeta_value).convert()
        elif codemeta_value.get("@type", None) == "Organization":
            return OrganizationConverter(codemeta_value).convert()
        else:
            raise ValueError(f"Unknown @type for {codemeta_value}")

    if codemeta_type in __CONVERTER_MAPPING__:
        return __CONVERTER_MAPPING__[codemeta_type](codemeta_value)
    else:
        raise ValueError(f"Unknown key type {codemeta_type}")


def is_url(url: str) -> bool:
    """
    Check if a given string is a valid URL.

    Parameters
    ----------
    url : str
        The string to check.

    Returns
    -------
    bool
        True if the string is a valid URL, False otherwise.

    Examples
    --------
    >>> is_url('https://github.com/')
    True

    >>> is_url('not_a_url')
    False
    """
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])


class BaseConverter:
    """
    Base class for all converters.

    Attributes:
    -----------
    value : Any
        The value to be converted.

    Methods:
    --------
    convert() -> Any:
        Converts the value to the desired format.
    check_type() -> None:
        Checks if the type of the value is valid.
    is_valid_type(valid_type) -> bool:
        Checks if the type of the value is valid.
    """

    def __init__(self, value):
        self.value = value
        self.check_type()

    def convert(self) -> Any:
        raise NotImplementedError

    def check_type(self) -> None:
        raise NotImplementedError

    def is_valid_type(self, valid_type):
        return isinstance(self.value, valid_type) or all(isinstance(x, valid_type) for x in self.value)


class DummyConverter(BaseConverter):
    def convert(self):
        return None


class ListConverter(BaseConverter):
    def convert(self):
        return [self.value]


class ReferencesConverter(ListConverter):
    """
    Converter for the 'references' field of CodeMeta to the 'references' field of Zenodo.
    """

    def check_type(self) -> None:
        """
        Check if the value is a valid URL.
        """
        if not is_url(self.value):
            raise ValueError(f"Invalid URL: {self.value}")


class TextConverter(BaseConverter):
    """
    A converter that converts a string to a string.

    Attributes:
    -----------
    value : str
        The string to be converted.
    """

    def check_type(self) -> None:
        if not isinstance(self.value, str):
            raise ValueError(f"{self.value} must be a string, not {type(self.value)}")

    def convert(self) -> str:
        """
        Returns the string to be converted.
        """
        return self.value


class URLConverter(BaseConverter):
    """A converter for URLs.

    This converter simply returns the input value as is, but checks that it is a valid URL.

    Attributes:
        value (str): The input URL to be converted.
    """

    def convert(self):
        """Converts the input URL.

        Returns:
            str: The input URL.
        """
        return self.value

    def check_type(self):
        """Checks that the input value is a valid URL.

        Raises:
            ValueError: If the input value is not a valid URL.
        """
        if not is_url(self.value):
            raise ValueError(f"Invalid URL: {self.value}")


class CodeRepositoryConverter(URLConverter):
    """
    `codeRepository` is a special case of URLConverter as the returned value is not directly the URL but a List[dict]
    "related_identifiers": [{
        "scheme": "url",
        "identifier": "https://github.com/myusername/mycode",
        "relation": "isDerivedFrom",
        "resource_type": "software"
        }
    ],
    """

    def convert(self):
        return [
            {
                "scheme": "url",
                "identifier": self.value,
                "relation": "isDerivedFrom",
                "resource_type": "software",
            }
        ]


class PersonConverter(BaseConverter):
    """
    A converter class for converting a Person object to a Zenodo-compatible format.

    Attributes:
        value (dict): The Person object to be converted.

    Raises:
        ValueError: If the Person object is not a dict or is not of type Person.
                    If the Person object does not have either givenName or familyName.
                    If the affiliation is not a dict or list of dicts.
    """


class PersonConverter(BaseConverter):
    def check_type(self):
        if not isinstance(self.value, dict):
            raise ValueError(f"Person must be a dict, not {type(self.value)}")
        if not self.value["@type"] == "Person":
            raise ValueError("Person must be of type Person")

    def convert(self):
        zenodo_person = {}
        name = self.value.get("givenName", "")
        family_name = self.value.get("familyName", "")
        if name and family_name:
            complete_name = f"{name} {family_name}"
        elif name:
            complete_name = name
        elif family_name:
            complete_name = family_name
        else:
            raise ValueError("Person must have either givenName or familyName")

        zenodo_person["name"] = complete_name

        affiliation = self.value.get("affiliation", None)
        if affiliation is None:
            pass
        elif isinstance(affiliation, dict):
            # OrganizationConverter always return a list of dicts (because that's what Zenodo expects)
            zenodo_person["affiliation"] = OrganizationConverter(affiliation).convert()[0]["name"]
        elif isinstance(affiliation, list):
            # if they are several affiliations, we join them in a single string
            zenodo_person["affiliation"] = "; ".join(
                [OrganizationConverter(org).convert()[0]["name"] for org in affiliation]
            )
        else:
            raise ValueError(f"Affiliation must be a dict or list of dicts, not {type(affiliation)}")

        identifier = self.value.get("identifier", None)
        if identifier and IDConverter(identifier).convert().get("orcid", None):
            zenodo_person["orcid"] = IDConverter(identifier).convert()["orcid"]

        return [zenodo_person]


class IDConverter(BaseConverter):
    """
    Zenodo supports only ORCID as ID
    """

    def check_type(self):
        if not isinstance(self.value, str):
            raise ValueError(f"{self.value} must be a string, not {type(self.value)}")

    @staticmethod
    def _check_orcid_number(number):
        if re.match(r"^\d{4}-\d{4}-\d{4}-\d{3}[0-9X]$", number):
            return True
        else:
            return False

    def convert(self):
        """
        Convert the ID to a Zenodo-compatible format.

        Returns:
            dict: A dictionary containing the ORCID number if the ID is valid, otherwise an empty dictionary.
        """
        if "orcid.org/" in self.value:
            orcid_number = self.value.split("orcid.org/")[1]
            if self._check_orcid_number(orcid_number):
                return {"orcid": self.value}
            else:
                return {}
        elif self._check_orcid_number(self.value):
            return {"orcid": self.value}
        else:
            return {}


class OrganizationConverter(BaseConverter):
    # handle Organization Conversion
    # take dict as entry and return a list of dict (because that's what Zenodo expect, even for a single organization)
    def check_type(self):
        if not isinstance(self.value, dict):
            raise ValueError(f"Organization must be a dict, not {type(self.value)}")

    def _convert_dict(self):
        if "name" not in self.value:
            raise ValueError("Organization must have a name")
        return {"name": self.value["name"]}

    def convert(self) -> List[Dict[str, Any]]:
        if isinstance(self.value, dict):
            return [self._convert_dict()]


class ComputerLanguageConverter(BaseConverter):
    def convert(self):
        return self.value["name"]


class TextOrUrlConverter(TextConverter):
    """
    Treat as text
    """

    pass


class NumberConverter(BaseConverter):
    def convert(self):
        return str(self.value)


class NumberOrTextConverter(BaseConverter):
    def check_type(self):
        pass

    def convert(self):
        return str(self.value)


class BooleanConverter(BaseConverter):
    def check_type(self):
        if not isinstance(self.value, bool):
            raise ValueError(f"{self.value} must be a bool, not {type(self.value)}")

    def convert(self):
        return self.value


class SoftwareSourceCodeConverter(BaseConverter):
    def convert(self):
        raise NotImplementedError


class CreativeWorkConverter(BaseConverter):
    def convert(self):
        raise NotImplementedError


class DataFeedConverter(BaseConverter):
    def convert(self):
        raise NotImplementedError


class ScholarlyArticleConverter(BaseConverter):
    def convert(self):
        raise NotImplementedError


class MediaObjectConverter(BaseConverter):
    def convert(self):
        raise NotImplementedError


class ReadmeConverter(TextConverter):
    """
    Readme is a special case of TextConverter as the returned value is not directly the text but a dict
    {
        "scheme": "url",
        "identifier": value,
        "relation": "isDocumentedBy",
        "resource_type": "publication-softwaredocumentation",
    }
    """

    def convert(self):
        return [
            {
                "scheme": "url",
                "identifier": self.value,
                "relation": "isDocumentedBy",
                "resource_type": "publication-softwaredocumentation",
            }
        ]


class DateConverter(BaseConverter):
    def check_type(self):
        # check that date is in ISO 8601 format
        try:
            datetime.datetime.fromisoformat(self.value)
        except ValueError as exc:
            raise ValueError(f"Incorrect date format, should be ISO 8601 format, but is {self.value}") from exc

    def convert(self):
        return self.value


class CommunityConverter(TextConverter):
    """
    A converter class for converting community metadata to Zenodo format.

    Attributes:
    -----------
    matching_communities : list
        A list of matching communities found in Zenodo.
    """

    def __init__(self, value):
        self._matching_communities = None
        super().__init__(value)

    @property
    def matching_communities(self):
        """
        A property that searches for matching communities in Zenodo.

        Returns:
        --------
        list
            A list of matching communities found in Zenodo.
        """
        if self._matching_communities is None:
            self._matching_communities = search_communities(
                self.value,
                size=100,
            )
        return self._matching_communities

    def convert(self):
        """
        A method that converts community metadata to Zenodo format.

        Returns:
        --------
        dict
            A dictionary containing the identifier of the community.
        """
        community = None
        for com in self.matching_communities:
            if com["slug"] == self.value:
                community = {"identifier": com["slug"]}
                break
        return community


class ReviewConverter(BaseConverter):
    def convert(self) -> Any:
        raise NotImplementedError("Should be implemented to support CodeMeta v3.0")


class OrganizationOrPersonConverter(BaseConverter):
    def check_type(self):
        if not isinstance(self.value, dict):
            raise ValueError(f"Organization or Person must be a dict, not {type(self.value)}")
        if "@type" not in self.value:
            raise ValueError("Organization or Person must have a @type")
        if self.value["@type"] not in ["Organization", "Person"]:
            raise ValueError(
                f"Organization or Person must be of type Organization or Person, not {self.value['@type']}"
            )

    def convert(self):
        if self.value.get("@type", None) == "Person":
            return PersonConverter(self.value).convert()
        elif self.value.get("@type", None) == "Organization":
            return OrganizationConverter(self.value).convert()
        else:
            raise ValueError(f"Unknown @type for {self.value}")


class ContributorConverter(OrganizationOrPersonConverter):
    """
    This class is responsible for converting a contributor from CodeMeta format to Zenodo format.
    """

    def __init__(self, value, zenodo_contributor_type):
        """
        Initialize the Converter object.

        Args:
            value (str): The value to be converted.
            zenodo_contributor_type (str): The type of contributor in Zenodo.

        Returns:
            None
        """
        self.contributor_type = zenodo_contributor_type
        super().__init__(value)

    def check_type(self):
        super().check_type()
        # if self.contributor_type not in CODEMETA_CONTRIBUTORS_ROLES:
        #     raise ValueError(f"Contributors roles are {CODEMETA_CONTRIBUTORS_ROLES}, {self.contributor_type} is not one of them")

    def convert(self):
        zenodo_contributor = OrganizationOrPersonConverter(self.value).convert()
        # OrganizationOrPersonConverter always returns a list of dicts (because that's what Zenodo expects)
        zenodo_contributor[0]["type"] = self.contributor_type

        return zenodo_contributor


class LicenseConverter(BaseConverter):
    """
    This class is responsible for converting a license string or a list of license strings to a Zenodo-compatible license string.
    """

    _all_zenodo_licenses = None
    _all_zenodo_license_ids = None
    _all_zenodo_license_titles = None

    def __init__(self, value: [str, List[str]]) -> [str, List[str]]:
        """
        Initializes an instance of MyClass with a given value.

        Args:
            value: A string or list of strings representing URLs.

        Returns:
            A string or list of strings representing the IDs of the URLs.
        """
        self.value = value
        self.check_type()

        def url_to_id(url):
            return url.rsplit("/")[-1].lower()

        if isinstance(self.value, str):
            self.value = url_to_id(self.value)
        elif isinstance(self.value, list):
            self.value = [url_to_id(val) for val in self.value]

    def check_type(self):
        if isinstance(self.value, list):
            [URLConverter(val).check_type() for val in self.value]
        else:
            URLConverter(self.value).check_type()

    @classmethod
    def all_zenodo_licenses(cls) -> List[Dict[str, Any]]:
        """
        Returns a list of dictionaries containing information about all the licenses available on Zenodo.

        :return: A list of dictionaries, where each dictionary contains information about a single license.
        :rtype: List[Dict[str, Any]]
        """
        if cls._all_zenodo_licenses is None:
            cls._all_zenodo_licenses = search_licenses()
        return cls._all_zenodo_licenses

    @classmethod
    def all_zenodo_license_ids(cls) -> np.ndarray:
        """
        Returns an array of all the Zenodo license IDs.

        :return: An array of all the Zenodo license IDs.
        :rtype: np.ndarray
        """
        if cls._all_zenodo_license_ids is None:
            cls._all_zenodo_license_ids = np.array([lic["id"] for lic in cls.all_zenodo_licenses()])
        return cls._all_zenodo_license_ids

    @classmethod
    def all_zenodo_license_titles(cls) -> np.ndarray:
        """
        Returns an array of all the Zenodo license titles.

        :return: An array of all the Zenodo license titles.
        :rtype: np.ndarray
        """
        if cls._all_zenodo_license_titles is None:
            cls._all_zenodo_license_titles = np.array([lic["title"]["en"] for lic in cls.all_zenodo_licenses()])
        return cls._all_zenodo_license_titles

    def _convert_string(self, license):
        """
        Converts a single license string to a Zenodo-compatible license string.

        :param license: The license string to convert.
        :type license: str
        :return: The Zenodo-compatible license string.
        :rtype: str
        """
        if license in self.all_zenodo_license_ids():
            return license
        elif license in self.all_zenodo_license_titles():
            return self.all_zenodo_license_ids()[self.all_zenodo_license_titles() == license][0]
        elif license in spdx_licenses(open_only=True):
            # should never happen as all open spdx licenses are in zenodo
            # keep to prevent from breaking if new open spdx licenses are added
            return "other-open"
        else:
            warnings.warn(
                "The license provided is not recognized as a known Zenodo license nor as an open-source one. Using 'other-closed'."
            )
            return "other-closed"

    def _convert_list(self, licenses):
        """
        Converts a list of license strings to a Zenodo-compatible license string.

        :param licenses: The list of license strings to convert.
        :type licenses: List[str]
        :return: The Zenodo-compatible license string.
        :rtype: str
        """
        converted_list = [self._convert_string(val) for val in licenses]
        if "other-closed" in converted_list:
            return "other-closed"
        else:
            return "other-open"

    def convert(self):
        """
        Converts the license string or list of license strings to a Zenodo-compatible license string.

        :return: The Zenodo-compatible license string.
        :rtype: str
        """
        if isinstance(self.value, str):
            return self._convert_string(self.value)
        elif isinstance(self.value, list):
            return self._convert_list(self.value)
        else:
            # check type should have raised an error here
            raise ValueError(f"License must be a string or a list of strings, not {type(self.value)}")
