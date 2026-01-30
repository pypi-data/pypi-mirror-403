# py-domaincolor

Domain coloring visualization for complex-valued functions. A convenience wrapper that combines:

- **[complex-expr-parser](https://pypi.org/project/complex-expr-parser/)**: Parses human-friendly mathematical notation like `z^2`, `sin(z)/z`, `e^z`
- **[cplot](https://pypi.org/project/cplot/)**: Renders beautiful domain coloring visualizations

This package provides a simple, unified API for creating domain coloring plots from expression strings.

## Installation

```bash
pip install py-domaincolor
```

This will automatically install the required dependencies (`complex-expr-parser`, `cplot`, `numpy`, `matplotlib`).

## Quick Start

**Command line:**
```bash
plot-complex "z^2"
plot-complex "sin(z)/z" --range -10 10
plot-complex "(z-1)/(z+1)" --resolution 800
```

**Python API:**
```python
from py_domaincolor import plot, parse, get_callable

# Generate a plot - simplest usage
plot("e^z", x_range=(-4, 4))

# Parse to sympy expression (uses complex-expr-parser)
expr = parse("sin(z)/z")  # Returns: sin(z)/z

# Get a callable function (uses complex-expr-parser)
f = get_callable("z^2 + 1")
f(1+1j)  # Returns: (1+2j)
```

---

## Architecture

py-domaincolor v2.0 is a thin convenience wrapper:

```
py-domaincolor
    |
    +-- complex-expr-parser  (expression parsing: "z^2" -> callable function)
    |
    +-- cplot                (domain coloring visualization)
```

The package provides:
1. Re-exports of parser functions from `complex-expr-parser`
2. A thin wrapper around `cplot.plot()` for domain coloring
3. A unified `plot()` function that parses expressions and renders them
4. A CLI tool for quick visualization

---

## Input Syntax Reference

The parser (via complex-expr-parser) accepts human-friendly mathematical notation.

### Variables

| Input | Description |
|-------|-------------|
| `z` | The complex variable |

### Arithmetic Operations

| Input | Description | Example |
|-------|-------------|---------|
| `+` | Addition | `z + 1` |
| `-` | Subtraction | `z - 1` |
| `*` | Multiplication | `z * 2` |
| `/` | Division | `1/z`, `(z-1)/(z+1)` |
| `^` or `**` | Exponentiation | `z^2`, `z**3` |

### Implicit Multiplication

| Input | Interpreted As |
|-------|----------------|
| `2z` | `2*z` |
| `3z + 2` | `3*z + 2` |
| `z(z+1)` | `z*(z+1)` |
| `(z+1)(z-1)` | `(z+1)*(z-1)` |

### Constants

| Input | Value | Description |
|-------|-------|-------------|
| `i` or `j` | sqrt(-1) | Imaginary unit |
| `e` | 2.718... | Euler's number |
| `pi` | 3.14159... | Pi |

### Functions

| Category | Functions |
|----------|-----------|
| Trigonometric | `sin(z)`, `cos(z)`, `tan(z)`, `asin(z)`, `acos(z)`, `atan(z)` |
| Hyperbolic | `sinh(z)`, `cosh(z)`, `tanh(z)`, `asinh(z)`, `acosh(z)`, `atanh(z)` |
| Exponential/Log | `exp(z)`, `e^z`, `log(z)`, `ln(z)`, `sqrt(z)` |
| Complex | `abs(z)`, `\|z\|`, `conjugate(z)`, `re(z)`, `im(z)`, `arg(z)` |
| Special | `gamma(z)`, `zeta(z)` |

---

## CLI Reference

```
usage: plot-complex [-h] [--range MIN MAX] [--xrange MIN MAX]
                    [--yrange MIN MAX] [--resolution N]
                    [--output PATH] [--no-legend] [--light]
                    function

positional arguments:
  function              Complex function to plot (e.g., "z^2", "sin(z)/z")

optional arguments:
  -h, --help            Show help message
  --range, -r MIN MAX   Range for both axes (default: -2 2)
  --xrange MIN MAX      Range for real axis (overrides --range)
  --yrange MIN MAX      Range for imaginary axis (overrides --range)
  --resolution, -n N    Grid resolution (default: 400)
  --output, -o PATH     Output file path
  --no-legend           Hide color wheel legend
  --light               Use light theme instead of dark
```

### Examples

```bash
# Basic polynomial
plot-complex "z^3 - 1"

# Rational function
plot-complex "(z-1)/(z+1)" --range -3 3

# Trigonometric function over wide range
plot-complex "sin(z)/z" --range -10 10

# High-resolution output
plot-complex "exp(1/z)" --resolution 800 -o output.png
```

---

## Python API Reference

### `plot(expression, **kwargs)`

Generate and save a domain coloring plot.

```python
from py_domaincolor import plot

plot("z^2",
     x_range=(-2, 2),      # Real axis range
     y_range=(-2, 2),      # Imaginary axis range (default: same as x_range)
     resolution=400,        # Grid resolution
     output_path=None,      # Output file (auto-generated if None)
     show_legend=True,      # Include color wheel
     dark_theme=True)       # Dark background
```

### `parse(expression)`

Parse a string into a sympy expression (via complex-expr-parser).

```python
from py_domaincolor import parse

expr = parse("z^2 + 2z + 1")
print(expr)  # z**2 + 2*z + 1
```

### `get_callable(expression, use_numpy=True)`

Get a callable function from a string expression (via complex-expr-parser).

```python
from py_domaincolor import get_callable
import numpy as np

f = get_callable("sin(z)/z")

# Scalar evaluation
f(1+1j)  # Returns complex number

# Array evaluation (vectorized with numpy)
z = np.linspace(-2, 2, 100) + 1j * np.linspace(-2, 2, 100)[:, None]
w = f(z)  # Returns array of complex numbers
```

### `domain_color_plot(f, **kwargs)`

Lower-level function that wraps cplot.plot(). Accepts a callable function.

```python
from py_domaincolor import domain_color_plot, get_callable

f = get_callable("z^2")
fig, ax = domain_color_plot(f, x_range=(-2, 2), resolution=400, show=False)
```

---

## Understanding Domain Coloring

Domain coloring visualizes complex functions by mapping:

- **Hue** -> Argument (phase) of f(z)
  - Red = 0 (positive real)
  - Cyan = pi (negative real)
  - Full rainbow = full rotation around origin

- **Brightness** -> Modulus (magnitude) of f(z)
  - Dark = small |f(z)|
  - Light = large |f(z)|

### Reading the Plots

- **Zeros**: Points where all colors meet (like spokes of a wheel)
- **Poles**: Points surrounded by all colors with brightness increasing outward
- **Branch cuts**: Lines where colors jump discontinuously

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Dependencies

- **complex-expr-parser**: Expression parsing
- **cplot**: Domain coloring visualization
- **numpy**: Numerical arrays
- **matplotlib**: Plotting backend

## Upgrading from v1.x

In v2.0, the package was refactored as a thin wrapper:

- Expression parsing is now handled by `complex-expr-parser`
- Visualization is now handled by `cplot`
- The public API (`plot()`, `parse()`, `get_callable()`) remains the same
- Some advanced options (like `mode`, `mod_contours`) are now handled by cplot

If you need the old standalone implementation, use v1.x.

## License

MIT License
