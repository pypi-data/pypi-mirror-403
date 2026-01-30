API Reference
=============

This section provides detailed API documentation for py-domaincolor.

High-Level Functions
--------------------

These are the main entry points for most users.

plot
~~~~

.. autofunction:: py_domaincolor.plot_complex.plot_complex_function

parse
~~~~~

.. autofunction:: py_domaincolor.complex_parser.parse_complex_function

get_callable
~~~~~~~~~~~~

.. autofunction:: py_domaincolor.complex_parser.get_callable

validate_expression
~~~~~~~~~~~~~~~~~~~

.. autofunction:: py_domaincolor.complex_parser.validate_expression

Parser Module
-------------

.. automodule:: py_domaincolor.complex_parser
   :members:
   :undoc-members:
   :show-inheritance:

ComplexFunctionParser
~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: py_domaincolor.complex_parser.ComplexFunctionParser
   :members:
   :undoc-members:
   :show-inheritance:

Domain Coloring Module
----------------------

.. automodule:: py_domaincolor.domain_coloring
   :members:
   :undoc-members:
   :show-inheritance:

Core Functions
~~~~~~~~~~~~~~

.. autofunction:: py_domaincolor.domain_coloring.domain_color_plot

.. autofunction:: py_domaincolor.domain_coloring.complex_to_rgb

.. autofunction:: py_domaincolor.domain_coloring.create_domain_grid

.. autofunction:: py_domaincolor.domain_coloring.create_colorwheel

Helper Functions
~~~~~~~~~~~~~~~~

.. autofunction:: py_domaincolor.domain_coloring.arg_to_hue

.. autofunction:: py_domaincolor.domain_coloring.modulus_to_lightness

.. autofunction:: py_domaincolor.domain_coloring.arg_contours

Plot Complex Module
-------------------

.. automodule:: py_domaincolor.plot_complex
   :members:
   :undoc-members:
   :show-inheritance:

Symbols
-------

z
~

The complex variable symbol used in expressions:

.. code-block:: python

   from py_domaincolor import z
   from sympy import sin

   # Use z directly in SymPy expressions
   expr = sin(z) / z
