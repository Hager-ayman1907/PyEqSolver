"""Custom exceptions for PyEqSolver
"""


class PyEqSolverError(Exception):
    """Base class for all PyEqSolver errors. Never raised directly."""


class InvalidFileFormatException(PyEqSolverError):
    """A line breaks the syntax rules, or the file contains no equations."""


class DimensionMismatchException(PyEqSolverError):
    """There are fewer equations than variables."""


class InconsistentSystemException(PyEqSolverError):
    """The system has no solution (a row reduces to ``0 = c`` with c != 0)."""


class InfiniteSolutionsException(PyEqSolverError):
    """The system has infinitely many solutions (rank < number of variables)."""
