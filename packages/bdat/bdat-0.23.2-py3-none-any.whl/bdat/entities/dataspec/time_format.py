from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd

from bdat.entities.dataspec.unit import Unit


@dataclass
class TimeFormat(ABC):
    @abstractmethod
    def toSeconds(self, values: np.ndarray) -> np.ndarray:
        raise NotImplementedError()


@dataclass
class Seconds(TimeFormat):
    unit: Unit = Unit.BASE

    def toSeconds(self, values: np.ndarray) -> np.ndarray:
        return values * self.unit.value


@dataclass
class Timestamp(TimeFormat):
    def toSeconds(self, values: np.ndarray | pd.Timestamp) -> np.ndarray:
        if isinstance(values, pd.Timestamp):
            return np.array(values.value / 1e9)
        if isinstance(values, np.ndarray) and values.dtype == pd.Timestamp:
            values = np.array([t.value for t in values])
        return np.array([int(t) for t in values]) / 1e9


@dataclass
class Datetime(TimeFormat):
    def toSeconds(self, values: np.ndarray) -> np.ndarray:
        raise NotImplementedError()
