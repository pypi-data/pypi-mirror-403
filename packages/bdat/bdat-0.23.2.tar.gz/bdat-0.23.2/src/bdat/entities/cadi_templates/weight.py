import typing
from dataclasses import dataclass
from datetime import datetime

from . import legalentity, location, objectofresearch, tool
from .measurement import Measurement


@dataclass
class Weight(Measurement):
    actor: "legalentity.LegalEntity"
    object: "objectofresearch.ObjectOfResearch"
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    time: "datetime | None" = None
    weight: "float | None" = None
