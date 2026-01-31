import typing
from dataclasses import dataclass
from datetime import datetime

from . import legalentity, location, objectofresearch, tool
from .measurement import Measurement


@dataclass
class Size(Measurement):
    actor: "legalentity.LegalEntity"
    object: "objectofresearch.ObjectOfResearch"
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    time: "datetime | None" = None
    width: "float | None" = None
    length: "float | None" = None
    height: "float | None" = None
    diameter: "float | None" = None
