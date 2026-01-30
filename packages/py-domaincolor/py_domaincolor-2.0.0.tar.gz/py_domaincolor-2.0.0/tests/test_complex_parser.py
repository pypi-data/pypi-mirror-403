"""
Tests for the complex function parser (delegated to complex-expr-parser).

These tests verify that the re-exported parser functions from complex-expr-parser
work correctly through our package's interface.
"""

import pytest
import numpy as np

# Import from our package (which re-exports from complex-expr-parser)
from py_domaincolor import parse, get_callable, validate_expression, z


class TestParserReexports:
    """Test that parser functions are correctly re-exported."""

    def test_parse_basic(self):
        """Test basic parsing."""
        expr = parse("z^2")
        assert "z**2" in str(expr) or str(expr) == "z**2"

    def test_parse_complex_expression(self):
        """Test parsing a more complex expression."""
        expr = parse("sin(z)/z")
        assert "sin" in str(expr)
        assert "z" in str(expr)

    def test_get_callable_basic(self):
        """Test getting a callable function."""
        f = get_callable("z^2")
        result = f(2 + 0j)
        assert result == pytest.approx(4 + 0j)

    def test_get_callable_complex_input(self):
        """Test callable with complex input."""
        f = get_callable("z^2")
        # (1+i)^2 = 1 + 2i - 1 = 2i
        result = f(1 + 1j)
        assert result == pytest.approx(2j)

    def test_validate_expression_valid(self):
        """Test validation of valid expressions."""
        is_valid, error = validate_expression("z^2 + 1")
        assert is_valid is True
        assert error is None

    def test_validate_expression_invalid(self):
        """Test validation of invalid expressions."""
        is_valid, error = validate_expression("z +* invalid")
        assert is_valid is False
        assert error is not None

    def test_z_symbol_exported(self):
        """Test that z symbol is exported."""
        assert z is not None
        assert str(z) == "z"


class TestFunctionEvaluation:
    """Test function evaluation through our interface."""

    def test_trig_function(self):
        """Test trigonometric function."""
        f = get_callable("sin(z)")
        result = f(1 + 1j)
        expected = np.sin(1 + 1j)
        assert result == pytest.approx(expected)

    def test_exponential(self):
        """Test exponential function."""
        f = get_callable("exp(z)")
        result = f(1 + 1j)
        expected = np.exp(1 + 1j)
        assert result == pytest.approx(expected)

    def test_power_notation(self):
        """Test e^z notation."""
        f = get_callable("e^z")
        result = f(1 + 0j)
        expected = np.exp(1)
        assert result == pytest.approx(expected)

    def test_implicit_multiplication(self):
        """Test implicit multiplication."""
        f = get_callable("2z + 3")
        result = f(1 + 1j)
        expected = 2 * (1 + 1j) + 3
        assert result == pytest.approx(expected)

    def test_polynomial(self):
        """Test polynomial evaluation."""
        f = get_callable("z^2 + 2z + 1")
        result = f(2 + 1j)
        # (2+i)^2 + 2(2+i) + 1 = (3+4i) + (4+2i) + 1 = 8+6i
        assert result == pytest.approx(8 + 6j)


class TestArrayEvaluation:
    """Test that functions work with numpy arrays."""

    def test_array_input(self):
        f = get_callable("z^2")
        z_arr = np.array([1+0j, 1+1j, 0+1j, -1+0j])
        result = f(z_arr)
        expected = z_arr ** 2
        np.testing.assert_array_almost_equal(result, expected)

    def test_2d_array_input(self):
        f = get_callable("z^2 + 1")
        x = np.linspace(-1, 1, 5)
        y = np.linspace(-1, 1, 5)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y
        result = f(Z)
        expected = Z**2 + 1
        np.testing.assert_array_almost_equal(result, expected)


class TestIntegrationWithPlot:
    """Test integration between parser and plotting."""

    def test_parse_and_plot_integration(self):
        """Test that parsed functions work with plotting."""
        from py_domaincolor import plot
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            result_path = plot(
                "z^2",
                output_path=temp_path,
                resolution=50  # Low resolution for speed
            )
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
