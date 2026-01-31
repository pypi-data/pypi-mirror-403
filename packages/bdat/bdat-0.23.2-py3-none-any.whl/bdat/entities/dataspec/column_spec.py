from dataclasses import dataclass

import numpy as np
import pandas as pd
from typing_extensions import Self

from bdat.entities.dataspec.time_format import Seconds, TimeFormat
from bdat.entities.dataspec.unit import Unit


@dataclass
class ColumnSpec:
    name: str
    unit: Unit = Unit.BASE

    def convert(self, values: np.ndarray, target: Self) -> np.ndarray:
        return self.unit.convert(values, target.unit)

    def from_df(self, df: pd.DataFrame, unit: Unit | None) -> np.ndarray:
        values = df[self.name].to_numpy(dtype=np.float64)
        if unit is not None:
            values = self.unit.convert(values, unit)
        return values


@dataclass
class TimeColumnSpec:
    name: str
    timeFormat: TimeFormat

    def convert(self, values: np.ndarray, target: Self) -> np.ndarray:
        if not isinstance(target.timeFormat, Seconds):
            raise NotImplementedError()
        return self.timeFormat.toSeconds(values)
