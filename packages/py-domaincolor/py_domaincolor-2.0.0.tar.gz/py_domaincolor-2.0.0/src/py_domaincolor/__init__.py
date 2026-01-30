"""
py_domaincolor - Domain coloring visualization for complex functions.

A convenience wrapper that combines:
- complex-expr-parser: For parsing human-friendly mathematical expressions
- cplot: For domain coloring visualization

Quick start:
    >>> from py_domaincolor import plot
    >>> plot("z^2")  # Plots z squared and saves to file

    >>> from py_domaincolor import parse, get_callable
    >>> expr = parse("sin(z)/z")  # Parse to sympy expression
    >>> f = get_callable("e^z")    # Get callable function

Features:
    - Fault-tolerant parser for human-friendly input (via complex-expr-parser)
    - Domain coloring visualization (via cplot)
    - Simple unified API

Input syntax supported:
    - Powers: z^2, z**2
    - Trig: sin(z), cos(z), tan(z), sinh(z), cosh(z), tanh(z)
    - Inverse trig: asin(z), arcsin(z), etc.
    - Exponential/log: exp(z), e^z, log(z), ln(z)
    - Roots: sqrt(z)
    - Absolute value: |z|, abs(z)
    - Conjugate: z*, conjugate(z)
    - Real/imag parts: re(z), im(z), Re(z), Im(z)
    - Special: gamma(z), zeta(z)
    - Constants: i, j, e, pi
    - Implicit multiplication: 2z, z(z+1), (z+1)(z-1)
"""

# Re-export parser functions from complex-expr-parser
from complex_expr_parser import (
    ComplexFunctionParser,
    parse_complex_function as parse,
    get_callable,
    validate_expression,
    z,  # The sympy symbol for z
)

# Import our thin wrapper around cplot
from .domain_coloring import (
    domain_color_plot,
    create_colorwheel,
)

# Import the main plotting function
from .plot_complex import plot_complex_function as plot


__version__ = "2.0.0"
__all__ = [
    # Parser (from complex-expr-parser)
    'ComplexFunctionParser',
    'parse',
    'get_callable',
    'validate_expression',
    'z',

    # Visualization
    'plot',
    'domain_color_plot',
    'create_colorwheel',
]
