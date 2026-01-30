Getting Started
===============

Installation
------------

Install py-domaincolor using pip:

.. code-block:: bash

   pip install py-domaincolor

Or install from source with development dependencies:

.. code-block:: bash

   pip install -e ".[dev]"

Requirements
~~~~~~~~~~~~

- Python 3.8+
- NumPy >= 1.20.0
- Matplotlib >= 3.4.0
- SymPy >= 1.9
- mpmath >= 1.2.0

Basic Usage
-----------

Python API
~~~~~~~~~~

The simplest way to create a domain coloring plot:

.. code-block:: python

   from py_domaincolor import plot

   # Plot z squared
   plot("z^2")

   # Plot with custom range and contours
   plot("sin(z)/z", x_range=(-5, 5), mod_contours=True)

You can also parse expressions and get callable functions:

.. code-block:: python

   from py_domaincolor import parse, get_callable

   # Parse to SymPy expression
   expr = parse("z^2 + 1")
   print(expr)  # z**2 + 1

   # Get a callable function
   f = get_callable("sin(z)/z")
   result = f(1 + 1j)  # Evaluate at z = 1 + i

Command Line
~~~~~~~~~~~~

Use the ``plot-complex`` CLI tool:

.. code-block:: bash

   # Basic plot
   plot-complex "z^2"

   # With options
   plot-complex "sin(z)/z" --range -5 5 --contours -o output.png

   # Phase-only coloring
   plot-complex "z^3 - 1" --mode phase

Input Syntax
------------

The parser accepts human-friendly mathematical notation:

Variables and Constants
~~~~~~~~~~~~~~~~~~~~~~~

- ``z`` - The complex variable
- ``i`` or ``j`` - Imaginary unit
- ``e`` - Euler's number
- ``pi`` - Pi

Arithmetic
~~~~~~~~~~

- ``+``, ``-``, ``*``, ``/`` - Basic operations
- ``^`` or ``**`` - Exponentiation
- Implicit multiplication: ``2z`` becomes ``2*z``, ``(z+1)(z-1)`` becomes ``(z+1)*(z-1)``

Functions
~~~~~~~~~

Trigonometric:
   ``sin(z)``, ``cos(z)``, ``tan(z)``, ``asin(z)``, ``acos(z)``, ``atan(z)``

Hyperbolic:
   ``sinh(z)``, ``cosh(z)``, ``tanh(z)``, ``asinh(z)``, ``acosh(z)``, ``atanh(z)``

Exponential/Logarithmic:
   ``exp(z)``, ``e^z``, ``log(z)``, ``ln(z)``, ``sqrt(z)``

Complex Operations:
   ``|z|`` or ``abs(z)`` - Absolute value
   ``conjugate(z)`` or ``z*`` - Complex conjugate
   ``re(z)``, ``im(z)`` - Real and imaginary parts
   ``arg(z)`` - Argument (phase)

Special Functions:
   ``gamma(z)`` - Gamma function
   ``zeta(z)`` - Riemann zeta function

Understanding Domain Coloring
-----------------------------

Domain coloring visualizes complex functions by mapping:

**Hue** represents the argument (phase) of f(z):
   - Red = 0 (positive real axis)
   - Cyan = pi (negative real axis)
   - Full rainbow = full rotation around the origin

**Brightness** represents the modulus (magnitude):
   - Dark = small |f(z)|
   - Light = large |f(z)|
   - Uses logarithmic scaling for wide dynamic range

Coloring Modes
~~~~~~~~~~~~~~

``standard`` (default):
   Both hue (from argument) and brightness (from modulus)

``phase``:
   Only hue from argument, constant brightness

``modulus``:
   Grayscale based on modulus only

Reading the Plots
~~~~~~~~~~~~~~~~~

- **Zeros**: Points where all colors meet (like wheel spokes)
- **Poles**: Points surrounded by all colors, brightness increasing outward
- **Branch cuts**: Lines where colors jump discontinuously

Examples
--------

Polynomial with Roots
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from py_domaincolor import plot

   # z^3 - 1 has three roots at the cube roots of unity
   plot("z^3 - 1", x_range=(-2, 2), mod_contours=True)

Rational Function
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Mobius transformation
   plot("(z - 1)/(z + 1)", x_range=(-3, 3))

Special Functions
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Gamma function (slower due to mpmath)
   plot("gamma(z)", x_range=(-5, 5), resolution=400)

   # Riemann zeta function
   plot("zeta(z)", x_range=(-5, 5), resolution=400)
