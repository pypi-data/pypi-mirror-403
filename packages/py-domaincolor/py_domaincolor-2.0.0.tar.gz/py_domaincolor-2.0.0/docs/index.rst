py-domaincolor Documentation
============================

**py-domaincolor** is a Python package for visualizing complex-valued functions
using domain coloring, where the color of each point represents the value of the
function at that point.

.. image:: https://img.shields.io/pypi/v/py-domaincolor.svg
   :target: https://pypi.org/project/py-domaincolor/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/py-domaincolor.svg
   :target: https://pypi.org/project/py-domaincolor/
   :alt: Python versions

Features
--------

- **Human-friendly parser** for mathematical expressions (e.g., ``z^2``, ``sin(z)/z``, ``e^z``)
- **Multiple visualization modes**: standard, phase-only, and modulus-only
- **Contour lines** for modulus and argument
- **Special functions** support: gamma, zeta, and more
- **High-resolution output** with customizable themes
- **CLI tool** for quick plotting from the command line

Quick Start
-----------

.. code-block:: python

   from py_domaincolor import plot

   # Generate a domain coloring plot
   plot("z^2")

.. code-block:: bash

   # Or use the command-line interface
   plot-complex "sin(z)/z" --range -5 5 --contours

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   getting_started
   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
