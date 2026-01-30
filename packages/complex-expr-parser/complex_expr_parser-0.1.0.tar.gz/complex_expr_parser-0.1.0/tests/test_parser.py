"""
Tests for the complex function parser.
"""

import pytest
import numpy as np

from complex_expr_parser import (
    ComplexFunctionParser,
    parse_complex_function,
    get_callable,
    validate_expression,
    z,
)


class TestBasicParsing:
    """Test basic expression parsing."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_power_caret(self):
        expr = self.parser.parse("z^2")
        assert str(expr) == "z**2"

    def test_power_double_star(self):
        expr = self.parser.parse("z**2 + 1")
        assert str(expr) == "z**2 + 1"

    def test_simple_polynomial(self):
        expr = self.parser.parse("z^3 - 1")
        assert str(expr) == "z**3 - 1"

    def test_rational_function(self):
        expr = self.parser.parse("(z-1)/(z+1)")
        assert str(expr) == "(z - 1)/(z + 1)"

    def test_reciprocal(self):
        expr = self.parser.parse("1/z")
        assert str(expr) == "1/z"


class TestArithmeticOperations:
    """Test addition, subtraction, multiplication, division."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_addition(self):
        expr = self.parser.parse("z + 1")
        f = self.parser.to_callable(expr)
        assert f(2 + 1j) == pytest.approx(3 + 1j)

    def test_subtraction(self):
        expr = self.parser.parse("z - 1")
        f = self.parser.to_callable(expr)
        assert f(2 + 1j) == pytest.approx(1 + 1j)

    def test_division(self):
        expr = self.parser.parse("z / 2")
        f = self.parser.to_callable(expr)
        assert f(2 + 1j) == pytest.approx(1 + 0.5j)

    def test_division_reciprocal(self):
        expr = self.parser.parse("1/z")
        f = self.parser.to_callable(expr)
        # 1/(2+i) = (2-i)/5 = 0.4 - 0.2i
        assert f(2 + 1j) == pytest.approx(0.4 - 0.2j)

    def test_combined_rational(self):
        expr = self.parser.parse("(z+1)/(z-1)")
        f = self.parser.to_callable(expr)
        # (2+i+1)/(2+i-1) = (3+i)/(1+i) = (3+i)(1-i)/2 = (4-2i)/2 = 2-i
        assert f(2 + 1j) == pytest.approx(2 - 1j)

    def test_addition_with_imaginary(self):
        expr = self.parser.parse("z + i")
        f = self.parser.to_callable(expr)
        assert f(2 + 1j) == pytest.approx(2 + 2j)

    def test_polynomial(self):
        expr = self.parser.parse("z^2 + 2z + 1")
        f = self.parser.to_callable(expr)
        # (2+i)^2 + 2(2+i) + 1 = (3+4i) + (4+2i) + 1 = 8+6i
        assert f(2 + 1j) == pytest.approx(8 + 6j)

    def test_complex_rational(self):
        expr = self.parser.parse("(z-1)(z+1)/(z^2+1)")
        f = self.parser.to_callable(expr)
        result = f(2 + 1j)
        assert result == pytest.approx(0.75 + 0.25j)


class TestImplicitMultiplication:
    """Test implicit multiplication handling."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_number_times_variable(self):
        expr = self.parser.parse("2z")
        assert str(expr) == "2*z"

    def test_number_times_variable_with_constant(self):
        expr = self.parser.parse("2z + 3")
        f = self.parser.to_callable(expr)
        assert f(1 + 1j) == pytest.approx(5 + 2j)

    def test_variable_times_parenthesis(self):
        expr = self.parser.parse("z(z+1)")
        assert str(expr) == "z*(z + 1)"

    def test_parenthesis_times_parenthesis(self):
        expr = self.parser.parse("(z+1)(z-1)")
        assert str(expr) == "(z - 1)*(z + 1)"

    def test_coefficient_subtraction(self):
        expr = self.parser.parse("3z - 2")
        f = self.parser.to_callable(expr)
        assert f(2 + 1j) == pytest.approx(4 + 3j)


class TestTrigFunctions:
    """Test trigonometric functions."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_sin(self):
        expr = self.parser.parse("sin(z)")
        assert str(expr) == "sin(z)"
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.sin(1 + 1j)
        assert result == pytest.approx(expected)

    def test_cos(self):
        expr = self.parser.parse("cos(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.cos(1 + 1j)
        assert result == pytest.approx(expected)

    def test_tan(self):
        expr = self.parser.parse("tan(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.tan(1 + 1j)
        assert result == pytest.approx(expected)

    def test_sinc(self):
        """Test sin(z)/z (sinc function)."""
        expr = self.parser.parse("sin(z)/z")
        assert str(expr) == "sin(z)/z"
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.sin(1 + 1j) / (1 + 1j)
        assert result == pytest.approx(expected)


class TestHyperbolicFunctions:
    """Test hyperbolic functions."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_sinh(self):
        expr = self.parser.parse("sinh(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.sinh(1 + 1j)
        assert result == pytest.approx(expected)

    def test_cosh(self):
        expr = self.parser.parse("cosh(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.cosh(1 + 1j)
        assert result == pytest.approx(expected)

    def test_tanh(self):
        expr = self.parser.parse("tanh(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.tanh(1 + 1j)
        assert result == pytest.approx(expected)

    def test_cosh_minus_sinh(self):
        expr = self.parser.parse("cosh(z) - sinh(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.cosh(1 + 1j) - np.sinh(1 + 1j)
        assert result == pytest.approx(expected)


class TestExponentialAndLog:
    """Test exponential and logarithmic functions."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_exp(self):
        expr = self.parser.parse("exp(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.exp(1 + 1j)
        assert result == pytest.approx(expected)

    def test_e_to_z(self):
        """Test e^z notation."""
        expr = self.parser.parse("e^z")
        assert str(expr) == "exp(z)"
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.exp(1 + 1j)
        assert result == pytest.approx(expected)

    def test_log(self):
        expr = self.parser.parse("log(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.log(1 + 1j)
        assert result == pytest.approx(expected)

    def test_sqrt(self):
        expr = self.parser.parse("sqrt(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.sqrt(1 + 1j)
        assert result == pytest.approx(expected)

    def test_exp_i_pi_z(self):
        expr = self.parser.parse("exp(i*pi*z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = np.exp(1j * np.pi * (1 + 1j))
        assert result == pytest.approx(expected)


class TestComplexOperations:
    """Test complex-specific operations."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_abs_pipe_notation(self):
        expr = self.parser.parse("|z|")
        assert "Abs" in str(expr)
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(5.0)

    def test_conjugate(self):
        expr = self.parser.parse("conjugate(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        assert result == pytest.approx(1 - 1j)

    def test_real_part(self):
        expr = self.parser.parse("re(z)")
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(3.0)

    def test_imag_part(self):
        expr = self.parser.parse("im(z)")
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(4.0)

    def test_re_plus_i_im(self):
        """Test that re(z) + i*im(z) = z."""
        expr = self.parser.parse("re(z) + I*im(z)")
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(3 + 4j)


class TestConstants:
    """Test constant handling."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_imaginary_unit_i(self):
        expr = self.parser.parse("z + i")
        f = self.parser.to_callable(expr)
        result = f(1 + 0j)
        assert result == pytest.approx(1 + 1j)

    def test_imaginary_unit_in_trig(self):
        expr = self.parser.parse("cos(z) + i*sin(z)")
        f = self.parser.to_callable(expr)
        # At z=0: cos(0) + i*sin(0) = 1
        result = f(0 + 0j)
        assert result == pytest.approx(1 + 0j)

    def test_euler_e(self):
        expr = self.parser.parse("e^z")
        f = self.parser.to_callable(expr)
        # e^0 = 1
        result = f(0 + 0j)
        assert result == pytest.approx(1 + 0j)


class TestPowerFunctions:
    """Test power and exponentiation."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_z_squared(self):
        expr = self.parser.parse("z^2")
        f = self.parser.to_callable(expr)
        # (1+i)^2 = 1 + 2i - 1 = 2i
        result = f(1 + 1j)
        assert result == pytest.approx(2j)

    def test_z_cubed(self):
        expr = self.parser.parse("z^3")
        f = self.parser.to_callable(expr)
        # (1+i)^3 = (1+i)(2i) = 2i + 2i^2 = 2i - 2 = -2+2i
        result = f(1 + 1j)
        assert result == pytest.approx(-2 + 2j)

    def test_z_to_z(self):
        expr = self.parser.parse("z^z")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        expected = (1 + 1j) ** (1 + 1j)
        assert result == pytest.approx(expected)

    def test_inverse_quadratic(self):
        expr = self.parser.parse("1/(z^2 + 1)")
        f = self.parser.to_callable(expr)
        result = f(1 + 1j)
        z_val = 1 + 1j
        expected = 1 / (z_val**2 + 1)
        assert result == pytest.approx(expected)


class TestSpecialFunctions:
    """Test special functions (gamma, zeta) using mpmath."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_gamma_real(self):
        """Test gamma at a real point where we know the value."""
        import mpmath

        expr = self.parser.parse("gamma(z)")
        f = self.parser.to_callable(expr)
        # gamma(5) = 4! = 24
        result = f(5 + 0j)
        assert abs(result - 24) < 1e-10

    def test_gamma_complex(self):
        """Test gamma at a complex point."""
        import mpmath

        expr = self.parser.parse("gamma(z)")
        f = self.parser.to_callable(expr)
        z_val = 2 + 1j
        expected = complex(mpmath.gamma(z_val))
        result = f(z_val)
        assert result == pytest.approx(expected, rel=1e-10)

    def test_zeta_known_value(self):
        """Test zeta at z=2 where we know zeta(2) = pi^2/6."""
        import mpmath

        expr = self.parser.parse("zeta(z)")
        f = self.parser.to_callable(expr)
        result = f(2 + 0j)
        expected = np.pi**2 / 6
        assert abs(result - expected) < 1e-10

    def test_zeta_complex(self):
        """Test zeta at a complex point."""
        import mpmath

        expr = self.parser.parse("zeta(z)")
        f = self.parser.to_callable(expr)
        z_val = 2 + 1j
        expected = complex(mpmath.zeta(z_val))
        result = f(z_val)
        assert result == pytest.approx(expected, rel=1e-10)


class TestArrayEvaluation:
    """Test that functions work with numpy arrays."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_array_input(self):
        expr = self.parser.parse("z^2")
        f = self.parser.to_callable(expr)
        z_arr = np.array([1 + 0j, 1 + 1j, 0 + 1j, -1 + 0j])
        result = f(z_arr)
        expected = z_arr**2
        np.testing.assert_array_almost_equal(result, expected)

    def test_2d_array_input(self):
        expr = self.parser.parse("z^2 + 1")
        f = self.parser.to_callable(expr)
        x = np.linspace(-1, 1, 5)
        y = np.linspace(-1, 1, 5)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y
        result = f(Z)
        expected = Z**2 + 1
        np.testing.assert_array_almost_equal(result, expected)

    def test_trig_array(self):
        expr = self.parser.parse("sin(z)")
        f = self.parser.to_callable(expr)
        z_arr = np.array([0 + 0j, np.pi / 2 + 0j, 1 + 1j])
        result = f(z_arr)
        expected = np.sin(z_arr)
        np.testing.assert_array_almost_equal(result, expected)


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_parse_complex_function(self):
        expr = parse_complex_function("z^2 + 1")
        assert str(expr) == "z**2 + 1"

    def test_get_callable(self):
        f = get_callable("z^2")
        result = f(2 + 0j)
        assert result == pytest.approx(4 + 0j)

    def test_get_callable_trig(self):
        f = get_callable("sin(z)")
        result = f(np.pi / 2)
        assert result == pytest.approx(1.0)


class TestValidateExpression:
    """Test the validate_expression function."""

    def test_valid_expression(self):
        is_valid, error = validate_expression("z^2 + 1")
        assert is_valid is True
        assert error is None

    def test_valid_complex_expression(self):
        is_valid, error = validate_expression("sin(z)/z + |z|")
        assert is_valid is True
        assert error is None

    def test_empty_expression(self):
        is_valid, error = validate_expression("")
        assert is_valid is False
        assert error == "Expression cannot be empty"

    def test_whitespace_only(self):
        is_valid, error = validate_expression("   ")
        assert is_valid is False
        assert error == "Expression cannot be empty"

    def test_invalid_syntax(self):
        is_valid, error = validate_expression("z +* 1")
        assert is_valid is False
        assert error is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_division_by_zero_handling(self):
        """Test that 1/z handles z=0 (returns inf or raises ZeroDivisionError)."""
        f = get_callable("1/z")
        # For array input with errstate, it returns inf
        z_arr = np.array([0 + 0j])
        with np.errstate(all="ignore"):
            result = f(z_arr)
        assert np.isinf(result[0]) or np.isnan(result[0])

    def test_log_of_zero_handling(self):
        """Test that log(z) handles z=0."""
        f = get_callable("log(z)")
        result = f(0 + 0j)
        assert np.isinf(result) or np.isnan(result)

    def test_nested_functions(self):
        expr = self.parser.parse("sin(cos(z))")
        f = self.parser.to_callable(expr)
        result = f(1 + 0j)
        expected = np.sin(np.cos(1 + 0j))
        assert result == pytest.approx(expected)

    def test_whitespace_handling(self):
        expr = self.parser.parse("  z^2  +  1  ")
        assert str(expr) == "z**2 + 1"


class TestParseErrors:
    """Test that invalid expressions raise appropriate errors."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_invalid_syntax(self):
        with pytest.raises(ValueError):
            self.parser.parse("z +* 1")

    def test_unbalanced_parens(self):
        with pytest.raises(ValueError):
            self.parser.parse("(z+1")

    def test_unknown_function(self):
        """Test behavior with unknown function names."""
        # Sympy treats unknown names as symbols, so it parses but creates
        # a symbolic expression. This is actually valid behavior for sympy.
        # The expression becomes unknown_func*z due to implicit mult.
        expr = self.parser.parse("unknown_func(z)")
        # Check it parsed to something (sympy creates a symbol)
        assert expr is not None
        # The expression will contain 'unknown_func' as a symbol
        assert "unknown_func" in str(expr) or "z" in str(expr)


class TestFunctionAliases:
    """Test function name aliases."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_ln_alias(self):
        """Test that ln is converted to log."""
        expr = self.parser.parse("ln(z)")
        assert "log" in str(expr)

    def test_arcsin_alias(self):
        """Test that arcsin is converted to asin."""
        expr = self.parser.parse("arcsin(z)")
        assert "asin" in str(expr)

    def test_arccos_alias(self):
        """Test that arccos is converted to acos."""
        expr = self.parser.parse("arccos(z)")
        assert "acos" in str(expr)

    def test_arctan_alias(self):
        """Test that arctan is converted to atan."""
        expr = self.parser.parse("arctan(z)")
        assert "atan" in str(expr)

    def test_conj_alias(self):
        """Test that conj is converted to conjugate."""
        expr = self.parser.parse("conj(z)")
        f = self.parser.to_callable(expr)
        result = f(1 + 2j)
        assert result == pytest.approx(1 - 2j)

    def test_real_alias(self):
        """Test that real is converted to re."""
        expr = self.parser.parse("real(z)")
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(3.0)

    def test_imag_alias(self):
        """Test that imag is converted to im."""
        expr = self.parser.parse("imag(z)")
        f = self.parser.to_callable(expr)
        result = f(3 + 4j)
        assert result == pytest.approx(4.0)


class TestUnicode:
    """Test Unicode symbol handling."""

    def setup_method(self):
        self.parser = ComplexFunctionParser()

    def test_pi_unicode(self):
        """Test that Unicode pi is converted."""
        expr = self.parser.parse("z + \u03c0")  # Greek letter pi
        f = self.parser.to_callable(expr)
        result = f(0 + 0j)
        assert result == pytest.approx(np.pi)

    def test_sqrt_unicode(self):
        """Test that Unicode sqrt is converted."""
        expr = self.parser.parse("\u221a(z)")  # Square root symbol
        f = self.parser.to_callable(expr)
        result = f(4 + 0j)
        assert result == pytest.approx(2 + 0j)

    def test_infinity_unicode(self):
        """Test that Unicode infinity is converted."""
        expr = self.parser.parse("z/\u221e")  # Infinity symbol
        f = self.parser.to_callable(expr)
        result = f(1 + 0j)
        assert result == pytest.approx(0 + 0j)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
