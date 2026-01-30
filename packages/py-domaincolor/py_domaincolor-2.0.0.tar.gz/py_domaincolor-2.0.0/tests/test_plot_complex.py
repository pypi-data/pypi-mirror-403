"""
Tests for the high-level plot_complex module and CLI.

This tests the main plot() function that combines complex-expr-parser
and cplot for a simple end-to-end experience.
"""

import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import tempfile
import subprocess
import sys

from py_domaincolor.plot_complex import plot_complex_function
from py_domaincolor import plot


class TestPlotComplexFunction:
    """Test the main plot_complex_function."""

    def test_basic_plot(self):
        """Test basic plotting functionality."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot_complex_function(
                "z^2",
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_trig_function(self):
        """Test plotting trigonometric function."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot_complex_function(
                "sin(z)/z",
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_custom_range(self):
        """Test with custom axis range."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot_complex_function(
                "z^2",
                x_range=(-5, 5),
                y_range=(-3, 3),
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_no_legend(self):
        """Test with legend disabled."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot_complex_function(
                "z^2",
                show_legend=False,
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_light_theme(self):
        """Test with light theme."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot_complex_function(
                "z^2",
                dark_theme=False,
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_invalid_expression_raises(self):
        """Test that invalid expression raises ValueError."""
        with pytest.raises(ValueError):
            plot_complex_function(
                "z +* invalid",
                resolution=50
            )


class TestPlotAlias:
    """Test the plot() function alias."""

    def test_plot_alias(self):
        """Test that plot() works as alias."""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot(
                "z^2",
                output_path=temp_path,
                resolution=50
            )
            assert os.path.exists(result_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestExpressionVariety:
    """Test plotting various types of expressions."""

    def setup_method(self):
        self.temp_files = []

    def teardown_method(self):
        for f in self.temp_files:
            if os.path.exists(f):
                os.unlink(f)

    def _temp_path(self):
        f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        path = f.name
        f.close()
        self.temp_files.append(path)
        return path

    def test_polynomial(self):
        path = self._temp_path()
        plot_complex_function("z^3 - 1", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_rational(self):
        path = self._temp_path()
        plot_complex_function("(z-1)/(z+1)", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_exponential(self):
        path = self._temp_path()
        plot_complex_function("e^z", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_trig(self):
        path = self._temp_path()
        plot_complex_function("sin(z)", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_hyperbolic(self):
        path = self._temp_path()
        plot_complex_function("sinh(z)", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_logarithm(self):
        path = self._temp_path()
        plot_complex_function("log(z)", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_sqrt(self):
        path = self._temp_path()
        plot_complex_function("sqrt(z)", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_inverse(self):
        path = self._temp_path()
        plot_complex_function("1/z", output_path=path, resolution=50)
        assert os.path.exists(path)

    def test_combined(self):
        path = self._temp_path()
        plot_complex_function("sin(z)/z + cos(z)", output_path=path, resolution=50)
        assert os.path.exists(path)


class TestCLI:
    """Test command-line interface."""

    def setup_method(self):
        self.temp_files = []

    def teardown_method(self):
        for f in self.temp_files:
            if os.path.exists(f):
                os.unlink(f)

    def _temp_path(self):
        f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        path = f.name
        f.close()
        self.temp_files.append(path)
        return path

    def test_cli_basic(self):
        """Test basic CLI invocation."""
        output_path = self._temp_path()
        result = subprocess.run(
            [sys.executable, "-m", "py_domaincolor.plot_complex", "z^2", "-o", output_path, "-n", "50"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert os.path.exists(output_path)

    def test_cli_with_range(self):
        """Test CLI with custom range."""
        output_path = self._temp_path()
        result = subprocess.run(
            [sys.executable, "-m", "py_domaincolor.plot_complex", "z^2", "--range", "-5", "5",
             "-o", output_path, "-n", "50"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_trig_function(self):
        """Test CLI with trig function."""
        output_path = self._temp_path()
        result = subprocess.run(
            [sys.executable, "-m", "py_domaincolor.plot_complex", "sin(z)/z",
             "-o", output_path, "-n", "50"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0

    def test_cli_invalid_expression(self):
        """Test CLI with invalid expression returns error."""
        result = subprocess.run(
            [sys.executable, "-m", "py_domaincolor.plot_complex", "z +* invalid"],
            capture_output=True,
            text=True
        )
        assert result.returncode != 0
        assert "Error" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
