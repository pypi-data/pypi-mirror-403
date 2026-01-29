=================
Useful  resources
=================


Schema.org & CodeMeta tools
===========================

`Schema.org <https://schema.org/>`_ provides a structured metadata schema for many resources on the Internet.

It also comes with `an online validator <https://validator.schema.org/>`_ for your JSON-LD file.

CodeMeta extend the schema.org with `specific terms for software <https://codemeta.github.io/terms/>`_.


CodeMeta generators and converters
----------------------------------

These tools can help you either generate your `codemeta.json` from scratch or maintain it automatically from other metadata sources.
You may also visit the `codemeta website for more <https://codemeta.github.io/tools/>`_.

* https://pypi.org/project/CodeMetaPy/ - generate codemeta files for Python packages
* https://github.com/ropensci/codemetar - generate codemeta files for R packages
* https://con.github.io/tributors/ - allows you to update a codemeta file with contributors information from different sources
* https://github.com/citation-file-format/cff-converter-python - converts `CITATION.cff` to several formats, including CodeMeta and Zenodo.
* https://github.com/caltechlibrary/codemeta2cff - converts codemeta to `CITATION.cff` using GitHub actions
* https://github.com/caltechlibrary/datatools - converts codemeta to `CITATION.cff` with a command-line tool

You can also generate your `codemeta.json` file online using the OSSR Codemeta generator:

* https://escape2020.pages.in2p3.fr/wp3/codemeta-generator/


The metadata jungle
-------------------

.. image:: https://mermaid.ink/img/pako:eNqFU8FOwzAM_ZUoB9RJbAeOPXABxA4MTQwJaSuHNHHXQJtUicM0Vv4dt121bjCoVDW133t-dpIdl1YBjzmjJyvsRubCIXu-TUxi2P5Za1zRy3Lt0brtKxuPr1kpdFGK6gSXh7QEFKt7jdOQJolp_pRA0ZGWd48HuNQoUFszkVn2b5bSnWYUdd_RaIClHppCkzdvTQMm9OJlGkULm-FGOCAjU3CkuIYhb_IJxirb01oHUbRsg-f1JwSswXrv6iOFM95bOC3G0poPcAhuXG0xt6Y-0b04o1ZVq3lLYJWQ79RCN8v6htgzYs-3J0p_Gu9DV2SpPnL620Z2HHQ6DbT1_rhhcnym7v5w_GD_3fDwLPmQrp2ocvYAazDqkFDagWwss4enQ3S2WPUnjfba2-AkjYnK1_upe6YN2pqAV78gh0LNcGvtWfCgWEqznUdRVQiEzLpyeCrIFr_kJTjqVtEV2jWphGNOLSY8pqWCTIQCE56YL4KGiqrCndI0DB5novBwyQWNZrE1ksfoAvSgWy2o_bIPQsuZdVe1vbFf36JbM_w?type=png)](https://mermaid.live/edit#pako:eNqFU8FOwzAM_ZUoB9RJbAeOPXABxA4MTQwJaSuHNHHXQJtUicM0Vv4dt121bjCoVDW133t-dpIdl1YBjzmjJyvsRubCIXu-TUxi2P5Za1zRy3Lt0brtKxuPr1kpdFGK6gSXh7QEFKt7jdOQJolp_pRA0ZGWd48HuNQoUFszkVn2b5bSnWYUdd_RaIClHppCkzdvTQMm9OJlGkULm-FGOCAjU3CkuIYhb_IJxirb01oHUbRsg-f1JwSswXrv6iOFM95bOC3G0poPcAhuXG0xt6Y-0b04o1ZVq3lLYJWQ79RCN8v6htgzYs-3J0p_Gu9DV2SpPnL620Z2HHQ6DbT1_rhhcnym7v5w_GD_3fDwLPmQrp2ocvYAazDqkFDagWwss4enQ3S2WPUnjfba2-AkjYnK1_upe6YN2pqAV78gh0LNcGvtWfCgWEqznUdRVQiEzLpyeCrIFr_kJTjqVtEV2jWphGNOLSY8pqWCTIQCE56YL4KGiqrCndI0DB5novBwyQWNZrE1ksfoAvSgWy2o_bIPQsuZdVe1vbFf36JbM_w
   :alt: the metadata jungle diagram
   :align: center

.. code to reproduce mermaid diagram of the metadata jungle
.. mermaid::
    flowchart TD
        git[git history] --> mailmap
        githubmeta[GitHub\nmetadata] --> ZEN
        citation.cff --> ZEN
        citation.cff ---> GitHub((GitHub))
        codemeta.json ----> SWH((Software\nHeritage))
        .zenodo.json --> ZEN((Zenodo))
        codemeta.json .-> |eossr| .zenodo.json
        citation.cff .-> |cff-converter-python| codemeta.json & .zenodo.json
        pp[Python package] --> |CodeMetaPy| codemeta.json
        codemeta.json .-> |codemeta2cff| citation.cff
        githubmeta .-> |tributors| .zenodo.json & codemeta.json
        mailmap .-> |tributors| codemeta.json & .zenodo.json
        subgraph Legend
        direction LR
        MS[metadata\nsource] .->|converts into| MS2[metadata\nsource]
        MS -->|is used by| P((plateform))
        end


Zenodo
======

* https://zenodo.org/
* API: https://zenodo.org/api
* Developers help: https://developers.zenodo.org/
* Search guide: https://help.zenodo.org/guides/search/
