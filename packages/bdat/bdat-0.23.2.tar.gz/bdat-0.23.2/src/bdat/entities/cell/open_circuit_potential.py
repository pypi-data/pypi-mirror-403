import typing
from dataclasses import dataclass

import pandas as pd

from bdat.database.storage.entity import Entity, Filetype, file


@dataclass
@file("data", "data", Filetype.CSV)
class OpenCircuitPotential(Entity):
    data: pd.DataFrame
