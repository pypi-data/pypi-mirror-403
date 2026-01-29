def handle_version_type(zenodo_dict):
    """
    Make sure that the version is a string, not a list of strings
    """
    if "version" in zenodo_dict and isinstance(zenodo_dict["version"], list):
        if not all(x == zenodo_dict["version"][0] for x in zenodo_dict["version"]):
            raise ValueError(f"Multiple versions provided: {zenodo_dict['version']}")
        else:
            zenodo_dict["version"] = zenodo_dict["version"][0]


def remove_duplicates(list):
    """
    loop through author list and remove duplicates
    persons are dictionnaries with name, affiliation (optional) and orcid (optional)
    """
    new_list = []
    for value in list:
        if value not in new_list:
            new_list.append(value)
    return new_list
