"""Parse a text file of linear equations into an augmented matrix [A | b]."""

from __future__ import annotations

import re
from fractions import Fraction
from pathlib import Path
from typing import Union

from .exceptions import InvalidFileFormatException


Number = Union[float, Fraction]

_NUM = r"(?:\d+(?:\.\d*)?|\.\d+)"
_VAR = r"[A-Za-z_][A-Za-z0-9_]*"

_ALLOWED_CHAR = re.compile(r"[A-Za-z0-9_.+\-*= \t]")
_TERM = re.compile(rf"(?:({_NUM})\s*\*?\s*)?({_VAR})")
_BARE_NUMBER = re.compile(_NUM)
_CONSTANT = re.compile(rf"([+-])?\s*({_NUM})")


class EquationParser:
    """it reads equations from a file and builds the augmented matrix"""
    def __init__(self, file_path: str | Path, exact: bool = False) -> None:
        self.file_path = file_path
        self._exact = exact

        if exact:
            self._zero = Fraction(0)
            self._one = Fraction(1)
        else:
            self._zero = 0.0
            self._one = 1.0

    def parse(self) -> tuple[list[list[Number]], list[str]]:
        """Return the augmented matrix and variable names"""

        lines = self._read_lines()   # to read content of file and return it as lines
        equations = []
        variables = []

        for lineno, raw in enumerate(lines, start=1):
            text = raw.strip()

            # Skip blank lines and comments.
            if not text or text.startswith("#"):
                continue

            coeffs, constant = self._parse_line(text, lineno)
            equations.append((coeffs, constant))

            # keep variables in order of first appearance
            for name in coeffs:
                if name not in variables:
                    variables.append(name)

        if not equations:
            raise InvalidFileFormatException(f"No equations found in {self.file_path}")

        # give each variable a column number
        index = {name: i for i, name in enumerate(variables)}

        matrix = []

        for coeffs, constant in equations:
            # start with zeros, then put the constant at the end
            row = [self._zero] * len(variables) + [constant]

            for name, value in coeffs.items():
                row[index[name]] = value

            matrix.append(row)

        return matrix, variables

    def _read_lines(self) -> list[str]:
        path = Path(self.file_path)

        if not path.is_file():
            raise FileNotFoundError(f"Input file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            raise InvalidFileFormatException(f"{path} is not a valid UTF-8 text file") from None

        return content.splitlines()

    def _number(self, text: str) -> Number:
        if self._exact:
            return Fraction(text)

        return float(text)

    @staticmethod
    def _error(lineno: int, reason: str, text: str) -> InvalidFileFormatException:
        return InvalidFileFormatException( f'Line {lineno}: {reason} in "{text}"' )

    def _parse_line(self, text: str, lineno: int) -> tuple[dict[str, Number], Number]:

        # only one equal sign is allowed
        if text.count("=") != 1:
            raise self._error(lineno, "equation must contain one '='", text)

        left, right = text.split("=")

        if not left.strip():
            raise self._error(lineno, "empty left side", text)

        if not right.strip():
            raise self._error(lineno, "empty right side", text)

        # check for characters that are not supported
        for ch in text:
            if not _ALLOWED_CHAR.fullmatch(ch):
                raise self._error( lineno, f"unsupported character {ch!r}", text )

        coeffs = self._parse_left(left, lineno, text)
        constant = self._parse_right(right, lineno, text)

        return coeffs, constant

    def _parse_left(self, left: str, lineno: int, text: str) -> dict[str, Number]:

        # split the expression at + and -, while keeping the signs
        tokens = re.split(r"([+-])", left)
        tokens = [token.strip() for token in tokens if token.strip()]

        coeffs = {}
        pending = None

        for token in tokens:
            if token in ("+", "-"):
                if pending is not None:
                    raise self._error(lineno, "two operators in a row", text)

                pending = token
                continue

            match = _TERM.fullmatch(token)

            if match is None:
                if _BARE_NUMBER.fullmatch(token):
                    reason = f"number {token} has no variable on the left side"
                else:
                    reason = f"cannot read term {token!r}"

                raise self._error(lineno, reason, text)

            number, name = match.groups()

            # if no number is written, the coefficient is 1
            coef = self._number(number) if number else self._one

            if pending == "-":
                coef = -coef

            # Add coefficients if the same variable appears more than once
            coeffs[name] = coeffs.get(name, self._zero) + coef
            pending = None

        if pending is not None:
            raise self._error(lineno, "left side ends with an operator", text)

        return coeffs

    def _parse_right(self, right: str, lineno: int, text: str) -> Number:

        right = right.strip()
        match = _CONSTANT.fullmatch(right)

        if match is None:
            if re.search(r"[A-Za-z_]", right):
                reason = "variables on the right side are not supported"
            else:
                reason = "right side must be a single number"

            raise self._error(lineno, reason, text)

        sign, number = match.groups()
        value = self._number(number)

        if sign == "-":
            value = -value

        return value