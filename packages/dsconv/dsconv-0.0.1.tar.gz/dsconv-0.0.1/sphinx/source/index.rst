.. dsconv documentation master file, created by
   sphinx-quickstart on Mon Feb 26 12:00:00 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. note Please be warned that this introduction file is shared between the
   Sphinx doc (Gitlab Pages) and the PyPI project description (pypi.org).
   Hence it should not contain internal API documentation references but rather online HTTP links.
   The reason is simple:
   pypi.org website makes no parsing of any syntax of the sphinx extensions.
   It understands only raw RST. We could make some pre-filtering to avoid any
   issue but until then just keep it simple (no internal API reference here).

Documentation
=============

``dsconv`` is a Python toolbox to ease and accelerate down-sampled convolutions using Numba.

.. admonition:: note
   :class: admonition note

   ``dsconv`` does not compute the complete convolution but only a sub-sample.
   It is particularly interesting for Discrete-Wavelet-Transform that is a signal processing tool that needs to compute two down-sampled convolutions of a signal.

Getting started with dsconv
---------------------------

**Quick install using PIP**
::

        pip install dsconv

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
