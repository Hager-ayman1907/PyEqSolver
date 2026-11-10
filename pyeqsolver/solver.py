"""Gaussian Elimination written by hand on plain Python lists"""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence, Union

from .exceptions import (
    DimensionMismatchException,
    InconsistentSystemException,
    InfiniteSolutionsException,
)

Number = Union[float, Fraction]


class GaussianSolver:
    """solves a system using an augmented matrix [A | b]"""

    TOLERANCE = 1e-9

    def __init__(self, matrix: Sequence[Sequence[Number]], variables: Sequence[str], exact: bool = False) -> None:
        self._exact = exact
        self._zero = Fraction(0) if exact else 0.0

        # keep a copy so the original matrix is not changed
        convert = Fraction if exact else float
        width = len(variables) + 1
        self._matrix = []

        for number, row in enumerate(matrix, start=1):
            if len(row) != width:
                raise ValueError("Row {number} has {len(row)} entries, expected {width}" )

            self._matrix.append([convert(value) for value in row])

        self._variables = list(variables)

    def get_metadata(self) -> dict[str, int]:
        """return the number of variables and equations"""
        return {"num_variables": len(self._variables), "num_equations": len(self._matrix)}

    def solve(self) -> dict[str, Number]:
        n = len(self._variables)
        m = len(self._matrix)

        # check this before doing elimination
        if m < n:
            raise DimensionMismatchException( f"{m} equations for {n} variables ({', '.join(self._variables)})" )

        # work on a copy of the matrix
        work = [row[:] for row in self._matrix]

        self._forward_eliminate(work)

        # check for a row like 0x + 0y = 5
        for row in work:
            all_coefficients_are_zero = all( self._is_zero(value) for value in row[:n])

            if all_coefficients_are_zero and not self._is_zero(row[n]):
                raise InconsistentSystemException(
                    f"The system has no solution "
                    f"(row reduces to 0 = {self._fmt(row[n])})" )

        # if rank is too small, there are free variables
        rank = self._rank(work)

        if rank < n:
            raise InfiniteSolutionsException( f"Infinitely many solutions: rank {rank} < {n} variables")

        return self._back_substitute(work)

    def _is_zero(self, value: Number) -> bool:
        """check zero exactly or using a tolerance"""
        if self._exact:         # in fraction
            return value == 0

        return abs(value) < self.TOLERANCE   # in float

    def _fmt(self, value: Number) -> str:
        """Format a number for an error message"""
        if self._exact:
            return str(value)

        return format(value, "g")

    def _forward_eliminate(self, a: list[list[Number]]) -> None:
        """turn the matrix into row echelon form"""

        m = len(a)
        n = len(self._variables)
        top = 0

        for col in range(n):
            if top == m:
                break

            # find the row with the largest value in this column
            best = top

            for r in range(top + 1, m):
                if abs(a[r][col]) > abs(a[best][col]):
                    best = r

            # if the whole column below this point is zero, skip it
            if self._is_zero(a[best][col]):
                for r in range(top, m):
                    a[r][col] = self._zero
                continue

            # move the selected pivot row into position
            a[top], a[best] = a[best], a[top]    ## swap two rows

            # make the entries below the pivot equal to zero
            for r in range(top + 1, m):
                factor = a[r][col] / a[top][col]

                for c in range(col, n + 1):
                    a[r][c] -= factor * a[top][c]

                    if self._is_zero(a[r][c]):
                        a[r][c] = self._zero

                a[r][col] = self._zero

            top += 1

    def _rank(self, a: list[list[Number]]) -> int:
        """count rows that contain at least one non-zero coefficient"""

        n = len(self._variables)
        rank = 0

        for row in a:
            has_nonzero_coefficient = any(not self._is_zero(value) for value in row[:n])

            if has_nonzero_coefficient:
                rank += 1

        return rank

    def _back_substitute(self, a: list[list[Number]]) -> dict[str, Number]:
        """find the variables' values, starting from the last row"""

        n = len(self._variables)
        x = [self._zero] * n

        for i in range(n - 1, -1, -1):
            total = a[i][n]

            # subtract the values we already found
            for j in range(i + 1, n):
                total -= a[i][j] * x[j]

            x[i] = total / a[i][i]

        # match each variable name with its solution
        return dict(zip(self._variables, x))