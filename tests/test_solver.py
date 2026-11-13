"""unit tests for GaussianSolver (the 13 spec cases plus extras)"""

import unittest
from fractions import Fraction
from pathlib import Path

from pyeqsolver import EquationParser, GaussianSolver
from pyeqsolver.exceptions import (
    DimensionMismatchException,
    InconsistentSystemException,
    InfiniteSolutionsException,
    PyEqSolverError,
)

DATA = Path(__file__).parent / "data"


def solve_file(name, **kwargs):
    matrix, variables = EquationParser(DATA / name, exact=kwargs.get("exact", False)).parse()
    return GaussianSolver(matrix, variables, **kwargs).solve()


class SpecCaseTests(unittest.TestCase):
    def assert_solution(self, actual, expected):
        self.assertEqual(set(actual), set(expected))
        for name, value in expected.items():
            self.assertAlmostEqual(actual[name], value, places=4)

    def test_case01_unique(self):
        self.assert_solution(solve_file("case01_basic.txt"), {"x1": 0, "x2": 1, "x3": 2})

    def test_case02_needs_row_swap(self):
        self.assert_solution(solve_file("case02_row_swap.txt"), {"x": 1, "y": 2, "z": 3})

    def test_case03_decimals(self):
        self.assert_solution(solve_file("case03_decimals.txt"), {"a": 1, "b": 2})

    def test_case04_single_equation(self):
        self.assert_solution(solve_file("case04_single.txt"), {"x": 0.3333})

    def test_case05_repeated_variable(self):
        self.assert_solution(solve_file("case05_repeated.txt"), {"x": 2})

    def test_case06_extra_consistent_equation(self):
        self.assert_solution(solve_file("case06_extra_equation.txt"), {"x": 2, "y": 1})

    def test_case07_inconsistent(self):
        with self.assertRaises(InconsistentSystemException) as ctx:
            solve_file("case07_inconsistent.txt")
        self.assertIn("no solution", str(ctx.exception))
        self.assertIn("0 = 1", str(ctx.exception))

    def test_case08_infinite(self):
        with self.assertRaises(InfiniteSolutionsException) as ctx:
            solve_file("case08_infinite.txt")
        self.assertIn("rank 1 < 2 variables", str(ctx.exception))

    def test_case09_dimension_mismatch(self):
        with self.assertRaises(DimensionMismatchException) as ctx:
            solve_file("case09_dimension.txt")
        self.assertIn("2 equations for 3 variables (x, y, z)", str(ctx.exception))

    def test_second_example_from_spec(self):
        self.assert_solution(
            solve_file("example2_varied_syntax.txt"), {"x": 5, "y": 3, "z": -2}
        )


class BehaviourTests(unittest.TestCase):
    def test_caller_matrix_is_not_modified(self):
        matrix = [[2.0, 1.0, 5.0], [1.0, 3.0, 10.0]]
        snapshot = [row[:] for row in matrix]
        GaussianSolver(matrix, ["x", "y"]).solve()
        self.assertEqual(matrix, snapshot)

    def test_metadata(self):
        solver = GaussianSolver([[1.0, 0.0, 1.0], [0.0, 1.0, 2.0], [1.0, 1.0, 3.0]], ["x", "y"])
        self.assertEqual(solver.get_metadata(), {"num_variables": 2, "num_equations": 3})

    def test_solve_twice_gives_same_answer(self):
        solver = GaussianSolver([[2.0, 1.0, 5.0], [1.0, 3.0, 10.0]], ["x", "y"])
        self.assertEqual(solver.solve(), solver.solve())

    def test_zero_pivot_without_crash(self):
        # first column pivot is 0 in row 0 -> must swap, not divide by zero
        result = GaussianSolver([[0.0, 1.0, 2.0], [1.0, 1.0, 3.0]], ["x", "y"]).solve()
        self.assertAlmostEqual(result["x"], 1.0, places=4)
        self.assertAlmostEqual(result["y"], 2.0, places=4)

    def test_float_noise_counts_as_zero(self):
        # 0.1 + 0.2 != 0.3 exactly; the rows are equal up to rounding noise
        solver = GaussianSolver([[0.1 + 0.2, 1.0, 1.0], [0.3, 1.0, 1.0]], ["x", "y"])
        with self.assertRaises(InfiniteSolutionsException):
            solver.solve()

    def test_extra_equation_makes_system_inconsistent(self):
        solver = GaussianSolver(
            [[1.0, 1.0, 1.0], [1.0, -1.0, 1.0], [1.0, 0.0, 5.0]], ["x", "y"]
        )
        with self.assertRaises(InconsistentSystemException):
            solver.solve()

    def test_inconsistent_checked_before_rank(self):
        # rank 1 < 2 variables, but 0 = 1 must win
        solver = GaussianSolver([[1.0, 1.0, 2.0], [2.0, 2.0, 5.0]], ["x", "y"])
        with self.assertRaises(InconsistentSystemException):
            solver.solve()

    def test_partial_pivoting_accuracy(self):
        result = GaussianSolver([[1e-8, 1.0, 1.0], [1.0, 1.0, 2.0]], ["x", "y"]).solve()
        self.assertAlmostEqual(result["x"], 1 / 0.99999999, places=8)
        self.assertAlmostEqual(result["y"], 0.99999999, places=8)

    def test_exact_mode(self):
        result = GaussianSolver([[3, 1]], ["x"], exact=True).solve()
        self.assertEqual(result, {"x": Fraction(1, 3)})

    def test_exact_mode_two_variables(self):
        matrix = [[Fraction(1, 3), Fraction(1, 2), 1], [1, 1, 1]]
        result = GaussianSolver(matrix, ["x", "y"], exact=True).solve()
        self.assertEqual(result, {"x": Fraction(-3), "y": Fraction(4)})

    def test_bad_row_length_raises_value_error(self):
        with self.assertRaises(ValueError):
            GaussianSolver([[1.0, 2.0]], ["x", "y"])

    def test_all_errors_share_the_base_class(self):
        for exc in (
            DimensionMismatchException,
            InconsistentSystemException,
            InfiniteSolutionsException,
        ):
            self.assertTrue(issubclass(exc, PyEqSolverError))


if __name__ == "__main__":
    unittest.main()
