import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Filetype, file, identifier
from bdat.entities.aging.aging_conditions import AgingConditions
from bdat.entities.aging.testmatrix import Testmatrix
from bdat.entities.cadi_templates import Battery
from bdat.entities.data_processing import DataProcessing
from bdat.entities.patterns import DischargeCapacityEval, PulseEval
from bdat.entities.patterns.test_eval import TestEval


@dataclass
@identifier("bdat-celllife-{battery.id}")
@file("conditions", "conditions", Filetype.JSON)
@file("capacity", "capacity", Filetype.JSON)
@file("resistance", "resistance", Filetype.JSON)
@file("plotdata", "plotdata_{key}", Filetype.JSON, explode=True)
class CellLife(DataProcessing):
    battery: Battery
    conditions: typing.List[AgingConditions]
    capacity: typing.List[DischargeCapacityEval]
    resistance: typing.List[PulseEval]
    evals: typing.List[TestEval]
    testmatrix: Testmatrix | None = None
    plotdata: typing.Dict[str, typing.List[typing.Dict]] | None = None
