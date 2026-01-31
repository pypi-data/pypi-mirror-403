import typing
from dataclasses import dataclass
from datetime import datetime

from .managemententity import ManagementEntity


@dataclass
class Project(ManagementEntity):
    status: "str | None" = None
    start: "datetime | None" = None
    end: "datetime | None" = None
