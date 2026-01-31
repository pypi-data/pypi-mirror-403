import typing
from dataclasses import dataclass

import bdat.database.storage.entity


@dataclass
class Entity(bdat.database.storage.entity.Entity):
    title: "str"
