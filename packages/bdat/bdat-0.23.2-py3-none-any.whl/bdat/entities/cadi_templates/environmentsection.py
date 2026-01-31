import typing
from dataclasses import dataclass
from datetime import datetime

from . import (
    activityset,
    environmentmeasurement,
    legalentity,
    location,
    objectofresearch,
    project,
    tool,
)
from .measurement import Measurement


@dataclass
class EnvironmentSection(Measurement):
    object: "objectofresearch.ObjectOfResearch"
    actor: "legalentity.LegalEntity | None" = None
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    environment: "environmentmeasurement.EnvironmentMeasurement | None" = None
    set: "activityset.ActivitySet | None" = None
    project: "project.Project | None" = None
    start: "datetime | None" = None
    end: "datetime | None" = None
