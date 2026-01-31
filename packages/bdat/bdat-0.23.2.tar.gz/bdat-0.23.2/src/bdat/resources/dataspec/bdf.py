import pandas as pd

from bdat.entities.dataspec.charge_spec import Calculate, SeparateColumns
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec, Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Seconds


class BDFDataSpec(DataSpec):
    def __init__(
        self,
        df: pd.DataFrame,
        timeUnit: Unit = Unit.BASE,
        currentUnit: Unit = Unit.BASE,
    ):
        duration = TimeColumnSpec("Test Time / s", Seconds(unit=timeUnit))
        current = ColumnSpec("Current / A", currentUnit)
        super().__init__(
            "bdf",
            duration,
            current,
            ColumnSpec("Voltage / V"),
            Calculate(current, duration),
        )
