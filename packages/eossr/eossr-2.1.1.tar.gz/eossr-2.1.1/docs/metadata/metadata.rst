OSSR metadata introduction
==========================

Among the `OSSR guidelines and rules of
participation <http://purl.org/escape/ossr>`__, a metadata file must be added to your record.

In the ESCAPE context, the use of the `CodeMeta
schema <https://codemeta.github.io/>`__ is strongly advised for uploads
containing software. This is the format used by ESCAPE services.


Quickstart - How to incorporate a CodeMeta metadata file into your project.
---------------------------------------------------------------------------

1. Go to the `ESCAPE CodeMeta
   generator <https://escape2020.pages.in2p3.fr/wp3/codemeta-generator/>`__.
   Generate a ``codemeta.json`` file based on your project. You may also check in the same web application that the generated file is valid !

2. Copy the generated metadata into a ``codemeta.json`` file and include
   it in the **root directory** of your project.

3. Help, description and the list of mandatory metadata may be found in the OSSR metadata table <ossr_metadata.html>


Keywords list
~~~~~~~~~~~~~

* Multiple keywords must be separated with a comma ``,`` and between double ``"``, such as:

.. code:: json

    {
      ...
    "keywords": ["CTA", "Astroparticle physics", "jupyter-notebook", ...],
      ...
    }

* Here is a list of recommended keywords you can use to ensure better findability and usability of your software or dataset in ESCAPE context and beyond:

#. Project category:

   -  CTA
   -  LSST
   -  LOFAR
   -  SKA
   -  EGO-Virgo
   -  KM3NeT
   -  ELT
   -  EST
   -  HL-LHC
   -  FAIR
   -  CERN
   -  ESO
   -  JIVE
   -  IVOA
   -  EOSC
   -  ESO

#. Domain category (single keywords):

   -  ``Astronomy``
   -  ``Astroparticle physics``
   -  ``Particle physics``

#. Add ``jupyter-notebook`` as keyword if you project is based on or contains jupyter notebooks. This keyword is notably used by the `ESAP <https://projectescape.eu/services/esfri-science-analysis-platform>`_ to filter interactive analysis.

#. Use well defined and broadly recognised keywords from formalized thesauri, such as `the Unified Astronomy Thesaurus <https://astrothesaurus.org/>`_


Create a Zenodo metadata file from the a CodeMeta schema file
-------------------------------------------------------------

The zenodo repository does not accept codemeta metadata files yet.
Meanwhile, the `eossr
library <https://gitlab.com/escape-ossr/eossr>`__ provides a
simple tool to create a native Zenodo metadata file (``.zenodo.json``)
from a ``codemeta.json`` file. To do so:

1. Create a ``codemeta.json`` file and include all your metadata

2. Install the eOSSR package

3. And then just run

.. code:: bash

   $ eossr-codemeta2zenodo --help
   $ eossr-codemeta2zenodo -i codemeta.json

Also, you can check and use the `online
codemeta2zenodo <https://escape2020.pages.in2p3.fr/wp3/codemeta2zenodo/codemeta2zenodo.html>`__
converter, based on the same library.


Extending the CodeMeta Context schema
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In case you find that CodeMeta context does not describe deep enough
your digital resource, you can extend the metadata context and combine
it with all the terms available at
`https://schema.org <https://schema.org/docs/full.html>`__. For this
purpose, and following the `CodeMeta’s developer
guide <https://codemeta.github.io/developer-guide/>`__

1. Modify the ``"@Context"`` key of the ``codemeta.json`` as:

::

   "@context": ["https://raw.githubusercontent.com/codemeta/codemeta/2.0-rc/codemeta.jsonld",
                "http://schema.org/"]

2. Include the desired terms / properties following the ``schema.org``
   context.
