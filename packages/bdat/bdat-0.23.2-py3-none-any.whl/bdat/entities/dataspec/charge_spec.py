from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

import numpy as np
import pandas as pd

from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec
from bdat.entities.dataspec.unit import Unit


@dataclass
class ChargeSpec(ABC):
    @abstractmethod
    def getChargeAh(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError()

    @abstractmethod
    def getDischargeAh(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError()

    @abstractmethod
    def getDiffAh(self, df: pd.DataFrame) -> np.ndarray:
        raise NotImplementedError()

    @abstractmethod
    def getColumns(self) -> List[ColumnSpec | TimeColumnSpec]:
        raise NotImplementedError()


@dataclass
class SeparateColumns(ChargeSpec):
    chargeColumn: ColumnSpec
    dischargeColumn: ColumnSpec

    def getChargeAh(self, df: pd.DataFrame) -> np.ndarray:
        charge = np.diff(
            df[self.chargeColumn.name].to_numpy(dtype=np.float64), prepend=0
        )
        charge[charge < 0] = 0
        return self.chargeColumn.unit.convert(np.cumsum(charge), Unit.BASE)

    def getDischargeAh(self, df: pd.DataFrame) -> np.ndarray:
        charge = np.diff(
            df[self.dischargeColumn.name].to_numpy(dtype=np.float64), prepend=0
        )
        charge[charge < 0] = 0
        return self.dischargeColumn.unit.convert(np.cumsum(charge), Unit.BASE)

    def getDiffAh(self, df: pd.DataFrame) -> np.ndarray:
        return self.getChargeAh(df) - self.getDischargeAh(df)

    def getColumns(self) -> List[ColumnSpec | TimeColumnSpec]:
        return [self.chargeColumn, self.dischargeColumn]


@dataclass
class Calculate(ChargeSpec):
    currentColumn: ColumnSpec
    durationColumn: TimeColumnSpec

    def getChargeAh(self, df: pd.DataFrame) -> np.ndarray:
        charge = self._getChargeValues(df)
        charge[charge < 0] = 0
        return np.cumsum(charge)

    def getDischargeAh(self, df: pd.DataFrame) -> np.ndarray:
        charge = self._getChargeValues(df)
        charge[charge > 0] = 0
        return -np.cumsum(charge)

    def getDiffAh(self, df: pd.DataFrame) -> np.ndarray:
        return np.cumsum(self._getChargeValues(df))

    def getColumns(self) -> List[ColumnSpec | TimeColumnSpec]:
        return [self.currentColumn, self.durationColumn]

    def _getChargeValues(self, df: pd.DataFrame) -> np.ndarray:
        current = self.currentColumn.unit.convert(
            df[self.currentColumn.name].to_numpy(dtype=np.float64), Unit.BASE
        )
        dt = (
            np.diff(
                self.durationColumn.timeFormat.toSeconds(
                    df[self.durationColumn.name].to_numpy()
                ),
                prepend=0,
            ),
        )
        return current * dt / 3600
