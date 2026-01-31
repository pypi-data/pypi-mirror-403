import typing
from dataclasses import dataclass, field

import bdat.entities as entities
from bdat.entities.group import Group


@dataclass
class TestGroup(Group):
    tests: typing.List["entities.Cycling"] = field(default_factory=list)
