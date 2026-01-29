=======================
Add funding to metadata
=======================


Find your funding
#################


To add your fundings to your ``codemeta.json`` file, you will need to find its DOI first.

Too find your funding DOI, you may use search engines such as:

- https://search.crossref.org/funding
- https://ecrcentral.org/funders/


Zenodo services
---------------

1. Through the web portal, when preparing a new upload or editing a record metadata, you can look for funding:

.. image:: ../images/zenodo_funding.png
    :width: 600px
    :align: center

2. Or you may use Zenodo API:

* Online:
    * funders: https://zenodo.org/api/funders/?q=
    * grants: https://zenodo.org/api/grants/?q=

* Or using the eOSSR:

.. code-block::

    from eossr.api.zenodo import search_grants
    search_grants('ESCAPE European Science Cluster of Astronomy & Particle physics ESFRI research infrastructures')

Note Zenodo's search guide to help you refine your search: https://help.zenodo.org/guides/search/


Add funding to ``codemeta.json``
################################

See terms definition on CodeMeta's page.

In codemeta v2.0, funders are provided as a list of organizations and funding is a text entry.
There is work in progress in schema.org and in codemeta to refine that schema.

However, here is the current suggestion to provide funders in codemeta:


.. code-block::

    "funder":[
        {
          "@type": "Organization",
          "name": "European Commission",
          "@id": "https://doi.org/10.13039/501100000780"
        }
      ],
      "funding": "ESCAPE: European Science Cluster of Astronomy & Particle physics ESFRI research infrastructures; Another funding"
