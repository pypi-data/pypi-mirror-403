==================================
docp-docling Library Documentation
==================================

.. contents:: Page Contents
    :local:
    :depth: 1


Overview
========
The ``docp-*`` project suite is designed as a comprehensive (**doc**)ument
(**p**)arsing library. Built in CPython, it consolidates the capabilities
of various lower-level libraries, offering a unified solution for parsing
binary document structures.

The suite is extended by several sister projects, each providing unique
functionality:

.. list-table:: Extended Functionality
  :widths: 50 150
  :header-rows: 1

  * - Project
    - Description
  * - **docp-core**
    - Centralised core objects, functionality and settings.
  * - **docp-parsers**
    - Parse binary documents (e.g. PDF, PPTX, etc.) into Python objects.
  * - **docp-loaders**
    - Load a parsed document's embeddings into a Chroma vector database, for RAG-enabled LLM use.
  * - **docp-docling**
    - Convert a PDF into Markdown or HTML format via wrappers to the ``docling`` libraries and models.
  * - **docp-dbi**
    - Interfaces to document databases such as ChromaDB, and Neo4j (coming soon).

Toolset (Converters)
--------------------
As of this release, PDF conversion into the following types is supported:

- PDF --> Markdown
- PDF --> HTML

Quickstart
==========

Installation
------------
To install ``docp-docling``, first activate your target virtual environment,
then use ``pip``::

    pip install docp-docling

For older releases, visit `PyPI <pypi-history_>`_ or the
`GitHub Releases <releases_>`_ page.

Model Fetching
--------------
If your project must remain offline, you’ll need to `download the docling language model <download_>`_
locally. The ``pdfparser.PDFParser`` class requires this model to be
accessible, so it must be pre-fetched and set up before use. This section
outlines how to download and configure the model for offline functionality.

1) Download the model:

.. code-block:: bash

    docling-tools models download \
        --output-dir /path/to/models/docling-project

2) Update ``config.toml`` in ``docp-core``:

   Update the ``docling`` key in the ``paths.models`` table to match the
   download path specified in the previous step.

   .. important:: Note the ``config.toml`` file can be found in ``docp-core``.


Enabling GPU Support
--------------------
GPU support (CUDA) should be automatically detected by library internals.
However, guidance for `enabling GPU-support <gpu-support_>`_ is available.

Example Usage
-------------
For convenience, here are a couple examples for how to parse the supported
document types.

Parse a PDF into **Markdown** format:

.. code-block:: python

    >>> from docp_docling import PDFParser

    # Convert
    >>> pdf = PDFParser(path='/path/to/file.pdf')
    >>> pdf.to_markdown()

    # Access the converted content
    >>> pdf.content

    # Render extracted text as HTML and preview in a browser.
    >>> pdf.preview()

Parse a single page from a PDF into **Markdown** format, including images, and store to a file:

.. code-block:: python

    >>> from docp_docling import PDFParser

    # Convert
    >>> pdf = PDFParser(path='/path/to/file.pdf')
    >>> pdf.to_markdown(page_no=1,
                        image_mode='embedded',  # <-- Include images
                        to_file=True)

    # Render extracted text as HTML and preview in a browser.
    >>> pdf.preview()

Parse a single page from a PDF into **HTML** format, including images:

.. code-block:: python

    >>> from docp_docling import PDFParser

    # Convert
    >>> pdf = PDFParser(path='/path/to/file.pdf')
    >>> pdf.to_html(page_no=1,
                    image_mode='embedded')  # <-- Include images

    # Render extracted text and preview in a browser.
    >>> pdf.preview()

Using the Library
=================
This documentation provides detailed explanations and usage examples for
each importable module. For in-depth documentation, code examples, and
source links, refer to the :ref:`library-api` page.

A **search** field is available in the left navigation bar to help you
quickly locate specific modules or methods.

Troubleshooting
===============
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions,
please :ref:`contact us <contact-us>` or open an issue on `GitHub <github_>`_.

Documentation Contents
======================
.. toctree::
    :maxdepth: 1

    library
    changelog
    contact

Indices and Tables
==================
* :ref:`genindex`
* :ref:`modindex`

.. _api: https://docp-docling.readthedocs.io/en/latest/
.. _download: https://docling-project.github.io/docling/usage/advanced_options/#model-prefetching-and-offline-usage
.. _github: https://github.com/s3dev/docp-docling
.. _gpu-support: https://docling-project.github.io/docling/usage/gpu/
.. _pypi-history: https://pypi.org/project/docp-docling/#history
.. _releases: https://github.com/s3dev/docp-docling/releases

|lastupdated|
