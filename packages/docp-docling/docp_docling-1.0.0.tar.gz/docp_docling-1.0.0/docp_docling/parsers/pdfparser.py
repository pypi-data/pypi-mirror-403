#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
:Purpose:   This module provides the implementation for the docling-based
            PDF parser. This parser is specifically designed for
            converting content from a PDF file to Markdown and/or HTML
            format.

:Platform:  Linux/Windows | Python 3.11+
:Developer: J Berendt
:Email:     development@s3dev.uk

:Comments:  The :class:`PDFParser` class requires the ``docling`` project
            model to be accessible. The following guidance can be used
            to obtain the model and set the model's path in the config
            file.

            **Model Pre-Fetching:**
            The ``docling`` project `model`_ must be downloaded and
            available for use before this module can be used. Below is
            guidance for pre-fetching the model for offline usage.

            1) Download the model::

                   docling-tools models download \\
                        --output-dir /path/to/models/docling-project

            2) Update ``config.toml``:

               With the ``docp-core/config/config.toml`` file, update the
               ``docling`` key in the ``paths.models`` table to match the
               download path specified in the previous step.

            **GPU Support:**
            GPU support (CUDA) should be enabled automatically by the
            internals. However, guidance for enabling GPU-support can be
            found `here <gpu-support_>`_.

.. _model: https://docling-project.github.io/docling/usage/advanced_options/
    #model-prefetching-and-offline-usage
.. _gpu-support: https://docling-project.github.io/docling/usage/gpu/

"""
# pylint: disable=wrong-import-order

import os
import logging
import tempfile
import torch
import webbrowser
from docling_core.types.doc.base import ImageRefMode
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.datamodel.pipeline_options import PdfPipelineOptions
# This import must be commented when building the docs.
from docling.document_converter import DocumentConverter, PdfFormatOption
from docp_core import Document
from docp_core import SETTINGS
from docp_core.objects.textobject import TextObject
from docp_core.utilities import utilities
from docp_parsers import PDFParser as _PDFParser
from ghmdlib import converter

# Silence logging output. Cannot seem to silence the output for RapidOCR.
_logger_docling = logging.getLogger('docling')
_logger_docling.setLevel(logging.ERROR)


class PDFParser(_PDFParser):
    """Docling-based PDF parser class.

    Args:
        path (str): Path to the PDF file to be parsed.
        detailed_extraction (bool, optional): Optimise extraction of
            additional features such as code and formulae.
            Defaults to False.

            .. tip::

                While useful in certain cases, this extraction mode
                increases processing time by ~2x.

    .. note::

        For basic text or table extraction from PDFs, the ``PDFParser``
        class available from the ``docp-parsers`` library is recommended
        as it’s fast and straightforward.

        For converting PDFs into **Markdown** or **HTML** formats, this
        class provides the functionality you need:

            - **HTML:** Use the :meth:`to_html` method.
            - **Markdown:** Use the :meth:`to_markdown` method.

        As an extension of :class:`docp-parsers.PDFParser`, it also
        supports all the core PDF extraction features, so you can also
        use it for text and table extraction.

    .. important::

        If parsing a single document several times, (e.g. for testing
        different method options) the content of each parse will be
        appended to the :attr:`texts` attribute. This can lead to
        unexpected content. If applicable to your use case, ensure to
        call the :meth:`initialise` method between parsings to clear the
        content.

    :Example:

        Parse a PDF into **Markdown** format::

            >>> from docp_docling import PDFParser

            # Convert
            >>> pdf = PDFParser(path='/path/to/file.pdf')
            >>> pdf.to_markdown()

            # Access the converted content
            >>> pdf.content

            # Render extracted text as HTML and preview in a browser.
            >>> pdf.preview()


        Parse a single page from a PDF into **Markdown** format,
        including images, and store to a file::

            >>> from docp_docling import PDFParser

            # Convert
            >>> pdf = PDFParser(path='/path/to/file.pdf')
            >>> pdf.to_markdown(page_no=1,
                                image_mode='embedded',  # <-- Include images
                                to_file=True)

            # Render extracted text as HTML and preview in a browser.
            >>> pdf.preview()


        Parse a single page from a PDF into **Markdown** format,
        including images, and store to a file (manually)::

            >>> from docp_docling import PDFParser

            # Convert
            >>> pdf = PDFParser(path='/path/to/file.pdf')
            >>> pdf.to_markdown(page_no=1)

            # Render extracted text as HTML and preview in a browser.
            >>> pdf.preview()

            # Write the converted Markdown content to a file.
            >>> pdf.write(ext='.md')


        Parse a single page from a PDF into **HTML** format, including
        images::

            >>> from docp_docling import PDFParser

            # Convert
            >>> pdf = PDFParser(path='/path/to/file.pdf')
            >>> pdf.to_html(page_no=1,
                            image_mode='embedded')  # <-- Include images

            # Render extracted text and preview in a browser.
            >>> pdf.preview(raw=True)

    """

    _IMAGE_MODES = (ImageRefMode.EMBEDDED, ImageRefMode.PLACEHOLDER, ImageRefMode.REFERENCED)
    _SETTINGS = SETTINGS['docp-docling']

    def __init__(self, path: str, detailed_extraction: bool=False):
        """Docling-based PDF parser class."""
        super().__init__(path=path)
        self._conv = None       # Docling DocumentConverter object.
        self._document = None   # Docling results.document object.
        self._texts = []        # List of TextObjects
        self._tmpfiles = []     # A collection of temp files to be cleaned up.
        self._optmode = 'detail' if detailed_extraction else 'speed'
        self._create_converter()

    def __del__(self) -> None:
        """Actions to be performed on class destruction.

        - Remove all generated temp files.

        """
        # Corner case where the parent class does not have this attribute.
        if hasattr(self, '_tmpfiles'):  # nocover  # Unreachable in testing.
            for f in self._tmpfiles:
                os.unlink(f)

    @property
    def content(self) -> str:
        """Accessor to all content by merging all :attr:`texts`.

        Returns:
            str: Returns a continuous string of converted text by joining
            the :attr:`content` attribute for all elements of the
            :attr:`texts` property.

        """
        return ''.join(x.content for x in self._texts)

    @property
    def texts(self) -> list:
        """Accessor to parsed text as TextObject instances.

        For each text in the list, use the :attr:`.content` attribute to
        access the extracted text.

        """
        return self._texts

    def initialise(self) -> None:
        """Clean up the preview extraction activities and start over."""
        # pylint: disable=unnecessary-dunder-call
        self.__init__(path=self.doc.filepath)

    def to_html(self,
                *,
                page_no: int=None,
                image_mode: str='placeholder',
                include_annotations: bool=True,
                unique_lines: bool=False,
                to_file: bool=False,
                auto_open: bool=False,
                **kwargs) -> str | None:
        r"""Convert a PDF to HTML format.

        Args:
            page_no (int, optional): Page number to convert.
                Defaults to None (for all pages).
            image_mode (str, optional): The mode to use for including
                images in the markdown. Options are: 'embedded',
                'placeholder', 'referenced'. Defaults to 'placeholder'.
            include_annotations (bool, optional): Whether to include
                annotations in the export. Defaults to True.
            unique_lines (bool, optional): Remove any duplicated lines
                from the document's content. Generally used to remove
                repeated header and footer strings. Defaults to False.
            to_file (bool, optional): Write the converted text to a text
                file. Defaults to False.

                .. tip::
                    If you change your mind, call the :meth:`write`
                    method to store the converted text to a file.

            auto_open (bool, optional): On completion, display the
                converted text as rendered HTML in a web browser.
                Defaults to False.

                .. tip::
                    To view later, simply call the :meth:`preview`
                    method.

                    Ensure to pass ``raw=True`` to display the converted
                    HTML in the browser rather than converting HTML to
                    MD and back to HTML.

        :Keyword Arguments:
            All \*\*kwargs are passed directly into docling's
            :func:`export_to_html` function.

        Returns:
            str | None: If the file is written successfully, a string
            containing the full path to the output file is returned.
            Otherwise, None.

        """
        self._image_mode_override(image_mode=image_mode)
        path = None
        if self._convert():
            text = self._document.export_to_html(page_no=page_no,
                                                 image_mode=image_mode,
                                                 include_annotations=include_annotations,
                                                 **kwargs)
            if unique_lines:
                text = utilities.remove_duplicate_lines(text=text)
            self._texts.append(TextObject(content=text))
            self._add_document_objects()
            if to_file:
                path = self.write(ext='.html')
            if auto_open:  # nocover
                # Set offline to true to be more robust for offline environments.
                self.preview(raw=True, offline=True)
        return path

    def to_markdown(self,
                    *,
                    page_no: int=None,
                    image_mode: str='placeholder',
                    include_annotations: bool=True,
                    unique_lines: bool=False,
                    to_file: bool=False,
                    auto_open: bool=False,
                    **kwargs) -> str | None:
        r"""Convert a PDF to Markdown format.

        Args:
            page_no (int, optional): Page number to convert.
                Defaults to None (for all pages).
            image_mode (str, optional): The mode to use for including
                images in the markdown. Options are: 'embedded',
                'placeholder', 'referenced'. Defaults to 'placeholder'.
            include_annotations (bool, optional): Whether to include
                annotations in the export. Defaults to True.
            unique_lines (bool, optional): Remove any duplicated lines
                from the document's content. Generally used to remove
                repeated header and footer strings. Defaults to False.
            to_file (bool, optional): Write the converted text to a text
                file. Defaults to False.

                .. tip::
                    If you change your mind, call the :meth:`write`
                    method to store the converted text to a file.

            auto_open (bool, optional): On completion, display the
                converted text as rendered HTML in a web browser.
                Defaults to False.

                .. tip::
                    To view later, simply call the :meth:`preview`
                    method.

        :Keyword Arguments:
            All \*\*kwargs are passed directly into docling's
            :func:`export_to_html` function.

        Returns:
            str | None: If the file is written successfully, a string
            containing the full path to the output file is returned.
            Otherwise, None.

        """
        self._image_mode_override(image_mode=image_mode)
        path = None
        if self._convert():
            text = self._document.export_to_markdown(page_no=page_no,
                                                     image_mode=image_mode,
                                                     include_annotations=include_annotations,
                                                     **kwargs)
            if unique_lines:
                text = utilities.remove_duplicate_lines(text=text)
            self._texts.append(TextObject(content=text))
            self._add_document_objects()
            if to_file:
                path = self.write(ext='.md')
            if auto_open:  # nocover
                # Set offline to true to be more robust for offline environments.
                self.preview(offline=True)
        return path

    def preview(self, raw: bool=False, offline: bool=False, **kwargs) -> None:  # nocover
        """Preview the conversion as rendered text in a web browser.

        .. note::
            Each conversion (``TextObject``) is rendered to it own page
            in the web browser.

        Args:
            raw (bool, optional): If viewing a Markdown formatted file,
                preview the *raw* Markdown (i.e. do not render as HTML).
                Defaults to False.
            offline (bool, optional): If ``True``, this prevents
                ``ghmdlib`` from calling the GitHub Markdown conversion
                API, and performing the conversion internally.
                Defaults to False.

        :Keyword Arguments:
            These arguments are passed directly into the
            :func:`ghmdlib.ghmd.Converter.convert` method. Refer to that
            method's documentation for the accepted arguments.

        """
        for text in self.texts:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, delete_on_close=False) as f:
                # Register the temp filenames for deletion.
                self._tmpfiles.append(f.name)            # Original MD file to be converted.
                self._tmpfiles.append(f'{f.name}.html')  # HTML file created by ghmdlib.
                f.write(text.content)
            if raw:
                webbrowser.open(f.name)
            else:
                converter.convert(path=f.name,
                                  offline=offline,
                                  preview=True,
                                  **kwargs)

    def write(self, ext: str) -> str | None:
        """Write the extracted Markdown or HTML content to disk.

        Args:
            ext (str): File extension to be applied to the output file.
                For example: ``'.html'``

        Returns:
            str | None: If the file is written successfully, a string
            containing the full path to the output file is returned.
            Otherwise, None.

        """
        ext = f'.{ext}' if not ext.startswith('.') else ext
        base = utilities.build_project_outpath(subpath='conversions')
        fname = f'{os.path.splitext(self.doc.basename)[0]}{ext}'
        path = os.path.join(base, fname)
        c = 0
        if os.path.exists(path):
            os.unlink(path)
        for text in self.texts:
            with open(path, 'a', encoding='utf-8') as f:
                c += f.write(text.content)
        if c == sum(map(lambda x: len(x.content), self.texts)):
            print(f'File written successfully: {path}')
            return path
        return None  # nocover  # Should be unreachable.

    def _add_document_objects(self) -> None:
        """Create Document objects from the parsed text.

        :class:`Document` objects are used by the text splitter and data
        loaders to encapsulate a document's metadata and page content.

        The metadata extracted by ``pdfplumber`` is automatically added
        to the :class:`Document` object's metadata.

        """
        metadata = self.doc.metadata  # Metadata from pdfplumber
        metadata.update({'source': self.doc.basename, 'pageno': 0})
        for text in self._texts:
            doc = Document(page_content=text.content,
                           metadata=metadata)
            self._doc.documents.append(doc)

    def _convert(self) -> bool:
        """Convert the PDF file into docling objects for extraction.

        Returns:
            bool: True if the conversion was successful, otherwise False.

        """
        result = self._conv.convert(self._path)
        self._document = result.document
        return result.status == ConversionStatus.SUCCESS

    def _create_converter(self) -> None:
        """Setup the Docling document converter object."""
        pipeline_options = self._set_pipeline_options()
        self._conv = DocumentConverter(format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        })

    def _image_mode_override(self, image_mode: str) -> None:
        """Override the preset image generation options.

        Args:
            image_mode (str): Image mode selected by the user.

        If the ``image_mode`` is 'embedded', the converter is updated to
        allow image generation; which is False by default.

        Raises:
            ValueError: Raised if an invalid ``image_mode`` is received.

        """
        if image_mode not in self._IMAGE_MODES:
            msg = (f'Invalid image mode selected (\'{image_mode}\').\n'
                   f'Valid options: {', '.join(self._IMAGE_MODES)}')
            raise ValueError(msg)
        if image_mode == ImageRefMode.EMBEDDED:
            self._conv.format_to_options['pdf'].pipeline_options.generate_page_images = True
            self._conv.format_to_options['pdf'].pipeline_options.generate_picture_images = True

    def _set_pipeline_options(self) -> None:
        """Setup the Docling PDF pipeline options for file parsing.

        .. note::

            The majority of the options are defined in the following
            config file keys:

                - GPU_PIPELINE_OPTIONS
                - PIPELINE_OPTIONS

        Raises:
            FileNotFoundError: Raised if the path to the model does not
            exist.

        """
        # pylint: disable=line-too-long
        # pylint: disable=no-member      # multiprocessing.cpu_count
        model_path = SETTINGS['paths']['models']['docling']
        if not os.path.exists(model_path):
            msg = f'[ERROR]: The model path does not exist: {model_path}'
            raise FileNotFoundError(msg)
        opts = self._SETTINGS['options']['pipeline_options'].get(self._optmode)
        opts.update(self._SETTINGS['options']['gpu_pipeline_options'].get(AcceleratorDevice.CUDA
                                                                          if torch.cuda.is_available()
                                                                          else AcceleratorDevice.CPU))
        device = opts.pop('device')
        return PdfPipelineOptions(
            accelerator_options=AcceleratorOptions(device=device,
                                                   num_threads=os.cpu_count()),
            artifacts_path=model_path,
            enable_remote_services=False,       # Keep offline
            min_picture_page_surface_ratio=0,   # Process all images
            **opts,                             # Defined by config values
        )
