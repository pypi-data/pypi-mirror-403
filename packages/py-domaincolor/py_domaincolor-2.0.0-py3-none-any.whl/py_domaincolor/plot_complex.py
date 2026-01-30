#!/usr/bin/env python3
"""
Domain coloring plotter for complex functions.

A convenience wrapper combining complex-expr-parser for expression parsing
and cplot for visualization.

Usage:
    plot-complex "z^2"
    plot-complex "sin(z)/z" --range -5 5
    plot-complex "gamma(z)" --resolution 1000

Supports human-friendly input:
    - z^2, z**2                    Powers
    - sin(z), cos(z), tan(z)       Trig functions
    - sinh(z), cosh(z), tanh(z)    Hyperbolic functions
    - exp(z), e^z                  Exponential
    - log(z), ln(z)                Logarithm
    - sqrt(z)                      Square root
    - |z|, abs(z)                  Absolute value
    - z*, conjugate(z)             Conjugate
    - re(z), im(z)                 Real/imaginary parts
    - gamma(z), zeta(z)            Special functions
    - i, j                         Imaginary unit
    - e, pi                        Constants
"""

import argparse
import sys
import os
import tempfile

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb

# Use complex-expr-parser for parsing
from complex_expr_parser import get_callable, parse_complex_function

# Use our cplot wrapper
from .domain_coloring import domain_color_plot, create_colorwheel


def add_colorbar_legend(ax: plt.Axes, fig: plt.Figure):
    """Add a small color wheel legend showing phase mapping."""
    # Create inset axes for color wheel
    inset_ax = fig.add_axes([0.85, 0.02, 0.12, 0.12])

    # Create color wheel
    wheel = create_colorwheel(100)
    inset_ax.imshow(wheel, extent=[-1, 1, -1, 1], origin='lower')
    inset_ax.set_xlim(-1.2, 1.2)
    inset_ax.set_ylim(-1.2, 1.2)
    inset_ax.axis('off')

    # Add labels
    inset_ax.text(0, -1.35, '+/-pi', ha='center', va='top', fontsize=8, color='white')
    inset_ax.text(1.1, 0, '0', ha='left', va='center', fontsize=8, color='white')
    inset_ax.text(0, 1.15, 'pi/2', ha='center', va='bottom', fontsize=8, color='white')


def plot_complex_function(
    expression: str,
    x_range: tuple = (-2, 2),
    y_range: tuple = None,
    resolution: int = 400,
    output_path: str = None,
    show_legend: bool = True,
    dark_theme: bool = True
) -> str:
    """
    Parse and plot a complex function using domain coloring.

    This function:
    1. Parses the expression string using complex-expr-parser
    2. Renders the domain coloring plot using cplot (via our wrapper)
    3. Saves and returns the output path

    Args:
        expression: Human-friendly function string (e.g., "z^2", "sin(z)/z")
        x_range: (min, max) for real axis
        y_range: (min, max) for imaginary axis (defaults to match x_range)
        resolution: Grid resolution
        output_path: Where to save the image
        show_legend: Include color wheel legend
        dark_theme: Use dark background

    Returns:
        Path to saved image
    """
    if y_range is None:
        y_range = x_range

    # Parse the expression using complex-expr-parser
    try:
        sympy_expr = parse_complex_function(expression)
        f = get_callable(expression, use_numpy=True)
    except Exception as e:
        raise ValueError(f"Failed to parse '{expression}': {e}")

    # Set up the figure with dark theme
    if dark_theme:
        plt.style.use('dark_background')
    else:
        plt.style.use('default')

    fig, ax = plt.subplots(figsize=(10, 10))

    # Use cplot for the domain coloring
    try:
        domain_color_plot(
            f,
            x_range=x_range,
            y_range=y_range,
            resolution=resolution,
            title=f'f(z) = {sympy_expr}',
            ax=ax,
            show=False,
        )
    except ImportError:
        # Fallback: if cplot not available, create a basic visualization
        _fallback_plot(f, x_range, y_range, resolution, ax)
        ax.set_title(f'f(z) = {sympy_expr}', fontsize=14)
        ax.set_xlabel('Re(z)', fontsize=12)
        ax.set_ylabel('Im(z)', fontsize=12)

    # Add subtle grid lines at origin
    ax.axhline(y=0, color='white', linewidth=0.5, alpha=0.3)
    ax.axvline(x=0, color='white', linewidth=0.5, alpha=0.3)

    # Add color wheel legend
    if show_legend:
        add_colorbar_legend(ax, fig)

    # Generate output path if not provided
    if output_path is None:
        # Create a safe filename from the expression
        safe_name = expression.replace('/', '_div_').replace('*', '_mul_')
        safe_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in safe_name)
        safe_name = safe_name[:50]  # Limit length
        output_path = os.path.join(tempfile.gettempdir(), f'{safe_name}.png')

    plt.savefig(output_path, dpi=150, bbox_inches='tight',
                facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)

    return output_path


def _fallback_plot(f, x_range, y_range, resolution, ax):
    """
    Fallback domain coloring when cplot is not available.
    Creates a basic HSV-based visualization.
    """
    x = np.linspace(x_range[0], x_range[1], resolution)
    y = np.linspace(y_range[0], y_range[1], resolution)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    with np.errstate(all='ignore'):
        W = f(Z)

    # Convert to RGB using basic domain coloring
    arg_w = np.angle(W)
    mod_w = np.abs(W)

    # Hue from argument
    hue = (arg_w + np.pi) / (2 * np.pi)

    # Saturation constant
    saturation = np.ones_like(hue) * 0.8

    # Value from modulus (logarithmic scaling)
    with np.warnings.catch_warnings():
        np.warnings.simplefilter("ignore")
        log_mod = np.log(mod_w + 1e-10)
        value = 0.5 + np.arctan(log_mod) / np.pi

    # Handle NaN values
    nan_mask = ~np.isfinite(W)
    hue[nan_mask] = 0
    saturation[nan_mask] = 0
    value[nan_mask] = 0

    value = np.clip(value, 0, 1)

    hsv = np.stack([hue, saturation, value], axis=-1)
    rgb = hsv_to_rgb(hsv)

    ax.imshow(rgb, extent=[x_range[0], x_range[1], y_range[0], y_range[1]],
              origin='lower', aspect='equal')


def main():
    """Main entry point for the plot-complex CLI."""
    parser = argparse.ArgumentParser(
        description='Domain coloring plots for complex functions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument('function', type=str,
                        help='Complex function to plot (e.g., "z^2", "sin(z)/z")')

    parser.add_argument('--range', '-r', type=float, nargs=2, default=[-2, 2],
                        metavar=('MIN', 'MAX'),
                        help='Range for both axes (default: -2 2)')

    parser.add_argument('--xrange', type=float, nargs=2, default=None,
                        metavar=('MIN', 'MAX'),
                        help='Range for real axis (overrides --range)')

    parser.add_argument('--yrange', type=float, nargs=2, default=None,
                        metavar=('MIN', 'MAX'),
                        help='Range for imaginary axis (overrides --range)')

    parser.add_argument('--resolution', '-n', type=int, default=400,
                        help='Grid resolution (default: 400)')

    parser.add_argument('--output', '-o', type=str, default=None,
                        help='Output file path (default: auto-generated)')

    parser.add_argument('--no-legend', action='store_true',
                        help='Hide color wheel legend')

    parser.add_argument('--light', action='store_true',
                        help='Use light theme instead of dark')

    # Keep these for backward compatibility, but they're handled by cplot now
    parser.add_argument('--mode', '-m', choices=['standard', 'phase', 'modulus'],
                        default='standard',
                        help='Coloring mode (note: simplified in v2, uses cplot defaults)')

    parser.add_argument('--contours', '-c', action='store_true',
                        help='Show modulus contour lines (note: handled by cplot)')

    parser.add_argument('--arg-contours', '-a', action='store_true',
                        help='Show argument contour lines (note: handled by cplot)')

    args = parser.parse_args()

    # Determine ranges
    x_range = tuple(args.xrange) if args.xrange else tuple(args.range)
    y_range = tuple(args.yrange) if args.yrange else tuple(args.range)

    try:
        output_path = plot_complex_function(
            expression=args.function,
            x_range=x_range,
            y_range=y_range,
            resolution=args.resolution,
            output_path=args.output,
            show_legend=not args.no_legend,
            dark_theme=not args.light
        )
        print(f"Saved: {output_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
