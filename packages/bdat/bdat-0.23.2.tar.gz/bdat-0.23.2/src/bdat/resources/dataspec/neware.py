import pandas as pd

import bdat.entities as entities
from bdat.entities.dataspec.charge_spec import Calculate, ChargeSpec, SeparateColumns
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec
from bdat.entities.dataspec.data_spec import DataSpec
from bdat.entities.dataspec.time_format import Timestamp


class NewareAhjoDataSpec(DataSpec):
    def __init__(self, test: entities.Cycling, df: pd.DataFrame):
        # TODO: check if temperature column exists in aux data
        timeName = None
        currentName = None
        voltageName = None
        chargeName = None
        dischargeName = None
        for col in df.columns:
            if col.startswith("Time##T"):
                timeName = col
            elif col == "test_atime":
                timeName = col
            elif col.startswith("Current#A#D"):
                currentName = col
            elif col == "test_cur":
                currentName = col
            elif col.startswith("Voltage#V#D"):
                voltageName = col
            elif col == "test_vol":
                voltageName = col
            elif col.startswith("Charge Capacity#Ah#D"):
                chargeName = col
            elif col.startswith("Discharge Capacity#Ah#D"):
                dischargeName = col
        if not (timeName and currentName and voltageName):
            raise RuntimeError("Could not find Neware column names")
        timeColumn = TimeColumnSpec(timeName, Timestamp())
        currentColumn = ColumnSpec(currentName)
        voltageColumn = ColumnSpec(voltageName)
        if chargeName and dischargeName:
            chargeColumn: ChargeSpec = SeparateColumns(
                ColumnSpec(chargeName), ColumnSpec(dischargeName)
            )
        else:
            chargeColumn = Calculate(currentColumn, timeColumn)
        super().__init__(
            "neware_ahjo",
            timeColumn,
            currentColumn,
            voltageColumn,
            chargeColumn,
        )
