import typing
from dataclasses import dataclass, field

from bdat.database.storage.entity import Filetype, file
from bdat.entities.group.group import Group
from bdat.entities.patterns import PatternEval, TestEval


@dataclass
@file("evaldata", "evaldata", Filetype.PICKLE)
class EvalGroup(Group):
    evals: "typing.List[TestEval]" = field(default_factory=list)
    evaldata: "typing.List[PatternEval]" = field(default_factory=list)
    evaltype: str | None = None

    def __iter__(self):
        return self.evaldata.__iter__()
