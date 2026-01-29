# A basic document parsing and loading utility - Markdown/HTML Conversion

[![PyPI - Version](https://img.shields.io/pypi/v/docp-docling?style=flat-square)](https://pypi.org/project/docp-docling)
[![PyPI - Implementation](https://img.shields.io/pypi/implementation/docp-docling?style=flat-square)](https://pypi.org/project/docp-docling)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/docp-docling?style=flat-square)](https://pypi.org/project/docp-docling)
[![PyPI - Status](https://img.shields.io/pypi/status/docp-docling?style=flat-square)](https://pypi.org/project/docp-docling)
[![Static Badge](https://img.shields.io/badge/tests-passing-brightgreen?style=flat-square)](https://pypi.org/project/docp-docling)
[![Static Badge](https://img.shields.io/badge/code_coverage-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-docling)
[![Static Badge](https://img.shields.io/badge/pylint_analysis-100%25-brightgreen?style=flat-square)](https://pypi.org/project/docp-docling)
[![Documentation Status](https://readthedocs.org/projects/docp-docling/badge/?version=latest&style=flat-square)](https://docp-docling.readthedocs.io/en/latest/)
[![PyPI - License](https://img.shields.io/pypi/l/docp-docling?style=flat-square)](https://opensource.org/license/gpl-3-0)
[![PyPI - Wheel](https://img.shields.io/pypi/wheel/docp-docling?style=flat-square)](https://pypi.org/project/docp-docling)

## Overview
The `docp-*` project suite is designed as a comprehensive (**doc**)ument \(**p**)arsing library. Built in CPython, it consolidates the capabilities of various lower-level libraries, offering a unified solution for parsing binary document structures.

The suite is extended by several sister projects, each providing unique functionality:

Project | Description
|:---|:---
**docp-core** | Centralized core objects, functionality and settings.
**docp-parsers** | Parse binary documents (e.g. PDF, PPTX, etc.) into Python objects.
**docp-loaders** | Load a parsed document's embeddings into a Chroma vector database, for RAG-enabled LLM use.
**docp-docling** | Convert a PDF into Markdown or HTML format via wrappers to the `docling` libraries and models.
**docp-dbi** | Interfaces to document databases such as ChromaDB, and Neo4j (coming soon).

### The Toolset (Converters)
As of this release, PDF conversion into the following types is supported:

- PDF --> Markdown
- PDF --> HTML

## Quickstart

### Installation
To install `docp-docling`, first activate your target virtual environment, then use `pip`:

```bash
pip install docp-docling
```

For older releases, visit [PyPI][pypi-history] or the [GitHub Releases][releases] page.

### Model Fetching
If your project must remain offline, you’ll need to [download the docling language model][download] locally. The ``pdfparser.PDFParser`` class requires this model to be accessible, so it must be pre-fetched and set up before use. This section outlines how to download and configure the model for offline functionality.

1) Download the model:

``` bash
docling-tools models download \
    --output-dir /path/to/models/docling-project
```

2) Update ``config.toml`` **in ``docp-core``**:

    - Update the ``docling`` key in the ``paths.models`` table to match the download path specified in the previous step.

#### Enabling GPU Support
GPU support (CUDA) should be automatically detected by library internals. However, guidance for [enabling GPU-support][gpu-support] is available.

### Example Usage
For convenience, here are a couple examples for how to convert a PDF into the supported formats.

**Parse a PDF into *Markdown* format:**

```python
>>> from docp_docling import PDFParser

# Convert
>>> pdf = PDFParser(path='/path/to/file.pdf')
>>> pdf.to_markdown()

# Access the converted content
>>> pdf.content

# Render extracted text as HTML and preview in a browser.
>>> pdf.preview()
```

**Parse a single page from a PDF into *Markdown* format, including images, and store to a file:**

```python
>>> from docp_docling import PDFParser

# Convert
>>> pdf = PDFParser(path='/path/to/file.pdf')
>>> pdf.to_markdown(page_no=1,
                    image_mode='embedded',  # <-- Include images
                    to_file=True)

# Render extracted text as HTML and preview in a browser.
>>> pdf.preview()
```

**Parse a single page from a PDF into *HTML* format, including images:**

```python
>>> from docp_docling import PDFParser

# Convert
>>> pdf = PDFParser(path='/path/to/file.pdf')
>>> pdf.to_html(page_no=1,
                image_mode='embedded')  # <-- Include images

# Render extracted text and preview in a browser.
>>> pdf.preview()
```

## Using the Library
The documentation suite provides detailed explanations and usage examples for each importable module. For in-depth documentation, code examples, and source links, refer to the [Library API][api] page.


A **search** field is available in the left navigation bar to help you quickly locate specific modules or methods.

## Troubleshooting
No troubleshooting guidance is available at this time.

For questions not covered here, or to report bugs, issues, or suggestions, please open an issue on [GitHub][github].


[api]: https://docp-docling.readthedocs.io/en/latest/
[download]: https://docling-project.github.io/docling/usage/advanced_options/#model-prefetching-and-offline-usage
[github]: https://github.com/s3dev/docp-docling
[gpu-support]: https://docling-project.github.io/docling/usage/gpu/
[pypi-history]: https://pypi.org/project/docp-docling/#history
[releases]: https://github.com/s3dev/docp-docling/releases
