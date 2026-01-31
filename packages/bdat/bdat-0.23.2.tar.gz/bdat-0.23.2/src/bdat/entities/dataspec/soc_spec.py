from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
import pandas as pd
from typing_extensions import Self

from bdat.entities.dataspec.charge_spec import ChargeSpec
from bdat.entities.dataspec.time_format import Seconds, TimeFormat
from bdat.entities.dataspec.unit import Unit


@dataclass
class SocSpec(ABC):
    chargeSpec: ChargeSpec
    capacity: float

    @abstractmethod
    def calculate(self, df: pd.DataFrame, initialSoc: float) -> np.ndarray:
        raise NotImplementedError()


@dataclass
class CoulombCounting(SocSpec):
    def calculate(self, df: pd.DataFrame, initialSoc: float) -> np.ndarray:
        soc = initialSoc + self.chargeSpec.getDiffAh(df) / self.capacity * 100
        return soc
