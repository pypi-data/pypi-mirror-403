import typing
from dataclasses import dataclass

import bdat.entities.patterns.pattern_eval as pattern_eval
from bdat.database.storage.entity import Filetype, file, identifier
from bdat.entities.cadi_templates import Cycling
from bdat.entities.data_processing import DataProcessing
from bdat.entities.steps.steplist import Steplist


@identifier("bdat-testeval-{test.id}")
@file("evals", "evals", Filetype.PICKLE)
@file("plotdata", "plotdata_{key}", Filetype.JSON, explode=True)
@dataclass
class TestEval(DataProcessing):
    """Base class for all eval results"""

    test: Cycling
    steps: Steplist
    evals: "typing.List[pattern_eval.PatternEval]"
    plotdata: typing.Dict[str, typing.List[typing.Dict]] | None = None
    previous: "TestEval | None" = None

    def __iter__(self):
        return self.evals.__iter__()
