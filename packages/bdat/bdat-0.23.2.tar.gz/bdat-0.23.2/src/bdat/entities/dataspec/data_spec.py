from dataclasses import dataclass

import pandas as pd

from bdat.database.storage.entity import Entity
from bdat.entities.dataspec.charge_spec import ChargeSpec
from bdat.entities.dataspec.column_spec import ColumnSpec, TimeColumnSpec
from bdat.entities.dataspec.soc_spec import SocSpec


@dataclass
class DataSpec(Entity[str]):
    id: str
    durationColumn: TimeColumnSpec
    currentColumn: ColumnSpec
    voltageColumn: ColumnSpec
    chargeSpec: ChargeSpec
    # socSpec: SocSpec
    temperatureColumn: ColumnSpec | None = None

    def tryOnTest(self, testdata: pd.DataFrame) -> bool:
        if not self.durationColumn.name in testdata.columns:
            # print(f"Missing {self.durationColumn.name}")
            return False
        if not self.currentColumn.name in testdata.columns:
            # print(f"Missing {self.currentColumn.name}")
            return False
        if not self.voltageColumn.name in testdata.columns:
            # print(f"Missing {self.voltageColumn.name}")
            return False
        if not all([c.name in testdata.columns for c in self.chargeSpec.getColumns()]):
            # print(f"Missing {[c.name for c in self.chargeSpec.getColumns()]}")
            return False
        if (
            self.temperatureColumn
            and not self.temperatureColumn.name in testdata.columns
        ):
            # print(f"Missing {self.temperatureColumn.name}")
            return False
        return True
