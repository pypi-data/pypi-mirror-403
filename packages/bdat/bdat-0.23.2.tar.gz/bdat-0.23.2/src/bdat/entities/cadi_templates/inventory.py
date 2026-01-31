import typing
from dataclasses import dataclass

from . import legalentity, location, measurement, objectofresearch, tool
from .measurement import Measurement


@dataclass
class Inventory(Measurement):
    actor: "legalentity.LegalEntity"
    object: "objectofresearch.ObjectOfResearch"
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    measurement: "measurement.Measurement | None" = None
