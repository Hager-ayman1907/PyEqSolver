"""Unit tests for EquationParser."""

import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from pyeqsolver import EquationParser
from pyeqsolver.exceptions import InvalidFileFormatException, PyEqSolverError

DATA = Path(__file__).parent / "data"


def parse_text(text, **kwargs):
    """Write ``text`` to a temporary file and parse it."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "equations.txt"
        path.write_text(text, encoding="utf-8")
        return EquationParser(file_path=str(path), **kwargs).parse()


class ValidInputTests(unittest.TestCase):
    def test_case01_matrix_and_variable_order(self):
        matrix, variables = EquationParser(DATA / "case01_basic.txt").parse()
        self.assertEqual(variables, ["x1", "x2", "x3"])
        self.assertEqual(
            matrix,
            [[10.0, 5.0, 0.0, 5.0], [0.0, 4.0, 3.0, 10.0], [1.0, 0.0, 6.0, 12.0]],
        )

    def test_case03_decimals(self):
        matrix, variables = EquationParser(DATA / "case03_decimals.txt").parse()
        self.assertEqual(variables, ["a", "b"])
        self.assertEqual(matrix, [[0.5, 1.5, 3.5], [2.0, -1.0, 0.0]])

    def test_case05_repeated_variables_are_added(self):
        matrix, variables = EquationParser(DATA / "case05_repeated.txt").parse()
        self.assertEqual(variables, ["x"])
        self.assertEqual(matrix, [[5.0, 10.0]])

    def test_varied_syntax_file(self):
        matrix, variables = EquationParser(DATA / "example2_varied_syntax.txt").parse()
        self.assertEqual(variables, ["x", "y", "z"])
        self.assertEqual(
            matrix,
            [[1.0, 1.0, 1.0, 6.0], [0.0, 2.0, 5.0, -4.0], [2.0, 5.0, -1.0, 27.0]],
        )

    def test_implicit_one_and_signs(self):
        matrix, _ = parse_text("-x + y - 0.75z = 1\n+ 2x - y = -2\n")
        self.assertEqual(matrix, [[-1.0, 1.0, -0.75, 1.0], [2.0, -1.0, 0.0, -2.0]])

    def test_star_multiplication(self):
        matrix, _ = parse_text("3*x + 2 * y = 1\n")
        self.assertEqual(matrix, [[3.0, 2.0, 1.0]])

    def test_spacing_does_not_matter(self):
        self.assertEqual(parse_text("2x+3y=5\n"), parse_text("2x + 3y = 5\n"))

    def test_missing_variable_gets_zero(self):
        matrix, variables = parse_text("x + y = 1\nz = 2\nx + z = 3\n")
        self.assertEqual(variables, ["x", "y", "z"])
        self.assertEqual(matrix[1], [0.0, 0.0, 1.0, 2.0])

    def test_comments_and_blank_lines_are_skipped(self):
        matrix, _ = parse_text("# header\n\nx = 1\n   \n# end\n")
        self.assertEqual(matrix, [[1.0, 1.0]])

    def test_underscore_and_digit_names(self):
        _, variables = parse_text("price_2 + _tmp = 4\n")
        self.assertEqual(variables, ["price_2", "_tmp"])

    def test_exact_mode_returns_fractions(self):
        matrix, _ = parse_text("0.5x + y = -1.25\n", exact=True)
        self.assertEqual(matrix, [[Fraction(1, 2), Fraction(1), Fraction(-5, 4)]])


class InvalidInputTests(unittest.TestCase):
    def assert_invalid(self, text, *fragments):
        with self.assertRaises(InvalidFileFormatException) as ctx:
            parse_text(text)
        for fragment in fragments:
            self.assertIn(fragment, str(ctx.exception))

    def test_case10_missing_equals_names_line_and_text(self):
        with self.assertRaises(InvalidFileFormatException) as ctx:
            EquationParser(DATA / "case10_missing_equals.txt").parse()
        self.assertIn("Line 1", str(ctx.exception))
        self.assertIn("2x + 3y 7", str(ctx.exception))

    def test_case11_brackets(self):
        with self.assertRaises(InvalidFileFormatException):
            EquationParser(DATA / "case11_brackets.txt").parse()

    def test_case12_only_comments(self):
        with self.assertRaises(InvalidFileFormatException):
            EquationParser(DATA / "case12_only_comments.txt").parse()

    def test_case12_empty_file(self):
        self.assert_invalid("")

    def test_case13_missing_file(self):
        with self.assertRaises(FileNotFoundError) as ctx:
            EquationParser(DATA / "does_not_exist.txt").parse()
        self.assertIn("does_not_exist.txt", str(ctx.exception))

    def test_line_number_counts_comments_and_blanks(self):
        self.assert_invalid("# c\n\nx = 1\ny 2\n", "Line 4")

    def test_two_equals_signs(self):
        self.assert_invalid("x = 1 = 2\n", "Line 1", "more than one")

    def test_empty_sides(self):
        self.assert_invalid("2x + 3y =\n", "empty right side")
        self.assert_invalid("= 4\n", "empty left side")

    def test_two_operators_in_a_row(self):
        self.assert_invalid("2x + - 3y = 1\n", "two operators")

    def test_trailing_operator(self):
        self.assert_invalid("2x + = 1\n", "operator")

    def test_number_without_variable_on_left(self):
        self.assert_invalid("2x + 5 = 9\n", "no variable")

    def test_unsupported_characters(self):
        self.assert_invalid("2x / 3 = 1\n", "unsupported character")
        self.assert_invalid("x^2 = 4\n", "unsupported character")

    def test_variables_on_right_side(self):
        self.assert_invalid("x = y\n", "right side")

    def test_right_side_must_be_one_number(self):
        self.assert_invalid("x = 1 2\n", "right side")
        self.assert_invalid("x = --2\n", "right side")

    def test_invalid_term(self):
        self.assert_invalid("2x 3y = 1\n", "cannot read term")
        self.assert_invalid("x*3 = 1\n", "cannot read term")

    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(InvalidFileFormatException, PyEqSolverError))


if __name__ == "__main__":
    unittest.main()
