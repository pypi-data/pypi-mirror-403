from bdat.entities.dataspec.charge_spec import Calculate
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec, Unit
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Seconds

DefaultTargetSpec = DataSpec(
    "normalized",
    TimeColumnSpec("Duration", Seconds()),
    ColumnSpec("Current", Unit.BASE),
    ColumnSpec("Voltage", Unit.BASE),
    Calculate(ColumnSpec("Current", Unit.BASE), TimeColumnSpec("Duration", Seconds())),
)
