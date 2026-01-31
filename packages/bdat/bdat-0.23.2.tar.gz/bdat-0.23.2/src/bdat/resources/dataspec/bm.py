from bdat.entities.dataspec.charge_spec import Calculate, SeparateColumns
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec, Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Seconds


class BMDataSpec(DataSpec):
    def __init__(
        self,
        timeUnit: Unit = Unit.BASE,
        currentUnit: Unit = Unit.BASE,
        temperatureName: str | None = None,
    ):
        if temperatureName:
            temperatureColumn = ColumnSpec(temperatureName, Unit.BASE)
        else:
            temperatureColumn = None
        super().__init__(
            "bm",
            TimeColumnSpec("Programmdauer##D", Seconds(unit=timeUnit)),
            ColumnSpec("Strom#A#D", currentUnit),
            ColumnSpec("Spannung#V#D"),
            SeparateColumns(
                chargeColumn=ColumnSpec("AhLad#AhCha#D"),
                dischargeColumn=ColumnSpec("AhEla#AhDch#D"),
            ),
            # Calculate(
            #     ColumnSpec("Strom#A#D", currentUnit),
            #     TimeColumnSpec("Programmdauer##D", Seconds(unit=timeUnit)),
            # ),
            temperatureColumn,
        )
