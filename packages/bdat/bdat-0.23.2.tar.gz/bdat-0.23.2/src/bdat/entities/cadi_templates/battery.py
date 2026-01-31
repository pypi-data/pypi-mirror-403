import typing
from dataclasses import dataclass
from datetime import datetime

from . import batteryspecies, person, project
from .objectofresearch import ObjectOfResearch


@dataclass
class Battery(ObjectOfResearch):
    project: "project.Project | None" = None
    type: "batteryspecies.BatterySpecies | None" = None
    inventoryUser: "person.Person | None" = None
    properties: "typing.Dict[str, typing.Any] | None" = None
    inventoryDate: "datetime | None" = None
