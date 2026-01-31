import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Embedded, Filetype, file, identifier
from bdat.entities.aging.aging_conditions import AgingConditions
from bdat.entities.cadi_templates import Battery, Project
from bdat.entities.data_processing import DataProcessing


@dataclass
class TestmatrixEntry(Embedded):
    battery: Battery
    conditions: typing.List[AgingConditions]


@dataclass
@identifier("bdat-testmatrix-{title}")
@file("entries", "entries", Filetype.JSON)
class Testmatrix(DataProcessing):
    project: Project
    entries: typing.List[TestmatrixEntry]
