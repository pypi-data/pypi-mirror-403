import typing
from dataclasses import dataclass

from bdat.database.storage.entity import Filetype, file, identifier
from bdat.entities.aging.cell_life import CellLife
from bdat.entities.aging.testmatrix import Testmatrix
from bdat.entities.data_processing import DataProcessing


@dataclass
@file("plotdata", "plotdata_{key}", Filetype.JSON, explode=True)
@identifier("bdat-agingdata-{title}")
class AgingData(DataProcessing):
    data: typing.List[CellLife]
    plotdata: typing.Dict[str, typing.List[typing.Dict]] | None = None
    testmatrix: Testmatrix | None = None
    doi: str | typing.List[str] | None = None
