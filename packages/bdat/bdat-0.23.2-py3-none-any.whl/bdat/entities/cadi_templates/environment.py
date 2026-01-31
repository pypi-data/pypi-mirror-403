import typing
from dataclasses import dataclass
from datetime import datetime

from . import legalentity, location, objectofresearch, tool
from .measurement import Measurement


@dataclass
class Environment(Measurement):
    actor: "legalentity.LegalEntity"
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    object: "objectofresearch.ObjectOfResearch | None" = None
    start: "datetime | None" = None
    end: "datetime | None" = None
