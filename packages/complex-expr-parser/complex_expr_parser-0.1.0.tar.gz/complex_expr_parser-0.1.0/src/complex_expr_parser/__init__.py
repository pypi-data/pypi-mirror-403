"""
Complex Expression Parser - A fault-tolerant parser for complex-valued mathematical functions.

This package provides tools to parse human-friendly mathematical notation into
sympy expressions, supporting features like:

- Implicit multiplication: ``2z`` -> ``2*z``
- Power notation: ``z^2`` -> ``z**2``
- Absolute value: ``|z|`` -> ``Abs(z)``
- Conjugate shorthand: ``z*`` -> ``conjugate(z)``
- Unicode symbols: ``pi``, ``sqrt``, ``oo``
- Function aliases: ``ln`` -> ``log``, ``arcsin`` -> ``asin``, etc.

Example usage:

    >>> from complex_expr_parser import parse_complex_function, get_callable
    >>> expr = parse_complex_function("z^2 + 2z + 1")
    >>> print(expr)
    z**2 + 2*z + 1
    >>> f = get_callable("sin(z)/z")
    >>> f(1+1j)
    (0.6349639147847361+0.2988350886551747j)
"""

from complex_expr_parser._parser import (
    ComplexFunctionParser,
    get_callable,
    parse_complex_function,
    validate_expression,
    z,
    KNOWN_FUNCTIONS,
)

__version__ = "0.1.0"

__all__ = [
    "ComplexFunctionParser",
    "parse_complex_function",
    "get_callable",
    "validate_expression",
    "z",
    "KNOWN_FUNCTIONS",
    "__version__",
]
