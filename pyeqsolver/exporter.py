"""Write solver results (or errors) to a JSON file."""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Mapping, Union


Number = Union[float, Fraction]

class JSONExporter:
    """saves a success or error report as JSON"""

    def __init__(self, output_path: str | Path, precision: int = 4) -> None:
        self.output_path = Path(output_path)
        self.precision = precision

    def save( self, solutions: Mapping[str, Number], metadata: Mapping[str, int], ) -> None:
        """save the solution and system information"""

        payload = {
            "status": "SUCCESS",
            "system_info": dict(metadata),
            "solution": {},
        }

        for name, value in solutions.items():
            payload["solution"][name] = self._clean(value)

        self._write(payload)

    def save_error(self, exc: BaseException) -> None:
        """save information about an error """

        payload = {
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "message": str(exc),
        }

        self._write(payload)

    def _clean(self, value: Number) -> Any:
        """round numbers and avoid writing -0.0 """

        # keep exact fractions as text, such as "1/3"
        if isinstance(value, Fraction):
            return str(value)

        rounded = round(float(value), self.precision)   # for float numbers, rounded to 4 precision
        if rounded == 0:   # convert -0.0 or 0.0 to 0.0
            return 0.0
        return rounded

    def _write(self, payload: dict[str, Any]) -> None:
        """create the output folder and write the JSON file """

        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with self.output_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")