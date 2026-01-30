"""
Fault-tolerant parser for complex-valued functions in symbolic notation.

Handles various human-friendly input formats and normalizes them for sympy.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Callable

from sympy import (
    Abs,
    E,
    I,
    Symbol,
    acos,
    acosh,
    arg,
    asin,
    asinh,
    atan,
    atanh,
    binomial,
    ceiling,
    conjugate,
    cos,
    cosh,
    exp,
    factorial,
    floor,
    gamma,
    lambdify,
    log,
    oo,
    pi,
    sin,
    sinh,
    sqrt,
    symbols,
    sympify,
    tan,
    tanh,
    zeta,
)
from sympy import im as imag_part
from sympy import re as real_part
from sympy.parsing.sympy_parser import (
    convert_xor,
    function_exponentiation,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

if TYPE_CHECKING:
    from sympy import Expr

# Define the complex variable
z: Symbol = symbols("z", complex=True)


# Known function names - sorted by length (longest first) to avoid partial matches
KNOWN_FUNCTIONS: list[str] = sorted(
    [
        "sin",
        "cos",
        "tan",
        "exp",
        "log",
        "ln",
        "sqrt",
        "abs",
        "Abs",
        "sinh",
        "cosh",
        "tanh",
        "asin",
        "acos",
        "atan",
        "asinh",
        "acosh",
        "atanh",
        "gamma",
        "zeta",
        "conjugate",
        "re",
        "im",
        "arg",
        "factorial",
        "binomial",
        "ceiling",
        "floor",
        "arcsin",
        "arccos",
        "arctan",
        "arcsinh",
        "arccosh",
        "arctanh",
        "Re",
        "Im",
        "conj",
        "real",
        "imag",
        "phase",
        "angle",
    ],
    key=len,
    reverse=True,
)


class ComplexFunctionParser:
    """
    Fault-tolerant parser for complex functions.

    Accepts various human-friendly notations and converts to sympy expressions.

    Supported notations:

    - Power notation: ``z^2`` or ``z**2``
    - Implicit multiplication: ``2z``, ``z(z+1)``, ``(z+1)(z-1)``
    - Absolute value: ``|z|`` -> ``Abs(z)``
    - Conjugate: ``z*`` -> ``conjugate(z)`` (note: ``z**`` is power)
    - Unicode: ``pi`` -> pi, ``sqrt`` -> sqrt, ``oo`` -> infinity
    - Function aliases:
        - ``ln`` -> ``log``
        - ``arcsin/arccos/arctan`` -> ``asin/acos/atan``
        - ``Re/real`` -> ``re``, ``Im/imag`` -> ``im``
        - ``phase/angle`` -> ``arg``
        - ``conj`` -> ``conjugate``
    - Imaginary unit: ``i`` or ``j`` -> ``I``
    - Euler's number: standalone ``e`` -> ``E``

    Example:
        >>> parser = ComplexFunctionParser()
        >>> expr = parser.parse("2z^2 + 3z + 1")
        >>> print(expr)
        2*z**2 + 3*z + 1
        >>> f = parser.to_callable(expr)
        >>> f(1+1j)
        (5+8j)
    """

    def __init__(self) -> None:
        """Initialize the parser with sympy transformations and namespace."""
        self.transformations = (
            standard_transformations
            + (implicit_multiplication_application, convert_xor, function_exponentiation)
        )

        # Local namespace for parsing
        self.local_dict: dict[str, Any] = {
            "z": z,
            "I": I,
            "E": E,
            "e": E,
            "pi": pi,
            "oo": oo,
            "sin": sin,
            "cos": cos,
            "tan": tan,
            "exp": exp,
            "log": log,
            "sqrt": sqrt,
            "Abs": Abs,
            "sinh": sinh,
            "cosh": cosh,
            "tanh": tanh,
            "asin": asin,
            "acos": acos,
            "atan": atan,
            "asinh": asinh,
            "acosh": acosh,
            "atanh": atanh,
            "gamma": gamma,
            "zeta": zeta,
            "conjugate": conjugate,
            "re": real_part,
            "im": imag_part,
            "arg": arg,
            "factorial": factorial,
            "binomial": binomial,
            "ceiling": ceiling,
            "floor": floor,
        }

    def preprocess(self, expr_str: str) -> str:
        """
        Apply substitutions and normalizations to input string.

        Args:
            expr_str: The raw expression string.

        Returns:
            Preprocessed expression string ready for sympy parsing.
        """
        result = expr_str.strip()

        # First pass: handle special notations

        # Absolute value: |...| -> Abs(...)
        result = re.sub(r"\|([^|]+)\|", r"Abs(\1)", result)

        # Conjugate: z* -> conjugate(z), but not z**
        result = re.sub(r"z\*(?!\*)", "conjugate(z)", result)

        # Unicode
        result = result.replace("\u03c0", "pi")  # pi
        result = result.replace("\u221a", "sqrt")  # sqrt
        result = result.replace("\u221e", "oo")  # oo

        # Power: ^ -> **
        result = result.replace("^", "**")

        # Function name normalizations (before implicit mult)
        replacements = [
            (r"\bln\b", "log"),
            (r"\barcsin\b", "asin"),
            (r"\barccos\b", "acos"),
            (r"\barctan\b", "atan"),
            (r"\barcsinh\b", "asinh"),
            (r"\barccosh\b", "acosh"),
            (r"\barctanh\b", "atanh"),
            (r"\babs\b", "Abs"),
            (r"\bRe\b", "re"),
            (r"\bIm\b", "im"),
            (r"\breal\b", "re"),
            (r"\bimag\b", "im"),
            (r"\bphase\b", "arg"),
            (r"\bangle\b", "arg"),
            (r"\bconj\b", "conjugate"),
        ]
        for pattern, repl in replacements:
            result = re.sub(pattern, repl, result)

        # Factorial: n! -> factorial(n)
        result = re.sub(r"(\w+)!", r"factorial(\1)", result)

        # Now handle implicit multiplication carefully
        # We need to NOT add * between function names and their arguments

        # Build a regex pattern for all known functions
        func_pattern = "|".join(re.escape(f) for f in KNOWN_FUNCTIONS)

        # Step 1: Mark function calls to protect them
        # Replace "func(" with "func@(" temporarily
        result = re.sub(rf"\b({func_pattern})\s*\(", r"\1@(", result, flags=re.IGNORECASE)

        # Step 2: Apply implicit multiplication

        # Number followed by letter: 2z -> 2*z
        result = re.sub(r"(\d)([a-zA-Z])", r"\1*\2", result)

        # Letter/digit followed by parenthesis (but not function calls marked with @)
        result = re.sub(r"(\w)(\()(?<!@\()", r"\1*\2", result)

        # Closing paren followed by opening paren: )( -> )*(
        result = re.sub(r"\)\s*\(", ")*(", result)

        # Closing paren followed by letter/digit: )z -> )*z
        result = re.sub(r"\)\s*(\w)", r")*\1", result)

        # Step 3: Restore function calls
        result = result.replace("@(", "(")

        # Handle imaginary unit: standalone i or j
        # Must be careful not to replace i in function names
        # Match i/j that are not part of a word
        result = re.sub(r"(?<![a-zA-Z])i(?![a-zA-Z])", "I", result)
        result = re.sub(r"(?<![a-zA-Z])j(?![a-zA-Z])", "I", result)

        # Handle Euler's number: standalone e (not in exp, etc.)
        result = re.sub(r"(?<![a-zA-Z])e(?![a-zA-Z])", "E", result)

        return result

    def parse(self, expr_str: str) -> Expr:
        """
        Parse a human-friendly complex function string into a sympy expression.

        This method attempts multiple parsing strategies to handle various
        input formats gracefully.

        Args:
            expr_str: String representation of the function.

        Returns:
            A sympy expression with ``z`` as the variable.

        Raises:
            ValueError: If parsing fails with all strategies.

        Example:
            >>> parser = ComplexFunctionParser()
            >>> parser.parse("z^2 + 1")
            z**2 + 1
            >>> parser.parse("sin(z)/z")
            sin(z)/z
            >>> parser.parse("|z|")
            Abs(z)
        """
        original = expr_str
        processed = self.preprocess(expr_str)

        errors: list[str] = []

        # Attempt 1: Direct sympify
        try:
            expr = sympify(processed, locals=self.local_dict)
            return expr
        except Exception as e:
            errors.append(f"Sympify: {e}")

        # Attempt 2: parse_expr with transformations
        try:
            expr = parse_expr(
                processed,
                local_dict=self.local_dict,
                transformations=self.transformations,
            )
            return expr
        except Exception as e:
            errors.append(f"Parse_expr: {e}")

        # Attempt 3: Original with minimal preprocessing
        try:
            basic = expr_str.replace("^", "**")
            expr = sympify(basic, locals=self.local_dict)
            return expr
        except Exception as e:
            errors.append(f"Basic: {e}")

        raise ValueError(
            f"Could not parse expression: '{original}'\n"
            f"Preprocessed to: '{processed}'\n"
            f"Errors: {'; '.join(errors)}"
        )

    def to_callable(
        self, expr: Expr, use_numpy: bool = True
    ) -> Callable[[complex | Any], complex | Any]:
        """
        Convert sympy expression to a callable function.

        Args:
            expr: A sympy expression.
            use_numpy: If True, use numpy for vectorized evaluation (faster).
                      If False or if special functions are needed, use mpmath.

        Returns:
            A callable that takes complex numbers (or numpy arrays) and
            returns complex numbers.

        Note:
            Special functions like ``gamma`` and ``zeta`` automatically
            use mpmath for evaluation regardless of the ``use_numpy`` setting.

        Example:
            >>> parser = ComplexFunctionParser()
            >>> expr = parser.parse("z^2")
            >>> f = parser.to_callable(expr)
            >>> f(1+1j)
            2j
            >>> import numpy as np
            >>> f(np.array([1, 1j, -1]))
            array([ 1.+0.j, -1.+0.j,  1.+0.j])
        """
        # Check if expression contains special functions needing mpmath
        expr_str = str(expr)
        needs_mpmath = any(
            fn in expr_str for fn in ["gamma", "zeta", "polygamma", "digamma"]
        )

        if use_numpy and not needs_mpmath:
            # Use numpy for fast vectorized evaluation
            try:
                import numpy as np

                f = lambdify(z, expr, modules=["numpy"])

                def safe_eval(z_val: complex | Any) -> complex | Any:
                    with np.errstate(all="ignore"):
                        return f(z_val)

                return safe_eval
            except ImportError:
                # Fall back to mpmath if numpy not available
                pass

        # Use mpmath for special functions or scalar evaluation
        import mpmath

        f = lambdify(z, expr, modules=["mpmath"])

        def safe_eval_mpmath(z_val: complex | Any) -> complex | Any:
            """Evaluate using mpmath, handles both scalars and arrays."""
            try:
                import numpy as np

                if isinstance(z_val, np.ndarray):
                    # Vectorize the mpmath evaluation
                    result = np.empty(z_val.shape, dtype=complex)
                    flat_z = z_val.flatten()
                    flat_result = result.flatten()
                    for i, zv in enumerate(flat_z):
                        try:
                            val = f(complex(zv))
                            flat_result[i] = complex(val)
                        except (ValueError, ZeroDivisionError, OverflowError, TypeError):
                            flat_result[i] = complex("nan")
                    return flat_result.reshape(z_val.shape)
            except ImportError:
                pass

            try:
                return complex(f(complex(z_val)))
            except (ValueError, ZeroDivisionError, OverflowError, TypeError):
                return complex("nan")

        return safe_eval_mpmath


def parse_complex_function(expr_str: str) -> Expr:
    """
    Parse a complex function string into a sympy expression.

    This is a convenience function that creates a parser and parses the
    given expression in one call.

    Args:
        expr_str: Human-friendly function string.

    Returns:
        A sympy expression with ``z`` as the variable.

    Raises:
        ValueError: If the expression cannot be parsed.

    Example:
        >>> parse_complex_function("z^2 + 1")
        z**2 + 1
        >>> parse_complex_function("sin(z)/z")
        sin(z)/z
        >>> parse_complex_function("e^z")
        exp(z)
    """
    parser = ComplexFunctionParser()
    return parser.parse(expr_str)


def get_callable(
    expr_str: str, use_numpy: bool = True
) -> Callable[[complex | Any], complex | Any]:
    """
    Parse and return a callable function for the given expression.

    This is a convenience function that parses an expression and converts
    it to a callable in one step.

    Args:
        expr_str: Human-friendly function string.
        use_numpy: Use numpy for vectorized evaluation (faster for plotting).

    Returns:
        A callable function ``f(z) -> complex`` that evaluates the expression.

    Example:
        >>> f = get_callable("z^2 + 1")
        >>> f(1+1j)
        (1+2j)
        >>> import numpy as np
        >>> f(np.array([1, 1j, -1]))
        array([2.+0.j, 0.+0.j, 2.+0.j])
    """
    parser = ComplexFunctionParser()
    expr = parser.parse(expr_str)
    return parser.to_callable(expr, use_numpy)


def validate_expression(expr_str: str) -> tuple[bool, str | None]:
    """
    Validate a complex function expression without fully evaluating it.

    This function checks if an expression can be parsed and converted to
    a callable function. Useful for input validation in user interfaces.

    Args:
        expr_str: Human-friendly function string.

    Returns:
        A tuple of ``(is_valid, error_message)``.
        If valid, ``error_message`` is ``None``.

    Example:
        >>> validate_expression("z^2 + 1")
        (True, None)
        >>> validate_expression("z +* 1")
        (False, "Could not parse expression: 'z +* 1'...")
        >>> validate_expression("")
        (False, "Expression cannot be empty")
    """
    if not expr_str or not expr_str.strip():
        return False, "Expression cannot be empty"

    try:
        parser = ComplexFunctionParser()
        expr = parser.parse(expr_str)
        # Try to make a callable to verify it's valid
        _ = parser.to_callable(expr, use_numpy=False)
        return True, None
    except Exception as e:
        return False, str(e)
