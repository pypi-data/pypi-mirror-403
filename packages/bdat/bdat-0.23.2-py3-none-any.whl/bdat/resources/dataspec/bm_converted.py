import pandas as pd

from bdat.entities.dataspec.charge_spec import Calculate, SeparateColumns
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec, Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Seconds


class BMConvertedDataSpec(DataSpec):
    def __init__(
        self,
        df: pd.DataFrame,
        timeUnit: Unit = Unit.BASE,
        currentUnit: Unit = Unit.BASE,
        temperatureName: str | None = None,
    ):
        if temperatureName:
            temperatureColumn = ColumnSpec(temperatureName, Unit.BASE)
        else:
            temperatureColumn = None
        if "Program Duration#s" in df.columns:
            timeUnit = Unit.BASE
            timeColumn = "Program Duration#s"
        else:
            timeUnit = Unit.MILLI
            timeColumn = "Program Duration#ms"
        super().__init__(
            "bm",
            TimeColumnSpec(timeColumn, Seconds(unit=timeUnit)),
            ColumnSpec("Current#A", currentUnit),
            ColumnSpec("Voltage#V"),
            SeparateColumns(
                chargeColumn=ColumnSpec(
                    "AhCha#AH" if "AhCha#AH" in df.columns else "AhCha#Ah"
                ),
                dischargeColumn=ColumnSpec("AhDch#Ah"),
            ),
            temperatureColumn,
        )
