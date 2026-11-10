# PyEqSolver

Solve a system of linear equations from a text file with a hand-written
**Gaussian Elimination**, and save the result as JSON. Pure Python 3.10+ and
the standard library only (no `pip install`; `requirements.txt` is not needed).

## Run it

```bash
python main.py
# reads data/input_equations.txt, writes data/solution.json
```

Options (CLI bonus):

```bash
python main.py --input data/example2_varied_syntax.txt --output data/results.json --precision 6
python main.py --input my_eqs.txt --exact      # answers as fractions, e.g. "1/3"
```

The exit code is `0` on success and `1` on any error. In both cases the
output file is written (`status: SUCCESS` or `status: ERROR`).

## Run the tests

```bash
python -m unittest discover -s tests -v
```

The 13 required cases live in `tests/data/` (case 13, a missing path, needs
no file). Extra tests cover the exporter, the solver's edge cases and the
parser's error messages.

## Input format

One equation per line, variables on the left, a single number on the right.

```
# comment lines and blank lines are skipped
10x1 + 5x2 = 5
2y+5z=-4
2*x + 5y - z = 27
```

- Variable names: a letter or `_`, then letters, digits or `_`.
- Order of the variables = order of first appearance in the file.
- Coefficients: integers or decimals, signed; `x` means 1, `-x` means -1,
  `3*x` is allowed; spaces are optional.
- A variable missing from an equation gets coefficient 0; a repeated variable
  is added (`2x + 3x = 10` is `5x = 10`).
- Invalid lines raise `InvalidFileFormatException` with the line number and
  the text: no or several `=`, an empty side, characters other than
  digits/letters/`_`/`.`/`+`/`-`/`*`/`=`/space (brackets included), two
  operators in a row, or a bare number on the left side.

## Output format

Success:

```json
{
  "status": "SUCCESS",
  "system_info": {"num_variables": 3, "num_equations": 3},
  "solution": {"x1": 0.0, "x2": 1.0, "x3": 2.0}
}
```

Error (`error_type` is the exception class name):

```json
{
  "status": "ERROR",
  "error_type": "InconsistentSystemException",
  "message": "The system has no solution (row reduces to 0 = 1)"
}
```

Values are rounded (4 places by default) and `-0.0` is written as `0.0`.

## Project layout

```
pyeqsolver/
  exceptions.py   PyEqSolverError + 4 subclasses
  parser.py       EquationParser   (file -> [A | b] + variable names)
  solver.py       GaussianSolver   (elimination, rank check, back substitution)
  exporter.py     JSONExporter     (rounding, -0.0 clean-up, JSON files)
main.py           CLI entry point (the only place that prints)
tests/            unittest tests + tests/data/ input files
data/             sample inputs: one success case, one per error type
```

## How errors are detected

The solver first checks that there are at least as many equations as
variables (otherwise `DimensionMismatchException`, before any elimination).
It then reduces the matrix to row echelon form, treating anything with an
absolute value below `1e-9` as zero so floating-point noise such as
`0.1 + 0.2 - 0.3` cannot create a fake pivot. After elimination, a row whose
coefficients are all zero but whose constant is not means `0 = c`, so no
solution exists (`InconsistentSystemException`). If no such row exists, the
number of non-zero rows is the rank: a rank smaller than the number of
variables leaves free variables and therefore infinitely many solutions
(`InfiniteSolutionsException`). Otherwise every column has a pivot and back
substitution gives the unique answer; extra consistent equations just reduce
to all-zero rows and are ignored.

## Bonuses implemented

- **Partial pivoting.** In every column the row with the largest absolute
  entry is swapped up. This also handles the mandatory zero-pivot swap.
  For `0.00000001x + y = 1`, `x + y = 2` the raw floats are:

  | Method | x | y |
  | --- | --- | --- |
  | Without pivoting (first row as pivot) | 1.0000000050247593 | 0.99999999 |
  | With partial pivoting (this project) | 1.00000001 | 0.99999999 |

  The exact answer is x = 1 / 0.99999999 ≈ 1.00000001.
- **CLI.** `--input`, `--output`, `--precision` via `argparse`.
- **Exact arithmetic.** `--exact` runs the same algorithm on
  `fractions.Fraction` values and writes strings such as `"1/3"`.

Not implemented: free-form equations (variables or constants on both sides).
