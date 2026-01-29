
.. _library-api:

=========================
Library API Documentation
=========================
The page contains simple library usage examples and the module-level
documentation for each of the importable modules in ``docp-docling``.

.. contents::
    :local:
    :depth: 1

Use Cases
=========
To save digging through the documentation for each module and cobbling
together what a 'standard use case' may look like, a couple have been
provided here.

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

Module Documentation
====================
In addition to the module-level documentation, most of the public
classes and/or methods come with one or more usage examples and access
to the source code itself.

There are two type of modules listed here:

    - Those whose API is designed to be accessed by the user/caller
    - Those which are designated 'private' and designed only for internal
      use

We've exposed both here for completeness and to aid in understanding how
the library is implemented:

.. toctree::
   :maxdepth: 1

   parsers_pdfparser

|lastupdated|
