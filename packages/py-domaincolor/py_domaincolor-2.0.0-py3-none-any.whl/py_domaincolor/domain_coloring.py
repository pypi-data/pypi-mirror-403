"""
Domain coloring visualization wrapper around cplot.

This module provides a thin wrapper around the cplot library for domain coloring
visualization. It exposes a simplified interface that accepts expression strings
and common options, delegating the actual rendering to cplot.

cplot reference:
    cplot.plot(f, (x_min, x_max, n_x), (y_min, y_max, n_y), **kwargs)

Note: cplot.plot() does not accept an 'ax' parameter - it creates its own figure.
This wrapper handles figure management appropriately.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb
from typing import Callable, Tuple, Optional

try:
    import cplot
    CPLOT_AVAILABLE = True
except ImportError:
    CPLOT_AVAILABLE = False


def domain_color_plot(
    f: Callable,
    x_range: Tuple[float, float] = (-2, 2),
    y_range: Tuple[float, float] = (-2, 2),
    resolution: int = 400,
    title: Optional[str] = None,
    figsize: Tuple[int, int] = (10, 10),
    save_path: Optional[str] = None,
    show: bool = False,
    ax: Optional[plt.Axes] = None,
    abs_scaling: Optional[Callable] = None,
    add_colorbars: bool = False,
    add_axes_labels: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create a domain coloring plot for a complex function using cplot.

    This is a convenience wrapper around cplot.plot() that provides a simpler
    interface with sensible defaults.

    Args:
        f: Complex function f(z) - must accept numpy arrays
        x_range: (min, max) for real axis
        y_range: (min, max) for imaginary axis
        resolution: Grid resolution (number of points along each axis)
        title: Plot title
        figsize: Figure size
        save_path: Path to save image (if provided)
        show: Whether to display the plot (default False)
        ax: Ignored for compatibility - cplot creates its own figure
        abs_scaling: Function to scale the absolute value for brightness.
                     Common options from cplot:
                     - lambda x: x / (1 + x)  (default-like behavior)
                     - lambda x: np.arctan(x) / (np.pi/2)  (compress large values)
                     - lambda x: np.log(x + 1)  (logarithmic)
        add_colorbars: Whether to add colorbars (default False)
        add_axes_labels: Whether to add axis labels (default True)

    Returns:
        (fig, ax) tuple
    """
    if not CPLOT_AVAILABLE:
        raise ImportError(
            "cplot is required for domain coloring. "
            "Install it with: pip install cplot"
        )

    # Build cplot arguments
    # cplot.plot expects (min, max, n) tuples for ranges
    x_spec = (x_range[0], x_range[1], resolution)
    y_spec = (y_range[0], y_range[1], resolution)

    # Build kwargs for cplot
    cplot_kwargs = {
        "add_colorbars": add_colorbars,
        "add_axes_labels": add_axes_labels,
    }
    if abs_scaling is not None:
        cplot_kwargs["abs_scaling"] = abs_scaling

    # cplot.plot() returns a matplotlib figure
    # It creates its own figure internally
    plt.figure(figsize=figsize)
    cplot.plot(f, x_spec, y_spec, **cplot_kwargs)

    # Get the current figure and axes that cplot created
    fig = plt.gcf()
    ax = plt.gca()

    # Add title if provided
    if title:
        ax.set_title(title, fontsize=14)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')

    if show:
        plt.show()

    return fig, ax


def create_colorwheel(size: int = 200) -> np.ndarray:
    """
    Create a color wheel showing the phase-to-color mapping.

    This is useful for legends showing how argument maps to hue.

    Args:
        size: Size of the output array (size x size pixels)

    Returns:
        RGB array for the color wheel
    """
    x = np.linspace(-1, 1, size)
    y = np.linspace(-1, 1, size)
    X, Y = np.meshgrid(x, y)
    Z = X + 1j * Y

    # Mask to create circular wheel
    mask = np.abs(Z) <= 1

    # Create HSV values
    # Map argument from [-pi, pi] to [0, 1] for hue
    hue = (np.angle(Z) + np.pi) / (2 * np.pi)
    saturation = np.ones_like(hue) * 0.9
    value = np.where(mask, 0.9, 0)

    hsv = np.stack([hue, saturation, value], axis=-1)
    rgb = hsv_to_rgb(hsv)

    return rgb


# For backward compatibility, expose a simpler interface
def plot_function(
    f: Callable,
    xlim: Tuple[float, float] = (-2, 2),
    ylim: Tuple[float, float] = (-2, 2),
    n: int = 400,
    **kwargs
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Simplified interface for plotting a complex function.

    Args:
        f: Complex function
        xlim: Real axis limits
        ylim: Imaginary axis limits
        n: Resolution
        **kwargs: Additional arguments passed to domain_color_plot

    Returns:
        (fig, ax) tuple
    """
    return domain_color_plot(
        f,
        x_range=xlim,
        y_range=ylim,
        resolution=n,
        **kwargs
    )
