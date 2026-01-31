import typing
from dataclasses import dataclass

from . import project, typeofobject
from .entity import Entity


@dataclass
class ObjectOfResearch(Entity):
    project: "project.Project | None" = None
    type: "typeofobject.TypeOfObject | None" = None
