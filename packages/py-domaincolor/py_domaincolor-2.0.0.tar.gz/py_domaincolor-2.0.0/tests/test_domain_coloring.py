"""
Tests for the domain coloring visualization module.

This module wraps cplot for domain coloring. These tests verify our wrapper
functions work correctly.
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend
import matplotlib.pyplot as plt
import os
import tempfile

from py_domaincolor.domain_coloring import (
    domain_color_plot,
    create_colorwheel,
)
from py_domaincolor import get_callable


class TestDomainColorPlot:
    """Test the main domain_color_plot wrapper function."""

    def test_returns_figure_and_axes(self):
        """Should return (fig, ax) tuple."""
        fig, ax = domain_color_plot(
            lambda z: z**2,
            resolution=50,
            show=False
        )
        assert isinstance(fig, plt.Figure)
        assert isinstance(ax, plt.Axes)
        plt.close(fig)

    def test_save_to_file(self):
        """Should save image when path provided."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            fig, ax = domain_color_plot(
                lambda z: z**2,
                resolution=50,
                save_path=temp_path,
                show=False
            )
            plt.close(fig)
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_custom_ranges(self):
        """Should handle custom x and y ranges."""
        fig, ax = domain_color_plot(
            lambda z: z,
            x_range=(-5, 5),
            y_range=(-3, 3),
            resolution=50,
            show=False
        )
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        # cplot sets limits approximately based on the range (may have small margin)
        assert xlim[0] <= -4.5 and xlim[1] >= 4.5
        assert ylim[0] <= -2.5 and ylim[1] >= 2.5
        plt.close(fig)

    def test_with_title(self):
        """Should set title when provided."""
        fig, ax = domain_color_plot(
            lambda z: z**2,
            title="Test Title",
            resolution=50,
            show=False
        )
        assert ax.get_title() == "Test Title"
        plt.close(fig)

    def test_with_parsed_function(self):
        """Test plotting a function parsed from string."""
        f = get_callable("z^2 + 1")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_with_trig_function(self):
        """Test plotting a trigonometric function."""
        f = get_callable("sin(z)")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_ax_parameter_ignored(self):
        """Test that ax parameter is accepted but ignored (cplot limitation)."""
        # cplot.plot() doesn't support passing an existing axes,
        # so we accept the parameter for API compatibility but ignore it
        fig_original, ax_original = plt.subplots()
        result_fig, result_ax = domain_color_plot(
            lambda z: z**2,
            resolution=50,
            ax=ax_original,  # This will be ignored
            show=False
        )
        # Result should be a new figure/axes created by cplot
        assert isinstance(result_fig, plt.Figure)
        assert isinstance(result_ax, plt.Axes)
        plt.close(fig_original)
        plt.close(result_fig)


class TestCreateColorwheel:
    """Test color wheel creation."""

    def test_output_shape(self):
        """Should return square RGB array."""
        wheel = create_colorwheel(size=100)
        assert wheel.shape == (100, 100, 3)

    def test_output_range(self):
        """RGB values should be in [0, 1]."""
        wheel = create_colorwheel(size=100)
        assert np.all(wheel >= 0)
        assert np.all(wheel <= 1)

    def test_circular_mask(self):
        """Corners should be black (outside circle)."""
        wheel = create_colorwheel(size=100)
        # Check corner
        np.testing.assert_array_almost_equal(wheel[0, 0], [0, 0, 0])

    def test_center_not_black(self):
        """Center should have color."""
        wheel = create_colorwheel(size=100)
        center = wheel[50, 50]
        assert np.sum(center) > 0  # Not black


class TestIntegration:
    """Integration tests combining parser and plotting."""

    def test_plot_parsed_function(self):
        """Test plotting a function parsed from string."""
        f = get_callable("z^2 + 1")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        plt.close(fig)

    def test_plot_trig_function(self):
        """Test plotting a trigonometric function."""
        f = get_callable("sin(z)")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        plt.close(fig)

    def test_plot_rational_function(self):
        """Test plotting a rational function."""
        f = get_callable("(z-1)/(z+1)")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        plt.close(fig)

    def test_plot_exp_function(self):
        """Test plotting exponential function."""
        f = get_callable("e^z")
        fig, ax = domain_color_plot(
            f,
            resolution=50,
            show=False
        )
        plt.close(fig)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
