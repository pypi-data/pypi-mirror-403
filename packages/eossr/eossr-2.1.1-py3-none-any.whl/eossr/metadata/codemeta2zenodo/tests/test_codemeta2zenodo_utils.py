from eossr.metadata.codemeta2zenodo.utils import handle_version_type, remove_duplicates


def test_handle_version_type():
    # Test that a list of versions is converted to a string
    zenodo_dict = {"version": ["1.0", "1.0", "1.0"]}
    handle_version_type(zenodo_dict)
    assert zenodo_dict["version"] == "1.0"

    # Test that a single version string is not modified
    zenodo_dict = {"version": "1.0"}
    handle_version_type(zenodo_dict)
    assert zenodo_dict["version"] == "1.0"

    # Test that an error is raised if multiple versions are provided
    zenodo_dict = {"version": ["1.0", "2.0"]}
    try:
        handle_version_type(zenodo_dict)
    except ValueError:
        pass
    else:
        assert False, "Expected ValueError"


def test_remove_duplicates():
    # Test that duplicates are removed from a list of dictionaries
    author_list = [
        {"name": "Alice", "affiliation": "University of X", "orcid": "0000-0001-2345-6789"},
        {"name": "Bob", "affiliation": "University of Y", "orcid": "0000-0002-3456-7890"},
        {"name": "Alice", "affiliation": "University of X", "orcid": "0000-0001-2345-6789"},
    ]
    new_list = remove_duplicates(author_list)
    assert len(new_list) == 2
    assert new_list[0]["name"] == "Alice"
    assert new_list[1]["name"] == "Bob"

    # Test that duplicates are removed from a list of strings
    string_list = ["a", "b", "c", "a", "b"]
    new_list = remove_duplicates(string_list)
    assert len(new_list) == 3
    assert new_list[0] == "a"
    assert new_list[1] == "b"
    assert new_list[2] == "c"
