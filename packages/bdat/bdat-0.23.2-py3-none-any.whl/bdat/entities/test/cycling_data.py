import numpy as np
import pandas as pd

import bdat.entities as entities
from bdat.entities.cadi_templates import Cycling
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.unit import Unit


class CyclingData:
    test: Cycling
    df: pd.DataFrame
    dataSpec: DataSpec

    time: np.ndarray  # time as unix timestamp in seconds
    current: np.ndarray  # current in Ampere
    voltage: np.ndarray  # voltage in Volt
    charge: np.ndarray  # cumulative sum of charge over all tests for this battery in Ah
    discharge: (
        np.ndarray
    )  # cumulative sum of discharge over all tests for this battery in Ah
    diffcharge: np.ndarray  # difference between charge and discharge in Ah
    soc: np.ndarray  # SOC in percent (from 0 to 100) or NaN
    temperature: np.ndarray | None  # temperature in degrees Celsius
    age: np.ndarray | None  # total age of the battery in seconds
    power: np.ndarray  # power in Watt

    def __init__(
        self,
        test: Cycling,
        df: pd.DataFrame,
        dataSpec: DataSpec,
        initialCharge: float = 0,
        initialDischarge: float = 0,
        initialSoc: float | None = None,
    ):
        self.__sort_df(df, dataSpec)

        self.test = test
        self.df = df
        self.dataSpec = dataSpec

        self.time = dataSpec.durationColumn.timeFormat.toSeconds(
            df[dataSpec.durationColumn.name].to_numpy()
        )
        self.current = dataSpec.currentColumn.from_df(df, Unit.BASE)
        self.voltage = dataSpec.voltageColumn.from_df(df, Unit.BASE)
        self.charge = dataSpec.chargeSpec.getChargeAh(df) + initialCharge
        self.discharge = dataSpec.chargeSpec.getDischargeAh(df) + initialDischarge
        self.diffcharge = self.charge - self.discharge
        if dataSpec.temperatureColumn is not None:
            self.temperature = dataSpec.temperatureColumn.from_df(df, Unit.BASE)
        else:
            self.temperature = None
        # if initialSoc is None:
        #     self.soc = np.full(self.time.shape, np.nan)
        # else:
        #     self.soc = dataSpec.socSpec.calculate(df, initialSoc)
        self.soc = np.full(self.time.shape, np.nan)
        self.power = self.current * self.voltage

    def __sort_df(self, df: pd.DataFrame, dataSpec: DataSpec):
        t = dataSpec.durationColumn.timeFormat.toSeconds(
            df[dataSpec.durationColumn.name].to_numpy()
        )
        current = df[dataSpec.currentColumn.name].to_numpy()
        dupes = np.nonzero(np.diff(t) == 0)
        for idx in dupes[0]:
            if idx < 1 or idx > len(df) - 3:
                continue
            if np.abs(current[idx] - current[idx - 1]) > np.abs(
                current[idx] - current[idx + 2]
            ) and np.abs(current[idx + 1] - current[idx + 2]) > np.abs(
                current[idx + 1] - current[idx - 1]
            ):
                temp = df.iloc[idx].copy()
                df.iloc[idx] = df.iloc[idx + 1]
                df.iloc[idx + 1] = temp
