import typing
from dataclasses import dataclass

from . import legalentity, location, objectofresearch, tool
from .activity import Activity


@dataclass
class Measurement(Activity):
    actor: "legalentity.LegalEntity | None" = None
    tool: "tool.Tool | None" = None
    location: "location.Location | None" = None
    object: "objectofresearch.ObjectOfResearch | None" = None
