import typing
from dataclasses import dataclass

from . import project
from .managemententity import ManagementEntity


@dataclass
class ActivitySet(ManagementEntity):
    project: "project.Project"
