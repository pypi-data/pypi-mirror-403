from enum import Enum

import numpy as np
from typing_extensions import Self


class Unit(Enum):
    DECA = 1e1
    BASE = 1
    DECI = 1e-1
    MILLI = 1e-3

    def convert(self, values: np.ndarray, target: Self) -> np.ndarray:
        return values * self.value / target.value
