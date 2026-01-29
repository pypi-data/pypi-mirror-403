
.. _library-api:

=========================
Library API Documentation
=========================
The page contains simple library usage examples and the module-level
documentation for each of the importable modules in ``docp-parsers``.

.. contents::
    :local:
    :depth: 1


Use Cases
=========
To save digging through the documentation for each module and cobbling 
together what a 'standard use case' may look like, a couple have been
provided here.

Extract text from a PDF file
----------------------------

.. code-block:: python


    >>> from docp_parsers import PDFParser

    >>> pdf = PDFParser(path='/path/to/myfile.pdf')
    >>> pdf.extract_text()

    # Access the content of page 1.
    >>> pg1 = pdf.pages[1].content


Extracting text from a PowerPoint presentation
----------------------------------------------

.. code-block:: python

    >>> from docp_parsers import PPTXParser

    >>> pptx = PPTXParser(path='/path/to/myfile.pptx')
    >>> pptx.extract_text()

    # Access the text on slide 1.
    >>> pg1 = pptx.slides[1].content


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
   parsers_pptxparser

   objects_pdfobject
   objects_pptxobject
   parsers_putilities
   
   objects__docbaseobject
   objects__pageobject
   objects__slideobject
   parsers__pdfbaseparser
   parsers__pdftableparser
   parsers__pdftextparser
   parsers__pptxbaseparser
   parsers__pptxtextparser

|lastupdated|

