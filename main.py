"""main file: parse, solve and export a linear system"""

import sys
from pyeqsolver import EquationParser, GaussianSolver, JSONExporter
from pyeqsolver.exceptions import PyEqSolverError


def main():
    input_file = "data/input_equations.txt"   #data/error_infinite.txt   #tests/data/case10_missing_equals.txt
    output_file = "data/solution.json"
    precision = 4
    exact = False

    exporter = JSONExporter( output_path=output_file, precision=precision)

    try:
        parser = EquationParser( file_path=input_file, exact=exact)

        matrix, variables = parser.parse()

        solver = GaussianSolver(matrix=matrix, variables=variables, exact=exact)

        solutions = solver.solve()

        exporter.save(solutions=solutions,  metadata=solver.get_metadata())

        print(f"Solved. Results written to {output_file}")
        return 0

    except (PyEqSolverError, FileNotFoundError) as e:
        exporter.save_error(e)
        print(f"Could not solve the system: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())