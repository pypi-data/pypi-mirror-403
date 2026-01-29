================
GitLab to Zenodo
================

This page details the steps needed to automatise the publication to the
`ESCAPE
OSSR <https://zenodo.org/communities/escape2020/?page=1&size=20>`__ from
a gitlab project.

You would need to follow these steps just **once**! After this, every
time you create a new release of your project, it will be automatically
uploaded and published to the OSSR.

Note that you can **test the upload** first using the `Zenodo
sandbox <https://sandbox.zenodo.org/>`__.


Upload from GitLab in 4 steps
=============================


1. Include an ESCAPE CodeMeta metadata file
-------------------------------------------

See the `metadata description <metadata.html>`__
and place the ``codemeta.json`` file in the root directory of your repository (it replaces completely the `.zenodo.json` file that should therefore be removed). Check the
conformity to our standards! If required fields in the file are missing,
the upload will not work.

2. Link your GitLab project with Zenodo.
----------------------------------------

To allow GitLab to communicate with Zenodo through their APIs, a personal
access token must be created and included into the GitLab project (as a
**masked !!** environment variable).

Please note that (to date) the token can be assigned **only to a
single** Zenodo account.

To create the token:

* Go to the token creation page `Zenodo account <https://zenodo.org/account/settings/applications/tokens/new/>`_.

(`zenodo.org <https://zenodo.org/>`_ –>
``Account`` –> ``Applications`` –> ``Personal access token`` –>
``New token``)

* Name the token and select the desired ``Scopes`` (we recommend ticking all three boxes).

This token will be used later by the deployment stage.

For not sharing publicly your personal token, you should create a
**masked** environment variable in your GitLab repository. This way, the
token could be used as a variable without revealing its value. To create
an environment variable:

* Go to your GitLab project.
* Click on ``Settings`` –> ``CI/CD`` –> ``Variables`` –> ``Add variable`` –> Fill the fields –> **Mask your variable(s) !!**

Please name your environment variables as follows (so that no changes
should be done to the ``.gitlab-ci.yml`` file):

* ``ZENODO_TOKEN`` or ``SANDBOX_ZENODO_TOKEN`` if using Zenodo sandbox
* ``ZENODO_PROJECT_ID`` or ``SANDBOX_ZENODO_PROJECT_ID`` if using Zenodo sandbox

so that environment variable(s) should look like:

.. code:: sh

       $ eossr-upload-repository --token $ZENODO_TOKEN --input-directory zenodo_build

or

.. code:: sh

       $ eossr-upload-repository -t $SANDBOX_ZENODO_TOKEN --sandbox -i zenodo_build -id $SANDBOX_ZENODO_PROJECT_ID


3. Into your ``.gitlab-ci.yml`` file
------------------------------------

Add the following `code
snippet <snippets/3.ex_CI_upload_ossr.html>`__.

**Important note**. Please read the full documentation of the page !

-  The first time the CI is run, remove ``-id $ZENODO_PROJECT_ID`` to create
   a new record.
-  After that, **you need to create the CI variable**
   ``$ZENODO_PROJECT_ID`` (or ``$SANDBOX_ZENODO_PROJECT_ID``) using the
   newly created record ID.
-  **If you don’t,** the next release will either create a new record instead
   of updating the existing one, or fail.

To recover and save the project ID:

* Go to https://zenodo.org/deposit (or https://sandbox.zenodo.org/deposit)
* Click into your just uploaded project
* From your browser search bar, **just** copy the number (your ``deposit id``) that it is included in the https direction - ex: ``https://zenodo.org/record/3884963`` –> just copy ``3884963``
* Save it as a new environment variable in your GitLab project: Go to your GitLab project. Click on ``Settings`` –> ``CI/CD`` –> ``Variables`` –> ``Add variable`` –> ``KEY``\ =\ ``ZENODO_DEPOSIT_ID`` or ``SANDBOX_ZENODO_PROJECT_ID`` and fill the value with the deposit id.


4. ‘One-click-build-and-publish’
--------------------------------

1. Go to your GitLab project.
2. Click on ``Project overview`` –> ``Releases`` –> ``New release``
3. In order to see your project on zenodo, make sure the pipeline is
   run.

What happens during the GitLab-Zenodo CI process
================================================

.. figure:: https://mermaid.ink/img/pako:eNp1UsFu4jAQ_ZWRT0GCatu9cdhDYYWQqq6UlAvKZbAHcOt4ImdMRQn_vg5JpYJa-2K992Y879knpdmQmqqt43e9xyDw8lh6SKuJm13Aeg8LK0-46cHFfdYVVCR499qwH_UweTPwFy1MJn-gfaZ3yMkRNtTCIj8NXB69p3Ae9PlF-68o8slseYW1XItlj66F1Uu28lZAqJFm9JNqPsseo3UG5qzfKIBmL2jTXT9WFMuhorB-Fx0GK0dYVrij0U0GVwPmv7IFCdSBX0kLhN7jUJLfZzP2B0pJXiUFwnD3QZ4Nf00uf8jWtv7Sq-bGCofjJ_87W9WO0YDsCT6SFIPe2wN1_daXdrdvMMzam63jxlmNneP2wnxjrIfWWf9gmoO5bVn6fgOosaooVGhN-jSnDilVmqyiUk3T0dAWo5NSlf6cpLE2KPTXdI7UdIuuobHCKFwcvVZTCZE-RXOLaaJqUJ3_A8NJ1x8
    :alt: OSSR-CI-diagram



Trigger the GitLabCI and publish your project to Zenodo.
-----------------------------------------------------------

-  If you have included the ``deploy``
   `stage </snippets/3.ex_CI_upload_ossr.html>`_
   into your ``.gitlab-ci.yml`` file, the gitlab runner will download
   and use a Docker container specifically created for this purpose.
-  The Docker container is available at the `GitLab in2p3 container registry <https://gitlab.com/escape-ossr/eossr/container_registry>`_.
-  This container contains the eOSSR library installed in order to process your upload to the OSSR

-  The GitLab runner will perform the following stages:

   1. Search for the last release / commit of your project.
   2. Search for a CodeMeta metadata file and convert it to the Zenodo compliant format.
   3. Upload a new record version to the OSSR. The entry will contain the information within the metadata files.
