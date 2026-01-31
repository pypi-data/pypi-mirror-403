import typing
from dataclasses import dataclass
from datetime import datetime

from . import (
    activityset,
    battery,
    cyclercircuit,
    environmentsection,
    legalentity,
    location,
    project,
)
from .measurement import Measurement


@dataclass
class Cycling(Measurement):
    object: "battery.Battery"
    actor: "legalentity.LegalEntity | None" = None
    tool: "cyclercircuit.CyclerCircuit | None" = None
    location: "location.Location | None" = None
    set: "activityset.ActivitySet | None" = None
    project: "project.Project | None" = None
    parent: "Cycling | None" = None
    environmentSection: "environmentsection.EnvironmentSection | None" = None
    start: "datetime | None" = None
    end: "datetime | None" = None
