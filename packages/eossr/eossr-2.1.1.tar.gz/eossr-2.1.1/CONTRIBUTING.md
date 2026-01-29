# Contributing

Contributions are most welcome.

When contributing to this repository, it is good practice to first discuss
the requested change through issues with the owners of this repository
before making a change.
This will ensure the change you wish to make is aligned with current of planned developments.

## GitLab account

To open issues or merge requests, you need first to create a gitlab account.

## Merge request process

1. If you are a new contributor, please add your contact information to `codemeta.json`

2. Update the `modifiedDate`, `version` and other necessary information in `codemeta.json`.
You may use the script `eossr/script/update_codemeta.py`.

3. (Re-)Install the eossr after you made changes: `pip install ".[extras]"`

4. Unit tests:

   - If you are adding a new function / method,
   please add the corresponding unit tests.
   - Run `pytest eossr`.
   - Note that some tests will not run if you don't setup
   a zenodo token in your env (see README).

   These will be tested during the CI after you opened a merge request though.

5. Committing your changes will automatically run pre-commit hooks
that will lint your code.
Some changes might need to be addressed and/or committed again.

6. Open a merge request.
All tests must pass for the merge request to be reviewed (and accepted).

Note that all contributions will be under the MIT license.

## Issues

### Bug report / features requests

If you wish to report a bug and request for a new feature,
please open an issue and use the corresponding template.
Be as precise and exhaustive as possible to fasten the implementation of a fix.

### Metadata discussion

The eOSSR repository is also the place to discuss the metadata schema
of the OSSR implemented in `codemeta.json`.
If you want to modify OSSR metadata schema,
open an issue and add the `MetaData` label.
